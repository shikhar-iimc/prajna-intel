
import streamlit as st
from neo4j import GraphDatabase
from groq import Groq
from pyvis.network import Network
import streamlit.components.v1 as components
import os, json
from collections import defaultdict
from datetime import datetime, timezone

# ── Connections ──
NEO4J_URI      = os.environ.get("NEO4J_URI")
NEO4J_USERNAME = os.environ.get("NEO4J_USERNAME")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")
GROQ_API_KEY   = os.environ.get("GROQ_API_KEY")

@st.cache_resource
def get_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

@st.cache_resource
def get_groq_client():
    return Groq(api_key=GROQ_API_KEY)

driver      = get_driver()
groq_client = get_groq_client()

def get_week_key():
    now = datetime.now(timezone.utc)
    return f"{now.year}-W{now.strftime('%W')}"

def ask_groq(prompt):
    r = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"user","content":prompt}],
        max_tokens=600, temperature=0.3
    )
    return r.choices[0].message.content

@st.cache_data(ttl=300)
def get_stats():
    with driver.session() as session:
        articles = session.run("MATCH (a:Article) RETURN count(a) as c").single()["c"]
        entities = session.run("MATCH (e:Entity) RETURN count(e) as c").single()["c"]
        rels     = session.run("MATCH ()-[r:CO_OCCURS_WITH]->() RETURN count(r) as c").single()["c"]
    return articles, entities, rels

def get_graph_context(keywords):
    with driver.session() as session:
        result = session.run("""
            MATCH (e:Entity)-[r:CO_OCCURS_WITH]-(other:Entity)
            WHERE any(kw IN $keywords WHERE toLower(e.name) CONTAINS toLower(kw))
            RETURN e.name AS e1, other.name AS e2, r.count AS strength
            ORDER BY r.count DESC LIMIT 20
        """, {"keywords": keywords})
        return [(r["e1"], r["e2"], r["strength"]) for r in result]

def get_articles(keywords):
    with driver.session() as session:
        result = session.run("""
            MATCH (a:Article)-[:MENTIONS]->(e:Entity)
            WHERE any(kw IN $keywords WHERE toLower(e.name) CONTAINS toLower(kw))
            RETURN DISTINCT a.title AS title, a.source AS source
            LIMIT 5
        """, {"keywords": keywords})
        return [(r["title"], r["source"]) for r in result]

def get_trajectory(e1, e2):
    with driver.session() as session:
        result = session.run("""
            MATCH (a:Entity {name:$e1})-[r:CO_OCCURS_WITH]-(b:Entity {name:$e2})
            RETURN r.weekly_counts_json AS wcj, r.count AS total
        """, {"e1": e1, "e2": e2}).single()
    if not result or not result["wcj"]:
        return None, None
    wc = json.loads(result["wcj"])
    return sorted(wc.items()), result["total"]

def find_path(e1, e2):
    with driver.session() as session:
        result = session.run("""
            MATCH path = shortestPath(
                (a:Entity {name:$e1})-[:CO_OCCURS_WITH*1..4]-(b:Entity {name:$e2})
            )
            RETURN [node IN nodes(path) | node.name] AS nodes,
                   [rel IN relationships(path) | rel.count] AS strengths,
                   length(path) AS hops
        """, {"e1": e1, "e2": e2}).single()
    if not result:
        return None
    return {"nodes": result["nodes"], "strengths": result["strengths"], "hops": result["hops"]}

BLOCKLIST = {
    "Supreme","Asian","Islam","American","European","Western","Eastern",
    "T20 World Cup","West Indies","BBC","CNN","Reuters","Bloomberg",
    "NDTV","Mint","Hindu","Express","ANI","PTI","AFP","AP","Wire","Tribune","Times"
}

