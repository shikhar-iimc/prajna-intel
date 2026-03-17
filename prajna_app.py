# ════════════════════════════════════════════════════════════════
# PRAJNA INTELLIGENCE SUITE — prajna_app.py
# Prajna · Raksha · Artha · Sangam
# India Innovates 2026 · TeamIIMC · IIM Calcutta
# ════════════════════════════════════════════════════════════════

import streamlit as st
from neo4j import GraphDatabase
from groq import Groq
from pyvis.network import Network
import streamlit.components.v1 as components
import os, json, pandas as pd, io
from collections import defaultdict
from datetime import datetime, timezone
from fpdf import FPDF

def _get_secret(key):
    val = os.environ.get(key)
    if val:
        return val
    try:
        from google.colab import userdata
        return userdata.get(key)
    except Exception:
        pass
    try:
        return st.secrets.get(key)
    except Exception:
        return None

NEO4J_URI        = _get_secret("NEO4J_URI")
NEO4J_USERNAME   = _get_secret("NEO4J_USERNAME")
NEO4J_PASSWORD   = _get_secret("NEO4J_PASSWORD")
GROQ_API_KEY     = _get_secret("GROQ_API_KEY")
NEO4J_URI_2      = _get_secret("NEO4J_URI_2")
NEO4J_USERNAME_2 = _get_secret("NEO4J_USERNAME_2")
NEO4J_PASSWORD_2 = _get_secret("NEO4J_PASSWORD_2")

LOGO_B64 = ""  # unused, logo loaded directly from GitHub

@st.cache_resource
def get_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

@st.cache_resource
def get_driver_2():
    try:
        return GraphDatabase.driver(NEO4J_URI_2, auth=(NEO4J_USERNAME_2, NEO4J_PASSWORD_2))
    except:
        return None

@st.cache_resource
def get_groq():
    return Groq(api_key=GROQ_API_KEY)

driver      = get_driver()
driver_2    = get_driver_2()
groq_client = get_groq()

def get_week_key():
    now = datetime.now(timezone.utc)
    return f"{now.year}-W{now.strftime('%W')}"

def ask_groq(prompt, max_tokens=600):
    r = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens, temperature=0.3
    )
    return r.choices[0].message.content

def render_sources(sources, color="#C8A96E"):
    """Render a styled source bar below any brief. sources = list of (title, source_name) tuples."""
    if not sources:
        return
    src_html = (
        '<div style="margin-top:12px;padding-top:10px;border-top:1px solid #1C2A38;'
        'font-family:IBM Plex Mono;font-size:9px;color:#3A5068;line-height:1.8">'
        '<span style="color:' + color + ';letter-spacing:0.15em">SOURCES &nbsp;</span>'
    )
    for title, source in sources[:6]:
        if title and source:
            src_html += f'<span style="color:#3A5068">[{source}] </span><span style="color:#4A6A8A">{title[:80]}{"..." if len(title)>80 else ""}</span> &nbsp; '
    src_html += "</div>"
    st.markdown(src_html, unsafe_allow_html=True)

