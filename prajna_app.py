
import streamlit as st
from neo4j import GraphDatabase
from groq import Groq
from pyvis.network import Network
import streamlit.components.v1 as components
import os, json, pandas as pd
from collections import defaultdict
from datetime import datetime, timezone

# ── Connections ──
NEO4J_URI      = os.environ.get("NEO4J_URI")      or st.secrets.get("NEO4J_URI")
NEO4J_USERNAME = os.environ.get("NEO4J_USERNAME") or st.secrets.get("NEO4J_USERNAME")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD") or st.secrets.get("NEO4J_PASSWORD")
GROQ_API_KEY   = os.environ.get("GROQ_API_KEY")   or st.secrets.get("GROQ_API_KEY")

LOGO_B64 = "{LOGO_B64}"

@st.cache_resource
def get_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

@st.cache_resource
def get_groq():
    return Groq(api_key=GROQ_API_KEY)

driver      = get_driver()
groq_client = get_groq()

def get_week_key():
    now = datetime.now(timezone.utc)
    return f"{{now.year}}-W{{now.strftime('%W')}}"

def ask_groq(prompt):
    r = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{{"role": "user", "content": prompt}}],
        max_tokens=600, temperature=0.3
    )
    return r.choices[0].message.content

@st.cache_data(ttl=300)
def get_stats():
    with driver.session() as session:
        a = session.run("MATCH (a:Article) RETURN count(a) as c").single()["c"]
        e = session.run("MATCH (e:Entity)  RETURN count(e) as c").single()["c"]
        r = session.run("MATCH ()-[r:CO_OCCURS_WITH]->() RETURN count(r) as c").single()["c"]
    return a, e, r

@st.cache_data(ttl=300)
def get_available_weeks():
    with driver.session() as session:
        result = session.run("""
            MATCH (a:Article)
            RETURN DISTINCT a.week as week
            ORDER BY week DESC
        """).data()
    return [r["week"] for r in result if r["week"]]

def get_graph_context(keywords):
    with driver.session() as session:
        result = session.run("""
            MATCH (e:Entity)-[r:CO_OCCURS_WITH]-(other:Entity)
            WHERE any(kw IN $kw WHERE toLower(e.name) CONTAINS toLower(kw))
            RETURN e.name AS e1, other.name AS e2, r.count AS strength
            ORDER BY r.count DESC LIMIT 20
        """, {{"kw": keywords}})
        return [(r["e1"], r["e2"], r["strength"]) for r in result]

def get_articles(keywords):
    with driver.session() as session:
        result = session.run("""
            MATCH (a:Article)-[:MENTIONS]->(e:Entity)
            WHERE any(kw IN $kw WHERE toLower(e.name) CONTAINS toLower(kw))
            RETURN DISTINCT a.title AS title, a.source AS source LIMIT 5
        """, {{"kw": keywords}})
        return [(r["title"], r["source"]) for r in result]

def get_trajectory(e1, e2):
    import re as _re
    with driver.session() as session:
        rows = session.run("""
            MATCH (a:Article)-[:MENTIONS]->(x:Entity {name:$e1})
            MATCH (a)-[:MENTIONS]->(y:Entity {name:$e2})
            WHERE a.week IS NOT NULL
            RETURN a.week AS week, COUNT(a) AS cnt
            ORDER BY week
        """, {"e1": e1, "e2": e2}).data()
    if not rows:
        with driver.session() as session:
            result = session.run("""
                MATCH (a:Entity {name:$e1})-[r:CO_OCCURS_WITH]-(b:Entity {name:$e2})
                RETURN r.weekly_counts_json AS wcj, r.count AS total
            """, {"e1": e1, "e2": e2}).single()
        if not result or not result["wcj"]:
            return None, None
        try:
            wc = json.loads(result["wcj"])
        except:
            pairs = _re.findall('"(2026-W\d+)"\s*:\s*(\d+)', result["wcj"])
            wc = {k: int(v) for k,v in pairs}
        if not wc:
            return None, None
        return sorted(wc.items()), result["total"]
    wc = {r["week"]: r["cnt"] for r in rows}
    total = sum(wc.values())
    return sorted(wc.items()), total

def find_path(e1, e2):
    with driver.session() as session:
        result = session.run("""
            MATCH path = shortestPath(
                (a:Entity {{name:$e1}})-[:CO_OCCURS_WITH*1..4]-(b:Entity {{name:$e2}})
            )
            RETURN [node IN nodes(path) | node.name] AS nodes,
                   [rel IN relationships(path) | rel.count] AS strengths,
                   length(path) AS hops
        """, {{"e1": e1, "e2": e2}}).single()
    if not result:
        return None
    return {{"nodes": result["nodes"], "strengths": result["strengths"], "hops": result["hops"]}}

BLOCKLIST = {{
    "Supreme","Asian","Islam","American","European","Western","Eastern",
    "BBC","CNN","Reuters","Bloomberg","NDTV","Mint","Hindu","Express",
    "ANI","PTI","AFP","AP","Wire","Tribune","Times","Globe","Newswire"
}}