def detect_surges(threshold=1.5, top_n=5):
    week_key = get_week_key()
    with driver.session() as session:
        results = session.run("""
            MATCH (e:Entity)-[r:CO_OCCURS_WITH]-()
            WHERE r.weekly_counts_json IS NOT NULL
            RETURN e.name AS entity, e.type AS type,
                   r.weekly_counts_json AS wcj, r.count AS total
        """).data()

    entity_weekly = defaultdict(lambda: defaultdict(int))
    entity_total  = defaultdict(int)
    entity_type   = {}

    for row in results:
        e = row["entity"]
        entity_type[e] = row["type"]
        entity_total[e] += row["total"] or 0
        wc = json.loads(row["wcj"]) if row["wcj"] else {}
        for week, count in wc.items():
            entity_weekly[e][week] += count

    surges = []
    for entity, weekly in entity_weekly.items():
        if entity in BLOCKLIST: continue
        if entity_total[entity] < 8: continue
        if len(entity) > 35: continue
        if any(c.isdigit() for c in entity): continue
        if entity_type.get(entity) not in {"GPE","ORG","PERSON","NORP"}: continue

        weeks     = sorted(weekly.keys())
        latest_wk = weeks[-1]
        if latest_wk != week_key: continue

        latest   = weekly[latest_wk]
        hist     = [weekly[w] for w in weeks if w != latest_wk]
        baseline = sum(hist)/len(hist) if hist else entity_total[entity]/2
        if baseline == 0: continue

        ratio = latest / baseline
        if ratio >= threshold:
            surges.append({
                "entity":   entity,
                "type":     entity_type.get(entity,""),
                "latest":   latest,
                "baseline": round(baseline,1),
                "ratio":    round(ratio,2),
                "total":    entity_total[entity]
            })

    surges.sort(key=lambda x: x["ratio"], reverse=True)
    return surges[:top_n]

