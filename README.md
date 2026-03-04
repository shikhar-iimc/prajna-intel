# prajna-intel
AI-Powered Strategic Intelligence Engine

# Prajna — Strategic Intelligence Engine
### AI-Powered Global Ontology Engine | India Innovates 2026

**Live Demo:** https://prajna-intel.streamlit.app

## What is Prajna?
Prajna is a real-time knowledge graph that maps relationships between 
geopolitical entities — countries, organizations, leaders — extracted 
from 35 live news topics across 5 strategic domains.

Unlike LLM chatbots that hallucinate context, Prajna grounds every 
intelligence brief in a verifiable graph of source-cited relationships.

## Architecture
```
NewsAPI → spaCy NLP → Neo4j Knowledge Graph → Groq LLM → Streamlit
```

## Five Domains
- Geopolitics
- Domestic Politics  
- Economics
- Technology
- Society

## Features
- **Intelligence Brief** — AI briefs grounded in graph context
- **Trajectory Analysis** — weekly relationship strength tracking
- **Path Query** — shortest path between any two entities
- **Surge Detection** — anomaly detection on entity co-occurrence

## Stack
- Neo4j AuraDB (graph database)
- Groq Llama 3.1 (inference)
- spaCy (NLP entity extraction)
- Streamlit (dashboard)
- NewsAPI, GDELT API, The Guardian API (live ingestion)

## Team
IIM Calcutta PGP | India Innovates 2026 | Domain 02: Digital Democracy