def detect_surges(threshold=1.5, top_n=5):
    week_key = get_week_key()
    with driver.session() as session:
        results = session.run("""
            MATCH (a:Article)-[:MENTIONS]->(e:Entity)
            WHERE a.week IS NOT NULL
            AND e.type IN ["GPE","ORG","PERSON","NORP"]
            RETURN e.name AS entity, e.type AS type,
                   a.week AS week, COUNT(a) AS cnt
        """).data()

    entity_weekly = defaultdict(lambda: defaultdict(int))
    entity_type   = {}
    for row in results:
        e = row["entity"]
        entity_type[e] = row["type"]
        entity_weekly[e][row["week"]] += row["cnt"]

    entity_total = {e: sum(w.values()) for e, w in entity_weekly.items()}

    surges = []
    for entity, weekly in entity_weekly.items():
        if entity in BLOCKLIST:                                      continue
        if entity_total[entity] < 8:                                 continue
        if len(entity) > 35:                                         continue
        if any(c.isdigit() for c in entity):                         continue
        if entity_type.get(entity) not in {{"GPE","ORG","PERSON","NORP"}}: continue
        weeks = sorted(weekly.keys())
        if not weeks or weeks[-1] != week_key:                       continue
        latest   = weekly[weeks[-1]]
        hist     = [weekly[w] for w in weeks[:-1]]
        baseline = sum(hist)/len(hist) if hist else entity_total[entity]/2
        if baseline == 0: continue
        ratio = latest / baseline
        if ratio >= threshold:
            surges.append({{
                "entity":   entity,
                "type":     entity_type.get(entity, ""),
                "latest":   latest,
                "baseline": round(baseline, 1),
                "ratio":    round(ratio, 2),
                "total":    entity_total[entity]
            }})
    surges.sort(key=lambda x: x["ratio"], reverse=True)
    return surges[:top_n]

def build_graph_visual(keyword=None, week=None):
    TYPE_COLORS = {{
        "GPE":    "#C8A96E",
        "ORG":    "#6B8CAE",
        "PERSON": "#A8C5A0",
        "NORP":   "#B8956A",
        "LOC":    "#8AABBA",
        "EVENT":  "#C47B6E"
    }}
    import re as _re
    def _parse_wcj(s):
        if not s: return {{}}
        try: return json.loads(s)
        except:
            pairs = _re.findall(r'"(2026-W\d+)"\s*:\s*(\d+)', s)
            return {{k: int(v) for k,v in pairs}}

    with driver.session() as session:
        if week:
            if keyword:
                res = session.run("""
                    MATCH (a:Article {{week:$week}})-[:MENTIONS]->(e:Entity)
                    WHERE toLower(e.name) CONTAINS $kw
                    WITH COLLECT(DISTINCT e) AS seed
                    UNWIND seed AS e
                    MATCH (e)-[:CO_OCCURS_WITH]-(other:Entity)
                    WITH COLLECT(DISTINCT e)+COLLECT(DISTINCT other) AS nl
                    UNWIND nl AS node WITH DISTINCT node
                    MATCH (node)-[r:CO_OCCURS_WITH]-()
                    WHERE r.weekly_counts_json CONTAINS $week
                    WITH node, COUNT(r) AS conn
                    ORDER BY conn DESC LIMIT 40
                    RETURN node.name AS name, node.type AS type, conn
                """, {{"week": week, "kw": keyword.lower()}})
            else:
                res = session.run("""
                    MATCH (a:Article {{week:$week}})-[:MENTIONS]->(e:Entity)
                    WITH DISTINCT e
                    MATCH (e)-[r:CO_OCCURS_WITH]-()
                    WHERE r.weekly_counts_json CONTAINS $week
                    WITH e, COUNT(r) AS conn
                    ORDER BY conn DESC LIMIT 40
                    RETURN e.name AS name, e.type AS type, conn
                """, {{"week": week}})
        else:
            if keyword:
                res = session.run("""
                    MATCH (e:Entity) WHERE toLower(e.name) CONTAINS $kw
                    WITH e MATCH (e)-[:CO_OCCURS_WITH]-(other:Entity)
                    WITH collect(DISTINCT e)+collect(DISTINCT other) AS nl
                    UNWIND nl AS node WITH DISTINCT node
                    WITH node, COUNT{{(node)--()}} AS conn
                    ORDER BY conn DESC LIMIT 40
                    RETURN node.name AS name, node.type AS type, conn
                """, {{"kw": keyword.lower()}})
            else:
                res = session.run("""
                    MATCH (e:Entity)
                    WITH e, COUNT{{(e)--()}} AS conn
                    ORDER BY conn DESC LIMIT 40
                    RETURN e.name AS name, e.type AS type, conn
                """)
        top = {{r["name"]: r for r in res}}

        # ── Get edges — use weekly counts if week selected ──
        if week:
            rels = session.run("""
                MATCH (e1:Entity)-[r:CO_OCCURS_WITH]-(e2:Entity)
                WHERE e1.name IN $names AND e2.name IN $names
                AND r.weekly_counts_json IS NOT NULL
                RETURN e1.name AS source, e2.name AS target,
                       r.weekly_counts_json AS wcj
            """, {{"names": list(top.keys())}})
            relationships = []
            for r in rels:
                wc = json.loads(r["wcj"]) if r["wcj"] else {{}}
                w  = wc.get(week, 0)
                if w >= 1:
                    relationships.append({{
                        "source": r["source"],
                        "target": r["target"],
                        "weight": w
                    }})
        else:
            rels = session.run("""
                MATCH (e1:Entity)-[r:CO_OCCURS_WITH]-(e2:Entity)
                WHERE e1.name IN $names AND e2.name IN $names AND r.count >= 2
                RETURN e1.name AS source, e2.name AS target, r.count AS weight
            """, {{"names": list(top.keys())}})
            relationships = [dict(r) for r in rels]

    # ── Build PyVis ──
    net = Network(height="460px", width="100%", bgcolor="#0A0C0F",
                  font_color="#8A9BB0", notebook=False, cdn_resources="in_line")
    net.set_options("""
    {{
      "physics": {{
        "forceAtlas2Based": {{
          "gravitationalConstant": -60,
          "centralGravity": 0.008,
          "springLength": 140,
          "springConstant": 0.06
        }},
        "solver": "forceAtlas2Based",
        "stabilization": {{"iterations": 120}}
      }},
      "edges": {{
        "smooth": {{"type": "continuous"}},
        "color": {{"opacity": 0.4}}
      }}
    }}
    """)

    for name, data in top.items():
        is_india = (name == "India")
        color    = "#E8D5A3" if is_india else TYPE_COLORS.get(data["type"], "#5A6A7A")
        size     = 58 if is_india else min(12 + data["conn"] * 1.8, 52)
        net.add_node(name, label=name,
            color={{
                "background":  color,
                "border":      "#FFFFFF" if is_india else color,
                "highlight":   {{"background": "#E8D5A3", "border": "#FFFFFF"}}
            }},
            size=size,
            title=f"{{data['type']}} · {{data['conn']}} connections",
            font={{"size": 11, "color": "#C8D4E0", "face": "IBM Plex Mono"}})

    for r in relationships:
        if r["source"] in top and r["target"] in top:
            net.add_edge(r["source"], r["target"],
                value=min(r["weight"] * 0.4, 4),
                title=f"co-occurrence: {{r['weight']}}",
                color={{"color": "#2A3A4A", "highlight": "#C8A96E"}})

    net.save_graph("graph_visual.html")
    with open("graph_visual.html", "r") as f:
        return f.read()