def build_graph_visual(keyword=None):
    TYPE_COLORS = {
        "GPE":"#C8A96E","ORG":"#6B8CAE","PERSON":"#A8C5A0",
        "NORP":"#B8956A","LOC":"#8AABBA","EVENT":"#C47B6E"
    }
    with driver.session() as session:
        if keyword:
            res = session.run("""
                MATCH (e:Entity) WHERE toLower(e.name) CONTAINS $kw
                WITH e MATCH (e)-[r:CO_OCCURS_WITH]-(other:Entity)
                WITH collect(DISTINCT e)+collect(DISTINCT other) AS nl
                UNWIND nl AS node WITH DISTINCT node
                WITH node, COUNT{(node)--()} AS conn
                ORDER BY conn DESC LIMIT 40
                RETURN node.name AS name, node.type AS type, conn
            """, {"kw": keyword.lower()})
        else:
            res = session.run("""
                MATCH (e:Entity)
                WITH e, COUNT{(e)--()} AS conn
                ORDER BY conn DESC LIMIT 40
                RETURN e.name AS name, e.type AS type, conn
            """)
        top = {r["name"]: r for r in res}
        rels = session.run("""
            MATCH (e1:Entity)-[r:CO_OCCURS_WITH]-(e2:Entity)
            WHERE e1.name IN $names AND e2.name IN $names AND r.count >= 2
            RETURN e1.name AS source, e2.name AS target, r.count AS weight
        """, {"names": list(top.keys())})
        relationships = list(rels)

    net = Network(height="460px", width="100%", bgcolor="#0A0C0F",
                  font_color="#8A9BB0", notebook=False, cdn_resources="in_line")
    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -60,
          "centralGravity": 0.008,
          "springLength": 140,
          "springConstant": 0.06
        },
        "solver": "forceAtlas2Based",
        "stabilization": {"iterations": 120}
      },
      "edges": {
        "smooth": {"type": "continuous"},
        "color": {"opacity": 0.4}
      }
    }
    """)

    for name, data in top.items():
        is_india = name == "India"
        color    = "#E8D5A3" if is_india else TYPE_COLORS.get(data["type"], "#5A6A7A")
        size     = min(12 + data["conn"] * 1.8, 52) if not is_india else 58
        border   = "#FFFFFF" if is_india else color
        net.add_node(
            name, label=name, color={"background": color, "border": border,
            "highlight": {"background": "#E8D5A3", "border": "#FFFFFF"}},
            size=size, title=f"{data['type']} · {data['conn']} connections",
            font={"size": 11, "color": "#C8D4E0", "face": "IBM Plex Mono"}
        )

    for r in relationships:
        if r["source"] in top and r["target"] in top:
            w = min(r["weight"] * 0.4, 4)
            net.add_edge(
                r["source"], r["target"], value=w,
                title=f"co-occurrence: {r['weight']}",
                color={"color": "#2A3A4A", "highlight": "#C8A96E"}
            )

    net.save_graph("graph_visual.html")
    with open("graph_visual.html", "r") as f:
        return f.read()

# ════════════════════════════════════════
# PAGE CONFIG
# ════════════════════════════════════════

st.set_page_config(
    page_title="PRAJNA — Strategic Intelligence",
    page_icon="▪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp {
    background-color: #0A0C0F !important;
    color: #C8D4E0 !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
section[data-testid="stSidebar"] { display: none; }

/* Top navigation bar */
.prajna-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 0 20px 0;
    border-bottom: 1px solid #1C2A38;
    margin-bottom: 28px;
}
.prajna-logo {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.25em;
    color: #E8D5A3;
    text-transform: uppercase;
}
.prajna-logo span {
    color: #4A6A8A;
    margin: 0 12px;
}
.prajna-meta {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    color: #3A5068;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
.prajna-status {
    display: flex;
    align-items: center;
    gap: 6px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    color: #4A8A6A;
    letter-spacing: 0.1em;
}
.status-dot {
    width: 6px; height: 6px;
    background: #4A8A6A;
    border-radius: 50%;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}

/* Stat row */
.stat-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1px;
    background: #1C2A38;
    border: 1px solid #1C2A38;
    margin-bottom: 28px;
}
.stat-cell {
    background: #0A0C0F;
    padding: 16px 20px;
}
.stat-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 22px;
    font-weight: 500;
    color: #E8D5A3;
    line-height: 1;
    margin-bottom: 4px;
}
.stat-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 9px;
    color: #3A5068;
    text-transform: uppercase;
    letter-spacing: 0.15em;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #1C2A38 !important;
    gap: 0 !important;
    padding: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 10px !important;
    font-weight: 500 !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    color: #3A5068 !important;
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    padding: 10px 20px !important;
    border-radius: 0 !important;
}
.stTabs [aria-selected="true"] {
    color: #E8D5A3 !important;
    border-bottom: 2px solid #E8D5A3 !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 24px !important;
    background: transparent !important;
}

/* Inputs */
.stTextInput > div > div > input {
    background: #0D1117 !important;
    border: 1px solid #1C2A38 !important;
    border-radius: 0 !important;
    color: #C8D4E0 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 13px !important;
    padding: 10px 14px !important;
    outline: none !important;
}
.stTextInput > div > div > input:focus {
    border-color: #C8A96E !important;
    box-shadow: none !important;
}
.stTextInput label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 9px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.15em !important;
    color: #3A5068 !important;
}

/* Buttons */
.stButton > button {
    background: transparent !important;
    border: 1px solid #2A3A4A !important;
    border-radius: 0 !important;
    color: #8A9BB0 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 10px !important;
    font-weight: 500 !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    padding: 8px 20px !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover {
    background: #1C2A38 !important;
    border-color: #C8A96E !important;
    color: #E8D5A3 !important;
}
.stButton > button:focus {
    box-shadow: none !important;
    outline: none !important;
}

/* Primary action button */
.stButton > button[kind="primary"],
div[data-testid="stButton"] > button:first-child {
    border-color: #C8A96E !important;
    color: #E8D5A3 !important;
}

/* Slider */
.stSlider > div > div > div {
    background: #1C2A38 !important;
}
.stSlider label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 9px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.15em !important;
    color: #3A5068 !important;
}

/* Brief output box */
.brief-container {
    border: 1px solid #1C2A38;
    border-left: 3px solid #C8A96E;
    background: #0D1117;
    padding: 20px 24px;
    margin: 16px 0;
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 13px;
    line-height: 1.8;
    color: #A8B8C8;
}
.brief-header {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 9px;
    color: #C8A96E;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 1px solid #1C2A38;
}

/* Path node display */
.path-node {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 16px;
    margin: 2px 0;
    background: #0D1117;
    border: 1px solid #1C2A38;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    color: #C8D4E0;
}
.path-node.start { border-left: 3px solid #6B8CAE; }
.path-node.end   { border-left: 3px solid #C8A96E; }
.path-node.mid   { border-left: 3px solid #2A3A4A; margin-left: 20px; }
.path-connector  {
    margin-left: 28px;
    padding: 4px 16px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    color: #2A4A3A;
    letter-spacing: 0.1em;
}

/* Source tags */
.source-row {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #1C2A38;
}
.source-tag {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 9px;
    color: #3A5068;
    border: 1px solid #1C2A38;
    padding: 3px 8px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

/* Surge alert card */
.surge-card {
    border: 1px solid #1C2A38;
    border-left: 3px solid #8A4A3A;
    background: #0D1117;
    padding: 16px 20px;
    margin: 8px 0;
}
.surge-entity {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 13px;
    font-weight: 600;
    color: #E8D5A3;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
.surge-ratio {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    color: #C87B6A;
    margin-top: 2px;
}

/* Section labels */
.section-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 9px;
    color: #3A5068;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #1C2A38;
}

/* Context pills for graph */
.context-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 12px;
    border-bottom: 1px solid #0D1117;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    color: #5A7A9A;
}
.context-item:hover { background: #0D1117; }
.context-strength {
    color: #3A5068;
    font-size: 9px;
}

/* Metrics override */
div[data-testid="metric-container"] {
    background: #0D1117 !important;
    border: 1px solid #1C2A38 !important;
    border-radius: 0 !important;
    padding: 12px 16px !important;
}
div[data-testid="metric-container"] label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 9px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.15em !important;
    color: #3A5068 !important;
}
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 20px !important;
    color: #E8D5A3 !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: #0D1117 !important;
    border: 1px solid #1C2A38 !important;
    border-radius: 0 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 10px !important;
    color: #5A7A9A !important;
    letter-spacing: 0.1em !important;
}

/* Bar chart */
div[data-testid="stVegaLiteChart"] { border: 1px solid #1C2A38; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #0A0C0F; }
::-webkit-scrollbar-thumb { background: #1C2A38; }

/* Spinner */
.stSpinner > div { border-top-color: #C8A96E !important; }

/* Info / warning boxes */
.stAlert {
    background: #0D1117 !important;
    border: 1px solid #1C2A38 !important;
    border-radius: 0 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px !important;
    color: #5A7A9A !important;
}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════
# NAVIGATION BAR
# ════════════════════════════════════════

now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d  %H:%M UTC")

try:
    articles, entities, rels = get_stats()
    stats_html = f"""
    <div class="stat-row">
        <div class="stat-cell">
            <div class="stat-value">{articles}</div>
            <div class="stat-label">Articles Ingested</div>
        </div>
        <div class="stat-cell">
            <div class="stat-value">{entities}</div>
            <div class="stat-label">Entities Mapped</div>
        </div>
        <div class="stat-cell">
            <div class="stat-value">{rels}</div>
            <div class="stat-label">Relationships</div>
        </div>
        <div class="stat-cell">
            <div class="stat-value" style="color:#4A8A6A">LIVE</div>
            <div class="stat-label">Graph Status</div>
        </div>
    </div>
    """
except:
    stats_html = ""

st.markdown(f"""
<div class="prajna-nav">
    <div>
        <div class="prajna-logo">PRAJNA<span>▪</span>Strategic Intelligence Engine</div>
        <div class="prajna-meta" style="margin-top:4px">
            India Innovates 2026 &nbsp;·&nbsp; Domain 02: Digital Democracy &nbsp;·&nbsp; TeamIIMC
        </div>
    </div>
    <div style="text-align:right">
        <div class="prajna-status">
            <div class="status-dot"></div>
            GRAPH ACTIVE
        </div>
        <div class="prajna-meta" style="margin-top:4px">{now_str}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════