def sanitize(text):
    if not text:
        return ""
    replacements = {
        "\u2014": "-", "\u2013": "-", "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"', "\u2022": "*", "\u2026": "...",
        "\u00a0": " ", "\u00e9": "e", "\u00e8": "e", "\u00e0": "a",
        "\u00fb": "u", "\u00fc": "u", "\u00ef": "i", "\u00e7": "c",
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    text = text.encode("latin-1", errors="replace").decode("latin-1")
    words = text.split(" ")
    broken = []
    for w in words:
        if len(w) > 60:
            broken.append(w[:60] + " " + w[60:])
        else:
            broken.append(w)
    return " ".join(broken)

def pdf_write_line(pdf, line):
    line = line.strip()
    if not line:
        pdf.ln(3)
        return
    is_header = any(line.startswith(x) for x in [
        "STORY", "BOTTOM LINE", "WEEK", "EXECUTIVE",
        "STRATEGIC RISK", "HIGH RISK", "MEDIUM RISK", "OPPORTUNITY"
    ])
    if is_header:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(232, 213, 163)
    else:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(180, 195, 210)
    try:
        pdf.multi_cell(0, 6, line)
    except Exception:
        try:
            pdf.multi_cell(0, 6, line[:200])
        except Exception:
            pass

def generate_pdf_brief(brief_week, top_pairs, headlines, brief_text, names):
    brief_week_safe = sanitize(brief_week)
    brief_text_safe = sanitize(brief_text)

    class PDF(FPDF):
        def header(self):
            self.set_fill_color(10, 12, 15)
            self.rect(0, 0, 210, 297, 'F')
            self.set_font("Helvetica", "B", 16)
            self.set_text_color(232, 213, 163)
            self.cell(0, 12, "PRAJNA", ln=True, align="C")
            self.set_font("Helvetica", "", 8)
            self.set_text_color(74, 106, 138)
            self.cell(0, 6, "STRATEGIC INTELLIGENCE ENGINE  |  INDIA INNOVATES 2026  |  TEAM IIMC", ln=True, align="C")
            self.set_draw_color(28, 42, 56)
            self.line(15, 28, 195, 28)
            self.ln(4)
        def footer(self):
            self.set_y(-15)
            self.set_font("Helvetica", "", 7)
            self.set_text_color(42, 58, 74)
            self.cell(0, 10, "PRAJNA  |  " + brief_week_safe + "  |  CONFIDENTIAL  |  Page " + str(self.page_no()), align="C")

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(232, 213, 163)
    pdf.cell(0, 8, "WEEKLY INTELLIGENCE BRIEF  -  " + brief_week_safe, ln=True, align="C")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(74, 106, 138)
    pdf.cell(0, 6, str(len(names)) + " entities  |  " + str(len(top_pairs)) + " signal pairs  |  AUTO-GENERATED BY PRAJNA", ln=True, align="C")
    pdf.ln(6)
    pdf.set_draw_color(200, 169, 110)
    pdf.set_line_width(0.5)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(6)
    for line in brief_text_safe.split("\n"):
        pdf_write_line(pdf, line)
    pdf.ln(6)
    pdf.set_draw_color(28, 42, 56)
    pdf.set_line_width(0.3)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(74, 106, 138)
    pdf.cell(0, 6, "GRAPH SIGNAL PAIRS  -  SOURCE DATA", ln=True)
    pdf.ln(2)
    for p in top_pairs:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(200, 169, 110)
        try:
            pdf.cell(0, 5, "  " + sanitize(p["e1"]) + "  <>  " + sanitize(p["e2"]), ln=True)
        except Exception:
            pass
        arts = headlines.get(p["e1"] + " and " + p["e2"], [])
        for a in arts:
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(90, 122, 154)
            try:
                pdf.multi_cell(0, 5, "    [" + sanitize(a["source"]) + "]  " + sanitize(a["title"]))
            except Exception:
                pass
        pdf.ln(1)
    pdf.ln(4)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(42, 58, 74)
    pdf.multi_cell(0, 5, "Auto-generated by Prajna using knowledge graph analysis of real-time news data.")
    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf.read()

@st.cache_data(ttl=300)
def get_stats():
    with driver.session() as session:
        a = session.run("MATCH (a:Article) RETURN count(a) as c").single()["c"]
        e = session.run("MATCH (e:Entity)  RETURN count(e) as c").single()["c"]
        r = session.run("MATCH ()-[r:CO_OCCURS_WITH]->() RETURN count(r) as c").single()["c"]
        s = session.run("MATCH ()-[r:RELATES_TO]->() RETURN count(r) as c").single()["c"]
    return a, e, r, s

@st.cache_data(ttl=300)
def get_available_weeks():
    from datetime import datetime, timedelta
    with driver.session() as session:
        result = session.run("MATCH (a:Article) RETURN DISTINCT a.week as week ORDER BY week DESC").data()
    weeks = [r["week"] for r in result if r["week"]]
    def week_label(wk):
        try:
            monday = datetime.strptime(wk + "-1", "%Y-W%W-%w")
            sunday = monday + timedelta(days=6)
            return f"{wk}  ({monday.strftime('%d %b')} \u2013 {sunday.strftime('%d %b %Y')})"
        except:
            return wk
    return [week_label(w) for w in weeks]

def get_graph_context(keywords):
    with driver.session() as session:
        result = session.run("""
            MATCH (e:Entity)-[r:RELATES_TO]-(other:Entity)
            WHERE any(kw IN $kw WHERE toLower(e.name) CONTAINS toLower(kw))
            RETURN e.name AS e1, other.name AS e2, r.type AS rel, r.count AS strength
            ORDER BY r.count DESC LIMIT 20
        """, {"kw": keywords})
        return [(r["e1"], r["e2"], r["rel"], r["strength"]) for r in result]

def get_articles(keywords):
    with driver.session() as session:
        result = session.run("""
            MATCH (a:Article)-[:MENTIONS]->(e:Entity)
            WHERE any(kw IN $kw WHERE toLower(e.name) CONTAINS toLower(kw))
            RETURN DISTINCT a.title AS title, a.source AS source LIMIT 5
        """, {"kw": keywords})
        return [(r["title"], r["source"]) for r in result]

def get_trajectory(e1, e2):
    with driver.session() as session:
        rows = session.run("""
            MATCH (a:Article)-[:MENTIONS]->(x:Entity {name:$e1})
            MATCH (a)-[:MENTIONS]->(y:Entity {name:$e2})
            WHERE a.week IS NOT NULL
            RETURN a.week AS week, COUNT(a) AS cnt ORDER BY week
        """, {"e1": e1, "e2": e2}).data()
    if not rows:
        return None, None
    wc = {r["week"]: r["cnt"] for r in rows}
    return sorted(wc.items()), sum(wc.values())

def get_semantic_relations(entity):
    with driver.session() as session:
        outgoing = session.run("""
            MATCH (e:Entity {name:$name})-[r:RELATES_TO]->(other:Entity)
            RETURN other.name AS target, r.type AS rel, r.count AS cnt
            ORDER BY cnt DESC LIMIT 15
        """, {"name": entity}).data()
        incoming = session.run("""
            MATCH (other:Entity)-[r:RELATES_TO]->(e:Entity {name:$name})
            RETURN other.name AS source, r.type AS rel, r.count AS cnt
            ORDER BY cnt DESC LIMIT 15
        """, {"name": entity}).data()
    return outgoing, incoming

def find_path(e1, e2):
    with driver.session() as session:
        # Use CONTAINS for fuzzy matching, try multiple candidate pairs
        result = session.run("""
            MATCH (a:Entity) WHERE toLower(a.name) CONTAINS toLower($e1)
            WITH a LIMIT 5
            MATCH (b:Entity) WHERE toLower(b.name) CONTAINS toLower($e2)
            WITH a, b LIMIT 25
            MATCH path = shortestPath((a)-[:CO_OCCURS_WITH*1..4]-(b))
            RETURN [node IN nodes(path) | node.name] AS nodes,
                   [rel IN relationships(path) | rel.count] AS strengths,
                   length(path) AS hops
            ORDER BY hops ASC LIMIT 1
        """, {"e1": e1, "e2": e2}).single()
    if not result:
        return None
    return {"nodes": result["nodes"], "strengths": result["strengths"], "hops": result["hops"]}

BLOCKLIST = {
    "Supreme","Asian","Islam","American","European","Western","Eastern",
    "BBC","CNN","Reuters","Bloomberg","NDTV","Mint","Hindu","Express",
    "ANI","PTI","AFP","AP","Wire","Tribune","Times","Globe","Newswire",
    "NewsAPI","Monday","Tuesday","Wednesday","Thursday","Friday",
    "January","February","March","April","May","June",
    "July","August","September","October","November","December",
    "New Year","World","Global","International","National"
}

def detect_surges(threshold=1.5, top_n=5):
    week_key = get_week_key()
    with driver.session() as session:
        results = session.run("""
            MATCH (a:Article)-[:MENTIONS]->(e:Entity)
            WHERE a.week IS NOT NULL AND e.type IN ["GPE","ORG","PERSON","NORP"]
            RETURN e.name AS entity, e.type AS type, a.week AS week, COUNT(a) AS cnt
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
        if entity in BLOCKLIST: continue
        if entity_total[entity] < 8: continue
        if len(entity) > 35: continue
        if any(c.isdigit() for c in entity): continue
        if entity_type.get(entity) not in {"GPE","ORG","PERSON","NORP"}: continue
        weeks = sorted(weekly.keys())
        if not weeks or weeks[-1] != week_key: continue
        latest   = weekly[weeks[-1]]
        hist     = [weekly[w] for w in weeks[:-1]]
        baseline = sum(hist)/len(hist) if hist else latest
        if baseline == 0: continue
        ratio = latest / baseline
        if ratio >= threshold:
            surges.append({"entity": entity, "type": entity_type.get(entity, ""),
                           "latest": latest, "baseline": round(baseline, 1),
                           "ratio": round(ratio, 2), "total": entity_total[entity]})
    surges.sort(key=lambda x: x["ratio"], reverse=True)
    return surges[:top_n]

RELATION_COLORS = {
    "THREATENS": "#C87B6A", "ATTACKS": "#C87B6A", "CONFLICTS_WITH": "#C87B6A", "DEFEATS": "#C87B6A",
    "SUPPLIES_WEAPONS_TO": "#C8956A", "DEPLOYS_FORCES_IN": "#C8956A", "OCCUPIES": "#C8956A",
    "SANCTIONS": "#C8B86A", "ACCUSES": "#C8B86A", "CONDEMNS": "#C8B86A", "OPPOSES": "#C8B86A",
    "PROTESTS_AGAINST": "#C8B86A", "DISPUTES_TERRITORY_WITH": "#C8B86A", "EXPELS": "#C8B86A",
    "IMPORTS_FROM": "#6B8CAE", "EXPORTS_TO": "#6B8CAE", "TRADES_WITH": "#6B8CAE",
    "COMPETES_WITH": "#6B8CAE", "DEPENDS_ON": "#6B8CAE", "OWNS": "#6B8CAE",
    "ALLIES_WITH": "#4A8A6A", "SUPPORTS": "#4A8A6A", "COOPERATES_WITH": "#4A8A6A",
    "FUNDS": "#4A8A6A", "RECOGNIZES": "#4A8A6A",
    "GOVERNS": "#8A6AAE", "CONTROLS": "#8A6AAE", "LEADS": "#8A6AAE", "ELECTS": "#8A6AAE",
    "NEGOTIATES_WITH": "#4A8AAA", "MEDIATES": "#4A8AAA", "INFLUENCES": "#4A8AAA", "INVESTS_IN": "#4A8AAA",
}

NET_OPTIONS = '''{"physics":{"forceAtlas2Based":{"gravitationalConstant":-120,"centralGravity":0.03,"springLength":120,"springConstant":0.08,"damping":0.9,"avoidOverlap":0.8},"solver":"forceAtlas2Based","stabilization":{"iterations":200,"fit":true},"minVelocity":0.5},"edges":{"smooth":{"type":"curvedCW","roundness":0.15},"color":{"opacity":0.5},"arrows":{"to":{"enabled":true,"scaleFactor":0.3}},"font":{"size":0},"scaling":{"min":1,"max":4}},"nodes":{"borderWidth":1,"borderWidthSelected":3,"font":{"size":11,"face":"IBM Plex Mono"}},"interaction":{"hover":true,"tooltipDelay":80,"navigationButtons":false,"zoomView":true}}'''

def build_graph_visual(keyword=None, week=None, mode="semantic"):
    TYPE_COLORS = {"GPE": "#C8A96E", "ORG": "#6B8CAE", "PERSON": "#A8C5A0",
                   "NORP": "#B8956A", "LOC": "#8AABBA", "EVENT": "#C47B6E"}
    kw_list = [k.strip().lower() for k in keyword.split(",") if k.strip()] if keyword else []
    with driver.session() as session:
        if mode == "semantic":
            if kw_list:
                seed_results = session.run("""
                    MATCH (e:Entity)
                    WHERE any(kw IN $kw_list WHERE toLower(e.name) CONTAINS kw)
                    RETURN e.name AS name, e.type AS type LIMIT 20
                """, {"kw_list": kw_list})
                seeds = [r["name"] for r in seed_results]
                if not seeds:
                    res = session.run("""
                        MATCH (node:Entity)-[r:RELATES_TO]-()
                        WITH node, COUNT(r) AS conn ORDER BY conn DESC LIMIT 40
                        RETURN node.name AS name, node.type AS type, conn
                    """)
                    top = {r["name"]: r for r in res}
                else:
                    nb_results = session.run("""
                        MATCH (e:Entity)-[:RELATES_TO]-(nb:Entity) WHERE e.name IN $seeds
                        WITH COLLECT(DISTINCT nb.name) AS neighbors RETURN neighbors
                    """, {"seeds": seeds})
                    nb_row    = nb_results.single()
                    neighbors = nb_row["neighbors"] if nb_row else []
                    all_names = list(set(seeds + neighbors))
                    node_results = session.run("""
                        MATCH (node:Entity)-[r:RELATES_TO]-() WHERE node.name IN $all_names
                        WITH node, COUNT(r) AS conn ORDER BY conn DESC LIMIT 40
                        RETURN node.name AS name, node.type AS type, conn
                    """, {"all_names": all_names})
                    top = {r["name"]: r for r in node_results}
            else:
                res = session.run("""
                    MATCH (node:Entity)-[r:RELATES_TO]-()
                    WITH node, COUNT(r) AS conn ORDER BY conn DESC LIMIT 40
                    RETURN node.name AS name, node.type AS type, conn
                """)
                top = {r["name"]: r for r in res}
            rels = session.run("""
                MATCH (e1:Entity)-[r:RELATES_TO]->(e2:Entity)
                WHERE e1.name IN $names AND e2.name IN $names
                RETURN e1.name AS source, e2.name AS target, r.type AS rel_type, r.count AS weight
                ORDER BY weight DESC
            """, {"names": list(top.keys())})
            relationships = [dict(r) for r in rels]
        else:
            if week:
                if kw_list:
                    res = session.run("""
                        MATCH (a:Article {week:$week})-[:MENTIONS]->(e:Entity)
                        WHERE any(kw IN $kw_list WHERE toLower(e.name) CONTAINS kw)
                        WITH COLLECT(DISTINCT e) AS seed UNWIND seed AS e
                        MATCH (e)-[:CO_OCCURS_WITH]-(other:Entity)
                        WITH COLLECT(DISTINCT e)+COLLECT(DISTINCT other) AS nl
                        UNWIND nl AS node WITH DISTINCT node
                        MATCH (node)-[r:CO_OCCURS_WITH]-() WHERE r.weekly_counts_json CONTAINS $week
                        WITH node, COUNT(r) AS conn ORDER BY conn DESC LIMIT 40
                        RETURN node.name AS name, node.type AS type, conn
                    """, {"week": week, "kw_list": kw_list})
                else:
                    res = session.run("""
                        MATCH (a:Article {week:$week})-[:MENTIONS]->(e:Entity)
                        WITH DISTINCT e MATCH (e)-[r:CO_OCCURS_WITH]-()
                        WHERE r.weekly_counts_json CONTAINS $week
                        WITH e, COUNT(r) AS conn ORDER BY conn DESC LIMIT 40
                        RETURN e.name AS name, e.type AS type, conn
                    """, {"week": week})
            else:
                if kw_list:
                    res = session.run("""
                        MATCH (e:Entity) WHERE any(kw IN $kw_list WHERE toLower(e.name) CONTAINS kw)
                        WITH e MATCH (e)-[:CO_OCCURS_WITH]-(other:Entity)
                        WITH collect(DISTINCT e)+collect(DISTINCT other) AS nl
                        UNWIND nl AS node WITH DISTINCT node
                        MATCH (node)-[r:CO_OCCURS_WITH]-()
                        WITH node, COUNT(r) AS conn ORDER BY conn DESC LIMIT 40
                        RETURN node.name AS name, node.type AS type, conn
                    """, {"kw_list": kw_list})
                else:
                    res = session.run("""
                        MATCH (node:Entity)-[r:CO_OCCURS_WITH]-()
                        WITH node, COUNT(r) AS conn ORDER BY conn DESC LIMIT 40
                        RETURN node.name AS name, node.type AS type, conn
                    """)
            top = {r["name"]: r for r in res}
            if week:
                rels = session.run("""
                    MATCH (e1:Entity)-[r:CO_OCCURS_WITH]-(e2:Entity)
                    WHERE e1.name IN $names AND e2.name IN $names AND r.weekly_counts_json IS NOT NULL
                    RETURN e1.name AS source, e2.name AS target, r.weekly_counts_json AS wcj
                """, {"names": list(top.keys())})
                relationships = []
                for r in rels:
                    try:
                        wc = json.loads(r["wcj"]) if r["wcj"] else {}
                    except:
                        wc = {}
                    w = wc.get(week, 0)
                    if w >= 1:
                        relationships.append({"source": r["source"], "target": r["target"],
                                              "weight": w, "rel_type": "CO_OCCURS_WITH"})
            else:
                rels = session.run("""
                    MATCH (e1:Entity)-[r:CO_OCCURS_WITH]-(e2:Entity)
                    WHERE e1.name IN $names AND e2.name IN $names AND r.count >= 2
                    RETURN e1.name AS source, e2.name AS target, r.count AS weight
                """, {"names": list(top.keys())})
                relationships = [{"source": r["source"], "target": r["target"],
                                   "weight": r["weight"], "rel_type": "CO_OCCURS_WITH"} for r in rels]

    net = Network(height="480px", width="100%", bgcolor="#0A0C0F",
                  font_color="#8A9BB0", notebook=False, cdn_resources="in_line")
    net.set_options(NET_OPTIONS)
    for name, data in top.items():
        is_india = (name == "India")
        is_seed  = bool(kw_list and any(kw in name.lower() for kw in kw_list))
        color    = "#E8D5A3" if is_india else TYPE_COLORS.get(data["type"], "#5A6A7A")
        border   = "#FFFFFF" if is_india else ("#E8D5A3" if is_seed else color)
        size     = 58 if is_india else (40 if is_seed else min(12 + data["conn"] * 1.8, 38))
        net.add_node(name, label=name,
            color={"background": color, "border": border,
                   "highlight": {"background": "#E8D5A3", "border": "#FFFFFF"}},
            size=size, title=f"{data['type']} · {data['conn']} connections",
            font={"size": 11, "color": "#C8D4E0", "face": "IBM Plex Mono"})
    for r in relationships:
        if r["source"] in top and r["target"] in top:
            rel_type   = r.get("rel_type", "CO_OCCURS_WITH")
            edge_color = RELATION_COLORS.get(rel_type, "#3A5068")
            net.add_edge(r["source"], r["target"],
                value=min((r["weight"] or 1) * 0.4, 4),
                title=rel_type.replace("_", " ") + "  (" + str(r["weight"]) + "x)",
                color={"color": edge_color, "highlight": "#E8D5A3"})
    net.save_graph("graph_visual.html")
    with open("graph_visual.html", "r") as f:
        return f.read()

# Cyber relationship type colors (for semantic mode)
CYBER_RELATION_COLORS = {
    "EXPLOITS":        "#C87B6A",
    "TARGETS":         "#C8956A",
    "DEPLOYS":         "#B8476E",
    "ATTRIBUTED_TO":   "#C8956A",
    "AFFECTS":         "#C8B86A",
    "MITIGATED_BY":    "#4A8A6A",
    "OPERATES_IN":     "#6B8CAE",
    "COLLABORATES_WITH":"#4A8AAA",
    "SPONSORED_BY":    "#8A6AAE",
    "RESPONDS_TO":     "#4A8A6A",
    "DETECTED_BY":     "#4A8A6A",
    "PATCHES":         "#4A8A6A",
}

def build_cyber_graph(keyword=None, mode="co-occurrence"):
    CYBER_COLORS = {"THREAT_ACTOR": "#C47B6E", "CVE": "#E8D5A3", "MALWARE": "#B8476E",
                    "CYBER_ORG": "#6B8CAE", "SECTOR": "#A8C5A0", "ORG": "#6B8CAE", "GPE": "#C8A96E"}
    with driver_2.session() as s:
        if mode == "semantic":
            if keyword:
                kw_words = [w for w in keyword.strip().split() if len(w) > 2] or [keyword.strip()]
                seeds = s.run("""
                    MATCH (e:CyberEntity)
                    WHERE any(w IN $words WHERE toLower(e.name) CONTAINS toLower(w))
                    RETURN e.name AS name, e.type AS type LIMIT 10
                """, {"words": kw_words}).data()
                seed_names = [r["name"] for r in seeds]
                if not seed_names:
                    seed_names = []
                rows = s.run("""
                    MATCH (e1:CyberEntity)-[r:CYBER_RELATES_TO]->(e2:CyberEntity)
                    WHERE e1.name IN $seeds OR e2.name IN $seeds
                    RETURN e1.name AS e1, e1.type AS t1,
                           e2.name AS e2, e2.type AS t2,
                           r.type AS rel_type, r.count AS count
                    ORDER BY r.count DESC LIMIT 40
                """, {"seeds": seed_names}).data()
            else:
                rows = s.run("""
                    MATCH (e1:CyberEntity)-[r:CYBER_RELATES_TO]->(e2:CyberEntity)
                    RETURN e1.name AS e1, e1.type AS t1,
                           e2.name AS e2, e2.type AS t2,
                           r.type AS rel_type, r.count AS count
                    ORDER BY r.count DESC LIMIT 60
                """).data()
        else:
            if keyword:
                kw_words = [w for w in keyword.strip().split() if len(w) > 2] or [keyword.strip()]
                rows = s.run("""
                    MATCH (e:CyberEntity)
                    WHERE any(w IN $words WHERE toLower(e.name) CONTAINS toLower(w))
                    WITH e LIMIT 5
                    MATCH (e)-[r:CYBER_CO_OCCURS]-(other:CyberEntity)
                    RETURN e.name AS e1, "ORG" AS t1,
                           other.name AS e2, other.type AS t2,
                           "CYBER_CO_OCCURS" AS rel_type, r.count AS count
                    ORDER BY r.count DESC LIMIT 30
                """, {"words": kw_words}).data()
            else:
                rows = s.run("""
                    MATCH (e:CyberEntity)
                    WITH e, COUNT{(e)-[:CYBER_CO_OCCURS]-()} AS conn
                    ORDER BY conn DESC LIMIT 40
                    WITH collect(e) AS top_nodes
                    UNWIND top_nodes AS e
                    MATCH (e)-[r:CYBER_CO_OCCURS]-(other:CyberEntity)
                    WHERE other IN top_nodes
                    RETURN e.name AS e1, e.type AS t1,
                           other.name AS e2, other.type AS t2,
                           "CYBER_CO_OCCURS" AS rel_type, r.count AS count
                    ORDER BY r.count DESC LIMIT 60
                """).data()

    net = Network(height="460px", width="100%", bgcolor="#0A0C0F",
                  font_color="#8A9BB0", notebook=True, cdn_resources="in_line")
    net.set_options(NET_OPTIONS)
    nodes_seen = set()
    for r in rows:
        for name, ntype in [(r["e1"], r.get("t1","ORG")), (r["e2"], r.get("t2","ORG"))]:
            if name not in nodes_seen:
                nodes_seen.add(name)
                color = CYBER_COLORS.get(ntype, "#5A6A7A")
                size  = 28 if ntype == "THREAT_ACTOR" else (22 if ntype == "SECTOR" else 16)
                net.add_node(name, label=name,
                             color={"background": color, "border": color,
                                    "highlight": {"background": "#E8D5A3", "border": "#FFFFFF"}},
                             size=size, title=f"{ntype}",
                             font={"size": 11, "color": "#C8D4E0"})
        rel_type   = r.get("rel_type", "CYBER_CO_OCCURS")
        edge_color = CYBER_RELATION_COLORS.get(rel_type, "#2A3A4A")
        net.add_edge(r["e1"], r["e2"],
                     value=min(r["count"]*0.4, 4),
                     title=rel_type.replace("_", " ") + f" ({r['count']}x)",
                     color={"color": edge_color, "highlight": "#C8A96E"})
    net.save_graph("raksha_graph.html")
    with open("raksha_graph.html", "r", encoding="utf-8") as f:
        return f.read()

# Financial relationship type colors (for semantic mode)
FIN_RELATION_COLORS = {
    "SANCTIONED_BY":    "#C87B6A",
    "OWNS":             "#C8956A",
    "CONTROLS":         "#C8956A",
    "INCORPORATED_IN":  "#6B8CAE",
    "ASSOCIATED_WITH":  "#C8B86A",
    "INVESTIGATED_BY":  "#C87B6A",
    "TRANSACTS_WITH":   "#4A8AAA",
    "FRONT_FOR":        "#B8476E",
    "DESIGNATED_UNDER": "#C8B86A",
    "LINKED_TO":        "#4A8AAA",
}

def build_financial_graph(keyword=None, mode="co-occurrence"):
    ARTHA_COLORS = {"SANCTIONED_PERSON": "#C47B6E", "SANCTIONED_ORG": "#E8D5A3",
                    "SANCTIONS_BODY": "#6B8CAE", "JURISDICTION": "#A8C5A0",
                    "FINANCIAL_CRIME": "#B8476E", "ORG": "#6B8CAE",
                    "GPE": "#C8A96E", "PERSON": "#A8C5A0"}
    with driver_2.session() as s:
        if mode == "semantic":
            if keyword:
                kw_words = [w for w in keyword.strip().split() if len(w) > 2] or [keyword.strip()]
                seeds = s.run("""
                    MATCH (e:FinancialEntity)
                    WHERE any(w IN $words WHERE toLower(e.name) CONTAINS toLower(w))
                    RETURN e.name AS name, e.type AS type LIMIT 10
                """, {"words": kw_words}).data()
                seed_names = [r["name"] for r in seeds]
                rows = s.run("""
                    MATCH (e1:FinancialEntity)-[r:FIN_RELATES_TO]->(e2:FinancialEntity)
                    WHERE e1.name IN $seeds OR e2.name IN $seeds
                    RETURN e1.name AS e1, e1.type AS t1,
                           e2.name AS e2, e2.type AS t2,
                           r.type AS rel_type, r.count AS count
                    ORDER BY r.count DESC LIMIT 40
                """, {"seeds": seed_names}).data()
            else:
                rows = s.run("""
                    MATCH (e1:FinancialEntity)-[r:FIN_RELATES_TO]->(e2:FinancialEntity)
                    RETURN e1.name AS e1, e1.type AS t1,
                           e2.name AS e2, e2.type AS t2,
                           r.type AS rel_type, r.count AS count
                    ORDER BY r.count DESC LIMIT 60
                """).data()
        else:
            if keyword:
                kw_words = [w for w in keyword.strip().split() if len(w) > 2] or [keyword.strip()]
                rows = s.run("""
                    MATCH (e:FinancialEntity)
                    WHERE any(w IN $words WHERE toLower(e.name) CONTAINS toLower(w))
                    WITH e LIMIT 3
                    MATCH (e)-[r:FIN_CO_OCCURS]-(other:FinancialEntity)
                    RETURN e.name AS e1, e.type AS t1,
                           other.name AS e2, other.type AS t2,
                           "FIN_CO_OCCURS" AS rel_type, r.count AS count
                    ORDER BY r.count DESC LIMIT 30
                """, {"words": kw_words}).data()
            else:
                rows = s.run("""
                    MATCH (e:FinancialEntity)
                    WITH e, COUNT{(e)-[:FIN_CO_OCCURS]-()} AS conn
                    ORDER BY conn DESC LIMIT 40
                    WITH collect(e) AS top_nodes
                    UNWIND top_nodes AS e
                    MATCH (e)-[r:FIN_CO_OCCURS]-(other:FinancialEntity)
                    WHERE other IN top_nodes
                    RETURN e.name AS e1, e.type AS t1,
                           other.name AS e2, other.type AS t2,
                           "FIN_CO_OCCURS" AS rel_type, r.count AS count
                    ORDER BY r.count DESC LIMIT 60
                """).data()

    net = Network(height="460px", width="100%", bgcolor="#0A0C0F",
                  font_color="#8A9BB0", notebook=True, cdn_resources="in_line")
    net.set_options(NET_OPTIONS)
    nodes_seen = set()
    for r in rows:
        for name, ntype in [(r["e1"], r.get("t1","SANCTIONED_ORG")), (r["e2"], r.get("t2","SANCTIONED_ORG"))]:
            if name not in nodes_seen:
                nodes_seen.add(name)
                color = ARTHA_COLORS.get(ntype, "#5A6A7A")
                size  = 30 if ntype in ("SANCTIONED_PERSON","SANCTIONED_ORG") else 16
                net.add_node(name, label=name,
                             color={"background": color, "border": color,
                                    "highlight": {"background": "#E8D5A3", "border": "#FFFFFF"}},
                             size=size, title=f"{ntype}",
                             font={"size": 11, "color": "#C8D4E0"})
        rel_type   = r.get("rel_type", "FIN_CO_OCCURS")
        edge_color = FIN_RELATION_COLORS.get(rel_type, "#2A3A4A")
        net.add_edge(r["e1"], r["e2"],
                     value=min(r["count"]*0.4, 4),
                     title=rel_type.replace("_", " ") + f" ({r['count']}x)",
                     color={"color": edge_color, "highlight": "#E8D5A3"})
    net.save_graph("artha_graph.html")
    with open("artha_graph.html", "r", encoding="utf-8") as f:
        return f.read()

_page_icon = "https://raw.githubusercontent.com/shikhar-iimc/prajna-intel/main/prajna_logo_main.svg"

st.set_page_config(
    page_title="PRAJNA — Intelligence Suite",
    page_icon=_page_icon,
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
*, *::before, *::after { box-sizing: border-box; }
html, body, .stApp { background-color: #0A0C0F !important; color: #C8D4E0 !important; font-family: 'IBM Plex Sans', sans-serif !important; }
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
section[data-testid="stSidebar"] { display: none; }
.prajna-nav { display: flex; align-items: center; justify-content: space-between; padding: 0 0 20px 0; border-bottom: 1px solid #1C2A38; margin-bottom: 20px; }
.prajna-logo { font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; letter-spacing: 0.25em; color: #E8D5A3; text-transform: uppercase; }
.prajna-logo span { color: #4A6A8A; margin: 0 12px; }
.prajna-meta { font-family: 'IBM Plex Mono', monospace; font-size: 10px; color: #3A5068; letter-spacing: 0.1em; text-transform: uppercase; }
.prajna-status { display: flex; align-items: center; gap: 6px; font-family: 'IBM Plex Mono', monospace; font-size: 10px; color: #4A8A6A; letter-spacing: 0.1em; }
.status-dot { width: 6px; height: 6px; background: #4A8A6A; border-radius: 50%; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.3; } }
.stTabs [data-baseweb="tab-list"] { background: transparent !important; border-bottom: 1px solid #1C2A38 !important; gap: 0 !important; padding: 0 !important; }
.stTabs [data-baseweb="tab"] { font-family: 'IBM Plex Mono', monospace !important; font-size: 10px !important; font-weight: 500 !important; letter-spacing: 0.15em !important; text-transform: uppercase !important; color: #3A5068 !important; background: transparent !important; border: none !important; border-bottom: 2px solid transparent !important; padding: 10px 20px !important; border-radius: 0 !important; }
.stTabs [aria-selected="true"] { color: #E8D5A3 !important; border-bottom: 2px solid #E8D5A3 !important; background: transparent !important; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 24px !important; background: transparent !important; }
.stTextInput > div > div > input { background: #0D1117 !important; border: 1px solid #1C2A38 !important; border-radius: 0 !important; color: #C8D4E0 !important; font-family: 'IBM Plex Mono', monospace !important; font-size: 13px !important; padding: 10px 14px !important; }
.stTextInput > div > div > input:focus { border-color: #C8A96E !important; box-shadow: none !important; }
.stTextInput label { font-family: 'IBM Plex Mono', monospace !important; font-size: 9px !important; text-transform: uppercase !important; letter-spacing: 0.15em !important; color: #3A5068 !important; }
.stSelectbox > div > div { background: #0D1117 !important; border: 1px solid #1C2A38 !important; border-radius: 0 !important; color: #C8D4E0 !important; font-family: 'IBM Plex Mono', monospace !important; font-size: 11px !important; }
.stSelectbox label { font-family: 'IBM Plex Mono', monospace !important; font-size: 9px !important; text-transform: uppercase !important; letter-spacing: 0.15em !important; color: #3A5068 !important; }
.stButton > button { background: transparent !important; border: 1px solid #2A3A4A !important; border-radius: 0 !important; color: #8A9BB0 !important; font-family: 'IBM Plex Mono', monospace !important; font-size: 10px !important; font-weight: 500 !important; letter-spacing: 0.15em !important; text-transform: uppercase !important; padding: 8px 20px !important; transition: all 0.15s ease !important; }
.stButton > button:hover { background: #1C2A38 !important; border-color: #C8A96E !important; color: #E8D5A3 !important; }
.stButton > button:focus { box-shadow: none !important; outline: none !important; }
.stSlider > div > div > div { background: #1C2A38 !important; }
.stSlider label { font-family: 'IBM Plex Mono', monospace !important; font-size: 9px !important; text-transform: uppercase !important; letter-spacing: 0.15em !important; color: #3A5068 !important; }
.brief-container { border: 1px solid #1C2A38; border-left: 3px solid #C8A96E; background: #0D1117; padding: 20px 24px; margin: 16px 0; font-family: 'IBM Plex Sans', sans-serif; font-size: 13px; line-height: 1.8; color: #A8B8C8; }
.brief-header { font-family: 'IBM Plex Mono', monospace; font-size: 9px; color: #C8A96E; text-transform: uppercase; letter-spacing: 0.2em; margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px solid #1C2A38; }
.path-node { display: flex; align-items: center; gap: 12px; padding: 10px 16px; margin: 2px 0; background: #0D1117; border: 1px solid #1C2A38; font-family: 'IBM Plex Mono', monospace; font-size: 12px; color: #C8D4E0; }
.path-node.start { border-left: 3px solid #6B8CAE; }
.path-node.end { border-left: 3px solid #C8A96E; }
.path-node.mid { border-left: 3px solid #2A3A4A; margin-left: 20px; }
.path-connector { margin-left: 28px; padding: 4px 16px; font-family: 'IBM Plex Mono', monospace; font-size: 10px; color: #2A4A3A; letter-spacing: 0.1em; }
.surge-card { border: 1px solid #1C2A38; border-left: 3px solid #8A4A3A; background: #0D1117; padding: 16px 20px; margin: 8px 0; }
.surge-entity { font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; color: #E8D5A3; letter-spacing: 0.1em; text-transform: uppercase; }
.surge-ratio { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: #C87B6A; margin-top: 2px; }
.section-label { font-family: 'IBM Plex Mono', monospace; font-size: 9px; color: #3A5068; text-transform: uppercase; letter-spacing: 0.2em; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #1C2A38; }
div[data-testid="metric-container"] { background: #0D1117 !important; border: 1px solid #1C2A38 !important; border-radius: 0 !important; padding: 12px 16px !important; }
div[data-testid="metric-container"] label { font-family: 'IBM Plex Mono', monospace !important; font-size: 9px !important; text-transform: uppercase !important; letter-spacing: 0.15em !important; color: #3A5068 !important; }
div[data-testid="metric-container"] div[data-testid="stMetricValue"] { font-family: 'IBM Plex Mono', monospace !important; font-size: 20px !important; color: #E8D5A3 !important; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #0A0C0F; }
::-webkit-scrollbar-thumb { background: #1C2A38; }
.stSpinner > div { border-top-color: #C8A96E !important; }
.stAlert { background: #0D1117 !important; border: 1px solid #1C2A38 !important; border-radius: 0 !important; font-family: 'IBM Plex Mono', monospace !important; font-size: 11px !important; color: #5A7A9A !important; }
.stDownloadButton > button { background: #0D1117 !important; border: 1px solid #C8A96E !important; color: #C8A96E !important; font-family: 'IBM Plex Mono', monospace !important; font-size: 10px !important; letter-spacing: 0.15em !important; text-transform: uppercase !important; padding: 8px 20px !important; border-radius: 0 !important; }
.stDownloadButton > button:hover { background: #C8A96E !important; color: #0A0C0F !important; }
.graph-label { font-family: IBM Plex Mono, monospace; font-size: 9px; color: #3A5068; text-transform: uppercase; letter-spacing: 0.15em; margin: 16px 0 6px 0; }
</style>
""", unsafe_allow_html=True)

now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d  %H:%M UTC")
try:
    articles_n, entities_n, rels_n, semantic_n = get_stats()
except:
    articles_n, entities_n, rels_n, semantic_n = 0, 0, 0, 0

def _render_nav(now):
    logo_tag = (
        '<img src="https://raw.githubusercontent.com/shikhar-iimc/prajna-intel/main/prajna_logo_main.svg"'
        ' width="52" height="52" style="opacity:0.95"/>'
    )
    html = (
        '<div class="prajna-nav">'
        '<div style="display:flex;align-items:center;gap:16px">'
        + logo_tag +
        '<div>'
        '<div class="prajna-logo">PRAJNA<span>*</span>Intelligence Suite</div>'
        '<div class="prajna-meta" style="margin-top:4px">India Innovates 2026 &nbsp;·&nbsp; Domain 02: Digital Democracy &nbsp;·&nbsp; TeamIIMC</div>'
        '</div>'
        '</div>'
        '<div style="text-align:right">'
        '<div class="prajna-status"><div class="status-dot"></div>GRAPH ACTIVE</div>'
        '<div class="prajna-meta" style="margin-top:4px">' + now + '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)

_render_nav(now_str)

module = st.radio(
    "",
    ["PRAJNA — Strategic Intelligence", "RAKSHA — Cyber Intelligence",
     "ARTHA — Financial Intelligence", "SANGAM — Unified Intelligence"],
    horizontal=True,
    key="module_selector"
)
st.markdown("<hr style='border:1px solid #1C2A38;margin:0 0 24px 0'>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# PRAJNA MODULE
# ════════════════════════════════════════════════════════════════
if module == "PRAJNA — Strategic Intelligence":

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("ARTICLES INGESTED",  articles_n)
    c2.metric("ENTITIES MAPPED",    entities_n)
    c3.metric("CO-OCCURRENCE RELS", rels_n)
    c4.metric("SEMANTIC RELS",      semantic_n)
    c5.metric("GRAPH STATUS",       "● LIVE")
    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "INTELLIGENCE BRIEF", "TRAJECTORY ANALYSIS", "PATH QUERY",
        "SURGE DETECTION", "WEEKLY BRIEF"
    ])

    with tab1:
        # Always-visible graph — left column, brief — right column
        col_graph, col_brief = st.columns([1, 1])

        with col_graph:
            st.markdown('<div class="section-label">Knowledge Graph</div>', unsafe_allow_html=True)
            col_kw, col_gmode = st.columns([2, 1])
            with col_kw:
                graph_keyword = st.text_input("Filter entities", placeholder="India, China, Iran", key="graph_keyword")
            with col_gmode:
                selected_graph_mode = st.selectbox("Mode", ["semantic", "co-occurrence"], key="graph_mode_select")
            _is_semantic = selected_graph_mode == "semantic"
            available_weeks_graph = get_available_weeks()
            week_options_graph    = ["ALL WEEKS"] + available_weeks_graph
            selected_graph_week   = st.selectbox(
                "Week filter (co-occurrence only)",
                week_options_graph,
                key="graph_week_select",
                disabled=_is_semantic
            )

            week_param = None
            if not _is_semantic and selected_graph_week != "ALL WEEKS":
                week_param = selected_graph_week.split("  ")[0]

            with st.spinner("Rendering graph..."):
                graph_html = build_graph_visual(keyword=graph_keyword or None, week=week_param, mode=selected_graph_mode)
            components.html(graph_html, height=500, scrolling=False)

            # Entity type legend
            legend_items = [("#C8A96E","GPE"),("#6B8CAE","ORG"),("#A8C5A0","PERSON"),
                            ("#B8956A","NORP"),("#8AABBA","LOC"),("#C47B6E","EVENT")]
            legend_html = '<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:8px;margin-bottom:4px">'
            for color, label in legend_items:
                legend_html += (f'<div style="display:flex;align-items:center;gap:5px">'
                    f'<div style="width:8px;height:8px;border-radius:50%;background:{color}"></div>'
                    f'<span style="font-family:IBM Plex Mono;font-size:8px;color:#3A5068">{label}</span></div>')
            legend_html += "</div>"
            st.markdown(legend_html, unsafe_allow_html=True)

            # Semantic edge color legend (only shown in semantic mode)
            if _is_semantic:
                edge_legend_items = [
                    ("#C87B6A", "CONFLICT / THREAT"),
                    ("#C8956A", "MILITARY"),
                    ("#C8B86A", "SANCTIONS / OPPOSE"),
                    ("#6B8CAE", "TRADE / ECONOMIC"),
                    ("#4A8A6A", "ALLIANCE / SUPPORT"),
                    ("#8A6AAE", "GOVERNANCE"),
                    ("#4A8AAA", "DIPLOMACY"),
                ]
                edge_html = '<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:4px">'
                for color, label in edge_legend_items:
                    edge_html += (
                        f'<div style="display:flex;align-items:center;gap:5px">'
                        f'<div style="width:18px;height:3px;background:{color};border-radius:2px"></div>'
                        f'<span style="font-family:IBM Plex Mono;font-size:8px;color:#3A5068">{label}</span></div>'
                    )
                edge_html += "</div>"
                st.markdown(edge_html, unsafe_allow_html=True)

        with col_brief:
            st.markdown('<div class="section-label">Intelligence Query</div>', unsafe_allow_html=True)
            query_input = st.text_input("Query", placeholder="India China border / Iran nuclear / BRICS", key="query_input")
            run_query   = st.button("GENERATE BRIEF", key="run_query")

            if run_query and query_input:
                keywords = [kw.strip() for kw in query_input.replace(",", " ").split() if kw.strip()]
                with st.spinner("Querying graph..."):
                    context  = get_graph_context(keywords)
                    articles = get_articles(keywords)
                ctx_lines = [f"- {e1} {rel} {e2} (strength: {s})" for e1, e2, rel, s in context]
                art_lines = [f"[{src}] {title}" for title, src in articles]
                prompt = (
                    "You are Prajna, India's strategic intelligence engine.\n"
                    "Query: " + query_input + "\n\n"
                    "Graph context:\n" + "\n".join(ctx_lines) + "\n\n"
                    "Headlines:\n" + "\n".join(art_lines) + "\n\n"
                    "SITUATION: [2-3 sentences]\n\nCONNECTIONS: [Key graph relationships]\n\n"
                    "IMPLICATIONS FOR INDIA: [Strategic significance]\n\n"
                    "ACTION RECOMMENDED: [One specific action]\n\nMax 300 words."
                )
                with st.spinner("Generating brief..."):
                    brief = ask_groq(prompt)
                st.markdown(
                    '<div class="brief-container"><div class="brief-header">INTELLIGENCE BRIEF — '
                    + query_input.upper()[:50] + '</div>' + brief.replace("\n", "<br>") + "</div>",
                    unsafe_allow_html=True
                )
                render_sources(articles)

    with tab2:
        st.markdown('<div class="section-label">Week-on-Week Relationship Intensity</div>', unsafe_allow_html=True)
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            traj_e1 = st.text_input("Entity A", placeholder="India", key="traj_e1")
        with col_e2:
            traj_e2 = st.text_input("Entity B", placeholder="China", key="traj_e2")
        if st.button("ANALYSE TRAJECTORY", key="run_traj"):
            if not traj_e1 or not traj_e2:
                st.warning("Enter both entities.")
            else:
                trajectory, total = get_trajectory(traj_e1.strip(), traj_e2.strip())
                if not trajectory:
                    st.info(f"No co-occurrence data found for {traj_e1} ↔ {traj_e2}.")
                else:
                    weeks  = [w for w, _ in trajectory]
                    counts = [c for _, c in trajectory]
                    st.markdown(f'<div style="font-family:IBM Plex Mono;font-size:10px;color:#4A6A8A;margin-bottom:12px">{traj_e1.upper()} ↔ {traj_e2.upper()} · {total} total co-mentions</div>', unsafe_allow_html=True)
                    st.bar_chart(pd.DataFrame({"week": weeks, "co-occurrences": counts}).set_index("week"))
                    with st.spinner("Analysing pattern..."):
                        traj_str = "  ".join([f"{w}:{c}" for w, c in trajectory])
                        brief = ask_groq(f"Prajna trajectory.\nEntities: {traj_e1} and {traj_e2}\nData: {traj_str}\n\nPATTERN: intensifying/cooling/volatile?\nEXPLANATION: key drivers\nINDIA IMPLICATION:\nOUTLOOK:\nMax 200 words.")
                    st.markdown('<div class="brief-container"><div class="brief-header">TRAJECTORY — ' + traj_e1.upper() + " ↔ " + traj_e2.upper() + '</div>' + brief.replace("\n", "<br>") + "</div>", unsafe_allow_html=True)

    with tab3:
        subtab1, subtab2 = st.tabs(["GRAPH PATH QUERY", "ENTITY SEMANTIC PROFILE"])
        with subtab1:
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                path_e1 = st.text_input("From entity", placeholder="India", key="path_e1")
            with col_p2:
                path_e2 = st.text_input("To entity", placeholder="Taliban", key="path_e2")
            if st.button("FIND PATH", key="run_path"):
                if not path_e1 or not path_e2:
                    st.warning("Enter both entities.")
                else:
                    with st.spinner("Searching graph..."):
                        path = find_path(path_e1.strip(), path_e2.strip())
                    if not path:
                        st.info(f"No path found between {path_e1} and {path_e2} within 4 hops.")
                    else:
                        nodes     = path["nodes"]
                        strengths = path["strengths"]
                        hops      = path["hops"]
                        st.markdown(f'<div style="font-family:IBM Plex Mono;font-size:10px;color:#4A6A8A;margin-bottom:16px">PATH FOUND — {hops} hop{"s" if hops > 1 else ""}</div>', unsafe_allow_html=True)
                        for i, node in enumerate(nodes):
                            css_class = "start" if i == 0 else ("end" if i == len(nodes)-1 else "mid")
                            st.markdown(f'<div class="path-node {css_class}"><span style="font-family:IBM Plex Mono;font-size:10px;color:#3A5068">{i+1}</span><span>{node}</span></div>', unsafe_allow_html=True)
                            if i < len(strengths):
                                st.markdown(f'<div class="path-connector">↓ &nbsp; strength: {strengths[i]}</div>', unsafe_allow_html=True)
                        with st.spinner("Interpreting..."):
                            path_str = " → ".join(nodes)
                            brief = ask_groq(f"Prajna path: {path_str}\nINTERPRETATION: geopolitical meaning\nKEY INTERMEDIARY: most significant node\nINDIA ANGLE:\nMax 150 words.")
                        st.markdown('<div class="brief-container"><div class="brief-header">PATH INTERPRETATION</div>' + brief.replace("\n", "<br>") + "</div>", unsafe_allow_html=True)
        with subtab2:
            profile_entity = st.text_input("Entity name", placeholder="Iran", key="profile_entity")
            if st.button("BUILD PROFILE", key="run_profile"):
                if profile_entity:
                    with st.spinner("Building profile..."):
                        outgoing, incoming = get_semantic_relations(profile_entity.strip())
                    if not outgoing and not incoming:
                        st.info(f"No semantic relationships found for '{profile_entity}'.")
                    else:
                        col_out, col_in = st.columns(2)
                        with col_out:
                            st.markdown(f'<div style="font-family:IBM Plex Mono;font-size:9px;color:#C8A96E;letter-spacing:0.15em;margin-bottom:8px">{profile_entity.upper()} ACTS ON →</div>', unsafe_allow_html=True)
                            rows_html = ""
                            for r in outgoing:
                                rows_html += (f'<div style="display:flex;justify-content:space-between;align-items:center;padding:7px 12px;border-bottom:1px solid #1C2A38;font-family:IBM Plex Mono;font-size:11px"><span style="color:#C8D4E0">{r["target"]}</span><span style="color:{RELATION_COLORS.get(r["rel"],"#4A6A8A")};font-size:9px">{r["rel"].replace("_"," ")}</span><span style="color:#3A5068;font-size:9px">{r["cnt"]}x</span></div>')
                            st.markdown('<div style="border:1px solid #1C2A38;background:#0D1117">' + rows_html + '</div>', unsafe_allow_html=True)
                        with col_in:
                            st.markdown(f'<div style="font-family:IBM Plex Mono;font-size:9px;color:#6B8CAE;letter-spacing:0.15em;margin-bottom:8px">→ OTHERS ACT ON {profile_entity.upper()}</div>', unsafe_allow_html=True)
                            rows_html = ""
                            for r in incoming:
                                rows_html += (f'<div style="display:flex;justify-content:space-between;align-items:center;padding:7px 12px;border-bottom:1px solid #1C2A38;font-family:IBM Plex Mono;font-size:11px"><span style="color:#C8D4E0">{r["source"]}</span><span style="color:{RELATION_COLORS.get(r["rel"],"#4A6A8A")};font-size:9px">{r["rel"].replace("_"," ")}</span><span style="color:#3A5068;font-size:9px">{r["cnt"]}x</span></div>')
                            st.markdown('<div style="border:1px solid #1C2A38;background:#0D1117">' + rows_html + '</div>', unsafe_allow_html=True)
                        with st.spinner("Generating profile..."):
                            out_str = ", ".join([f"{r['target']} ({r['rel']})" for r in outgoing[:6]])
                            in_str  = ", ".join([f"{r['source']} ({r['rel']})" for r in incoming[:6]])
                            brief   = ask_groq(f"Prajna profile.\nEntity: {profile_entity}\nActs on: {out_str}\nOthers act on it: {in_str}\n\nPROFILE SUMMARY:\nKEY RELATIONSHIPS:\nINDIA RELEVANCE:\nMax 200 words.")
                        st.markdown('<div class="brief-container"><div class="brief-header">ENTITY PROFILE — ' + profile_entity.upper() + '</div>' + brief.replace("\n", "<br>") + "</div>", unsafe_allow_html=True)

    with tab4:
        st.markdown('<div class="section-label">Entity Surge Detection</div>', unsafe_allow_html=True)
        col_thresh, col_topn, col_run4 = st.columns([2, 2, 1])
        with col_thresh:
            threshold = st.slider("SURGE THRESHOLD (x baseline)", 1.2, 5.0, 1.5, 0.1, key="surge_threshold")
        with col_topn:
            top_n = st.slider("MAX RESULTS", 1, 10, 5, 1, key="surge_topn")
        with col_run4:
            st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
            run_surge = st.button("DETECT SURGES", key="run_surge")
        if run_surge:
            with st.spinner("Scanning graph..."):
                surges = detect_surges(threshold=threshold, top_n=top_n)
            if not surges:
                with driver.session() as session:
                    top = session.run("""
                        MATCH (e:Entity) WHERE e.type IN ["GPE","ORG","PERSON","NORP"]
                        WITH e, COUNT{(e)--()} as conn ORDER BY conn DESC LIMIT 10
                        RETURN e.name as name, e.type as type, conn
                    """).data()
                st.markdown('<div style="font-family:IBM Plex Mono;font-size:10px;color:#4A6A8A;border:1px solid #1C2A38;padding:10px 16px;background:#0D1117;margin-bottom:16px">No surges detected. Top entities:</div>', unsafe_allow_html=True)
                rows_html = ""
                for r in top:
                    if len(r["name"]) < 35:
                        rows_html += f'<div style="display:flex;justify-content:space-between;padding:7px 12px;border-bottom:1px solid #1C2A38;font-family:IBM Plex Mono;font-size:11px"><span style="color:#C8D4E0">{r["name"]}</span><span style="color:#3A5068">{r["type"]}</span><span style="color:#3A5068">{r["conn"]} connections</span></div>'
                st.markdown('<div style="border:1px solid #1C2A38;background:#0D1117">' + rows_html + '</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="font-family:IBM Plex Mono;font-size:10px;color:#C87B6A;border:1px solid #2A1A1A;padding:10px 16px;background:#0D0A0A;margin-bottom:16px">' + str(len(surges)) + ' ENTITIES FLAGGED ABOVE ' + str(threshold) + 'x BASELINE</div>', unsafe_allow_html=True)
                for surge in surges:
                    st.markdown('<div class="surge-card"><div class="surge-entity">' + surge["entity"] + '</div><div class="surge-ratio">' + str(surge["ratio"]) + 'x baseline &nbsp;·&nbsp; ' + str(surge["latest"]) + ' this week &nbsp;·&nbsp; baseline: ' + str(surge["baseline"]) + '/week</div></div>', unsafe_allow_html=True)
                    with st.spinner(""):
                        brief = ask_groq("Prajna surge alert:\nEntity: " + surge["entity"] + " (" + surge["type"] + ")\nThis week: " + str(surge["latest"]) + "\nBaseline: " + str(surge["baseline"]) + "/week\nRatio: " + str(surge["ratio"]) + "x\n\nSURGE EXPLANATION:\nINDIA RISK/OPPORTUNITY:\nURGENCY — Immediate/Days/Weeks\nRECOMMENDED ACTION:\nMax 130 words.")
                    st.markdown('<div class="brief-container" style="border-left-color:#8A4A3A;margin-bottom:20px"><div class="brief-header" style="color:#C87B6A">SURGE BRIEF — ' + surge["entity"].upper() + '</div>' + brief.replace("\n", "<br>") + '</div>', unsafe_allow_html=True)

    with tab5:
        st.markdown('<div class="section-label">Automated Weekly Intelligence Brief</div>', unsafe_allow_html=True)
        available_weeks_brief = get_available_weeks()
        c1b, c2b = st.columns([2, 1])
        with c1b:
            selected_brief_week = st.selectbox("SELECT WEEK", ["CURRENT WEEK"] + available_weeks_brief, key="brief_week")
        with c2b:
            st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
            run_weekly_brief = st.button("GENERATE BRIEF", key="run_weekly_brief")
        if run_weekly_brief:
            brief_week = get_week_key() if selected_brief_week == "CURRENT WEEK" else selected_brief_week
            with st.spinner("Analysing graph..."):
                with driver.session() as session:
                    top_entities = session.run(
                        "MATCH (a:Article {week:$w})-[:MENTIONS]->(e:Entity) WHERE e.type IN ['GPE','ORG','PERSON','NORP'] AND NOT e.name IN ['United States','United Kingdom','Guardian','BBC','Reuters','AP','AFP'] RETURN e.name AS entity, e.type AS type, COUNT(a) AS mentions ORDER BY mentions DESC LIMIT 15",
                        {"w": brief_week}).data()
                    names = [r["entity"] for r in top_entities]
                    pairs = session.run(
                        "MATCH (a:Article {week:$w})-[:MENTIONS]->(e1:Entity) MATCH (a)-[:MENTIONS]->(e2:Entity) WHERE e1.name IN $names AND e2.name IN $names AND e1.name < e2.name RETURN e1.name AS e1, e2.name AS e2, COUNT(a) AS co_count ORDER BY co_count DESC LIMIT 20",
                        {"w": brief_week, "names": names}).data()
                    top_pairs = pairs[:5]
                    headlines = {}
                    for p in top_pairs:
                        arts = session.run(
                            "MATCH (a:Article {week:$w})-[:MENTIONS]->(x:Entity {name:$e1}) MATCH (a)-[:MENTIONS]->(y:Entity {name:$e2}) RETURN a.title AS title, a.source AS source LIMIT 3",
                            {"w": brief_week, "e1": p["e1"], "e2": p["e2"]}).data()
                        headlines[p["e1"] + " and " + p["e2"]] = arts
                    sem_context = session.run(
                        "MATCH (e1:Entity)-[r:RELATES_TO]->(e2:Entity) WHERE e1.name IN $names AND e2.name IN $names RETURN e1.name AS e1, r.type AS rel, e2.name AS e2, r.count AS cnt ORDER BY cnt DESC LIMIT 20",
                        {"names": names}).data()
                pairs_lines = ["Most active relationships:"] + ["  " + p["e1"] + " and " + p["e2"] + ": " + str(p["co_count"]) + " co-mentions" for p in top_pairs]
                hl_lines    = ["Headlines:"] + [k + ": " + ", ".join([f"[{a['source']}] {a['title']}" for a in v]) for k, v in headlines.items()]
                sem_lines   = ["Semantics:"] + ["  " + r["e1"] + " -[" + r["rel"] + "]-> " + r["e2"] + " (" + str(r["cnt"]) + "x)" for r in sem_context]
                prompt = ("You are Prajna, India's strategic intelligence engine.\nWeek: " + brief_week + "\n\n" + "\n".join(pairs_lines) + "\n\n" + "\n".join(hl_lines) + "\n\n" + "\n".join(sem_lines) + "\n\nGenerate WEEKLY INTELLIGENCE BRIEF for Indian policymakers.\n\nWEEK " + brief_week + " - STRATEGIC INTELLIGENCE BRIEF\n\nSTORY 1: [headline]\n[2-3 sentences]\n\nSTORY 2: [headline]\n[2-3 sentences]\n\nSTORY 3: [headline]\n[2-3 sentences]\n\nSTORY 4: [headline]\n[2-3 sentences]\n\nSTORY 5: [headline]\n[2-3 sentences]\n\nBOTTOM LINE FOR INDIA: One sentence.\n\nMax 400 words.")
                brief_text = ask_groq(prompt, max_tokens=800)
            all_sources = list({a["source"] for arts in headlines.values() for a in arts})
            src_str = "  ".join(["[" + s + "]" for s in all_sources[:8]])
            st.markdown('<div class="brief-container"><div class="brief-header">WEEKLY BRIEF - ' + brief_week + ' - ' + str(len(top_pairs)) + ' signal pairs</div>' + brief_text.replace("\n", "<br>") + '<div style="margin-top:12px;padding-top:12px;border-top:1px solid #1C2A38;font-family:IBM Plex Mono;font-size:9px;color:#3A5068">' + src_str + '</div></div>', unsafe_allow_html=True)
            with st.spinner("Generating PDF..."):
                detailed_prompt = ("You are Prajna.\nWeek: " + brief_week + "\n\n" + "\n".join(pairs_lines) + "\n\n" + "\n".join(hl_lines) + "\n\n" + "\n".join(sem_lines) + "\n\nDETAILED WEEKLY INTELLIGENCE BRIEF\n\nEXECUTIVE SUMMARY\n[3-4 sentences]\n\nSTORY 1: [headline]\n[4-5 sentences]\n\nSTORY 2: [headline]\n[4-5 sentences]\n\nSTORY 3: [headline]\n[4-5 sentences]\n\nSTORY 4: [headline]\n[4-5 sentences]\n\nSTORY 5: [headline]\n[4-5 sentences]\n\nSTRATEGIC RISK MATRIX\nHIGH RISK: [one line]\nMEDIUM RISK: [one line]\nOPPORTUNITY: [one line]\n\nBOTTOM LINE FOR INDIA: Two sentences.\n\nMax 700 words.")
                detailed_brief = ask_groq(detailed_prompt, max_tokens=1200)
                pdf_bytes = generate_pdf_brief(brief_week, top_pairs, headlines, detailed_brief, names)
            st.download_button(label="DOWNLOAD DETAILED BRIEF (PDF)", data=pdf_bytes,
                               file_name="Prajna_Brief_" + brief_week + ".pdf", mime="application/pdf")


# ════════════════════════════════════════════════════════════════
# RAKSHA MODULE
# ════════════════════════════════════════════════════════════════
elif module == "RAKSHA — Cyber Intelligence":

    st.markdown("""
        <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:0.2em;color:#4A6A8A;margin-bottom:4px">PRAJNA INTELLIGENCE SUITE</div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:22px;font-weight:700;color:#E8D5A3;letter-spacing:0.05em;margin-bottom:2px">RAKSHA</div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;color:#4A6A8A;letter-spacing:0.15em;margin-bottom:20px">CYBERSECURITY INTELLIGENCE · INDIA-CENTRIC THREAT ANALYSIS</div>
    """, unsafe_allow_html=True)

    if not driver_2:
        st.warning("Raksha graph not connected. Add NEO4J_URI_2 credentials to Streamlit secrets.")
        st.stop()

    with driver_2.session() as s:
        n_cart  = s.run("MATCH (a:CyberArticle)  RETURN count(a) AS c").single()["c"]
        n_cent  = s.run("MATCH (e:CyberEntity)   RETURN count(e) AS c").single()["c"]
        n_crels = s.run("MATCH ()-[r:CYBER_CO_OCCURS]-() RETURN count(r) AS c").single()["c"]

    c1, c2, c3 = st.columns(3)
    for col, label, val in [(c1,"CYBER ARTICLES",n_cart),(c2,"THREAT ENTITIES",n_cent),(c3,"SIGNAL PAIRS",n_crels)]:
        col.markdown(f'<div style="background:#0D1117;border:1px solid #1C2A38;border-radius:6px;padding:14px;text-align:center"><div style="font-family:IBM Plex Mono;font-size:9px;color:#4A6A8A;letter-spacing:0.15em">{label}</div><div style="font-family:IBM Plex Mono;font-size:22px;font-weight:700;color:#E8D5A3">{val}</div></div>', unsafe_allow_html=True)
    st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)

    rtab1, rtab2, rtab3 = st.tabs(["THREAT BRIEF", "SECTOR EXPOSURE", "CVE TRACKER"])

    with rtab1:
        # Always-visible graph on left, brief on right
        col_graph, col_brief = st.columns([1, 1])

        with col_graph:
            st.markdown('<div class="graph-label">CYBER THREAT GRAPH</div>', unsafe_allow_html=True)
            raksha_filter = st.text_input("Filter (entity/sector/actor)", placeholder="banking, APT, Microsoft", key="raksha_filter")
            raksha_mode   = st.selectbox("Mode", ["co-occurrence", "semantic"], key="raksha_mode")
            with st.spinner("Rendering cyber graph..."):
                try:
                    cyber_html = build_cyber_graph(keyword=raksha_filter or None, mode=raksha_mode)
                    components.html(cyber_html, height=460, scrolling=False)
                except Exception as e:
                    st.info("Graph rendering — run ingestion notebook first.")
            # Node legend
            cyber_legend = [("#C47B6E","THREAT ACTOR"),("#E8D5A3","CVE"),("#B8476E","MALWARE"),
                            ("#6B8CAE","CYBER ORG"),("#A8C5A0","SECTOR"),("#C8A96E","GPE")]
            leg = '<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:6px">'
            for color, label in cyber_legend:
                leg += f'<div style="display:flex;align-items:center;gap:5px"><div style="width:8px;height:8px;border-radius:50%;background:{color}"></div><span style="font-family:IBM Plex Mono;font-size:8px;color:#3A5068">{label}</span></div>'
            leg += "</div>"
            st.markdown(leg, unsafe_allow_html=True)
            # Semantic edge legend
            if raksha_mode == "semantic":
                cyber_edge_legend = [
                    ("#C87B6A","EXPLOITS / TARGETS"),("#B8476E","DEPLOYS / FRONT FOR"),
                    ("#C8B86A","AFFECTS / DESIGNATED"),("#4A8A6A","MITIGATES / PATCHES"),
                    ("#6B8CAE","OPERATES IN"),("#4A8AAA","COLLABORATES / LINKED"),
                    ("#8A6AAE","SPONSORED BY"),
                ]
                eleg = '<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:4px">'
                for color, label in cyber_edge_legend:
                    eleg += f'<div style="display:flex;align-items:center;gap:5px"><div style="width:18px;height:3px;background:{color};border-radius:2px"></div><span style="font-family:IBM Plex Mono;font-size:8px;color:#3A5068">{label}</span></div>'
                eleg += "</div>"
                st.markdown(eleg, unsafe_allow_html=True)

        with col_brief:
            st.markdown('<div class="graph-label">THREAT BRIEF</div>', unsafe_allow_html=True)
            query = st.text_input("Threat query", placeholder="APT attacks on Indian banking", key="raksha_query")
            if st.button("GENERATE THREAT BRIEF", key="raksha_brief_btn"):
                if not query:
                    st.warning("Enter a query.")
                else:
                    with st.spinner("Querying cyber graph..."):
                        with driver_2.session() as s:
                            _qwords = [w for w in query.strip().split() if len(w) > 2] or [query.strip()]
                        context_rows = s.run("""
                                MATCH (e:CyberEntity)
                                WHERE any(word IN $words WHERE toLower(e.name) CONTAINS toLower(word))
                                WITH e LIMIT 5
                                MATCH (e)-[r:CYBER_CO_OCCURS]-(other:CyberEntity)
                                RETURN e.name AS e1, other.name AS e2, r.count AS count, other.type AS type
                                ORDER BY r.count DESC LIMIT 20
                            """, {"words": _qwords}).data()
                        headlines = s.run("""
                                MATCH (e:CyberEntity)
                                WHERE any(word IN $words WHERE toLower(e.name) CONTAINS toLower(word))
                                WITH e LIMIT 3
                                MATCH (a:CyberArticle)-[:CYBER_MENTIONS]->(e)
                                RETURN a.title AS title, a.source AS source
                                ORDER BY a.published DESC LIMIT 10
                            """, {"words": _qwords}).data()
                        ctx_lines = [f"- {r['e1']} <-> {r['e2']} (strength: {r['count']}, type: {r['type']})" for r in context_rows]
                        hl_lines  = [f"[{h['source']}] {h['title']}" for h in headlines]
                        prompt = (f"You are Raksha, India's cybersecurity intelligence engine.\nQuery: {query}\n\nCYBER GRAPH CONTEXT:\n" + "\n".join(ctx_lines) + "\n\nHEADLINES:\n" + "\n".join(hl_lines) + "\n\nSITUATION: [2-3 sentences]\n\nTHREAT ACTORS: [APT groups, nation-state actors]\n\nINDIA EXPOSURE: [Specific sectors at risk]\n\nRECOMMENDED ACTIONS: [2-3 concrete steps]\n\nMax 350 words.")
                        brief = ask_groq(prompt, max_tokens=700)
                    st.markdown('<div class="brief-container"><div class="brief-header">CYBER THREAT BRIEF — ' + query.upper()[:50] + '</div>' + brief.replace("\n", "<br>") + "</div>", unsafe_allow_html=True)
                render_sources([(h['title'], h['source']) for h in headlines], color="#C47B6E")

    with rtab2:
        st.markdown('<div style="font-family:IBM Plex Mono;font-size:10px;color:#4A6A8A;letter-spacing:0.15em;margin-bottom:16px">SECTOR TARGETING ANALYSIS · WHICH SECTORS ARE MOST EXPOSED</div>', unsafe_allow_html=True)
        with st.spinner("Loading..."):
            with driver_2.session() as s:
                sector_rows = s.run("""
                    MATCH (s:CyberEntity {type:'SECTOR'})
                    WITH s, COUNT{(s)-[:CYBER_CO_OCCURS]-()} AS exposure
                    ORDER BY exposure DESC RETURN s.name AS sector, exposure
                """).data()
                actor_rows = s.run("""
                    MATCH (t:CyberEntity {type:'THREAT_ACTOR'})
                    WITH t, COUNT{(t)-[:CYBER_CO_OCCURS]-()} AS activity
                    ORDER BY activity DESC LIMIT 10 RETURN t.name AS actor, activity
                """).data()
        if sector_rows:
            st.bar_chart(pd.DataFrame(sector_rows).set_index("sector")["exposure"])
            with st.spinner("Generating sector risk brief..."):
                brief = ask_groq(f"Raksha India cybersecurity.\nSector exposure: {sector_rows[:8]}\nThreat actors: {actor_rows[:5]}\n\nHIGHEST RISK SECTORS: [Top 3]\n\nRESPONSIBLE THREAT ACTORS:\n\nINDIA-SPECIFIC RISK:\n\nPRIORITY ACTION FOR CERT-IN:\n\nMax 250 words.", max_tokens=500)
            st.markdown('<div class="brief-container"><div class="brief-header">SECTOR RISK ASSESSMENT</div>' + brief.replace("\n", "<br>") + "</div>", unsafe_allow_html=True)
        else:
            st.info("No sector data yet.")
        if actor_rows:
            st.markdown('<div style="font-family:IBM Plex Mono;font-size:9px;color:#4A6A8A;letter-spacing:0.15em;margin:20px 0 8px">ACTIVE THREAT ACTORS</div>', unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(actor_rows).rename(columns={"actor":"Threat Actor","activity":"Activity Score"}), use_container_width=True, hide_index=True)

    with rtab3:
        st.markdown('<div style="font-family:IBM Plex Mono;font-size:10px;color:#4A6A8A;letter-spacing:0.15em;margin-bottom:16px">ACTIVE CVE TRACKER · CISA KEV</div>', unsafe_allow_html=True)
        with driver_2.session() as s:
            cve_rows = s.run("""
                MATCH (c:CyberEntity {type:'CVE'})
                WITH c, COUNT{(c)-[:CYBER_CO_OCCURS]-()} AS signals
                ORDER BY c.last_seen DESC, signals DESC
                RETURN c.name AS cve, c.last_seen AS date, signals LIMIT 50
            """).data()
            enriched = []
            for row in cve_rows:
                actors = s.run("""
                    MATCH (c:CyberEntity {name:$cve, type:'CVE'})-[:CYBER_CO_OCCURS]-(t:CyberEntity {type:'THREAT_ACTOR'})
                    RETURN t.name AS actor LIMIT 3
                """, {"cve": row["cve"]}).data()
                enriched.append({"CVE ID": row["cve"], "Date Added": row["date"],
                                  "Signal Strength": row["signals"],
                                  "Linked Actors": ", ".join([a["actor"] for a in actors]) or "—"})
        if enriched:
            st.dataframe(pd.DataFrame(enriched), use_container_width=True, hide_index=True)
        else:
            st.info("No CVE data yet.")