# ════════════════════════════════════════════
# PAGE CONFIG
# ════════════════════════════════════════════
st.set_page_config(
    page_title="PRAJNA — Strategic Intelligence",
    page_icon="▪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

*, *::before, *::after {{ box-sizing: border-box; }}
html, body, .stApp {{
    background-color: #0A0C0F !important;
    color: #C8D4E0 !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
}}
#MainMenu, footer, header {{ visibility: hidden; }}
.stDeployButton {{ display: none; }}
section[data-testid="stSidebar"] {{ display: none; }}

.prajna-nav {{
    display: flex; align-items: center;
    justify-content: space-between;
    padding: 0 0 20px 0;
    border-bottom: 1px solid #1C2A38;
    margin-bottom: 20px;
}}
.prajna-logo {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 13px; font-weight: 600;
    letter-spacing: 0.25em; color: #E8D5A3; text-transform: uppercase;
}}
.prajna-logo span {{ color: #4A6A8A; margin: 0 12px; }}
.prajna-meta {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px; color: #3A5068;
    letter-spacing: 0.1em; text-transform: uppercase;
}}
.prajna-status {{
    display: flex; align-items: center; gap: 6px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px; color: #4A8A6A; letter-spacing: 0.1em;
}}
.status-dot {{
    width: 6px; height: 6px; background: #4A8A6A;
    border-radius: 50%; animation: pulse 2s infinite;
}}
@keyframes pulse {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.3; }} }}

.stTabs [data-baseweb="tab-list"] {{
    background: transparent !important;
    border-bottom: 1px solid #1C2A38 !important;
    gap: 0 !important; padding: 0 !important;
}}
.stTabs [data-baseweb="tab"] {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 10px !important; font-weight: 500 !important;
    letter-spacing: 0.15em !important; text-transform: uppercase !important;
    color: #3A5068 !important; background: transparent !important;
    border: none !important; border-bottom: 2px solid transparent !important;
    padding: 10px 20px !important; border-radius: 0 !important;
}}
.stTabs [aria-selected="true"] {{
    color: #E8D5A3 !important;
    border-bottom: 2px solid #E8D5A3 !important;
    background: transparent !important;
}}
.stTabs [data-baseweb="tab-panel"] {{
    padding-top: 24px !important; background: transparent !important;
}}

.stTextInput > div > div > input {{
    background: #0D1117 !important; border: 1px solid #1C2A38 !important;
    border-radius: 0 !important; color: #C8D4E0 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 13px !important; padding: 10px 14px !important;
}}
.stTextInput > div > div > input:focus {{
    border-color: #C8A96E !important; box-shadow: none !important;
}}
.stTextInput label {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 9px !important; text-transform: uppercase !important;
    letter-spacing: 0.15em !important; color: #3A5068 !important;
}}

.stSelectbox > div > div {{
    background: #0D1117 !important; border: 1px solid #1C2A38 !important;
    border-radius: 0 !important; color: #C8D4E0 !important;
    font-family: 'IBM Plex Mono', monospace !important; font-size: 11px !important;
}}
.stSelectbox label {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 9px !important; text-transform: uppercase !important;
    letter-spacing: 0.15em !important; color: #3A5068 !important;
}}