# TABS
# ════════════════════════════════════════

tab1, tab2, tab3, tab4 = st.tabs([
    "INTELLIGENCE BRIEF",
    "TRAJECTORY ANALYSIS",
    "PATH QUERY",
    "SURGE DETECTION"
])

# ── TAB 1: INTELLIGENCE BRIEF ──────────
with tab1:
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown('<div class="section-label">Query Interface</div>', unsafe_allow_html=True)

        query = st.text_input(
            "STRATEGIC QUESTION",
            placeholder="What are India's energy security risks from Iran?",
            key="query_input"
        )

        # Demo query buttons
        st.markdown('<div style="margin: 12px 0 8px; font-family: IBM Plex Mono; font-size: 9px; color: #2A3A4A; letter-spacing: 0.15em; text-transform: uppercase;">Suggested queries</div>', unsafe_allow_html=True)
        demo_queries = [
            "India Iran energy security",
            "Pakistan Afghanistan India impact",
            "India China border tensions",
            "India Russia defense cooperation",
            "Israel Iran war implications",
        ]
        for dq in demo_queries:
            if st.button(dq, key=f"dq_{dq}"):
                st.session_state["query_input"] = dq
                st.rerun()

        st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)
        run_query = st.button("EXECUTE QUERY ▶", key="run_brief")

        if run_query and query:
            with st.spinner(""):
                keywords     = [w for w in query.lower().split() if len(w) > 3][:5]
                context      = get_graph_context(keywords)
                articles_ctx = get_articles(keywords)

                ctx_str = "\n".join([f"  {e1} <-> {e2} (strength:{s})"
                                      for e1, e2, s in context])
                art_str = "\n".join([f"  [{src}] {title}"
                                      for title, src in articles_ctx])

                prompt = f"""You are Prajna, India strategic intelligence engine.
Answer ONLY from the graph context. Cite every claim with source.

KNOWLEDGE GRAPH:
{ctx_str}

NEWS SOURCES:
{art_str}

QUESTION: {query}

Structure response as:
SITUATION — 2-3 sentence summary
KEY CONNECTIONS — 3-4 bullet points from graph
STRATEGIC IMPLICATIONS — what this means for India
RECOMMENDED ACTION — one specific action
SOURCES — list all cited sources"""

                brief = ask_groq(prompt)

            sources_html = ""
            if articles_ctx:
                tags = "".join([f'<span class="source-tag">{src}</span>'
                                for _, src in articles_ctx[:6]])
                sources_html = f'<div class="source-row">{tags}</div>'

            st.markdown(f"""
            <div class="brief-container">
                <div class="brief-header">
                    ▪ INTELLIGENCE BRIEF &nbsp;·&nbsp; {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}
                    &nbsp;·&nbsp; {len(context)} graph connections analysed
                </div>
                {brief.replace(chr(10), "<br>")}
                {sources_html}
            </div>
            """, unsafe_allow_html=True)

        elif run_query and not query:
            st.warning("Enter a query to execute.")

    with col_right:
        st.markdown('<div class="section-label">Knowledge Graph</div>', unsafe_allow_html=True)
        graph_filter = st.text_input(
            "FILTER BY ENTITY",
            placeholder="Iran, China, Taliban...",
            key="graph_filter"
        )
        with st.spinner(""):
            try:
                graph_html = build_graph_visual(graph_filter if graph_filter else None)
                components.html(graph_html, height=460)
                st.markdown("""
                <div style="font-family:IBM Plex Mono;font-size:9px;color:#2A3A4A;
                     text-transform:uppercase;letter-spacing:0.1em;margin-top:8px;">
                    Node size = connection strength &nbsp;·&nbsp;
                    Drag to explore &nbsp;·&nbsp;
                    Hover for details
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Graph render error: {e}")

# ── TAB 2: TRAJECTORY ──────────────────
with tab2:
    st.markdown('<div class="section-label">Relationship Trajectory Analysis</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family:IBM Plex Mono;font-size:10px;color:#3A5068;margin-bottom:20px;line-height:1.7">
    Tracks how the co-occurrence strength between two entities evolves week-over-week.<br>
    Sustained increases = deepening strategic relationship. Spikes = event-driven. Drops = decoupling.
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        e1 = st.text_input("ENTITY A", value="India", key="traj_e1")
    with col2:
        e2 = st.text_input("ENTITY B", value="Iran", key="traj_e2")
    with col3:
        st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
        run_traj = st.button("RUN ANALYSIS ▶", key="run_traj")

    st.markdown("""
    <div style="font-family:IBM Plex Mono;font-size:9px;color:#2A3A4A;
         letter-spacing:0.1em;margin-bottom:16px">
    SUGGESTED PAIRS — India / Iran &nbsp;·&nbsp; India / Russia &nbsp;·&nbsp;
    Iran / Israel &nbsp;·&nbsp; India / China &nbsp;·&nbsp; Pakistan / Afghanistan
    </div>
    """, unsafe_allow_html=True)

    if run_traj:
        with st.spinner(""):
            weekly_data, total = get_trajectory(e1, e2)

        if not weekly_data:
            st.markdown(f"""
            <div style="font-family:IBM Plex Mono;font-size:11px;color:#5A3A3A;
                 border:1px solid #2A1A1A;padding:14px 18px;background:#0D0A0A">
            ▪ NO TRAJECTORY DATA — {e1.upper()} ↔ {e2.upper()}<br>
            <span style="color:#2A3A4A;font-size:9px">
            These entities may not co-occur in the current graph.
            Try: India/Iran · Iran/Israel · India/Russia
            </span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="font-family:IBM Plex Mono;font-size:10px;color:#4A6A4A;
                 border:1px solid #1A2A1A;padding:10px 16px;background:#0A0D0A;
                 margin-bottom:16px">
            ▪ {e1.upper()} ↔ {e2.upper()} &nbsp;·&nbsp;
            {total} TOTAL CO-OCCURRENCES &nbsp;·&nbsp; {len(weekly_data)} WEEK(S) OF DATA
            </div>
            """, unsafe_allow_html=True)

            import pandas as pd
            df = pd.DataFrame(weekly_data, columns=["Week", "Co-occurrences"])
            st.bar_chart(df.set_index("Week"), color="#C8A96E")

            traj_str = "\n".join([f"  {w}: {c}" for w, c in weekly_data])
            prompt = f"""You are Prajna. Analyse this trajectory for {e1} <-> {e2}:

{traj_str}
Total all-time: {total}

Provide concise analysis:
SITUATION — is this relationship intensifying, cooling, or volatile?
INFLECTION POINTS — any sharp changes and their likely causes
INDIA STRATEGIC IMPLICATIONS — what does this mean for India
WATCH FOR — specific developments to monitor

Be analytical and specific. Max 250 words."""

            with st.spinner(""):
                brief = ask_groq(prompt)

            st.markdown(f"""
            <div class="brief-container">
                <div class="brief-header">▪ TRAJECTORY INTERPRETATION — {e1.upper()} ↔ {e2.upper()}</div>
                {brief.replace(chr(10), "<br>")}
            </div>
            """, unsafe_allow_html=True)

# ── TAB 3: PATH QUERY ──────────────────
with tab3:
    st.markdown('<div class="section-label">Graph Path Query</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family:IBM Plex Mono;font-size:10px;color:#3A5068;margin-bottom:20px;line-height:1.7">
    Finds the shortest connection path between any two entities in the knowledge graph.<br>
    Surfaces non-obvious relationships invisible to human analysts and impossible for LLMs.
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        p1 = st.text_input("ORIGIN ENTITY", value="India", key="path_p1")
    with col2:
        p2 = st.text_input("TARGET ENTITY", value="Taliban", key="path_p2")
    with col3:
        st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
        run_path = st.button("FIND PATH ▶", key="run_path")

    st.markdown("""
    <div style="font-family:IBM Plex Mono;font-size:9px;color:#2A3A4A;
         letter-spacing:0.1em;margin-bottom:16px">
    SUGGESTED PAIRS — India → Taliban &nbsp;·&nbsp; Russia → Taliban &nbsp;·&nbsp;
    Israel → Pakistan &nbsp;·&nbsp; India → Dubai
    </div>
    """, unsafe_allow_html=True)

    if run_path:
        with st.spinner(""):
            path = find_path(p1, p2)

        if not path:
            st.markdown(f"""
            <div style="font-family:IBM Plex Mono;font-size:11px;color:#5A3A3A;
                 border:1px solid #2A1A1A;padding:14px 18px;background:#0D0A0A">
            ▪ NO PATH FOUND — {p1.upper()} → {p2.upper()}<br>
            <span style="color:#2A3A4A;font-size:9px">
            No connection within 4 hops. Try different entity names or pairs.
            </span>
            </div>
            """, unsafe_allow_html=True)
        else:
            nodes     = path["nodes"]
            strengths = path["strengths"]

            st.markdown(f"""
            <div style="font-family:IBM Plex Mono;font-size:10px;color:#4A6A4A;
                 border:1px solid #1A2A1A;padding:10px 16px;background:#0A0D0A;
                 margin-bottom:16px">
            ▪ PATH FOUND &nbsp;·&nbsp; {path["hops"]} HOP(S) &nbsp;·&nbsp;
            {p1.upper()} → {p2.upper()}
            </div>
            """, unsafe_allow_html=True)

            path_str = ""
            nodes_html = ""
            for i, node in enumerate(nodes):
                if i == 0:
                    nodes_html += f'<div class="path-node start">▶ &nbsp; {node.upper()}</div>'
                    path_str   += node
                elif i == len(nodes)-1:
                    nodes_html += f'<div class="path-node end">◼ &nbsp; {node.upper()}</div>'
                    path_str   += node
                else:
                    nodes_html += f'<div class="path-node mid">◦ &nbsp; {node}</div>'
                    path_str   += node

                if i < len(strengths):
                    nodes_html += f'<div class="path-connector">│ co-occurs {strengths[i]}× in news</div>'
                    path_str   += f" --[{strengths[i]}x]--> "

            st.markdown(nodes_html, unsafe_allow_html=True)

            prompt = f"""You are Prajna. A graph path query revealed this connection:

PATH: {path_str}
HOPS: {path["hops"]}

Each arrow = two entities co-appearing in real news articles.
The number = frequency of co-appearance.

Analyse:
HIDDEN CONNECTION — what does this path mean in plain English?
STRATEGIC SIGNIFICANCE — why does this matter for India specifically?
NON-OBVIOUS INSIGHT — what would an analyst miss without this graph?
RECOMMENDED ACTION — one specific action for Indian policymakers

Be direct and specific. Max 220 words."""

            with st.spinner(""):
                brief = ask_groq(prompt)

            st.markdown(f"""
            <div class="brief-container" style="margin-top:16px">
                <div class="brief-header">▪ PATH INTELLIGENCE — {p1.upper()} → {p2.upper()}</div>
                {brief.replace(chr(10), "<br>")}
            </div>
            """, unsafe_allow_html=True)

# ── TAB 4: SURGE DETECTION ─────────────
with tab4:
    st.markdown('<div class="section-label">Automated Surge Detection</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family:IBM Plex Mono;font-size:10px;color:#3A5068;margin-bottom:20px;line-height:1.7">
    Monitors the knowledge graph for entities whose news co-occurrence is growing anomalously fast.<br>
    No query required — Prajna surfaces what you did not know to ask about.
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        threshold = st.slider(
            "SURGE THRESHOLD (× WEEKLY BASELINE)",
            1.2, 3.0, 1.5, 0.1
        )
    with col2:
        st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
        run_surge = st.button("SCAN GRAPH ▶", key="run_surge")

    if run_surge:
        with st.spinner(""):
            surges = detect_surges(threshold=threshold)

        if not surges:
            st.markdown(f"""
            <div style="font-family:IBM Plex Mono;font-size:11px;color:#3A5068;
                 border:1px solid #1C2A38;padding:14px 18px;background:#0D1117;
                 margin-bottom:16px">
            ▪ NO SURGES DETECTED ABOVE {threshold}× THRESHOLD<br>
            <span style="font-size:9px;color:#2A3A4A">
            Week 1 — baselines being established.
            Surge detection activates fully from Week 2 as historical patterns accumulate.
            </span>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="section-label" style="margin-top:20px">Current Graph — Top Entities by Connection Strength</div>', unsafe_allow_html=True)
            with driver.session() as session:
                top = session.run("""
                    MATCH (e:Entity)-[r:CO_OCCURS_WITH]-()
                    RETURN e.name AS name, e.type AS type, count(r) AS conn
                    ORDER BY conn DESC LIMIT 12
                """).data()

            rows_html = ""
            for row in top:
                if row["type"] in {"GPE","ORG","PERSON"} and len(row["name"]) < 35:
                    bar_w = min(int(row["conn"] * 3), 200)
                    rows_html += f"""
                    <div class="context-item">
                        <span>{row["name"].upper()}</span>
                        <span style="display:flex;align-items:center;gap:10px">
                            <span style="width:{bar_w}px;height:2px;
                                  background:#1C2A38;display:inline-block"></span>
                            <span class="context-strength">{row["conn"]} conn</span>
                        </span>
                    </div>"""

            st.markdown(f"""
            <div style="border:1px solid #1C2A38;background:#0D1117">
                {rows_html}
            </div>
            """, unsafe_allow_html=True)

        else:
            st.markdown(f"""
            <div style="font-family:IBM Plex Mono;font-size:10px;color:#C87B6A;
                 border:1px solid #2A1A1A;padding:10px 16px;background:#0D0A0A;
                 margin-bottom:16px">
            ▪ {len(surges)} ENTITIES FLAGGED ABOVE {threshold}× BASELINE
            </div>
            """, unsafe_allow_html=True)

            for surge in surges:
                bar_w = min(int(surge["ratio"] * 40), 160)
                st.markdown(f"""
                <div class="surge-card">
                    <div class="surge-entity">▲ {surge["entity"]}</div>
                    <div class="surge-ratio">{surge["ratio"]}× baseline
                        &nbsp;·&nbsp; {surge["latest"]} connections this week
                        &nbsp;·&nbsp; baseline: {surge["baseline"]}/week
                    </div>
                </div>
                """, unsafe_allow_html=True)

                prompt = f"""Prajna surge alert:
Entity: {surge["entity"]} ({surge["type"]})
This week: {surge["latest"]} news connections
Baseline avg: {surge["baseline"]} per week
Surge ratio: {surge["ratio"]}×

SURGE EXPLANATION — why is this entity surging?
INDIA RISK / OPPORTUNITY — strategic implications
URGENCY — Immediate / Days / Weeks
RECOMMENDED ACTION — one specific action

Max 130 words. Be direct."""

                with st.spinner(""):
                    brief = ask_groq(prompt)

                st.markdown(f"""
                <div class="brief-container" style="border-left-color:#8A4A3A;margin-bottom:20px">
                    <div class="brief-header" style="color:#C87B6A">
                        ▪ SURGE BRIEF — {surge["entity"].upper()}
                    </div>
                    {brief.replace(chr(10), "<br>")}
                </div>
                """, unsafe_allow_html=True)