# ════════════════════════════════════════════════════════════════
# ARTHA MODULE
# ════════════════════════════════════════════════════════════════
elif module == "ARTHA — Financial Intelligence":

    st.markdown("""
        <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:0.2em;color:#4A6A8A;margin-bottom:4px">PRAJNA INTELLIGENCE SUITE</div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:22px;font-weight:700;color:#E8D5A3;letter-spacing:0.05em;margin-bottom:2px">ARTHA</div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;color:#4A6A8A;letter-spacing:0.15em;margin-bottom:20px">FINANCIAL INTELLIGENCE · SANCTIONS · SHELL NETWORKS · INDIA RISK</div>
    """, unsafe_allow_html=True)

    if not driver_2:
        st.warning("Artha graph not connected. Add NEO4J_URI_2 credentials to Streamlit secrets.")
        st.stop()

    with driver_2.session() as s:
        n_fart  = s.run("MATCH (a:FinancialArticle) RETURN count(a) AS c").single()["c"]
        n_fent  = s.run("MATCH (e:FinancialEntity)  RETURN count(e) AS c").single()["c"]
        n_cross = s.run("MATCH ()-[r:CROSS_DOMAIN]-() RETURN count(r) AS c").single()["c"]

    c1, c2, c3 = st.columns(3)
    for col, label, val in [(c1,"SANCTIONS ENTRIES",n_fart),(c2,"FINANCIAL ENTITIES",n_fent),(c3,"CROSS-DOMAIN LINKS",n_cross)]:
        col.markdown(f'<div style="background:#0D1117;border:1px solid #1C2A38;border-radius:6px;padding:14px;text-align:center"><div style="font-family:IBM Plex Mono;font-size:9px;color:#4A6A8A;letter-spacing:0.15em">{label}</div><div style="font-family:IBM Plex Mono;font-size:22px;font-weight:700;color:#E8D5A3">{val}</div></div>', unsafe_allow_html=True)
    st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)

    atab1, atab2, atab3 = st.tabs(["SANCTIONS QUERY", "SHELL NETWORK", "INDIA RISK EXPOSURE"])

    with atab1:
        st.markdown('<div style="font-family:IBM Plex Mono;font-size:10px;color:#4A6A8A;letter-spacing:0.15em;margin-bottom:16px">SEARCH 800+ SANCTIONS ENTRIES · OPENSANCTIONS + OFAC SDN</div>', unsafe_allow_html=True)
        entity_query = st.text_input("Entity name", placeholder="Rostec, Sberbank, IRGC", key="artha_sanctions_query")
        if st.button("SEARCH SANCTIONS GRAPH", key="artha_search_btn"):
            if not entity_query:
                st.warning("Enter an entity name.")
            else:
                _eq = entity_query.strip()
                with driver_2.session() as s:
                    results = s.run("""
                        MATCH (e:FinancialEntity)
                        WHERE any(word IN $words WHERE toLower(e.name) CONTAINS toLower(word))
                        RETURN e.name AS name, e.type AS type, e.source_list AS lists,
                               e.first_seen AS first_seen, e.last_seen AS last_seen
                        ORDER BY e.last_seen DESC LIMIT 20
                    """, {"words": [w for w in _eq.split() if len(w) > 2] or [_eq]}).data()
                    co_occurs = s.run("""
                        MATCH (e:FinancialEntity)
                        WHERE any(word IN $words WHERE toLower(e.name) CONTAINS toLower(word))
                        WITH e LIMIT 3
                        MATCH (e)-[r:FIN_CO_OCCURS]-(other:FinancialEntity)
                        RETURN e.name AS e1, other.name AS e2, r.count AS count
                        ORDER BY r.count DESC LIMIT 15
                    """, {"words": [w for w in _eq.split() if len(w) > 2] or [_eq]}).data()
                    cross = s.run("""
                        MATCH (f:FinancialEntity)
                        WHERE any(word IN $words WHERE toLower(f.name) CONTAINS toLower(word))
                        WITH f LIMIT 3
                        MATCH (c:CyberEntity)-[:CROSS_DOMAIN]->(f)
                        RETURN c.name AS cyber_entity, c.type AS cyber_type LIMIT 5
                    """, {"words": [w for w in _eq.split() if len(w) > 2] or [_eq]}).data()
                if results:
                    st.dataframe(pd.DataFrame(results).rename(columns={"name":"Entity","type":"Type","lists":"Sanctions Lists","first_seen":"First Sanctioned","last_seen":"Last Updated"}), use_container_width=True, hide_index=True)
                    if cross:
                        st.markdown('<div style="font-family:IBM Plex Mono;font-size:9px;color:#C47B6E;letter-spacing:0.15em;margin:12px 0 4px">⚠ CROSS-DOMAIN ALERT — ALSO APPEARS IN CYBER GRAPH</div>', unsafe_allow_html=True)
                        for c in cross:
                            st.markdown(f'<div style="font-family:IBM Plex Mono;font-size:10px;color:#E8D5A3">→ {c["cyber_entity"]} ({c["cyber_type"]})</div>', unsafe_allow_html=True)
                    with st.spinner("Generating brief..."):
                        brief = ask_groq(f"Artha financial intelligence.\nQuery: {entity_query}\nMatched: {[r['name'] for r in results[:5]]}\nSanctions: {results[0]['lists'] if results else ''}\nCo-occurring: {[r['e2'] for r in co_occurs[:8]]}\nCross-domain cyber: {[c['cyber_entity'] for c in cross] or 'None'}\n\nENTITY PROFILE:\nSANCTIONS EXPOSURE:\nINDIA EXPOSURE: [compliance risk for Indian banks]\nCROSS-DOMAIN RISK:\nMax 300 words.", max_tokens=600)
                    st.markdown('<div class="brief-container"><div class="brief-header">SANCTIONS INTELLIGENCE BRIEF — ' + entity_query.upper()[:50] + '</div>' + brief.replace("\n", "<br>") + "</div>", unsafe_allow_html=True)
                    render_sources(
                        [(r["name"], r.get("lists","")[:40] if r.get("lists") else "Sanctions DB") for r in results[:5]],
                        color="#C47B6E"
                    )
                else:
                    st.info(f"No results found for '{entity_query}'.")

    with atab2:
        # Always-visible financial network graph + path query
        col_graph, col_query = st.columns([1, 1])

        with col_graph:
            st.markdown('<div class="graph-label">FINANCIAL ENTITY NETWORK</div>', unsafe_allow_html=True)
            fin_filter = st.text_input("Filter entity", placeholder="Iran, Russia, OFAC", key="fin_filter")
            fin_mode   = st.selectbox("Mode", ["co-occurrence", "semantic"], key="fin_mode")
            with st.spinner("Rendering financial graph..."):
                try:
                    fin_html = build_financial_graph(keyword=fin_filter or None, mode=fin_mode)
                    components.html(fin_html, height=460, scrolling=False)
                except Exception as e:
                    st.info("Graph rendering — run ingestion notebook first.")
            # Node legend
            fin_legend = [("#C47B6E","SANCTIONED PERSON"),("#E8D5A3","SANCTIONED ORG"),
                          ("#6B8CAE","SANCTIONS BODY"),("#A8C5A0","JURISDICTION"),("#C8A96E","GPE")]
            leg = '<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:6px">'
            for color, label in fin_legend:
                leg += f'<div style="display:flex;align-items:center;gap:5px"><div style="width:8px;height:8px;border-radius:50%;background:{color}"></div><span style="font-family:IBM Plex Mono;font-size:8px;color:#3A5068">{label}</span></div>'
            leg += "</div>"
            st.markdown(leg, unsafe_allow_html=True)
            # Semantic edge legend
            if fin_mode == "semantic":
                fin_edge_legend = [
                    ("#C87B6A","SANCTIONED BY / INVESTIGATED"),("#C8956A","OWNS / CONTROLS"),
                    ("#B8476E","FRONT FOR"),("#C8B86A","ASSOCIATED / DESIGNATED"),
                    ("#4A8AAA","TRANSACTS / LINKED"),("#6B8CAE","INCORPORATED IN"),
                ]
                eleg = '<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:4px">'
                for color, label in fin_edge_legend:
                    eleg += f'<div style="display:flex;align-items:center;gap:5px"><div style="width:18px;height:3px;background:{color};border-radius:2px"></div><span style="font-family:IBM Plex Mono;font-size:8px;color:#3A5068">{label}</span></div>'
                eleg += "</div>"
                st.markdown(eleg, unsafe_allow_html=True)

        with col_query:
            st.markdown('<div class="graph-label">PATH QUERY · MAX 4 HOPS</div>', unsafe_allow_html=True)
            node_a = st.text_input("Entity A", placeholder="Rostec", key="shell_a")
            node_b = st.text_input("Entity B", placeholder="Iran", key="shell_b")
            if st.button("FIND NETWORK PATH", key="shell_btn"):
                if not node_a or not node_b:
                    st.warning("Enter both entities.")
                else:
                    with driver_2.session() as s:
                        path_result = s.run("""
                            MATCH (a:FinancialEntity)
                            WHERE toLower(a.name) CONTAINS toLower($a)
                            WITH a LIMIT 5
                            MATCH (b:FinancialEntity)
                            WHERE toLower(b.name) CONTAINS toLower($b)
                            WITH a, b LIMIT 25
                            MATCH path = shortestPath((a)-[:FIN_CO_OCCURS*..4]-(b))
                            RETURN [n IN nodes(path) | n.name] AS nodes,
                                   length(path) AS hops
                            ORDER BY hops ASC LIMIT 1
                        """, {"a": node_a, "b": node_b}).data()
                    if path_result:
                        path = path_result[0]
                        st.markdown(f'<div style="font-family:IBM Plex Mono;font-size:10px;color:#A8C5A0;margin-bottom:12px">PATH FOUND — {path["hops"]} hops: ' + " → ".join([f'<span style="color:#E8D5A3">{n}</span>' for n in path["nodes"]]) + '</div>', unsafe_allow_html=True)
                    else:
                        st.info("No direct path found within 4 hops.")

    with atab3:
        st.markdown('<div style="font-family:IBM Plex Mono;font-size:10px;color:#4A6A8A;letter-spacing:0.15em;margin-bottom:16px">CROSS-DOMAIN INDIA RISK · ENTITIES IN BOTH GEOPOLITICAL + SANCTIONS GRAPHS</div>', unsafe_allow_html=True)
        with st.spinner("Computing India risk exposure..."):
            with driver_2.session() as s:
                india_exposed = s.run("""
                    MATCH (f:FinancialEntity)
                    WHERE f.source_list CONTAINS 'India' OR f.source_list CONTAINS 'IN'
                    WITH f, COUNT{(f)--()} AS conn ORDER BY conn DESC LIMIT 30
                    RETURN f.name AS name, f.type AS type, f.source_list AS lists, conn
                """).data()
                cross_domain = s.run("""
                    MATCH (c:CyberEntity)-[r:CROSS_DOMAIN]->(f:FinancialEntity)
                    RETURN c.name AS cyber_name, c.type AS cyber_type,
                           f.name AS fin_name, f.type AS fin_type, f.source_list AS lists LIMIT 20
                """).data()
            if india_exposed:
                st.markdown('<div style="font-family:IBM Plex Mono;font-size:9px;color:#4A6A8A;letter-spacing:0.15em;margin-bottom:8px">INDIA-LINKED SANCTIONED ENTITIES</div>', unsafe_allow_html=True)
                st.dataframe(pd.DataFrame(india_exposed).rename(columns={"name":"Entity","type":"Type","lists":"Sanctions Lists","conn":"Connections"}), use_container_width=True, hide_index=True)
            if cross_domain:
                st.markdown('<div style="font-family:IBM Plex Mono;font-size:9px;color:#C47B6E;letter-spacing:0.15em;margin:20px 0 8px">⚠ CROSS-DOMAIN ENTITIES — APPEAR IN BOTH CYBER + FINANCIAL GRAPHS</div>', unsafe_allow_html=True)
                st.dataframe(pd.DataFrame(cross_domain).rename(columns={"cyber_name":"Cyber Entity","cyber_type":"Cyber Type","fin_name":"Financial Entity","fin_type":"Financial Type","lists":"Sanctions Lists"}), use_container_width=True, hide_index=True)
            with st.spinner("Generating India risk brief..."):
                india_str = ", ".join([r["name"] for r in india_exposed[:8]]) or "None found"
                cross_str = ", ".join([f"{r['cyber_name']} / {r['fin_name']}" for r in cross_domain[:5]]) or "None found"
                brief = ask_groq(f"Artha India financial intelligence.\nIndia-linked sanctioned entities: {india_str}\nCross-domain (cyber+financial): {cross_str}\n\nTOP 3 INDIA EXPOSURE RISKS:\n1.\n2.\n3.\n\nCROSS-DOMAIN ALERT:\n\nCOMPLIANCE IMPLICATIONS for Indian banks and PSUs:\n\nMax 300 words.", max_tokens=600)
            st.markdown('<div class="brief-container"><div class="brief-header">INDIA RISK EXPOSURE BRIEF — ' + get_week_key() + '</div>' + brief.replace("\n", "<br>") + "</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# SANGAM MODULE — UNIFIED INTELLIGENCE
# ════════════════════════════════════════════════════════════════
elif module == "SANGAM — Unified Intelligence":

    st.markdown("""
        <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:0.2em;color:#4A6A8A;margin-bottom:4px">PRAJNA INTELLIGENCE SUITE</div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:22px;font-weight:700;color:#E8D5A3;letter-spacing:0.05em;margin-bottom:2px">SANGAM</div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;color:#4A6A8A;letter-spacing:0.15em;margin-bottom:4px">UNIFIED INTELLIGENCE · CONVERGENCE OF GEOPOLITICAL · CYBER · FINANCIAL SIGNALS</div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:#3A5068;margin-bottom:20px">Sangam (Sanskrit: confluence) — where three intelligence streams meet</div>
    """, unsafe_allow_html=True)

    if not driver_2:
        st.warning("Sangam requires both Neo4j instances. Add NEO4J_URI_2 credentials.")
        st.stop()

    # Stats from all three graphs
    try:
        geo_a, geo_e, geo_r, geo_s = get_stats()
    except:
        geo_a, geo_e, geo_r, geo_s = 0, 0, 0, 0
    with driver_2.session() as s:
        cyber_e = s.run("MATCH (e:CyberEntity)    RETURN count(e) AS c").single()["c"]
        fin_e   = s.run("MATCH (e:FinancialEntity) RETURN count(e) AS c").single()["c"]
        cross_e = s.run("MATCH ()-[r:CROSS_DOMAIN]-() RETURN count(r) AS c").single()["c"]

    c1, c2, c3, c4 = st.columns(4)
    for col, label, val in [
        (c1, "GEO ENTITIES",     geo_e),
        (c2, "CYBER ENTITIES",   cyber_e),
        (c3, "FIN ENTITIES",     fin_e),
        (c4, "CROSS-DOMAIN",     cross_e),
    ]:
        col.markdown(f'<div style="background:#0D1117;border:1px solid #1C2A38;border-radius:6px;padding:14px;text-align:center"><div style="font-family:IBM Plex Mono;font-size:9px;color:#4A6A8A;letter-spacing:0.15em">{label}</div><div style="font-family:IBM Plex Mono;font-size:22px;font-weight:700;color:#E8D5A3">{val}</div></div>', unsafe_allow_html=True)
    st.markdown("<div style='margin-top:24px'></div>", unsafe_allow_html=True)

    stab1, stab2, stab3 = st.tabs(["THREAT CONVERGENCE", "CORRELATION TIMELINE", "UNIFIED BRIEF"])

    # ── SANGAM TAB 1 — THREAT CONVERGENCE ──
    with stab1:
        st.markdown('<div style="font-family:IBM Plex Mono;font-size:10px;color:#4A6A8A;letter-spacing:0.15em;margin-bottom:16px">ENTITIES APPEARING ACROSS MULTIPLE INTELLIGENCE DOMAINS · COMPOUND RISK SIGNALS</div>', unsafe_allow_html=True)

        with st.spinner("Computing cross-domain convergence..."):
            # Find entities in cyber graph
            with driver_2.session() as s:
                cyber_names = set(r["name"] for r in s.run("MATCH (e:CyberEntity) RETURN e.name AS name").data())
                fin_names   = set(r["name"] for r in s.run("MATCH (e:FinancialEntity) RETURN e.name AS name").data())
                cross_rows  = s.run("""
                    MATCH (c:CyberEntity)-[r:CROSS_DOMAIN]->(f:FinancialEntity)
                    WITH c, f, r
                    RETURN c.name AS cyber_name, c.type AS cyber_type,
                           f.name AS fin_name, f.type AS fin_type,
                           f.source_list AS sanctions_lists
                    ORDER BY f.source_list DESC LIMIT 30
                """).data()

            # Check which cross-domain entities also appear in geopolitical graph
            geo_cross = []
            if cross_rows:
                all_cross_names = list({r["cyber_name"] for r in cross_rows} | {r["fin_name"] for r in cross_rows})
                with driver.session() as session:
                    geo_matches = session.run("""
                        MATCH (e:Entity) WHERE e.name IN $names
                        RETURN e.name AS name, e.type AS type,
                               COUNT{(e)--()} AS geo_connections
                        ORDER BY geo_connections DESC
                    """, {"names": all_cross_names}).data()
                geo_match_names = {r["name"] for r in geo_matches}

                for row in cross_rows:
                    in_geo = row["cyber_name"] in geo_match_names or row["fin_name"] in geo_match_names
                    row["in_geopolitical_graph"] = "✅ YES" if in_geo else "—"
                    row["risk_level"] = "🔴 HIGH" if in_geo else "🟡 MEDIUM"
                    geo_cross.append(row)

        if geo_cross:
            df_cross = pd.DataFrame(geo_cross)
            st.markdown('<div style="font-family:IBM Plex Mono;font-size:9px;color:#C47B6E;letter-spacing:0.15em;margin-bottom:8px">⚠ CROSS-DOMAIN COMPOUND RISK ENTITIES</div>', unsafe_allow_html=True)
            st.dataframe(
                df_cross[["cyber_name","cyber_type","fin_name","fin_type","risk_level","in_geopolitical_graph"]].rename(columns={
                    "cyber_name": "Cyber Entity", "cyber_type": "Cyber Type",
                    "fin_name": "Financial Entity", "fin_type": "Financial Type",
                    "risk_level": "Risk Level", "in_geopolitical_graph": "In Geo Graph"
                }),
                use_container_width=True, hide_index=True
            )

            high_risk = [r for r in geo_cross if "HIGH" in r.get("risk_level","")]
            if high_risk:
                st.markdown('<div style="font-family:IBM Plex Mono;font-size:9px;color:#C87B6A;letter-spacing:0.15em;margin:16px 0 8px">🔴 TRIPLE-DOMAIN ENTITIES — GEOPOLITICAL + CYBER + FINANCIAL</div>', unsafe_allow_html=True)
                for r in high_risk[:5]:
                    st.markdown(f'<div style="font-family:IBM Plex Mono;font-size:11px;color:#E8D5A3;padding:8px 12px;border-left:3px solid #C87B6A;background:#0D1117;margin-bottom:6px">{r["cyber_name"]} / {r["fin_name"]}<span style="color:#4A6A8A;font-size:9px;margin-left:12px">CYBER: {r["cyber_type"]} · FINANCIAL: {r["fin_type"]}</span></div>', unsafe_allow_html=True)
        else:
            st.info("No cross-domain convergence detected yet — more ingestion runs will surface these signals.")

        # Convergence brief
        with st.spinner("Generating convergence brief..."):
            cross_str = ", ".join([f"{r['cyber_name']}/{r['fin_name']}" for r in (geo_cross or [])[:8]]) or "None yet"
            high_str  = ", ".join([f"{r['cyber_name']}" for r in (high_risk if geo_cross else [])[:5]]) or "None yet"
            prompt = (
                "You are Sangam, India's unified intelligence engine combining geopolitical, cyber, and financial intelligence.\n\n"
                f"Cross-domain entities (cyber + financial): {cross_str}\n"
                f"Triple-domain entities (geo + cyber + financial): {high_str}\n\n"
                "CONVERGENCE ASSESSMENT: What does the overlap between cyber threat actors and sanctioned financial entities tell us?\n\n"
                "COMPOUND RISK: Which entities represent the highest compound risk to India — appearing across multiple domains simultaneously?\n\n"
                "STRATEGIC IMPLICATION: What should Indian policymakers, CERT-In, and financial regulators prioritise based on this convergence?\n\n"
                "INTELLIGENCE GAP: What additional data would sharpen this picture?\n\n"
                "Max 350 words. India-centric, direct, analytical."
            )
            convergence_brief = ask_groq(prompt, max_tokens=700)
        st.markdown('<div class="brief-container"><div class="brief-header">CONVERGENCE INTELLIGENCE BRIEF — ' + get_week_key() + '</div>' + convergence_brief.replace("\n", "<br>") + "</div>", unsafe_allow_html=True)

    # ── SANGAM TAB 2 — CORRELATION TIMELINE ──
    with stab2:
        st.markdown('<div style="font-family:IBM Plex Mono;font-size:10px;color:#4A6A8A;letter-spacing:0.15em;margin-bottom:16px">WEEK-ON-WEEK CORRELATION · DOES GEOPOLITICAL TENSION SPIKE WITH CYBER ACTIVITY?</div>', unsafe_allow_html=True)

        col_geo, col_cyber = st.columns(2)
        with col_geo:
            geo_entity_a = st.text_input("Geopolitical entity pair A", placeholder="India", key="sangam_geo_a")
            geo_entity_b = st.text_input("Geopolitical entity pair B", placeholder="China", key="sangam_geo_b")
        with col_cyber:
            cyber_entity = st.text_input("Cyber entity to correlate", placeholder="banking or APT41", key="sangam_cyber")

        if st.button("RUN CORRELATION", key="sangam_correlate"):
            if not geo_entity_a or not geo_entity_b or not cyber_entity:
                st.warning("Enter all three fields.")
            else:
                with st.spinner("Fetching timeline data..."):
                    # Geopolitical trajectory
                    trajectory, total = get_trajectory(geo_entity_a.strip(), geo_entity_b.strip())

                    # Cyber entity weekly mentions
                    with driver_2.session() as s:
                        cyber_weekly = s.run("""
                            MATCH (a:CyberArticle)-[:CYBER_MENTIONS]->(e:CyberEntity)
                            WHERE toLower(e.name) CONTAINS toLower($kw) AND a.week IS NOT NULL
                            RETURN a.week AS week, COUNT(a) AS cnt ORDER BY week
                        """, {"kw": cyber_entity.split()[0]}).data()

                if trajectory and cyber_weekly:
                    geo_dict   = {w: c for w, c in trajectory}
                    cyber_dict = {r["week"]: r["cnt"] for r in cyber_weekly}
                    all_weeks  = sorted(set(list(geo_dict.keys()) + list(cyber_dict.keys())))

                    df_corr = pd.DataFrame({
                        "week":   all_weeks,
                        f"Geo: {geo_entity_a}↔{geo_entity_b}": [geo_dict.get(w, 0) for w in all_weeks],
                        f"Cyber: {cyber_entity}":               [cyber_dict.get(w, 0) for w in all_weeks],
                    }).set_index("week")

                    st.markdown(f'<div style="font-family:IBM Plex Mono;font-size:10px;color:#4A6A8A;margin-bottom:12px">CORRELATION: {geo_entity_a.upper()} ↔ {geo_entity_b.upper()} (geopolitical) vs {cyber_entity.upper()} (cyber activity)</div>', unsafe_allow_html=True)
                    st.line_chart(df_corr)

                    with st.spinner("Analysing correlation..."):
                        geo_str   = "  ".join([f"{w}:{geo_dict.get(w,0)}" for w in all_weeks])
                        cyber_str = "  ".join([f"{w}:{cyber_dict.get(w,0)}" for w in all_weeks])
                        prompt = (
                            f"Sangam correlation analysis.\n"
                            f"Geopolitical tension ({geo_entity_a} ↔ {geo_entity_b}) week by week: {geo_str}\n"
                            f"Cyber activity ({cyber_entity}) week by week: {cyber_str}\n\n"
                            "CORRELATION: Does cyber activity spike when geopolitical tension rises?\n\n"
                            "PATTERN: Are there specific weeks where both peaked simultaneously?\n\n"
                            "INDIA INTELLIGENCE IMPLICATION: What does this correlation tell Indian strategic analysts?\n\n"
                            "EARLY WARNING SIGNAL: Based on current geopolitical trajectory, what cyber activity should India anticipate?\n\n"
                            "Max 250 words."
                        )
                        corr_brief = ask_groq(prompt, max_tokens=500)
                    st.markdown('<div class="brief-container"><div class="brief-header">CORRELATION ANALYSIS</div>' + corr_brief.replace("\n", "<br>") + "</div>", unsafe_allow_html=True)
                elif not trajectory:
                    st.info(f"No geopolitical trajectory data for {geo_entity_a} ↔ {geo_entity_b}.")
                elif not cyber_weekly:
                    st.info(f"No cyber activity data for '{cyber_entity}'.")

    # ── SANGAM TAB 3 — UNIFIED BRIEF ──
    with stab3:
        st.markdown('<div style="font-family:IBM Plex Mono;font-size:10px;color:#4A6A8A;letter-spacing:0.15em;margin-bottom:16px">UNIFIED STRATEGIC INTELLIGENCE BRIEF · ALL THREE DOMAINS · GROQ 70B</div>', unsafe_allow_html=True)

        if st.button("GENERATE UNIFIED BRIEF", key="sangam_unified_btn"):
            with st.spinner("Querying all three graphs..."):
                # Geopolitical — top entities and semantic relations this week
                week_key = get_week_key()
                with driver.session() as session:
                    geo_top = session.run("""
                        MATCH (a:Article {week:$w})-[:MENTIONS]->(e:Entity)
                        WHERE e.type IN ['GPE','ORG','PERSON','NORP']
                        RETURN e.name AS name, COUNT(a) AS mentions
                        ORDER BY mentions DESC LIMIT 10
                    """, {"w": week_key}).data()
                    geo_rels = session.run("""
                        MATCH (e1:Entity)-[r:RELATES_TO]->(e2:Entity)
                        WHERE e1.type IN ['GPE','ORG'] AND e2.type IN ['GPE','ORG']
                        RETURN e1.name AS e1, r.type AS rel, e2.name AS e2, r.count AS cnt
                        ORDER BY cnt DESC LIMIT 10
                    """).data()

                # Cyber — top threat actors and sectors
                with driver_2.session() as s:
                    cyber_actors = s.run("""
                        MATCH (t:CyberEntity {type:'THREAT_ACTOR'})
                        WITH t, COUNT{(t)-[:CYBER_CO_OCCURS]-()} AS activity
                        ORDER BY activity DESC LIMIT 5
                        RETURN t.name AS name, activity
                    """).data()
                    cyber_sectors = s.run("""
                        MATCH (s:CyberEntity {type:'SECTOR'})
                        WITH s, COUNT{(s)-[:CYBER_CO_OCCURS]-()} AS exposure
                        ORDER BY exposure DESC LIMIT 5
                        RETURN s.name AS name, exposure
                    """).data()
                    fin_top = s.run("""
                        MATCH (e:FinancialEntity)
                        WHERE e.source_list CONTAINS 'India' OR e.source_list CONTAINS 'IN'
                        WITH e, COUNT{(e)--()} AS conn ORDER BY conn DESC LIMIT 5
                        RETURN e.name AS name, e.type AS type, conn
                    """).data()
                    cross_top = s.run("""
                        MATCH (c:CyberEntity)-[:CROSS_DOMAIN]->(f:FinancialEntity)
                        RETURN c.name AS cyber, f.name AS financial LIMIT 5
                    """).data()

                geo_str    = ", ".join([f"{r['name']} ({r['mentions']})" for r in geo_top[:8]])
                geo_rel_str = ", ".join([f"{r['e1']} {r['rel']} {r['e2']}" for r in geo_rels[:6]])
                cyber_str  = ", ".join([f"{r['name']} ({r['activity']})" for r in cyber_actors])
                sector_str = ", ".join([f"{r['name']} ({r['exposure']})" for r in cyber_sectors])
                fin_str    = ", ".join([f"{r['name']}" for r in fin_top[:5]])
                cross_str  = ", ".join([f"{r['cyber']}/{r['financial']}" for r in cross_top[:5]])

                prompt = (
                    "You are Sangam, India's unified strategic intelligence engine.\n"
                    f"Week: {week_key}\n\n"
                    f"GEOPOLITICAL SIGNALS (most active entities): {geo_str}\n"
                    f"KEY GEOPOLITICAL RELATIONSHIPS: {geo_rel_str}\n\n"
                    f"CYBER THREAT SIGNALS (most active threat actors): {cyber_str}\n"
                    f"MOST TARGETED SECTORS: {sector_str}\n\n"
                    f"FINANCIAL/SANCTIONS SIGNALS (India-linked sanctioned entities): {fin_str}\n"
                    f"CROSS-DOMAIN ENTITIES (appear in cyber AND financial graphs): {cross_str}\n\n"
                    "Generate a UNIFIED STRATEGIC INTELLIGENCE BRIEF for Indian policymakers.\n\n"
                    "EXECUTIVE SUMMARY: [3-4 sentences synthesising all three domains]\n\n"
                    "GEOPOLITICAL SITUATION: [Top 2 developments India should watch]\n\n"
                    "CYBER THREAT LANDSCAPE: [Top threat actors and targeted sectors]\n\n"
                    "FINANCIAL RISK EXPOSURE: [India's sanctions compliance and financial crime exposure]\n\n"
                    "CONVERGENCE ALERT: [Entities appearing across multiple domains — compound risk]\n\n"
                    "STRATEGIC RECOMMENDATION FOR INDIA: [One unified action across all three domains]\n\n"
                    "Be direct, analytical, India-centric. Max 500 words."
                )
                unified_brief = ask_groq(prompt, max_tokens=1000)

            st.markdown(
                '<div class="brief-container" style="border-left-color:#8A6AAE"><div class="brief-header" style="color:#8A6AAE">SANGAM UNIFIED INTELLIGENCE BRIEF — ' + week_key + '</div>'
                + unified_brief.replace("\n", "<br>") + "</div>",
                unsafe_allow_html=True
            )