.stButton > button {{
    background: transparent !important; border: 1px solid #2A3A4A !important;
    border-radius: 0 !important; color: #8A9BB0 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 10px !important; font-weight: 500 !important;
    letter-spacing: 0.15em !important; text-transform: uppercase !important;
    padding: 8px 20px !important; transition: all 0.15s ease !important;
}}
.stButton > button:hover {{
    background: #1C2A38 !important; border-color: #C8A96E !important;
    color: #E8D5A3 !important;
}}
.stButton > button:focus {{ box-shadow: none !important; outline: none !important; }}

.stSlider > div > div > div {{ background: #1C2A38 !important; }}
.stSlider label {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 9px !important; text-transform: uppercase !important;
    letter-spacing: 0.15em !important; color: #3A5068 !important;
}}

.brief-container {{
    border: 1px solid #1C2A38; border-left: 3px solid #C8A96E;
    background: #0D1117; padding: 20px 24px; margin: 16px 0;
    font-family: 'IBM Plex Sans', sans-serif; font-size: 13px;
    line-height: 1.8; color: #A8B8C8;
}}
.brief-header {{
    font-family: 'IBM Plex Mono', monospace; font-size: 9px;
    color: #C8A96E; text-transform: uppercase; letter-spacing: 0.2em;
    margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px solid #1C2A38;
}}
.path-node {{
    display: flex; align-items: center; gap: 12px;
    padding: 10px 16px; margin: 2px 0;
    background: #0D1117; border: 1px solid #1C2A38;
    font-family: 'IBM Plex Mono', monospace; font-size: 12px; color: #C8D4E0;
}}
.path-node.start {{ border-left: 3px solid #6B8CAE; }}
.path-node.end   {{ border-left: 3px solid #C8A96E; }}
.path-node.mid   {{ border-left: 3px solid #2A3A4A; margin-left: 20px; }}
.path-connector  {{
    margin-left: 28px; padding: 4px 16px;
    font-family: 'IBM Plex Mono', monospace; font-size: 10px;
    color: #2A4A3A; letter-spacing: 0.1em;
}}
.source-tag {{
    font-family: 'IBM Plex Mono', monospace; font-size: 9px;
    color: #3A5068; border: 1px solid #1C2A38;
    padding: 3px 8px; letter-spacing: 0.08em; text-transform: uppercase;
}}
.surge-card {{
    border: 1px solid #1C2A38; border-left: 3px solid #8A4A3A;
    background: #0D1117; padding: 16px 20px; margin: 8px 0;
}}
.surge-entity {{
    font-family: 'IBM Plex Mono', monospace; font-size: 13px;
    font-weight: 600; color: #E8D5A3;
    letter-spacing: 0.1em; text-transform: uppercase;
}}
.surge-ratio {{
    font-family: 'IBM Plex Mono', monospace; font-size: 11px;
    color: #C87B6A; margin-top: 2px;
}}
.section-label {{
    font-family: 'IBM Plex Mono', monospace; font-size: 9px;
    color: #3A5068; text-transform: uppercase; letter-spacing: 0.2em;
    margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #1C2A38;
}}
div[data-testid="metric-container"] {{
    background: #0D1117 !important; border: 1px solid #1C2A38 !important;
    border-radius: 0 !important; padding: 12px 16px !important;
}}
div[data-testid="metric-container"] label {{
    font-family: 'IBM Plex Mono', monospace !important; font-size: 9px !important;
    text-transform: uppercase !important; letter-spacing: 0.15em !important;
    color: #3A5068 !important;
}}
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 20px !important; color: #E8D5A3 !important;
}}
::-webkit-scrollbar {{ width: 4px; }}
::-webkit-scrollbar-track {{ background: #0A0C0F; }}
::-webkit-scrollbar-thumb {{ background: #1C2A38; }}
.stSpinner > div {{ border-top-color: #C8A96E !important; }}
.stAlert {{
    background: #0D1117 !important; border: 1px solid #1C2A38 !important;
    border-radius: 0 !important; font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px !important; color: #5A7A9A !important;
}}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════
# NAV BAR
# ════════════════════════════════════════════
now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d  %H:%M UTC")

try:
    articles_n, entities_n, rels_n = get_stats()
except:
    articles_n, entities_n, rels_n = 0, 0, 0

logo_html = f'<img src="data:image/svg+xml;base64,{{LOGO_B64}}" width="52" height="52" style="opacity:0.95"/>' if LOGO_B64 else ""

st.markdown(f"""
<div class="prajna-nav">
    <div style="display:flex;align-items:center;gap:16px">
        {{logo_html}}
        <div>
            <div class="prajna-logo">PRAJNA<span>▪</span>Strategic Intelligence Engine</div>
            <div class="prajna-meta" style="margin-top:4px">
                India Innovates 2026 &nbsp;·&nbsp; Domain 02: Digital Democracy &nbsp;·&nbsp; TeamIIMC
            </div>
        </div>
    </div>
    <div style="text-align:right">
        <div class="prajna-status">
            <div class="status-dot"></div>GRAPH ACTIVE
        </div>
        <div class="prajna-meta" style="margin-top:4px">{{now_str}}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Stats row
c1, c2, c3, c4 = st.columns(4)
c1.metric("ARTICLES INGESTED", articles_n)
c2.metric("ENTITIES MAPPED",   entities_n)
c3.metric("RELATIONSHIPS",     rels_n)
c4.metric("GRAPH STATUS",      "● LIVE")

st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)


# ════════════════════════════════════════════
# TABS
# ════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "INTELLIGENCE BRIEF",
    "TRAJECTORY ANALYSIS",
    "PATH QUERY",
    "SURGE DETECTION",
    "WEEKLY BRIEF"
])


# ── TAB 1: INTELLIGENCE BRIEF ──────────────
with tab1:
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown('<div class="section-label">Query Interface</div>', unsafe_allow_html=True)

        if "query_input" not in st.session_state:
            st.session_state["query_input"] = ""

        query = st.text_input(
            "STRATEGIC QUESTION",
            placeholder="What are India's energy security risks from Iran?",
            value=st.session_state["query_input"]
        )

        st.markdown('<div style="margin:12px 0 8px;font-family:IBM Plex Mono;font-size:9px;color:#2A3A4A;letter-spacing:0.15em;text-transform:uppercase;">Suggested Queries</div>', unsafe_allow_html=True)

        demo_queries = [
            "India Iran energy security",
            "Pakistan Afghanistan India impact",
            "India China border tensions",
            "India Russia defense cooperation",
            "Israel Iran war implications",
        ]
        for dq in demo_queries:
            if st.button(dq.upper(), key=f"dq_{{dq}}"):
                st.session_state["query_input"] = dq
                st.rerun()

        st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)
        run_query = st.button("EXECUTE QUERY ▶", key="run_brief")

        if run_query and query:
            with st.spinner(""):
                keywords     = [w for w in query.lower().split() if len(w) > 3][:5]
                context      = get_graph_context(keywords)
                articles_ctx = get_articles(keywords)
                ctx_str      = "\n".join([f"  {{e1}} <-> {{e2}} (strength:{{s}})" for e1, e2, s in context])
                art_str      = "\n".join([f"  [{{src}}] {{title}}" for title, src in articles_ctx])

                prompt = f"""You are Prajna, India's strategic intelligence engine.
Answer ONLY from the graph context below. Cite every claim with its source.

KNOWLEDGE GRAPH CONNECTIONS:
{{ctx_str}}

NEWS SOURCES:
{{art_str}}

QUESTION: {{query}}

Structure your response as:
SITUATION — 2-3 sentence summary of the current state
KEY CONNECTIONS — 3-4 bullet points directly from the graph data
STRATEGIC IMPLICATIONS — what this means specifically for India
RECOMMENDED ACTION — one concrete action for Indian policymakers
SOURCES — list all cited sources"""

                brief = ask_groq(prompt)

            sources_html = ""
            if articles_ctx:
                tags = "".join([f'<span class="source-tag">{{src}}</span>' for _, src in articles_ctx[:6]])
                sources_html = f'<div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:12px;padding-top:12px;border-top:1px solid #1C2A38">{{tags}}</div>'

            st.markdown(f"""
            <div class="brief-container">
                <div class="brief-header">
                    ▪ INTELLIGENCE BRIEF &nbsp;·&nbsp;
                    {{datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}}
                    &nbsp;·&nbsp; {{len(context)}} graph connections analysed
                </div>
                {{brief.replace(chr(10), "<br>")}}
                {{sources_html}}
            </div>
            """, unsafe_allow_html=True)

        elif run_query and not query:
            st.warning("Enter a strategic question first.")

    with col_right:
        st.markdown('<div class="section-label">Knowledge Graph</div>', unsafe_allow_html=True)

        # ── Week selector + entity filter ──
        available_weeks = get_available_weeks()
        week_options    = ["ALL TIME"] + available_weeks

        c_filter, c_week = st.columns([2, 1])
        with c_filter:
            graph_filter = st.text_input(
                "FILTER BY ENTITY",
                placeholder="Iran, China, Taliban...",
                key="graph_filter"
            )
        with c_week:
            selected_week = st.selectbox(
                "WEEK VIEW",
                week_options,
                key="graph_week"
            )

        week_param = None if selected_week == "ALL TIME" else selected_week

        with st.spinner(""):
            try:
                graph_html = build_graph_visual(
                    keyword=graph_filter or None,
                    week=week_param
                )
                components.html(graph_html, height=460)
                week_label = f"Showing: {{selected_week}}" if week_param else "Showing: All time"
                st.markdown(f'<div style="font-family:IBM Plex Mono;font-size:9px;color:#2A3A4A;text-transform:uppercase;letter-spacing:0.1em;margin-top:8px">{{week_label}} &nbsp;·&nbsp; Node size = connection strength &nbsp;·&nbsp; Drag to explore &nbsp;·&nbsp; Hover for details</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Graph error: {{e}}")


# ── TAB 2: TRAJECTORY ANALYSIS ─────────────
with tab2:
    st.markdown('<div class="section-label">Relationship Trajectory Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-family:IBM Plex Mono;font-size:10px;color:#3A5068;margin-bottom:20px;line-height:1.7">Tracks co-occurrence strength between two entities week-over-week.<br>Sustained increases = deepening relationship. Spikes = event-driven. Drops = decoupling.</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([2, 2, 1])
    with c1: e1 = st.text_input("ENTITY A", value="India", key="traj_e1")
    with c2: e2 = st.text_input("ENTITY B", value="Iran",  key="traj_e2")
    with c3:
        st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
        run_traj = st.button("RUN ANALYSIS ▶", key="run_traj")

    st.markdown('<div style="font-family:IBM Plex Mono;font-size:9px;color:#2A3A4A;letter-spacing:0.1em;margin-bottom:16px">SUGGESTED — India/Iran &nbsp;·&nbsp; India/Russia &nbsp;·&nbsp; Iran/Israel &nbsp;·&nbsp; India/China &nbsp;·&nbsp; Pakistan/Afghanistan</div>', unsafe_allow_html=True)

    if run_traj:
        with st.spinner(""):
            weekly_data, total = get_trajectory(e1, e2)

        if not weekly_data:
            st.markdown(f'<div style="font-family:IBM Plex Mono;font-size:11px;color:#5A3A3A;border:1px solid #2A1A1A;padding:14px 18px;background:#0D0A0A">▪ NO TRAJECTORY DATA — {{e1.upper()}} ↔ {{e2.upper()}}<br><span style="color:#2A3A4A;font-size:9px">These entities may not co-occur in graph. Try: India/Iran · Iran/Israel · India/Russia</span></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="font-family:IBM Plex Mono;font-size:10px;color:#4A6A4A;border:1px solid #1A2A1A;padding:10px 16px;background:#0A0D0A;margin-bottom:16px">▪ {{e1.upper()}} ↔ {{e2.upper()}} &nbsp;·&nbsp; {{total}} TOTAL CO-OCCURRENCES &nbsp;·&nbsp; {{len(weekly_data)}} WEEK(S) OF DATA</div>', unsafe_allow_html=True)

            df = pd.DataFrame(weekly_data, columns=["Week", "Co-occurrences"])
            st.bar_chart(df.set_index("Week"), color="#C8A96E")

            traj_str = "\n".join([f"  {{w}}: {{c}}" for w, c in weekly_data])
            prompt = f"""You are Prajna. Analyse this relationship trajectory:

{{e1}} ↔ {{e2}}
Weekly co-occurrence data:
{{traj_str}}
Total all-time co-occurrences: {{total}}

SITUATION — is this relationship intensifying, cooling, or volatile?
INFLECTION POINTS — any sharp changes and their likely geopolitical causes
INDIA STRATEGIC IMPLICATIONS — what does this trajectory mean for India specifically?
WATCH FOR — 2 specific developments to monitor in coming weeks

Be analytical and specific. Max 250 words."""

            with st.spinner(""):
                brief = ask_groq(prompt)

            st.markdown(f'<div class="brief-container"><div class="brief-header">▪ TRAJECTORY INTERPRETATION — {{e1.upper()}} ↔ {{e2.upper()}}</div>{{brief.replace(chr(10), "<br>")}}</div>', unsafe_allow_html=True)


# ── TAB 3: PATH QUERY ──────────────────────
with tab3:
    st.markdown('<div class="section-label">Graph Path Query</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-family:IBM Plex Mono;font-size:10px;color:#3A5068;margin-bottom:20px;line-height:1.7">Finds the shortest connection path between any two entities in the knowledge graph.<br>Surfaces non-obvious relationships invisible to human analysts — impossible for standard LLMs.</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([2, 2, 1])
    with c1: p1 = st.text_input("ORIGIN ENTITY",  value="India",   key="path_p1")
    with c2: p2 = st.text_input("TARGET ENTITY",  value="Taliban", key="path_p2")
    with c3:
        st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
        run_path = st.button("FIND PATH ▶", key="run_path")

    st.markdown('<div style="font-family:IBM Plex Mono;font-size:9px;color:#2A3A4A;letter-spacing:0.1em;margin-bottom:16px">SUGGESTED — India→Taliban &nbsp;·&nbsp; Russia→Taliban &nbsp;·&nbsp; Israel→Pakistan &nbsp;·&nbsp; India→Qatar</div>', unsafe_allow_html=True)

    if run_path:
        with st.spinner(""):
            path = find_path(p1, p2)

        if not path:
            st.markdown(f'<div style="font-family:IBM Plex Mono;font-size:11px;color:#5A3A3A;border:1px solid #2A1A1A;padding:14px 18px;background:#0D0A0A">▪ NO PATH FOUND — {{p1.upper()}} → {{p2.upper()}}<br><span style="color:#2A3A4A;font-size:9px">No connection within 4 hops. Try different entity names.</span></div>', unsafe_allow_html=True)
        else:
            nodes     = path["nodes"]
            strengths = path["strengths"]

            st.markdown(f'<div style="font-family:IBM Plex Mono;font-size:10px;color:#4A6A4A;border:1px solid #1A2A1A;padding:10px 16px;background:#0A0D0A;margin-bottom:16px">▪ PATH FOUND &nbsp;·&nbsp; {{path["hops"]}} HOP(S) &nbsp;·&nbsp; {{p1.upper()}} → {{p2.upper()}}</div>', unsafe_allow_html=True)

            nodes_html = ""
            path_str   = ""
            for i, node in enumerate(nodes):
                if i == 0:
                    nodes_html += f'<div class="path-node start">▶ &nbsp; {{node.upper()}}</div>'
                    path_str   += node
                elif i == len(nodes) - 1:
                    nodes_html += f'<div class="path-node end">◼ &nbsp; {{node.upper()}}</div>'
                    path_str   += node
                else:
                    nodes_html += f'<div class="path-node mid">◦ &nbsp; {{node}}</div>'
                    path_str   += node
                if i < len(strengths):
                    nodes_html += f'<div class="path-connector">│ co-occurs {{strengths[i]}}× in news</div>'
                    path_str   += f" --[{{strengths[i]}}x]--> "

            st.markdown(nodes_html, unsafe_allow_html=True)

            prompt = f"""You are Prajna. A knowledge graph path query revealed:

PATH: {{path_str}}
HOPS: {{path["hops"]}}

Each arrow represents two entities co-appearing in real news articles.
The number = frequency of co-appearance in the corpus.

HIDDEN CONNECTION — what does this path mean in plain English?
STRATEGIC SIGNIFICANCE — why does this specifically matter for India?
NON-OBVIOUS INSIGHT — what would an analyst miss without this graph?
RECOMMENDED ACTION — one concrete action for Indian policymakers

Be direct and specific. Max 220 words."""

            with st.spinner(""):
                brief = ask_groq(prompt)

            st.markdown(f'<div class="brief-container" style="margin-top:16px"><div class="brief-header">▪ PATH INTELLIGENCE — {{p1.upper()}} → {{p2.upper()}}</div>{{brief.replace(chr(10), "<br>")}}</div>', unsafe_allow_html=True)


# ── TAB 4: SURGE DETECTION ─────────────────
with tab4:
    st.markdown('<div class="section-label">Automated Surge Detection</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-family:IBM Plex Mono;font-size:10px;color:#3A5068;margin-bottom:20px;line-height:1.7">Monitors the knowledge graph for entities whose news co-occurrence is growing anomalously fast.<br>No query required — Prajna surfaces what you did not know to ask about.</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([2, 1])
    with c1:
        threshold = st.slider("SURGE THRESHOLD (× WEEKLY BASELINE)", 1.2, 3.0, 1.5, 0.1)
    with c2:
        st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
        run_surge = st.button("SCAN GRAPH ▶", key="run_surge")

    if run_surge:
        with st.spinner(""):
            surges = detect_surges(threshold=threshold)

        if not surges:
            st.markdown(f'<div style="font-family:IBM Plex Mono;font-size:11px;color:#3A5068;border:1px solid #1C2A38;padding:14px 18px;background:#0D1117;margin-bottom:16px">▪ NO SURGES DETECTED ABOVE {{threshold}}× THRESHOLD<br><span style="font-size:9px;color:#2A3A4A">Surge detection strengthens as more weeks accumulate in the graph.</span></div>', unsafe_allow_html=True)

            # Show top entities by connection as fallback
            st.markdown('<div class="section-label" style="margin-top:20px">Current Top Entities by Connection Strength</div>', unsafe_allow_html=True)
            with driver.session() as session:
                top = session.run("""
                    MATCH (e:Entity)-[r:CO_OCCURS_WITH]-()
                    WHERE e.type IN ['GPE','ORG','PERSON']
                    RETURN e.name AS name, e.type AS type, count(r) AS conn
                    ORDER BY conn DESC LIMIT 12
                """).data()
            rows = "".join([
                f'<div style="display:flex;justify-content:space-between;align-items:center;padding:6px 12px;border-bottom:1px solid #0D1117;font-family:IBM Plex Mono;font-size:10px;color:#5A7A9A"><span>{{r["name"].upper()}}</span><span style="color:#3A5068">{{r["conn"]}} connections</span></div>'
                for r in top if len(r["name"]) < 35
            ])
            st.markdown(f'<div style="border:1px solid #1C2A38;background:#0D1117">{{rows}}</div>', unsafe_allow_html=True)

        else:
            st.markdown(f'<div style="font-family:IBM Plex Mono;font-size:10px;color:#C87B6A;border:1px solid #2A1A1A;padding:10px 16px;background:#0D0A0A;margin-bottom:16px">▪ {{len(surges)}} ENTITIES FLAGGED ABOVE {{threshold}}× BASELINE</div>', unsafe_allow_html=True)

            for surge in surges:
                st.markdown(f'<div class="surge-card"><div class="surge-entity">▲ {{surge["entity"]}}</div><div class="surge-ratio">{{surge["ratio"]}}× baseline &nbsp;·&nbsp; {{surge["latest"]}} connections this week &nbsp;·&nbsp; baseline: {{surge["baseline"]}}/week</div></div>', unsafe_allow_html=True)

                prompt = f"""Prajna surge alert:
Entity: {{surge["entity"]}} ({{surge["type"]}})
This week: {{surge["latest"]}} news co-occurrences
Historical baseline: {{surge["baseline"]}} per week
Surge ratio: {{surge["ratio"]}}×

SURGE EXPLANATION — why is this entity surging in the news?
INDIA RISK/OPPORTUNITY — what are the strategic implications for India?
URGENCY — Immediate / Days / Weeks
RECOMMENDED ACTION — one specific action

Max 130 words. Be direct and analytical."""

                with st.spinner(""):
                    brief = ask_groq(prompt)

                st.markdown(f'<div class="brief-container" style="border-left-color:#8A4A3A;margin-bottom:20px"><div class="brief-header" style="color:#C87B6A">▪ SURGE BRIEF — {{surge["entity"].upper()}}</div>{{brief.replace(chr(10), "<br>")}}</div>', unsafe_allow_html=True)


# ── TAB 5: WEEKLY BRIEF ──────────────────────────────────────────────────────
with tab5:
    st.markdown('<div class="section-label">Automated Weekly Intelligence Brief</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-family:IBM Plex Mono;font-size:10px;color:#3A5068;margin-bottom:20px">Prajna automatically identifies the 5 most strategically significant developments India should monitor.</div>', unsafe_allow_html=True)

    available_weeks_brief = get_available_weeks()
    week_options_brief    = ["CURRENT WEEK"] + available_weeks_brief
    c1b, c2b = st.columns([2, 1])
    with c1b:
        selected_brief_week = st.selectbox("SELECT WEEK FOR BRIEF", week_options_brief, key="brief_week")
    with c2b:
        st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
        run_weekly_brief = st.button("GENERATE BRIEF", key="run_weekly_brief")

    if run_weekly_brief:
        brief_week = get_week_key() if selected_brief_week == "CURRENT WEEK" else selected_brief_week
        with st.spinner("Analysing graph..."):
            with driver.session() as session:
                top_entities = session.run(
                    "MATCH (a:Article {week:$w})-[:MENTIONS]->(e:Entity) "
                    "WHERE e.type IN ['GPE','ORG','PERSON','NORP'] "
                    "AND NOT e.name IN ['United States','United Kingdom','Guardian','BBC','Reuters','AP','AFP'] "
                    "RETURN e.name AS entity, e.type AS type, COUNT(a) AS mentions "
                    "ORDER BY mentions DESC LIMIT 15",
                    {"w": brief_week}
                ).data()
                names = [r["entity"] for r in top_entities]
                pairs = session.run(
                    "MATCH (a:Article {week:$w})-[:MENTIONS]->(e1:Entity) "
                    "MATCH (a)-[:MENTIONS]->(e2:Entity) "
                    "WHERE e1.name IN $names AND e2.name IN $names AND e1.name < e2.name "
                    "RETURN e1.name AS e1, e2.name AS e2, COUNT(a) AS co_count "
                    "ORDER BY co_count DESC LIMIT 20",
                    {"w": brief_week, "names": names}
                ).data()
                top_pairs = pairs[:5]
                headlines = {}
                for p in top_pairs:
                    arts = session.run(
                        "MATCH (a:Article {week:$w})-[:MENTIONS]->(x:Entity {name:$e1}) "
                        "MATCH (a)-[:MENTIONS]->(y:Entity {name:$e2}) "
                        "RETURN a.title AS title, a.source AS source LIMIT 3",
                        {"w": brief_week, "e1": p["e1"], "e2": p["e2"]}
                    ).data()
                    key = p["e1"] + " <> " + p["e2"]
                    headlines[key] = arts

            pairs_lines = []
            for p in top_pairs:
                pairs_lines.append("  " + p["e1"] + " <> " + p["e2"] + ": " + str(p["co_count"]) + " co-mentions")
            pairs_str = "
".join(pairs_lines)

            hl_lines = []
            for key, arts in headlines.items():
                hl_lines.append(key + ":")
                for a in arts:
                    hl_lines.append("  [" + a["source"] + "] " + a["title"])
            headlines_str = "
".join(hl_lines)

            prompt_lines = [
                "You are Prajna, India's strategic intelligence engine.",
                "Week: " + brief_week,
                "",
                "Most active entity relationships this week (knowledge graph):",
                pairs_str,
                "",
                "Supporting headlines:",
                headlines_str,
                "",
                "Generate a WEEKLY INTELLIGENCE BRIEF for Indian policymakers.",
                "Format exactly as:",
                "",
                "WEEK " + brief_week + " - STRATEGIC INTELLIGENCE BRIEF",
                "",
                "STORY 1: [headline]",
                "[2-3 sentences on why this matters for India specifically]",
                "",
                "STORY 2: [headline]",
                "[2-3 sentences]",
                "",
                "STORY 3: [headline]",
                "[2-3 sentences]",
                "",
                "STORY 4: [headline]",
                "[2-3 sentences]",
                "",
                "STORY 5: [headline]",
                "[2-3 sentences]",
                "",
                "BOTTOM LINE FOR INDIA: One sentence strategic summary.",
                "",
                "Be direct, analytical, India-centric. Max 400 words.",
            ]
            prompt = "
".join(prompt_lines)
            brief_text = ask_groq(prompt)

        all_sources = []
        for arts in headlines.values():
            for a in arts:
                if a["source"] not in all_sources:
                    all_sources.append(a["source"])
        source_tags = " ".join(["[" + s + "]" for s in all_sources[:8]])

        header = "WEEKLY BRIEF - " + brief_week + " - " + str(len(top_pairs)) + " signal pairs - " + str(len(names)) + " entities tracked"
        st.markdown('<div class="brief-container"><div class="brief-header">' + header + '</div>' + brief_text.replace("
", "<br>") + '<div style="margin-top:12px;padding-top:12px;border-top:1px solid #1C2A38;font-family:IBM Plex Mono;font-size:9px;color:#3A5068">' + source_tags + '</div></div>', unsafe_allow_html=True)

