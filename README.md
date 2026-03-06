# PRAJNA — Strategic Intelligence Engine
### *प्रज्ञा परम् बलम् — Wisdom is the highest strength*

**AI-Powered Global Ontology Engine for India's Strategic Decision-Making**

[![Live App](https://img.shields.io/badge/Live%20App-prajna--intel.streamlit.app-1B2B5E?style=for-the-badge)](https://prajna-intel.streamlit.app)
[![India Innovates 2026](https://img.shields.io/badge/India%20Innovates%202026-Domain%2002%3A%20Digital%20Democracy-E07B1A?style=for-the-badge)](https://indiainnovates.org)
[![IIM Calcutta](https://img.shields.io/badge/Team%20IIMC-IIM%20Calcutta%20PGP%202025--27-1B2B5E?style=for-the-badge)](#team)

---

## What is Prajna?

Prajna is an always-on strategic intelligence platform that continuously ingests global news, builds a **living knowledge graph** of geopolitical relationships, and generates **cited, India-centric intelligence briefs** — automatically, daily, at ₹0/month.

Unlike LLM chatbots that hallucinate context, Prajna grounds every intelligence brief in a verifiable, accumulating graph of source-cited relationships. The graph never resets — it compounds in value with every daily run.

> **The core gap Prajna solves:** Analysts spend 70%+ of their time aggregating, not analysing. Existing tools (Bloomberg Terminal at ₹16L+/yr, Palantir) are built for Western strategic priorities. India's specific concerns — BRICS, Quad, Iran energy, Russia defence ties — are treated as peripheral data. Prajna fixes this at zero cost.

---

## Live Stats

| Metric | Value |
|--------|-------|
| Articles Ingested | 1,042+ |
| Entities Mapped | 15,057+ |
| Co-occurrence Relationships | 26,773+ |
| Semantic Relationships | 2,216+ |
| Strategic Domains | 5 |
| Topics Monitored | 32 |
| Monthly Infrastructure Cost | ₹0 |

---

## Architecture

```
NewsAPI ──┐
GDELT    ─┼─→  spaCy NLP  →  Neo4j Knowledge Graph  →  Groq LLM  →  Streamlit Dashboard
Guardian ─┘    (NER +          (CO_OCCURS_WITH +        (RAG brief    (5 analytical tabs
               alias map)       RELATES_TO edges)        generation)   + PDF export)
```

### Five-Layer Pipeline

| Layer | Name | Technology | Role |
|-------|------|-----------|------|
| L1 | Data Ingestion | NewsAPI · GDELT · Guardian API | 32 topics, 3-source fallback chain, ~200 new articles/day |
| L2 | NLP Extraction | spaCy `en_core_web_sm` | NER: GPE, ORG, PERSON, NORP, LOC, EVENT + 40-entry alias normalisation |
| L3 | Knowledge Graph | Neo4j AuraDB · Cypher | Persistent accumulating graph — CO_OCCURS_WITH + RELATES_TO edges |
| L4 | AI Reasoning | Groq Llama 3.1 8B + 3.3 70B | RAG pattern: graph context retrieved before generation, zero hallucination by constraint |
| L5 | Intelligence UI | Streamlit · PyVis · fpdf2 | 5-tab dashboard, interactive graph, PDF brief export |

---

## Features

### 🧠 Intelligence Brief
Natural language query → structured 5-section brief: **Situation · Key Connections · Implications for India · Recommended Action · Sources**. Every claim cited to a real article headline. The LLM reasons only over graph-verified facts.

### 📈 Trajectory Analysis
Week-on-week bar chart of co-occurrence intensity between any two entities. Groq identifies inflection points and characterises the relationship as **warming / cooling / volatile** — with India's strategic exposure framed explicitly.

### 🔍 Graph Path Query
Shortest-path discovery via `CO_OCCURS_WITH` edges (up to 4 hops) between any two named entities. Reveals non-obvious strategic connections invisible to keyword search. Example: *India → Afghanistan → Taliban → Pakistan*.

### ⚡ Surge Detection
Compares current week entity mention counts against per-week historical baseline. Flags entities surging above **1.5× threshold** with **HIGH / MED / LOW** urgency ratings and auto-generates alert briefs.

### 🗂 Semantic Profile
All typed `RELATES_TO` edges for any entity — outgoing (entity acts on others) and incoming (others act on entity) — colour-coded by relationship class: conflict, military, economic, diplomatic, governance.

### 📄 Weekly PDF Brief
Auto-identifies top 5 India-relevant developments of the week. Downloadable PDF with executive summary, risk matrix, and full source citations — zero user input required.

---

## Knowledge Graph Schema

```
(Article) -[:MENTIONS]→ (Entity)
(Entity)  -[:CO_OCCURS_WITH {count, weekly_counts_json, domains_json}]- (Entity)
(Entity)  -[:RELATES_TO    {type, count, articles[]}]→               (Entity)
```

### 30-Type Semantic Relationship Taxonomy

| Class | Types |
|-------|-------|
| **Economic** | `IMPORTS_FROM` · `EXPORTS_TO` · `SANCTIONS` · `INVESTS_IN` · `TRADES_WITH` · `FUNDS` · `OWNS` · `COMPETES_WITH` |
| **Military** | `SUPPLIES_WEAPONS_TO` · `ATTACKS` · `THREATENS` · `ALLIES_WITH` · `DEPLOYS_FORCES_IN` · `DEFEATS` · `OCCUPIES` |
| **Diplomatic** | `SUPPORTS` · `OPPOSES` · `NEGOTIATES_WITH` · `RECOGNIZES` · `EXPELS` · `ACCUSES` · `CONDEMNS` · `MEDIATES` |
| **Political** | `GOVERNS` · `CONTROLS` · `DISPUTES_TERRITORY_WITH` · `PROTESTS_AGAINST` · `ELECTS` · `LEADS` |
| **General** | `COOPERATES_WITH` · `CONFLICTS_WITH` · `DEPENDS_ON` · `INFLUENCES` |

---

## Five Strategic Domains · 32 Topics

| Domain | Topics |
|--------|--------|
| 🌐 **Geopolitics** | India-China border · India-Pakistan · India-Russia defence · India-Iran energy · Quad · BRICS · SCO · Israel-Iran · Taliban · India-USA · UN Security Council · NATO · Gaza conflict |
| 🏛 **Domestic** | Indian elections · BJP · Opposition politics · Constitutional developments |
| 📈 **Economics** | India GDP · Trade policy · Semiconductor supply chain · Rupee · FDI |
| 💡 **Technology** | AI regulation · Cyber security · India space · Defence tech · Digital India |
| 🤝 **Society** | Climate · Education · Healthcare · Social movements · Media freedom |

---

## Technology Stack

| Component | Service | Tier |
|-----------|---------|------|
| Graph Database | Neo4j AuraDB | Free (400k rel limit) |
| LLM Inference | Groq — Llama 3.1 8B + 3.3 70B | Free tier |
| NLP | spaCy `en_core_web_sm` | Open source |
| Web Scraping | Trafilatura | Open source |
| News Sources | NewsAPI + GDELT + Guardian API | Free tiers |
| Pipeline | Google Colab | Free tier |
| Dashboard | Streamlit Cloud + GitHub | Free (public repo) |
| **Total monthly cost** | — | **₹0** |

---

## Running the Pipeline

All credentials are stored in **Colab Secrets** (🔑 icon in left sidebar).

### Required secrets
```
NEWSAPI_KEY       — NewsAPI access
GUARDIAN_KEY      — Guardian API (optional, falls back to test key)
NEO4J_URI         — Neo4j AuraDB connection URI
NEO4J_USERNAME    — Neo4j username
NEO4J_PASSWORD    — Neo4j password
GROQ_API_KEY      — Groq LLM API
```

### Daily run sequence (10–15 min)
```
Cell 1  →  Install packages + load credentials
Cell 2  →  Fetch new articles (skips URLs already in graph this week)
Cell 3  →  Write articles + entities to Neo4j (accumulate mode)
Cell 3B →  Extract typed RELATES_TO semantic edges via Groq
```

### Weekly (optional)
```
Cell 4  →  Cleanup + entity deduplication + graph stats
```

> **Week rollover is automatic.** `get_week_key()` calls `datetime.now()` on every run — no manual step required when weeks change.

---

## Graph Capacity

| Metric | Current | Limit | Used |
|--------|---------|-------|------|
| Nodes | ~15,057 | 200,000 | 7.5% |
| Relationships | ~29,000 | 400,000 | 7.3% |
| Est. runway | ~100+ days | — | At current ingestion rate |

`count=1` edge pruning runs after every ingestion, removing noise and extending runway.

---

## Competition

**India Innovates 2026** · Domain 02: Digital Democracy
📍 28 March 2026 · Bharat Mandapam, New Delhi
🏆 ₹10,05,000 Prize Pool · HN × MCD

Problem statement addressed: *"Global Ontology Intelligence Graph"*

---

## Team

**Team IIMC** — Indian Institute of Management Calcutta · PGP 2025–27

| Name | Contact |
|------|---------|
| Shikhar Sharma | shikhars2027@email.iimcal.ac.in |
| Aditya | aditya2027@email.iimcal.ac.in |
| Brinda Bansal | brindab2027@email.iimcal.ac.in |

---

*Built for India Innovates 2026 · Domain 02: Digital Democracy · Bharat Mandapam, 28 March 2026*
