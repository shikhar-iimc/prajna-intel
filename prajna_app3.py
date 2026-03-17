
# ════════════════════════════════════════════════════════════════
# PRAJNA INTELLIGENCE SUITE — prajna_app.py
# Prajna · Raksha · Artha
# Generated for India Innovates 2026 · TeamIIMC · IIM Calcutta
# ════════════════════════════════════════════════════════════════

# ── [SECTION: IMPORTS] ──────────────────────────────────────────
import streamlit as st
from neo4j import GraphDatabase
from groq import Groq
from pyvis.network import Network
import streamlit.components.v1 as components
import os, json, pandas as pd, io
from collections import defaultdict
from datetime import datetime, timezone
from fpdf import FPDF
# ── [END: IMPORTS] ──────────────────────────────────────────────


# ── [SECTION: CREDENTIALS] ──────────────────────────────────────
def _get_secret(key):
    # Try environment first, then Colab userdata, then Streamlit secrets
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
# ── [END: CREDENTIALS] ──────────────────────────────────────────


# ── [SECTION: LOGO PLACEHOLDER] ─────────────────────────────────
# Replaced by logo injection cell after %%writefile runs
LOGO_B64 = "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA0MDAgNDAwIiB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCI+CiAgPGRlZnM+CiAgICA8cmFkaWFsR3JhZGllbnQgaWQ9ImJnIiBjeD0iNTAlIiBjeT0iNTAlIiByPSI1MCUiPgogICAgICA8c3RvcCBvZmZzZXQ9IjAlIiBzdHlsZT0ic3RvcC1jb2xvcjojMEMwQTE0Ii8+CiAgICAgIDxzdG9wIG9mZnNldD0iMTAwJSIgc3R5bGU9InN0b3AtY29sb3I6IzA2MDQwOCIvPgogICAgPC9yYWRpYWxHcmFkaWVudD4KCiAgICA8cmFkaWFsR3JhZGllbnQgaWQ9ImNlbnRlckdsb3ciIGN4PSI1MCUiIGN5PSI1MCUiIHI9IjUwJSI+CiAgICAgIDxzdG9wIG9mZnNldD0iMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiNGRjk5MzM7c3RvcC1vcGFjaXR5OjAuMTUiLz4KICAgICAgPHN0b3Agb2Zmc2V0PSI3MCUiIHN0eWxlPSJzdG9wLWNvbG9yOiNGRjk5MzM7c3RvcC1vcGFjaXR5OjAuMDQiLz4KICAgICAgPHN0b3Agb2Zmc2V0PSIxMDAlIiBzdHlsZT0ic3RvcC1jb2xvcjojRkY5OTMzO3N0b3Atb3BhY2l0eTowIi8+CiAgICA8L3JhZGlhbEdyYWRpZW50PgoKICAgIDxsaW5lYXJHcmFkaWVudCBpZD0iZ29sZEdyYWQiIHgxPSIwJSIgeTE9IjAlIiB4Mj0iMTAwJSIgeTI9IjEwMCUiPgogICAgICA8c3RvcCBvZmZzZXQ9IjAlIiBzdHlsZT0ic3RvcC1jb2xvcjojQjg5NDNFIi8+CiAgICAgIDxzdG9wIG9mZnNldD0iNDUlIiBzdHlsZT0ic3RvcC1jb2xvcjojRThDOTZBIi8+CiAgICAgIDxzdG9wIG9mZnNldD0iMTAwJSIgc3R5bGU9InN0b3AtY29sb3I6I0I4OTQzRSIvPgogICAgPC9saW5lYXJHcmFkaWVudD4KCiAgICA8bGluZWFyR3JhZGllbnQgaWQ9InNhZmZyb24iIHgxPSIwJSIgeTE9IjAlIiB4Mj0iMTAwJSIgeTI9IjEwMCUiPgogICAgICA8c3RvcCBvZmZzZXQ9IjAlIiBzdHlsZT0ic3RvcC1jb2xvcjojRkY5OTMzIi8+CiAgICAgIDxzdG9wIG9mZnNldD0iMTAwJSIgc3R5bGU9InN0b3AtY29sb3I6I0U2NzMwMCIvPgogICAgPC9saW5lYXJHcmFkaWVudD4KCiAgICA8ZmlsdGVyIGlkPSJzb2Z0R2xvdyIgeD0iLTIwJSIgeT0iLTIwJSIgd2lkdGg9IjE0MCUiIGhlaWdodD0iMTQwJSI+CiAgICAgIDxmZUdhdXNzaWFuQmx1ciBzdGREZXZpYXRpb249IjIuNSIgcmVzdWx0PSJibHVyIi8+CiAgICAgIDxmZU1lcmdlPgogICAgICAgIDxmZU1lcmdlTm9kZSBpbj0iYmx1ciIvPgogICAgICAgIDxmZU1lcmdlTm9kZSBpbj0iU291cmNlR3JhcGhpYyIvPgogICAgICA8L2ZlTWVyZ2U+CiAgICA8L2ZpbHRlcj4KCiAgICA8ZmlsdGVyIGlkPSJzdWJ0bGVHbG93IiB4PSItMTAlIiB5PSItMTAlIiB3aWR0aD0iMTIwJSIgaGVpZ2h0PSIxMjAlIj4KICAgICAgPGZlR2F1c3NpYW5CbHVyIHN0ZERldmlhdGlvbj0iMS41IiByZXN1bHQ9ImJsdXIiLz4KICAgICAgPGZlTWVyZ2U+CiAgICAgICAgPGZlTWVyZ2VOb2RlIGluPSJibHVyIi8+CiAgICAgICAgPGZlTWVyZ2VOb2RlIGluPSJTb3VyY2VHcmFwaGljIi8+CiAgICAgIDwvZmVNZXJnZT4KICAgIDwvZmlsdGVyPgoKICAgIDxmaWx0ZXIgaWQ9InN0cm9uZ0dsb3ciIHg9Ii0zMCUiIHk9Ii0zMCUiIHdpZHRoPSIxNjAlIiBoZWlnaHQ9IjE2MCUiPgogICAgICA8ZmVHYXVzc2lhbkJsdXIgc3RkRGV2aWF0aW9uPSI1IiByZXN1bHQ9ImJsdXIiLz4KICAgICAgPGZlTWVyZ2U+CiAgICAgICAgPGZlTWVyZ2VOb2RlIGluPSJibHVyIi8+CiAgICAgICAgPGZlTWVyZ2VOb2RlIGluPSJTb3VyY2VHcmFwaGljIi8+CiAgICAgIDwvZmVNZXJnZT4KICAgIDwvZmlsdGVyPgogIDwvZGVmcz4KCiAgPCEtLSBCYWNrZ3JvdW5kIGNpcmNsZSAtLT4KICA8Y2lyY2xlIGN4PSIyMDAiIGN5PSIyMDAiIHI9IjIwMCIgZmlsbD0idXJsKCNiZykiLz4KCiAgPCEtLSBBbWJpZW50IGNlbnRyZSBnbG93IC0tPgogIDxjaXJjbGUgY3g9IjIwMCIgY3k9IjIwMCIgcj0iMTMwIiBmaWxsPSJ1cmwoI2NlbnRlckdsb3cpIi8+CgogIDwhLS0g4pSA4pSAIE9VVEVSTU9TVCBSSU5HIOKAlCBoYWlybGluZSBwcmVjaXNpb24g4pSA4pSAIC0tPgogIDxjaXJjbGUgY3g9IjIwMCIgY3k9IjIwMCIgcj0iMTc2IiBmaWxsPSJub25lIiAKICAgICAgICAgIHN0cm9rZT0iI0M4QTk2RSIgc3Ryb2tlLXdpZHRoPSIwLjUiIG9wYWNpdHk9IjAuMjUiLz4KCiAgPCEtLSDilIDilIAgT1VURVIgUklORyDigJQgbWFpbiBib3JkZXIg4pSA4pSAIC0tPgogIDxjaXJjbGUgY3g9IjIwMCIgY3k9IjIwMCIgcj0iMTY4IiBmaWxsPSJub25lIiAKICAgICAgICAgIHN0cm9rZT0idXJsKCNnb2xkR3JhZCkiIHN0cm9rZS13aWR0aD0iMS4yIiBvcGFjaXR5PSIwLjUiCiAgICAgICAgICBmaWx0ZXI9InVybCgjc3VidGxlR2xvdykiLz4KCiAgPCEtLSDilIDilIAgQVNIT0tBIENIQUtSQSBSSU5HIOKAlCBvdXRlciDilIDilIAgLS0+CiAgPGNpcmNsZSBjeD0iMjAwIiBjeT0iMjAwIiByPSIxMDgiIGZpbGw9Im5vbmUiCiAgICAgICAgICBzdHJva2U9InVybCgjZ29sZEdyYWQpIiBzdHJva2Utd2lkdGg9IjEuOCIgb3BhY2l0eT0iMC43IgogICAgICAgICAgZmlsdGVyPSJ1cmwoI3N1YnRsZUdsb3cpIi8+CgogIDwhLS0g4pSA4pSAIEFTSE9LQSBDSEFLUkEg4oCUIDI0IHNwb2tlcyDilIDilIAgLS0+CiAgPCEtLSBFYWNoIHNwb2tlIGZyb20gcj0xMDggaW53YXJkIHRvIHI9NzIgLS0+CiAgPGcgZmlsdGVyPSJ1cmwoI3N1YnRsZUdsb3cpIj4KICAgIDwhLS0gU2FmZnJvbiBzcG9rZSBsYXllciAtLT4KICAgIDxnIHN0cm9rZT0iI0ZGOTkzMyIgc3Ryb2tlLXdpZHRoPSIxIiBvcGFjaXR5PSIwLjU1IiBzdHJva2UtbGluZWNhcD0icm91bmQiPgogICAgICA8bGluZSB4MT0iMjAwIiB5MT0iOTIiIHgyPSIyMDAiIHkyPSIxMjgiLz4KICAgICAgPGxpbmUgeDE9IjIxNS45IiB5MT0iOTIuNyIgeDI9IjIxMS45IiB5Mj0iMTI4LjQiLz4KICAgICAgPGxpbmUgeDE9IjIzMS4yIiB5MT0iOTUuMyIgeDI9IjIyMy40IiB5Mj0iMTMwLjIiLz4KICAgICAgPGxpbmUgeDE9IjI0NS41IiB5MT0iOTkuOSIgeDI9IjIzNC4xIiB5Mj0iMTMzLjIiLz4KICAgICAgPGxpbmUgeDE9IjI1OC40IiB5MT0iMTA2LjMiIHgyPSIyNDQuMCIgeTI9IjEzNy41Ii8+CiAgICAgIDxsaW5lIHgxPSIyNjkuNyIgeTE9IjExNC40IiB4Mj0iMjUyLjkiIHkyPSIxNDIuOSIvPgogICAgICA8bGluZSB4MT0iMjc5LjAiIHkxPSIxMjQuMSIgeDI9IjI2MC42IiB5Mj0iMTQ5LjQiLz4KICAgICAgPGxpbmUgeDE9IjI4Ni4xIiB5MT0iMTM1LjEiIHgyPSIyNjYuOSIgeTI9IjE1Ni44Ii8+CiAgICAgIDxsaW5lIHgxPSIyOTAuOSIgeTE9IjE0Ny4zIiB4Mj0iMjcxLjYiIHkyPSIxNjUuMCIvPgogICAgICA8bGluZSB4MT0iMjkzLjMiIHkxPSIxNjAuMyIgeDI9IjI3NC42IiB5Mj0iMTczLjciLz4KICAgICAgPGxpbmUgeDE9IjI5My4zIiB5MT0iMTczLjciIHgyPSIyNzUuOSIgeTI9IjE4Mi41Ii8+CiAgICAgIDxsaW5lIHgxPSIyOTAuOSIgeTE9IjE4Ni44IiB4Mj0iMjc1LjUiIHkyPSIxOTEuMiIvPgogICAgICA8bGluZSB4MT0iMjg2LjEiIHkxPSIxOTkuMiIgeDI9IjI3My40IiB5Mj0iMTk5LjIiLz4KICAgICAgPGxpbmUgeDE9IjI3OS4wIiB5MT0iMjEwLjYiIHgyPSIyNjkuNyIgeTI9IjIwNi45Ii8+CiAgICAgIDxsaW5lIHgxPSIyNjkuNyIgeTE9IjIyMC44IiB4Mj0iMjY0LjYiIHkyPSIyMTQuMyIvPgogICAgICA8bGluZSB4MT0iMjU4LjQiIHkxPSIyMjkuMCIgeDI9IjI1Ny42IiB5Mj0iMjIxLjEiLz4KICAgICAgPGxpbmUgeDE9IjI0NS41IiB5MT0iMjM0LjkiIHgyPSIyNDguOSIgeTI9IjIyNy4yIi8+CiAgICAgIDxsaW5lIHgxPSIyMzEuMiIgeTE9IjIzOC41IiB4Mj0iMjM4LjUiIHkyPSIyMzIuNCIvPgogICAgICA8bGluZSB4MT0iMjE1LjkiIHkxPSIyMzkuOCIgeDI9IjIyNi41IiB5Mj0iMjM1LjgiLz4KICAgICAgPGxpbmUgeDE9IjIwMCIgeTE9IjIzOC44IiB4Mj0iMjEzLjEiIHkyPSIyMzcuNSIvPgogICAgICA8bGluZSB4MT0iMTg0LjEiIHkxPSIyMzUuNSIgeDI9IjE5OC44IiB5Mj0iMjM2LjgiLz4KICAgICAgPGxpbmUgeDE9IjE2OC44IiB5MT0iMjI5LjkiIHgyPSIxODMuOCIgeTI9IjIzMy44Ii8+CiAgICAgIDxsaW5lIHgxPSIxNTQuNSIgeTE9IjIyMi4xIiB4Mj0iMTY4LjMiIHkyPSIyMjguNiIvPgogICAgICA8bGluZSB4MT0iMTQxLjYiIHkxPSIyMTIuNSIgeDI9IjE1My44IiB5Mj0iMjIxLjYiLz4KICAgIDwvZz4KCiAgICA8IS0tIEdvbGQgc3Bva2Ugb3ZlcmxheSDigJQgYWx0ZXJuYXRlIHNwb2tlcywgdGhpbm5lciAtLT4KICAgIDxnIHN0cm9rZT0iI0M4QTk2RSIgc3Ryb2tlLXdpZHRoPSIwLjYiIG9wYWNpdHk9IjAuNCIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIj4KICAgICAgPGxpbmUgeDE9IjIwMCIgeTE9IjkyIiB4Mj0iMjAwIiB5Mj0iMTI4Ii8+CiAgICAgIDxsaW5lIHgxPSIyMzEuMiIgeTE9Ijk1LjMiIHgyPSIyMjMuNCIgeTI9IjEzMC4yIi8+CiAgICAgIDxsaW5lIHgxPSIyNTguNCIgeTE9IjEwNi4zIiB4Mj0iMjQ0LjAiIHkyPSIxMzcuNSIvPgogICAgICA8bGluZSB4MT0iMjc5LjAiIHkxPSIxMjQuMSIgeDI9IjI2MC42IiB5Mj0iMTQ5LjQiLz4KICAgICAgPGxpbmUgeDE9IjI5MC45IiB5MT0iMTQ3LjMiIHgyPSIyNzEuNiIgeTI9IjE2NS4wIi8+CiAgICAgIDxsaW5lIHgxPSIyOTMuMyIgeTE9IjE3My43IiB4Mj0iMjc1LjkiIHkyPSIxODIuNSIvPgogICAgICA8bGluZSB4MT0iMjg2LjEiIHkxPSIxOTkuMiIgeDI9IjI3My40IiB5Mj0iMTk5LjIiLz4KICAgICAgPGxpbmUgeDE9IjI2OS43IiB5MT0iMjIwLjgiIHgyPSIyNjQuNiIgeTI9IjIxNC4zIi8+CiAgICAgIDxsaW5lIHgxPSIyNDUuNSIgeTE9IjIzNC45IiB4Mj0iMjQ4LjkiIHkyPSIyMjcuMiIvPgogICAgICA8bGluZSB4MT0iMjE1LjkiIHkxPSIyMzkuOCIgeDI9IjIyNi41IiB5Mj0iMjM1LjgiLz4KICAgICAgPGxpbmUgeDE9IjE4NC4xIiB5MT0iMjM1LjUiIHgyPSIxOTguOCIgeTI9IjIzNi44Ii8+CiAgICAgIDxsaW5lIHgxPSIxNTQuNSIgeTE9IjIyMi4xIiB4Mj0iMTY4LjMiIHkyPSIyMjguNiIvPgogICAgPC9nPgogIDwvZz4KCiAgPCEtLSDilIDilIAgQ0hBS1JBIElOTkVSIFJJTkcg4pSA4pSAIC0tPgogIDxjaXJjbGUgY3g9IjIwMCIgY3k9IjIwMCIgcj0iNzIiIGZpbGw9Im5vbmUiCiAgICAgICAgICBzdHJva2U9InVybCgjZ29sZEdyYWQpIiBzdHJva2Utd2lkdGg9IjEuNSIgb3BhY2l0eT0iMC42NSIKICAgICAgICAgIGZpbHRlcj0idXJsKCNzdWJ0bGVHbG93KSIvPgoKICA8IS0tIOKUgOKUgCBJTk5FUiBSSU5HIOKUgOKUgCAtLT4KICA8Y2lyY2xlIGN4PSIyMDAiIGN5PSIyMDAiIHI9IjQ4IiBmaWxsPSJub25lIgogICAgICAgICAgc3Ryb2tlPSIjQzhBOTZFIiBzdHJva2Utd2lkdGg9IjAuOCIgb3BhY2l0eT0iMC4zIi8+CgogIDwhLS0g4pSA4pSAIFRSSUNPTE9VUiBBUkNTIOKAlCB1bHRyYSBzdWJ0bGUg4pSA4pSAIC0tPgogIDwhLS0gU2FmZnJvbiDigJQgdG9wIHF1YXJ0ZXIgYXJjIC0tPgogIDxwYXRoIGQ9Ik0gMTQ4IDE1MiBBIDczIDczIDAgMCAxIDI1MiAxNTIiCiAgICAgICAgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjRkY5OTMzIiBzdHJva2Utd2lkdGg9IjIuNSIgCiAgICAgICAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBvcGFjaXR5PSIwLjUiCiAgICAgICAgZmlsdGVyPSJ1cmwoI3N1YnRsZUdsb3cpIi8+CiAgPCEtLSBHcmVlbiDigJQgYm90dG9tIHF1YXJ0ZXIgYXJjIC0tPgogIDxwYXRoIGQ9Ik0gMTQ4IDI0OCBBIDczIDczIDAgMCAwIDI1MiAyNDgiCiAgICAgICAgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjMTM4ODA4IiBzdHJva2Utd2lkdGg9IjIuNSIKICAgICAgICBzdHJva2UtbGluZWNhcD0icm91bmQiIG9wYWNpdHk9IjAuNSIKICAgICAgICBmaWx0ZXI9InVybCgjc3VidGxlR2xvdykiLz4KICA8IS0tIE5hdnkg4oCUIHJpZ2h0IGFyYyAtLT4KICA8cGF0aCBkPSJNIDI3MyAyMDAgQSA3MyA3MyAwIDAgMSAyNTIgMjQ4IgogICAgICAgIGZpbGw9Im5vbmUiIHN0cm9rZT0iIzAwMDA2NiIgc3Ryb2tlLXdpZHRoPSIyIgogICAgICAgIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgb3BhY2l0eT0iMC42Ii8+CgogIDwhLS0g4pSA4pSAIE5FVVJBTCBDT05TVEVMTEFUSU9OIOKUgOKUgCAtLT4KICA8IS0tIE91dGVyIGNvbnN0ZWxsYXRpb24gcG9pbnRzIOKAlCA4IGNhcmRpbmFsL2ludGVyY2FyZGluYWwgcG9zaXRpb25zIC0tPgogIDxnIGZpbHRlcj0idXJsKCNzdWJ0bGVHbG93KSI+CiAgICA8IS0tIDggb3V0ZXIgbm9kZXMgYXQgcj01NSAtLT4KICAgIDxjaXJjbGUgY3g9IjIwMCIgY3k9IjE0NSIgcj0iMi4yIiBmaWxsPSIjRkY5OTMzIiBvcGFjaXR5PSIwLjciLz4KICAgIDxjaXJjbGUgY3g9IjIzOSIgY3k9IjE2MSIgcj0iMS44IiBmaWxsPSIjQzhBOTZFIiBvcGFjaXR5PSIwLjYiLz4KICAgIDxjaXJjbGUgY3g9IjI1NSIgY3k9IjIwMCIgcj0iMi4yIiBmaWxsPSIjRkY5OTMzIiBvcGFjaXR5PSIwLjciLz4KICAgIDxjaXJjbGUgY3g9IjIzOSIgY3k9IjIzOSIgcj0iMS44IiBmaWxsPSIjQzhBOTZFIiBvcGFjaXR5PSIwLjYiLz4KICAgIDxjaXJjbGUgY3g9IjIwMCIgY3k9IjI1NSIgcj0iMi4yIiBmaWxsPSIjRkY5OTMzIiBvcGFjaXR5PSIwLjciLz4KICAgIDxjaXJjbGUgY3g9IjE2MSIgY3k9IjIzOSIgcj0iMS44IiBmaWxsPSIjQzhBOTZFIiBvcGFjaXR5PSIwLjYiLz4KICAgIDxjaXJjbGUgY3g9IjE0NSIgY3k9IjIwMCIgcj0iMi4yIiBmaWxsPSIjRkY5OTMzIiBvcGFjaXR5PSIwLjciLz4KICAgIDxjaXJjbGUgY3g9IjE2MSIgY3k9IjE2MSIgcj0iMS44IiBmaWxsPSIjQzhBOTZFIiBvcGFjaXR5PSIwLjYiLz4KICA8L2c+CgogIDwhLS0gQ29ubmVjdGlvbiBsaW5lcyDigJQgbmV1cmFsIHdlYiAtLT4KICA8ZyBzdHJva2U9IiNGRjk5MzMiIHN0cm9rZS13aWR0aD0iMC41IiBvcGFjaXR5PSIwLjIiPgogICAgPGxpbmUgeDE9IjIwMCIgeTE9IjE0NSIgeDI9IjIzOSIgeTI9IjE2MSIvPgogICAgPGxpbmUgeDE9IjIzOSIgeTE9IjE2MSIgeDI9IjI1NSIgeTI9IjIwMCIvPgogICAgPGxpbmUgeDE9IjI1NSIgeTE9IjIwMCIgeDI9IjIzOSIgeTI9IjIzOSIvPgogICAgPGxpbmUgeDE9IjIzOSIgeTE9IjIzOSIgeDI9IjIwMCIgeTI9IjI1NSIvPgogICAgPGxpbmUgeDE9IjIwMCIgeTE9IjI1NSIgeDI9IjE2MSIgeTI9IjIzOSIvPgogICAgPGxpbmUgeDE9IjE2MSIgeTE9IjIzOSIgeDI9IjE0NSIgeTI9IjIwMCIvPgogICAgPGxpbmUgeDE9IjE0NSIgeTE9IjIwMCIgeDI9IjE2MSIgeTI9IjE2MSIvPgogICAgPGxpbmUgeDE9IjE2MSIgeTE9IjE2MSIgeDI9IjIwMCIgeTI9IjE0NSIvPgogICAgPCEtLSBDcm9zcyBjb25uZWN0aW9ucyAtLT4KICAgIDxsaW5lIHgxPSIyMDAiIHkxPSIxNDUiIHgyPSIyNTUiIHkyPSIyMDAiLz4KICAgIDxsaW5lIHgxPSIyNTUiIHkxPSIyMDAiIHgyPSIyMDAiIHkyPSIyNTUiLz4KICAgIDxsaW5lIHgxPSIyMDAiIHkxPSIyNTUiIHgyPSIxNDUiIHkyPSIyMDAiLz4KICAgIDxsaW5lIHgxPSIxNDUiIHkxPSIyMDAiIHgyPSIyMDAiIHkyPSIxNDUiLz4KICAgIDxsaW5lIHgxPSIyMzkiIHkxPSIxNjEiIHgyPSIyMzkiIHkyPSIyMzkiLz4KICAgIDxsaW5lIHgxPSIxNjEiIHkxPSIxNjEiIHgyPSIxNjEiIHkyPSIyMzkiLz4KICAgIDwhLS0gVG8gY2VudHJlIC0tPgogICAgPGxpbmUgeDE9IjIwMCIgeTE9IjE0NSIgeDI9IjIwMCIgeTI9IjIwMCIvPgogICAgPGxpbmUgeDE9IjI1NSIgeTE9IjIwMCIgeDI9IjIwMCIgeTI9IjIwMCIvPgogICAgPGxpbmUgeDE9IjIwMCIgeTE9IjI1NSIgeDI9IjIwMCIgeTI9IjIwMCIvPgogICAgPGxpbmUgeDE9IjE0NSIgeTE9IjIwMCIgeDI9IjIwMCIgeTI9IjIwMCIvPgogIDwvZz4KCiAgPCEtLSDilIDilIAgQ0VOVFJFIOKAlCB0aGUgZXllIG9mIHdpc2RvbSDilIDilIAgLS0+CiAgPCEtLSBPdXRlciBwdWxzZSByaW5nIC0tPgogIDxjaXJjbGUgY3g9IjIwMCIgY3k9IjIwMCIgcj0iMTgiIGZpbGw9Im5vbmUiCiAgICAgICAgICBzdHJva2U9IiNGRjk5MzMiIHN0cm9rZS13aWR0aD0iMC44IiBvcGFjaXR5PSIwLjIiLz4KICA8Y2lyY2xlIGN4PSIyMDAiIGN5PSIyMDAiIHI9IjEzIiBmaWxsPSJub25lIgogICAgICAgICAgc3Ryb2tlPSIjRkY5OTMzIiBzdHJva2Utd2lkdGg9IjAuNiIgb3BhY2l0eT0iMC4zIi8+CgogIDwhLS0gQ2VudHJlIG9yYiAtLT4KICA8Y2lyY2xlIGN4PSIyMDAiIGN5PSIyMDAiIHI9IjkiIAogICAgICAgICAgZmlsbD0iI0ZGOTkzMyIgb3BhY2l0eT0iMC4xMiIKICAgICAgICAgIGZpbHRlcj0idXJsKCNzdHJvbmdHbG93KSIvPgogIDxjaXJjbGUgY3g9IjIwMCIgY3k9IjIwMCIgcj0iNi41IiAKICAgICAgICAgIGZpbGw9IiMwQzBBMTQiIHN0cm9rZT0iI0ZGOTkzMyIgCiAgICAgICAgICBzdHJva2Utd2lkdGg9IjEuMiIgb3BhY2l0eT0iMC45IgogICAgICAgICAgZmlsdGVyPSJ1cmwoI3NvZnRHbG93KSIvPgogIDxjaXJjbGUgY3g9IjIwMCIgY3k9IjIwMCIgcj0iMy41IiAKICAgICAgICAgIGZpbGw9IiNGRjk5MzMiIG9wYWNpdHk9IjAuODUiCiAgICAgICAgICBmaWx0ZXI9InVybCgjc29mdEdsb3cpIi8+CiAgPCEtLSBJbm5lciBoaWdobGlnaHQgLS0+CiAgPGNpcmNsZSBjeD0iMTk4LjUiIGN5PSIxOTguNSIgcj0iMS4yIiBmaWxsPSIjRkZFMDY2IiBvcGFjaXR5PSIwLjgiLz4KCiAgPCEtLSDilIDilIAgRk9VUiBDQVJESU5BTCBESUFNT05EIE1BUktTIOKUgOKUgCAtLT4KICA8ZyBmaWxsPSIjQzhBOTZFIiBvcGFjaXR5PSIwLjQ1IiBmaWx0ZXI9InVybCgjc3VidGxlR2xvdykiPgogICAgPCEtLSBUb3AgLS0+CiAgICA8cG9seWdvbiBwb2ludHM9IjIwMCw3NyAyMDMsODMgMjAwLDg5IDE5Nyw4MyIvPgogICAgPCEtLSBSaWdodCAtLT4KICAgIDxwb2x5Z29uIHBvaW50cz0iMzIzLDIwMCAzMTcsMjAzIDMxMSwyMDAgMzE3LDE5NyIvPgogICAgPCEtLSBCb3R0b20gLS0+CiAgICA8cG9seWdvbiBwb2ludHM9IjIwMCwzMjMgMjAzLDMxNyAyMDAsMzExIDE5NywzMTciLz4KICAgIDwhLS0gTGVmdCAtLT4KICAgIDxwb2x5Z29uIHBvaW50cz0iNzcsMjAwIDgzLDIwMyA4OSwyMDAgODMsMTk3Ii8+CiAgPC9nPgoKICA8IS0tIOKUgOKUgCBDT1JORVIgUkVUSUNMRSBNQVJLUyDilIDilIAgLS0+CiAgPGcgc3Ryb2tlPSIjQzhBOTZFIiBzdHJva2Utd2lkdGg9IjAuOCIgb3BhY2l0eT0iMC4zIiBzdHJva2UtbGluZWNhcD0icm91bmQiPgogICAgPGxpbmUgeDE9IjQ4IiB5MT0iNjgiIHgyPSI2NCIgeTI9IjY4Ii8+CiAgICA8bGluZSB4MT0iNDgiIHkxPSI2OCIgeDI9IjQ4IiB5Mj0iODQiLz4KICAgIDxsaW5lIHgxPSIzNTIiIHkxPSI2OCIgeDI9IjMzNiIgeTI9IjY4Ii8+CiAgICA8bGluZSB4MT0iMzUyIiB5MT0iNjgiIHgyPSIzNTIiIHkyPSI4NCIvPgogICAgPGxpbmUgeDE9IjQ4IiB5MT0iMzMyIiB4Mj0iNjQiIHkyPSIzMzIiLz4KICAgIDxsaW5lIHgxPSI0OCIgeTE9IjMzMiIgeDI9IjQ4IiB5Mj0iMzE2Ii8+CiAgICA8bGluZSB4MT0iMzUyIiB5MT0iMzMyIiB4Mj0iMzM2IiB5Mj0iMzMyIi8+CiAgICA8bGluZSB4MT0iMzUyIiB5MT0iMzMyIiB4Mj0iMzUyIiB5Mj0iMzE2Ii8+CiAgPC9nPgoKICA8IS0tIOKUgOKUgCBERUdSRUUgTUFSS1Mgb24gb3V0ZXIgcmluZyDigJQgbGlrZSBhIGNvbXBhc3Mg4pSA4pSAIC0tPgogIDxnIHN0cm9rZT0iI0M4QTk2RSIgc3Ryb2tlLXdpZHRoPSIwLjciIG9wYWNpdHk9IjAuMjUiPgogICAgPCEtLSAxMiB0aWNrIG1hcmtzIGV2ZXJ5IDMwIGRlZ3JlZXMgLS0+CiAgICA8bGluZSB4MT0iMjAwIiB5MT0iMjQiIHgyPSIyMDAiIHkyPSIzNCIvPgogICAgPGxpbmUgeDE9IjI4OCIgeTE9IjUwIiB4Mj0iMjgzIiB5Mj0iNTkiLz4KICAgIDxsaW5lIHgxPSIzNTAiIHkxPSIxMTIiIHgyPSIzNDEiIHkyPSIxMTciLz4KICAgIDxsaW5lIHgxPSIzNzYiIHkxPSIyMDAiIHgyPSIzNjYiIHkyPSIyMDAiLz4KICAgIDxsaW5lIHgxPSIzNTAiIHkxPSIyODgiIHgyPSIzNDEiIHkyPSIyODMiLz4KICAgIDxsaW5lIHgxPSIyODgiIHkxPSIzNTAiIHgyPSIyODMiIHkyPSIzNDEiLz4KICAgIDxsaW5lIHgxPSIyMDAiIHkxPSIzNzYiIHgyPSIyMDAiIHkyPSIzNjYiLz4KICAgIDxsaW5lIHgxPSIxMTIiIHkxPSIzNTAiIHgyPSIxMTciIHkyPSIzNDEiLz4KICAgIDxsaW5lIHgxPSI1MCIgeTE9IjI4OCIgeDI9IjU5IiB5Mj0iMjgzIi8+CiAgICA8bGluZSB4MT0iMjQiIHkxPSIyMDAiIHgyPSIzNCIgeTI9IjIwMCIvPgogICAgPGxpbmUgeDE9IjUwIiB5MT0iMTEyIiB4Mj0iNTkiIHkyPSIxMTciLz4KICAgIDxsaW5lIHgxPSIxMTIiIHkxPSI1MCIgeDI9IjExNyIgeTI9IjU5Ii8+CiAgPC9nPgoKPC9zdmc+Cg=="
# ── [END: LOGO PLACEHOLDER] ─────────────────────────────────────


# ── [SECTION: CONNECTIONS] ──────────────────────────────────────
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
# ── [END: CONNECTIONS] ──────────────────────────────────────────


# ── [SECTION: UTILITY FUNCTIONS] ────────────────────────────────
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

def sanitize(text):
    if not text:
        return ""
    replacements = {
        "\u2014": "-", "\u2013": "-", "\u2012": "-",
        "\u2018": "'", "\u2019": "'", "\u201a": "'",
        "\u201c": '"', "\u201d": '"', "\u201e": '"',
        "\u2022": "*", "\u2023": "*", "\u25aa": "*",
        "\u2026": "...", "\u00a0": " ", "\u2032": "'",
        "\u00e9": "e", "\u00e8": "e", "\u00ea": "e",
        "\u00e0": "a", "\u00e2": "a", "\u00f4": "o",
        "\u00fb": "u", "\u00fc": "u", "\u00ef": "i",
        "\u00e7": "c", "\u00f1": "n",
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
# ── [END: UTILITY FUNCTIONS] ────────────────────────────────────


# ── [SECTION: PDF GENERATOR] ────────────────────────────────────
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
    pdf.multi_cell(0, 5, "Auto-generated by Prajna using knowledge graph analysis of real-time news data. For strategic assessment purposes only.")

    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf.read()
# ── [END: PDF GENERATOR] ────────────────────────────────────────


# ── [SECTION: NEO4J QUERY FUNCTIONS] ────────────────────────────
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
        result = session.run(
            "MATCH (a:Article) RETURN DISTINCT a.week as week ORDER BY week DESC"
        ).data()
    weeks = [r["week"] for r in result if r["week"]]

    def week_label(wk):
        try:
            monday = datetime.strptime(wk + "-1", "%Y-W%W-%w")
            sunday = monday + timedelta(days=6)
            return f"{wk}  ({monday.strftime('%d %b')} – {sunday.strftime('%d %b %Y')})"
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
            RETURN a.week AS week, COUNT(a) AS cnt
            ORDER BY week
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
# ── [END: NEO4J QUERY FUNCTIONS] ────────────────────────────────


# ── [SECTION: SURGE DETECTION] ──────────────────────────────────
BLOCKLIST = {
    "Supreme","Asian","Islam","American","European","Western","Eastern",
    "BBC","CNN","Reuters","Bloomberg","NDTV","Mint","Hindu","Express",
    "ANI","PTI","AFP","AP","Wire","Tribune","Times","Globe","Newswire", "Guardian", "Reuters", "Bloomberg", "BBC", "CNN", "AP", "AFP",
    "NewsAPI", "NDTV", "Mint", "Times", "Tribune", "Wire",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
    "New Year", "World", "Global", "International", "National"
}

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
        if entity in BLOCKLIST:                                           continue
        if entity_total[entity] < 8:                                      continue
        if len(entity) > 35:                                              continue
        if any(c.isdigit() for c in entity):                              continue
        if entity_type.get(entity) not in {"GPE","ORG","PERSON","NORP"}:  continue
        weeks = sorted(weekly.keys())
        if not weeks or weeks[-1] != week_key:                            continue
        latest   = weekly[weeks[-1]]
        hist     = [weekly[w] for w in weeks[:-1]]
        baseline = sum(hist)/len(hist) if hist else latest
        if baseline == 0: continue
        ratio = latest / baseline
        if ratio >= threshold:
            surges.append({
                "entity":   entity,
                "type":     entity_type.get(entity, ""),
                "latest":   latest,
                "baseline": round(baseline, 1),
                "ratio":    round(ratio, 2),
                "total":    entity_total[entity]
            })
    surges.sort(key=lambda x: x["ratio"], reverse=True)
    return surges[:top_n]
# ── [END: SURGE DETECTION] ──────────────────────────────────────


# ── [SECTION: RELATION COLOR MAP] ───────────────────────────────
RELATION_COLORS = {
    "THREATENS":              "#C87B6A",
    "ATTACKS":                "#C87B6A",
    "CONFLICTS_WITH":         "#C87B6A",
    "DEFEATS":                "#C87B6A",
    "SUPPLIES_WEAPONS_TO":    "#C8956A",
    "DEPLOYS_FORCES_IN":      "#C8956A",
    "OCCUPIES":               "#C8956A",
    "SANCTIONS":              "#C8B86A",
    "ACCUSES":                "#C8B86A",
    "CONDEMNS":               "#C8B86A",
    "OPPOSES":                "#C8B86A",
    "PROTESTS_AGAINST":       "#C8B86A",
    "DISPUTES_TERRITORY_WITH":"#C8B86A",
    "EXPELS":                 "#C8B86A",
    "IMPORTS_FROM":           "#6B8CAE",
    "EXPORTS_TO":             "#6B8CAE",
    "TRADES_WITH":            "#6B8CAE",
    "COMPETES_WITH":          "#6B8CAE",
    "DEPENDS_ON":             "#6B8CAE",
    "OWNS":                   "#6B8CAE",
    "ALLIES_WITH":            "#4A8A6A",
    "SUPPORTS":               "#4A8A6A",
    "COOPERATES_WITH":        "#4A8A6A",
    "FUNDS":                  "#4A8A6A",
    "RECOGNIZES":             "#4A8A6A",
    "GOVERNS":                "#8A6AAE",
    "CONTROLS":               "#8A6AAE",
    "LEADS":                  "#8A6AAE",
    "ELECTS":                 "#8A6AAE",
    "NEGOTIATES_WITH":        "#4A8AAA",
    "MEDIATES":               "#4A8AAA",
    "INFLUENCES":             "#4A8AAA",
    "INVESTS_IN":             "#4A8AAA",
}
# ── [END: RELATION COLOR MAP] ───────────────────────────────────


# ── [SECTION: GRAPH VISUALIZER] ─────────────────────────────────
def build_graph_visual(keyword=None, week=None, mode="semantic"):
    TYPE_COLORS = {
        "GPE":    "#C8A96E",
        "ORG":    "#6B8CAE",
        "PERSON": "#A8C5A0",
        "NORP":   "#B8956A",
        "LOC":    "#8AABBA",
        "EVENT":  "#C47B6E"
    }

    kw_list = [k.strip().lower() for k in keyword.split(",") if k.strip()] if keyword else []

    with driver.session() as session:

        if mode == "semantic":
            if kw_list:
                seed_results = session.run("""
                    MATCH (e:Entity)
                    WHERE any(kw IN $kw_list WHERE toLower(e.name) CONTAINS kw)
                    RETURN e.name AS name, e.type AS type
                    LIMIT 20
                """, {"kw_list": kw_list})
                seeds = [r["name"] for r in seed_results]

                if not seeds:
                    res = session.run("""
                        MATCH (node:Entity)-[r:RELATES_TO]-()
                        WITH node, COUNT(r) AS conn
                        ORDER BY conn DESC LIMIT 40
                        RETURN node.name AS name, node.type AS type, conn
                    """)
                    top = {r["name"]: r for r in res}
                else:
                    nb_results = session.run("""
                        MATCH (e:Entity)-[:RELATES_TO]-(nb:Entity)
                        WHERE e.name IN $seeds
                        WITH COLLECT(DISTINCT nb.name) AS neighbors
                        RETURN neighbors
                    """, {"seeds": seeds})
                    nb_row    = nb_results.single()
                    neighbors = nb_row["neighbors"] if nb_row else []
                    all_names = list(set(seeds + neighbors))

                    node_results = session.run("""
                        MATCH (node:Entity)-[r:RELATES_TO]-()
                        WHERE node.name IN $all_names
                        WITH node, COUNT(r) AS conn
                        ORDER BY conn DESC LIMIT 40
                        RETURN node.name AS name, node.type AS type, conn
                    """, {"all_names": all_names})
                    top = {r["name"]: r for r in node_results}
            else:
                res = session.run("""
                    MATCH (node:Entity)-[r:RELATES_TO]-()
                    WITH node, COUNT(r) AS conn
                    ORDER BY conn DESC LIMIT 40
                    RETURN node.name AS name, node.type AS type, conn
                """)
                top = {r["name"]: r for r in res}

            rels = session.run("""
                MATCH (e1:Entity)-[r:RELATES_TO]->(e2:Entity)
                WHERE e1.name IN $names AND e2.name IN $names
                RETURN e1.name AS source, e2.name AS target,
                       r.type AS rel_type, r.count AS weight
                ORDER BY weight DESC
            """, {"names": list(top.keys())})
            relationships = [dict(r) for r in rels]

        else:
            if week:
                if kw_list:
                    res = session.run("""
                        MATCH (a:Article {week:$week})-[:MENTIONS]->(e:Entity)
                        WHERE any(kw IN $kw_list WHERE toLower(e.name) CONTAINS kw)
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
                    """, {"week": week, "kw_list": kw_list})
                else:
                    res = session.run("""
                        MATCH (a:Article {week:$week})-[:MENTIONS]->(e:Entity)
                        WITH DISTINCT e
                        MATCH (e)-[r:CO_OCCURS_WITH]-()
                        WHERE r.weekly_counts_json CONTAINS $week
                        WITH e, COUNT(r) AS conn
                        ORDER BY conn DESC LIMIT 40
                        RETURN e.name AS name, e.type AS type, conn
                    """, {"week": week})
            else:
                if kw_list:
                    res = session.run("""
                        MATCH (e:Entity)
                        WHERE any(kw IN $kw_list WHERE toLower(e.name) CONTAINS kw)
                        WITH e
                        MATCH (e)-[:CO_OCCURS_WITH]-(other:Entity)
                        WITH collect(DISTINCT e)+collect(DISTINCT other) AS nl
                        UNWIND nl AS node WITH DISTINCT node
                        MATCH (node)-[r:CO_OCCURS_WITH]-()
                        WITH node, COUNT(r) AS conn
                        ORDER BY conn DESC LIMIT 40
                        RETURN node.name AS name, node.type AS type, conn
                    """, {"kw_list": kw_list})
                else:
                    res = session.run("""
                        MATCH (node:Entity)-[r:CO_OCCURS_WITH]-()
                        WITH node, COUNT(r) AS conn
                        ORDER BY conn DESC LIMIT 40
                        RETURN node.name AS name, node.type AS type, conn
                    """)
            top = {r["name"]: r for r in res}

            if week:
                rels = session.run("""
                    MATCH (e1:Entity)-[r:CO_OCCURS_WITH]-(e2:Entity)
                    WHERE e1.name IN $names AND e2.name IN $names
                    AND r.weekly_counts_json IS NOT NULL
                    RETURN e1.name AS source, e2.name AS target,
                           r.weekly_counts_json AS wcj
                """, {"names": list(top.keys())})
                relationships = []
                for r in rels:
                    try:
                        wc = json.loads(r["wcj"]) if r["wcj"] else {}
                    except:
                        wc = {}
                    w = wc.get(week, 0)
                    if w >= 1:
                        relationships.append({
                            "source": r["source"], "target": r["target"],
                            "weight": w, "rel_type": "CO_OCCURS_WITH"
                        })
            else:
                rels = session.run("""
                    MATCH (e1:Entity)-[r:CO_OCCURS_WITH]-(e2:Entity)
                    WHERE e1.name IN $names AND e2.name IN $names AND r.count >= 2
                    RETURN e1.name AS source, e2.name AS target, r.count AS weight
                """, {"names": list(top.keys())})
                relationships = [{
                    "source": r["source"], "target": r["target"],
                    "weight": r["weight"], "rel_type": "CO_OCCURS_WITH"
                } for r in rels]

    net = Network(height="480px", width="100%", bgcolor="#0A0C0F",
                  font_color="#8A9BB0", notebook=False, cdn_resources="in_line")
    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -120,
          "centralGravity": 0.03,
          "springLength": 120,
          "springConstant": 0.08,
          "damping": 0.9,
          "avoidOverlap": 0.8
        },
        "solver": "forceAtlas2Based",
        "stabilization": {"iterations": 200, "fit": true},
        "minVelocity": 0.5
      },
      "edges": {
        "smooth": {"type": "curvedCW", "roundness": 0.15},
        "color": {"opacity": 0.5},
        "arrows": {"to": {"enabled": true, "scaleFactor": 0.3}},
        "font": {"size": 0},
        "scaling": {"min": 1, "max": 4}
      },
      "nodes": {
        "borderWidth": 1,
        "borderWidthSelected": 3,
        "font": {"size": 11, "face": "IBM Plex Mono"}
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 80,
        "navigationButtons": false,
        "zoomView": true
      }
    }
    """)

    for name, data in top.items():
        is_india = (name == "India")
        is_seed  = bool(kw_list and any(kw in name.lower() for kw in kw_list))
        color    = "#E8D5A3" if is_india else TYPE_COLORS.get(data["type"], "#5A6A7A")
        border   = "#FFFFFF" if is_india else ("#E8D5A3" if is_seed else color)
        size     = 58 if is_india else (40 if is_seed else min(12 + data["conn"] * 1.8, 38))
        net.add_node(name, label=name,
            color={
                "background":  color,
                "border":      border,
                "highlight":   {"background": "#E8D5A3", "border": "#FFFFFF"}
            },
            size=size,
            title=f"{data['type']} · {data['conn']} connections",
            font={"size": 11, "color": "#C8D4E0", "face": "IBM Plex Mono"})

    for r in relationships:
        if r["source"] in top and r["target"] in top:
            rel_type   = r.get("rel_type", "CO_OCCURS_WITH")
            edge_color = RELATION_COLORS.get(rel_type, "#3A5068")
            net.add_edge(
                r["source"], r["target"],
                value=min((r["weight"] or 1) * 0.4, 4),
                title=rel_type.replace("_", " ") + "  (" + str(r["weight"]) + "x)",
                color={"color": edge_color, "highlight": "#E8D5A3"},
            )

    net.save_graph("graph_visual.html")
    with open("graph_visual.html", "r") as f:
        return f.read()
# ── [END: GRAPH VISUALIZER] ─────────────────────────────────────


# ── [SECTION: PAGE CONFIG] ──────────────────────────────────────

st.set_page_config(
    page_title="PRAJNA - Strategic Intelligence",
    page_icon="https://raw.githubusercontent.com/shikhar-iimc/prajna-intel/main/prajna_logo_main.svg",
    layout="wide",
    initial_sidebar_state="collapsed"
)
# ── [END: PAGE CONFIG] ──────────────────────────────────────────


# ── [SECTION: CSS] ──────────────────────────────────────────────
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
.source-tag { font-family: 'IBM Plex Mono', monospace; font-size: 9px; color: #3A5068; border: 1px solid #1C2A38; padding: 3px 8px; letter-spacing: 0.08em; text-transform: uppercase; }
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
</style>
""", unsafe_allow_html=True)
# ── [END: CSS] ──────────────────────────────────────────────────


# ── [SECTION: NAV BAR] ──────────────────────────────────────────
now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d  %H:%M UTC")
try:
    articles_n, entities_n, rels_n, semantic_n = get_stats()
except:
    articles_n, entities_n, rels_n, semantic_n = 0, 0, 0, 0

logo_html = f'<img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA0MDAgNDAwIiB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCI+CiAgPGRlZnM+CiAgICA8cmFkaWFsR3JhZGllbnQgaWQ9ImJnIiBjeD0iNTAlIiBjeT0iNTAlIiByPSI1MCUiPgogICAgICA8c3RvcCBvZmZzZXQ9IjAlIiBzdHlsZT0ic3RvcC1jb2xvcjojMEMwQTE0Ii8+CiAgICAgIDxzdG9wIG9mZnNldD0iMTAwJSIgc3R5bGU9InN0b3AtY29sb3I6IzA2MDQwOCIvPgogICAgPC9yYWRpYWxHcmFkaWVudD4KCiAgICA8cmFkaWFsR3JhZGllbnQgaWQ9ImNlbnRlckdsb3ciIGN4PSI1MCUiIGN5PSI1MCUiIHI9IjUwJSI+CiAgICAgIDxzdG9wIG9mZnNldD0iMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiNGRjk5MzM7c3RvcC1vcGFjaXR5OjAuMTUiLz4KICAgICAgPHN0b3Agb2Zmc2V0PSI3MCUiIHN0eWxlPSJzdG9wLWNvbG9yOiNGRjk5MzM7c3RvcC1vcGFjaXR5OjAuMDQiLz4KICAgICAgPHN0b3Agb2Zmc2V0PSIxMDAlIiBzdHlsZT0ic3RvcC1jb2xvcjojRkY5OTMzO3N0b3Atb3BhY2l0eTowIi8+CiAgICA8L3JhZGlhbEdyYWRpZW50PgoKICAgIDxsaW5lYXJHcmFkaWVudCBpZD0iZ29sZEdyYWQiIHgxPSIwJSIgeTE9IjAlIiB4Mj0iMTAwJSIgeTI9IjEwMCUiPgogICAgICA8c3RvcCBvZmZzZXQ9IjAlIiBzdHlsZT0ic3RvcC1jb2xvcjojQjg5NDNFIi8+CiAgICAgIDxzdG9wIG9mZnNldD0iNDUlIiBzdHlsZT0ic3RvcC1jb2xvcjojRThDOTZBIi8+CiAgICAgIDxzdG9wIG9mZnNldD0iMTAwJSIgc3R5bGU9InN0b3AtY29sb3I6I0I4OTQzRSIvPgogICAgPC9saW5lYXJHcmFkaWVudD4KCiAgICA8bGluZWFyR3JhZGllbnQgaWQ9InNhZmZyb24iIHgxPSIwJSIgeTE9IjAlIiB4Mj0iMTAwJSIgeTI9IjEwMCUiPgogICAgICA8c3RvcCBvZmZzZXQ9IjAlIiBzdHlsZT0ic3RvcC1jb2xvcjojRkY5OTMzIi8+CiAgICAgIDxzdG9wIG9mZnNldD0iMTAwJSIgc3R5bGU9InN0b3AtY29sb3I6I0U2NzMwMCIvPgogICAgPC9saW5lYXJHcmFkaWVudD4KCiAgICA8ZmlsdGVyIGlkPSJzb2Z0R2xvdyIgeD0iLTIwJSIgeT0iLTIwJSIgd2lkdGg9IjE0MCUiIGhlaWdodD0iMTQwJSI+CiAgICAgIDxmZUdhdXNzaWFuQmx1ciBzdGREZXZpYXRpb249IjIuNSIgcmVzdWx0PSJibHVyIi8+CiAgICAgIDxmZU1lcmdlPgogICAgICAgIDxmZU1lcmdlTm9kZSBpbj0iYmx1ciIvPgogICAgICAgIDxmZU1lcmdlTm9kZSBpbj0iU291cmNlR3JhcGhpYyIvPgogICAgICA8L2ZlTWVyZ2U+CiAgICA8L2ZpbHRlcj4KCiAgICA8ZmlsdGVyIGlkPSJzdWJ0bGVHbG93IiB4PSItMTAlIiB5PSItMTAlIiB3aWR0aD0iMTIwJSIgaGVpZ2h0PSIxMjAlIj4KICAgICAgPGZlR2F1c3NpYW5CbHVyIHN0ZERldmlhdGlvbj0iMS41IiByZXN1bHQ9ImJsdXIiLz4KICAgICAgPGZlTWVyZ2U+CiAgICAgICAgPGZlTWVyZ2VOb2RlIGluPSJibHVyIi8+CiAgICAgICAgPGZlTWVyZ2VOb2RlIGluPSJTb3VyY2VHcmFwaGljIi8+CiAgICAgIDwvZmVNZXJnZT4KICAgIDwvZmlsdGVyPgoKICAgIDxmaWx0ZXIgaWQ9InN0cm9uZ0dsb3ciIHg9Ii0zMCUiIHk9Ii0zMCUiIHdpZHRoPSIxNjAlIiBoZWlnaHQ9IjE2MCUiPgogICAgICA8ZmVHYXVzc2lhbkJsdXIgc3RkRGV2aWF0aW9uPSI1IiByZXN1bHQ9ImJsdXIiLz4KICAgICAgPGZlTWVyZ2U+CiAgICAgICAgPGZlTWVyZ2VOb2RlIGluPSJibHVyIi8+CiAgICAgICAgPGZlTWVyZ2VOb2RlIGluPSJTb3VyY2VHcmFwaGljIi8+CiAgICAgIDwvZmVNZXJnZT4KICAgIDwvZmlsdGVyPgogIDwvZGVmcz4KCiAgPCEtLSBCYWNrZ3JvdW5kIGNpcmNsZSAtLT4KICA8Y2lyY2xlIGN4PSIyMDAiIGN5PSIyMDAiIHI9IjIwMCIgZmlsbD0idXJsKCNiZykiLz4KCiAgPCEtLSBBbWJpZW50IGNlbnRyZSBnbG93IC0tPgogIDxjaXJjbGUgY3g9IjIwMCIgY3k9IjIwMCIgcj0iMTMwIiBmaWxsPSJ1cmwoI2NlbnRlckdsb3cpIi8+CgogIDwhLS0g4pSA4pSAIE9VVEVSTU9TVCBSSU5HIOKAlCBoYWlybGluZSBwcmVjaXNpb24g4pSA4pSAIC0tPgogIDxjaXJjbGUgY3g9IjIwMCIgY3k9IjIwMCIgcj0iMTc2IiBmaWxsPSJub25lIiAKICAgICAgICAgIHN0cm9rZT0iI0M4QTk2RSIgc3Ryb2tlLXdpZHRoPSIwLjUiIG9wYWNpdHk9IjAuMjUiLz4KCiAgPCEtLSDilIDilIAgT1VURVIgUklORyDigJQgbWFpbiBib3JkZXIg4pSA4pSAIC0tPgogIDxjaXJjbGUgY3g9IjIwMCIgY3k9IjIwMCIgcj0iMTY4IiBmaWxsPSJub25lIiAKICAgICAgICAgIHN0cm9rZT0idXJsKCNnb2xkR3JhZCkiIHN0cm9rZS13aWR0aD0iMS4yIiBvcGFjaXR5PSIwLjUiCiAgICAgICAgICBmaWx0ZXI9InVybCgjc3VidGxlR2xvdykiLz4KCiAgPCEtLSDilIDilIAgQVNIT0tBIENIQUtSQSBSSU5HIOKAlCBvdXRlciDilIDilIAgLS0+CiAgPGNpcmNsZSBjeD0iMjAwIiBjeT0iMjAwIiByPSIxMDgiIGZpbGw9Im5vbmUiCiAgICAgICAgICBzdHJva2U9InVybCgjZ29sZEdyYWQpIiBzdHJva2Utd2lkdGg9IjEuOCIgb3BhY2l0eT0iMC43IgogICAgICAgICAgZmlsdGVyPSJ1cmwoI3N1YnRsZUdsb3cpIi8+CgogIDwhLS0g4pSA4pSAIEFTSE9LQSBDSEFLUkEg4oCUIDI0IHNwb2tlcyDilIDilIAgLS0+CiAgPCEtLSBFYWNoIHNwb2tlIGZyb20gcj0xMDggaW53YXJkIHRvIHI9NzIgLS0+CiAgPGcgZmlsdGVyPSJ1cmwoI3N1YnRsZUdsb3cpIj4KICAgIDwhLS0gU2FmZnJvbiBzcG9rZSBsYXllciAtLT4KICAgIDxnIHN0cm9rZT0iI0ZGOTkzMyIgc3Ryb2tlLXdpZHRoPSIxIiBvcGFjaXR5PSIwLjU1IiBzdHJva2UtbGluZWNhcD0icm91bmQiPgogICAgICA8bGluZSB4MT0iMjAwIiB5MT0iOTIiIHgyPSIyMDAiIHkyPSIxMjgiLz4KICAgICAgPGxpbmUgeDE9IjIxNS45IiB5MT0iOTIuNyIgeDI9IjIxMS45IiB5Mj0iMTI4LjQiLz4KICAgICAgPGxpbmUgeDE9IjIzMS4yIiB5MT0iOTUuMyIgeDI9IjIyMy40IiB5Mj0iMTMwLjIiLz4KICAgICAgPGxpbmUgeDE9IjI0NS41IiB5MT0iOTkuOSIgeDI9IjIzNC4xIiB5Mj0iMTMzLjIiLz4KICAgICAgPGxpbmUgeDE9IjI1OC40IiB5MT0iMTA2LjMiIHgyPSIyNDQuMCIgeTI9IjEzNy41Ii8+CiAgICAgIDxsaW5lIHgxPSIyNjkuNyIgeTE9IjExNC40IiB4Mj0iMjUyLjkiIHkyPSIxNDIuOSIvPgogICAgICA8bGluZSB4MT0iMjc5LjAiIHkxPSIxMjQuMSIgeDI9IjI2MC42IiB5Mj0iMTQ5LjQiLz4KICAgICAgPGxpbmUgeDE9IjI4Ni4xIiB5MT0iMTM1LjEiIHgyPSIyNjYuOSIgeTI9IjE1Ni44Ii8+CiAgICAgIDxsaW5lIHgxPSIyOTAuOSIgeTE9IjE0Ny4zIiB4Mj0iMjcxLjYiIHkyPSIxNjUuMCIvPgogICAgICA8bGluZSB4MT0iMjkzLjMiIHkxPSIxNjAuMyIgeDI9IjI3NC42IiB5Mj0iMTczLjciLz4KICAgICAgPGxpbmUgeDE9IjI5My4zIiB5MT0iMTczLjciIHgyPSIyNzUuOSIgeTI9IjE4Mi41Ii8+CiAgICAgIDxsaW5lIHgxPSIyOTAuOSIgeTE9IjE4Ni44IiB4Mj0iMjc1LjUiIHkyPSIxOTEuMiIvPgogICAgICA8bGluZSB4MT0iMjg2LjEiIHkxPSIxOTkuMiIgeDI9IjI3My40IiB5Mj0iMTk5LjIiLz4KICAgICAgPGxpbmUgeDE9IjI3OS4wIiB5MT0iMjEwLjYiIHgyPSIyNjkuNyIgeTI9IjIwNi45Ii8+CiAgICAgIDxsaW5lIHgxPSIyNjkuNyIgeTE9IjIyMC44IiB4Mj0iMjY0LjYiIHkyPSIyMTQuMyIvPgogICAgICA8bGluZSB4MT0iMjU4LjQiIHkxPSIyMjkuMCIgeDI9IjI1Ny42IiB5Mj0iMjIxLjEiLz4KICAgICAgPGxpbmUgeDE9IjI0NS41IiB5MT0iMjM0LjkiIHgyPSIyNDguOSIgeTI9IjIyNy4yIi8+CiAgICAgIDxsaW5lIHgxPSIyMzEuMiIgeTE9IjIzOC41IiB4Mj0iMjM4LjUiIHkyPSIyMzIuNCIvPgogICAgICA8bGluZSB4MT0iMjE1LjkiIHkxPSIyMzkuOCIgeDI9IjIyNi41IiB5Mj0iMjM1LjgiLz4KICAgICAgPGxpbmUgeDE9IjIwMCIgeTE9IjIzOC44IiB4Mj0iMjEzLjEiIHkyPSIyMzcuNSIvPgogICAgICA8bGluZSB4MT0iMTg0LjEiIHkxPSIyMzUuNSIgeDI9IjE5OC44IiB5Mj0iMjM2LjgiLz4KICAgICAgPGxpbmUgeDE9IjE2OC44IiB5MT0iMjI5LjkiIHgyPSIxODMuOCIgeTI9IjIzMy44Ii8+CiAgICAgIDxsaW5lIHgxPSIxNTQuNSIgeTE9IjIyMi4xIiB4Mj0iMTY4LjMiIHkyPSIyMjguNiIvPgogICAgICA8bGluZSB4MT0iMTQxLjYiIHkxPSIyMTIuNSIgeDI9IjE1My44IiB5Mj0iMjIxLjYiLz4KICAgIDwvZz4KCiAgICA8IS0tIEdvbGQgc3Bva2Ugb3ZlcmxheSDigJQgYWx0ZXJuYXRlIHNwb2tlcywgdGhpbm5lciAtLT4KICAgIDxnIHN0cm9rZT0iI0M4QTk2RSIgc3Ryb2tlLXdpZHRoPSIwLjYiIG9wYWNpdHk9IjAuNCIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIj4KICAgICAgPGxpbmUgeDE9IjIwMCIgeTE9IjkyIiB4Mj0iMjAwIiB5Mj0iMTI4Ii8+CiAgICAgIDxsaW5lIHgxPSIyMzEuMiIgeTE9Ijk1LjMiIHgyPSIyMjMuNCIgeTI9IjEzMC4yIi8+CiAgICAgIDxsaW5lIHgxPSIyNTguNCIgeTE9IjEwNi4zIiB4Mj0iMjQ0LjAiIHkyPSIxMzcuNSIvPgogICAgICA8bGluZSB4MT0iMjc5LjAiIHkxPSIxMjQuMSIgeDI9IjI2MC42IiB5Mj0iMTQ5LjQiLz4KICAgICAgPGxpbmUgeDE9IjI5MC45IiB5MT0iMTQ3LjMiIHgyPSIyNzEuNiIgeTI9IjE2NS4wIi8+CiAgICAgIDxsaW5lIHgxPSIyOTMuMyIgeTE9IjE3My43IiB4Mj0iMjc1LjkiIHkyPSIxODIuNSIvPgogICAgICA8bGluZSB4MT0iMjg2LjEiIHkxPSIxOTkuMiIgeDI9IjI3My40IiB5Mj0iMTk5LjIiLz4KICAgICAgPGxpbmUgeDE9IjI2OS43IiB5MT0iMjIwLjgiIHgyPSIyNjQuNiIgeTI9IjIxNC4zIi8+CiAgICAgIDxsaW5lIHgxPSIyNDUuNSIgeTE9IjIzNC45IiB4Mj0iMjQ4LjkiIHkyPSIyMjcuMiIvPgogICAgICA8bGluZSB4MT0iMjE1LjkiIHkxPSIyMzkuOCIgeDI9IjIyNi41IiB5Mj0iMjM1LjgiLz4KICAgICAgPGxpbmUgeDE9IjE4NC4xIiB5MT0iMjM1LjUiIHgyPSIxOTguOCIgeTI9IjIzNi44Ii8+CiAgICAgIDxsaW5lIHgxPSIxNTQuNSIgeTE9IjIyMi4xIiB4Mj0iMTY4LjMiIHkyPSIyMjguNiIvPgogICAgPC9nPgogIDwvZz4KCiAgPCEtLSDilIDilIAgQ0hBS1JBIElOTkVSIFJJTkcg4pSA4pSAIC0tPgogIDxjaXJjbGUgY3g9IjIwMCIgY3k9IjIwMCIgcj0iNzIiIGZpbGw9Im5vbmUiCiAgICAgICAgICBzdHJva2U9InVybCgjZ29sZEdyYWQpIiBzdHJva2Utd2lkdGg9IjEuNSIgb3BhY2l0eT0iMC42NSIKICAgICAgICAgIGZpbHRlcj0idXJsKCNzdWJ0bGVHbG93KSIvPgoKICA8IS0tIOKUgOKUgCBJTk5FUiBSSU5HIOKUgOKUgCAtLT4KICA8Y2lyY2xlIGN4PSIyMDAiIGN5PSIyMDAiIHI9IjQ4IiBmaWxsPSJub25lIgogICAgICAgICAgc3Ryb2tlPSIjQzhBOTZFIiBzdHJva2Utd2lkdGg9IjAuOCIgb3BhY2l0eT0iMC4zIi8+CgogIDwhLS0g4pSA4pSAIFRSSUNPTE9VUiBBUkNTIOKAlCB1bHRyYSBzdWJ0bGUg4pSA4pSAIC0tPgogIDwhLS0gU2FmZnJvbiDigJQgdG9wIHF1YXJ0ZXIgYXJjIC0tPgogIDxwYXRoIGQ9Ik0gMTQ4IDE1MiBBIDczIDczIDAgMCAxIDI1MiAxNTIiCiAgICAgICAgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjRkY5OTMzIiBzdHJva2Utd2lkdGg9IjIuNSIgCiAgICAgICAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBvcGFjaXR5PSIwLjUiCiAgICAgICAgZmlsdGVyPSJ1cmwoI3N1YnRsZUdsb3cpIi8+CiAgPCEtLSBHcmVlbiDigJQgYm90dG9tIHF1YXJ0ZXIgYXJjIC0tPgogIDxwYXRoIGQ9Ik0gMTQ4IDI0OCBBIDczIDczIDAgMCAwIDI1MiAyNDgiCiAgICAgICAgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjMTM4ODA4IiBzdHJva2Utd2lkdGg9IjIuNSIKICAgICAgICBzdHJva2UtbGluZWNhcD0icm91bmQiIG9wYWNpdHk9IjAuNSIKICAgICAgICBmaWx0ZXI9InVybCgjc3VidGxlR2xvdykiLz4KICA8IS0tIE5hdnkg4oCUIHJpZ2h0IGFyYyAtLT4KICA8cGF0aCBkPSJNIDI3MyAyMDAgQSA3MyA3MyAwIDAgMSAyNTIgMjQ4IgogICAgICAgIGZpbGw9Im5vbmUiIHN0cm9rZT0iIzAwMDA2NiIgc3Ryb2tlLXdpZHRoPSIyIgogICAgICAgIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgb3BhY2l0eT0iMC42Ii8+CgogIDwhLS0g4pSA4pSAIE5FVVJBTCBDT05TVEVMTEFUSU9OIOKUgOKUgCAtLT4KICA8IS0tIE91dGVyIGNvbnN0ZWxsYXRpb24gcG9pbnRzIOKAlCA4IGNhcmRpbmFsL2ludGVyY2FyZGluYWwgcG9zaXRpb25zIC0tPgogIDxnIGZpbHRlcj0idXJsKCNzdWJ0bGVHbG93KSI+CiAgICA8IS0tIDggb3V0ZXIgbm9kZXMgYXQgcj01NSAtLT4KICAgIDxjaXJjbGUgY3g9IjIwMCIgY3k9IjE0NSIgcj0iMi4yIiBmaWxsPSIjRkY5OTMzIiBvcGFjaXR5PSIwLjciLz4KICAgIDxjaXJjbGUgY3g9IjIzOSIgY3k9IjE2MSIgcj0iMS44IiBmaWxsPSIjQzhBOTZFIiBvcGFjaXR5PSIwLjYiLz4KICAgIDxjaXJjbGUgY3g9IjI1NSIgY3k9IjIwMCIgcj0iMi4yIiBmaWxsPSIjRkY5OTMzIiBvcGFjaXR5PSIwLjciLz4KICAgIDxjaXJjbGUgY3g9IjIzOSIgY3k9IjIzOSIgcj0iMS44IiBmaWxsPSIjQzhBOTZFIiBvcGFjaXR5PSIwLjYiLz4KICAgIDxjaXJjbGUgY3g9IjIwMCIgY3k9IjI1NSIgcj0iMi4yIiBmaWxsPSIjRkY5OTMzIiBvcGFjaXR5PSIwLjciLz4KICAgIDxjaXJjbGUgY3g9IjE2MSIgY3k9IjIzOSIgcj0iMS44IiBmaWxsPSIjQzhBOTZFIiBvcGFjaXR5PSIwLjYiLz4KICAgIDxjaXJjbGUgY3g9IjE0NSIgY3k9IjIwMCIgcj0iMi4yIiBmaWxsPSIjRkY5OTMzIiBvcGFjaXR5PSIwLjciLz4KICAgIDxjaXJjbGUgY3g9IjE2MSIgY3k9IjE2MSIgcj0iMS44IiBmaWxsPSIjQzhBOTZFIiBvcGFjaXR5PSIwLjYiLz4KICA8L2c+CgogIDwhLS0gQ29ubmVjdGlvbiBsaW5lcyDigJQgbmV1cmFsIHdlYiAtLT4KICA8ZyBzdHJva2U9IiNGRjk5MzMiIHN0cm9rZS13aWR0aD0iMC41IiBvcGFjaXR5PSIwLjIiPgogICAgPGxpbmUgeDE9IjIwMCIgeTE9IjE0NSIgeDI9IjIzOSIgeTI9IjE2MSIvPgogICAgPGxpbmUgeDE9IjIzOSIgeTE9IjE2MSIgeDI9IjI1NSIgeTI9IjIwMCIvPgogICAgPGxpbmUgeDE9IjI1NSIgeTE9IjIwMCIgeDI9IjIzOSIgeTI9IjIzOSIvPgogICAgPGxpbmUgeDE9IjIzOSIgeTE9IjIzOSIgeDI9IjIwMCIgeTI9IjI1NSIvPgogICAgPGxpbmUgeDE9IjIwMCIgeTE9IjI1NSIgeDI9IjE2MSIgeTI9IjIzOSIvPgogICAgPGxpbmUgeDE9IjE2MSIgeTE9IjIzOSIgeDI9IjE0NSIgeTI9IjIwMCIvPgogICAgPGxpbmUgeDE9IjE0NSIgeTE9IjIwMCIgeDI9IjE2MSIgeTI9IjE2MSIvPgogICAgPGxpbmUgeDE9IjE2MSIgeTE9IjE2MSIgeDI9IjIwMCIgeTI9IjE0NSIvPgogICAgPCEtLSBDcm9zcyBjb25uZWN0aW9ucyAtLT4KICAgIDxsaW5lIHgxPSIyMDAiIHkxPSIxNDUiIHgyPSIyNTUiIHkyPSIyMDAiLz4KICAgIDxsaW5lIHgxPSIyNTUiIHkxPSIyMDAiIHgyPSIyMDAiIHkyPSIyNTUiLz4KICAgIDxsaW5lIHgxPSIyMDAiIHkxPSIyNTUiIHgyPSIxNDUiIHkyPSIyMDAiLz4KICAgIDxsaW5lIHgxPSIxNDUiIHkxPSIyMDAiIHgyPSIyMDAiIHkyPSIxNDUiLz4KICAgIDxsaW5lIHgxPSIyMzkiIHkxPSIxNjEiIHgyPSIyMzkiIHkyPSIyMzkiLz4KICAgIDxsaW5lIHgxPSIxNjEiIHkxPSIxNjEiIHgyPSIxNjEiIHkyPSIyMzkiLz4KICAgIDwhLS0gVG8gY2VudHJlIC0tPgogICAgPGxpbmUgeDE9IjIwMCIgeTE9IjE0NSIgeDI9IjIwMCIgeTI9IjIwMCIvPgogICAgPGxpbmUgeDE9IjI1NSIgeTE9IjIwMCIgeDI9IjIwMCIgeTI9IjIwMCIvPgogICAgPGxpbmUgeDE9IjIwMCIgeTE9IjI1NSIgeDI9IjIwMCIgeTI9IjIwMCIvPgogICAgPGxpbmUgeDE9IjE0NSIgeTE9IjIwMCIgeDI9IjIwMCIgeTI9IjIwMCIvPgogIDwvZz4KCiAgPCEtLSDilIDilIAgQ0VOVFJFIOKAlCB0aGUgZXllIG9mIHdpc2RvbSDilIDilIAgLS0+CiAgPCEtLSBPdXRlciBwdWxzZSByaW5nIC0tPgogIDxjaXJjbGUgY3g9IjIwMCIgY3k9IjIwMCIgcj0iMTgiIGZpbGw9Im5vbmUiCiAgICAgICAgICBzdHJva2U9IiNGRjk5MzMiIHN0cm9rZS13aWR0aD0iMC44IiBvcGFjaXR5PSIwLjIiLz4KICA8Y2lyY2xlIGN4PSIyMDAiIGN5PSIyMDAiIHI9IjEzIiBmaWxsPSJub25lIgogICAgICAgICAgc3Ryb2tlPSIjRkY5OTMzIiBzdHJva2Utd2lkdGg9IjAuNiIgb3BhY2l0eT0iMC4zIi8+CgogIDwhLS0gQ2VudHJlIG9yYiAtLT4KICA8Y2lyY2xlIGN4PSIyMDAiIGN5PSIyMDAiIHI9IjkiIAogICAgICAgICAgZmlsbD0iI0ZGOTkzMyIgb3BhY2l0eT0iMC4xMiIKICAgICAgICAgIGZpbHRlcj0idXJsKCNzdHJvbmdHbG93KSIvPgogIDxjaXJjbGUgY3g9IjIwMCIgY3k9IjIwMCIgcj0iNi41IiAKICAgICAgICAgIGZpbGw9IiMwQzBBMTQiIHN0cm9rZT0iI0ZGOTkzMyIgCiAgICAgICAgICBzdHJva2Utd2lkdGg9IjEuMiIgb3BhY2l0eT0iMC45IgogICAgICAgICAgZmlsdGVyPSJ1cmwoI3NvZnRHbG93KSIvPgogIDxjaXJjbGUgY3g9IjIwMCIgY3k9IjIwMCIgcj0iMy41IiAKICAgICAgICAgIGZpbGw9IiNGRjk5MzMiIG9wYWNpdHk9IjAuODUiCiAgICAgICAgICBmaWx0ZXI9InVybCgjc29mdEdsb3cpIi8+CiAgPCEtLSBJbm5lciBoaWdobGlnaHQgLS0+CiAgPGNpcmNsZSBjeD0iMTk4LjUiIGN5PSIxOTguNSIgcj0iMS4yIiBmaWxsPSIjRkZFMDY2IiBvcGFjaXR5PSIwLjgiLz4KCiAgPCEtLSDilIDilIAgRk9VUiBDQVJESU5BTCBESUFNT05EIE1BUktTIOKUgOKUgCAtLT4KICA8ZyBmaWxsPSIjQzhBOTZFIiBvcGFjaXR5PSIwLjQ1IiBmaWx0ZXI9InVybCgjc3VidGxlR2xvdykiPgogICAgPCEtLSBUb3AgLS0+CiAgICA8cG9seWdvbiBwb2ludHM9IjIwMCw3NyAyMDMsODMgMjAwLDg5IDE5Nyw4MyIvPgogICAgPCEtLSBSaWdodCAtLT4KICAgIDxwb2x5Z29uIHBvaW50cz0iMzIzLDIwMCAzMTcsMjAzIDMxMSwyMDAgMzE3LDE5NyIvPgogICAgPCEtLSBCb3R0b20gLS0+CiAgICA8cG9seWdvbiBwb2ludHM9IjIwMCwzMjMgMjAzLDMxNyAyMDAsMzExIDE5NywzMTciLz4KICAgIDwhLS0gTGVmdCAtLT4KICAgIDxwb2x5Z29uIHBvaW50cz0iNzcsMjAwIDgzLDIwMyA4OSwyMDAgODMsMTk3Ii8+CiAgPC9nPgoKICA8IS0tIOKUgOKUgCBDT1JORVIgUkVUSUNMRSBNQVJLUyDilIDilIAgLS0+CiAgPGcgc3Ryb2tlPSIjQzhBOTZFIiBzdHJva2Utd2lkdGg9IjAuOCIgb3BhY2l0eT0iMC4zIiBzdHJva2UtbGluZWNhcD0icm91bmQiPgogICAgPGxpbmUgeDE9IjQ4IiB5MT0iNjgiIHgyPSI2NCIgeTI9IjY4Ii8+CiAgICA8bGluZSB4MT0iNDgiIHkxPSI2OCIgeDI9IjQ4IiB5Mj0iODQiLz4KICAgIDxsaW5lIHgxPSIzNTIiIHkxPSI2OCIgeDI9IjMzNiIgeTI9IjY4Ii8+CiAgICA8bGluZSB4MT0iMzUyIiB5MT0iNjgiIHgyPSIzNTIiIHkyPSI4NCIvPgogICAgPGxpbmUgeDE9IjQ4IiB5MT0iMzMyIiB4Mj0iNjQiIHkyPSIzMzIiLz4KICAgIDxsaW5lIHgxPSI0OCIgeTE9IjMzMiIgeDI9IjQ4IiB5Mj0iMzE2Ii8+CiAgICA8bGluZSB4MT0iMzUyIiB5MT0iMzMyIiB4Mj0iMzM2IiB5Mj0iMzMyIi8+CiAgICA8bGluZSB4MT0iMzUyIiB5MT0iMzMyIiB4Mj0iMzUyIiB5Mj0iMzE2Ii8+CiAgPC9nPgoKICA8IS0tIOKUgOKUgCBERUdSRUUgTUFSS1Mgb24gb3V0ZXIgcmluZyDigJQgbGlrZSBhIGNvbXBhc3Mg4pSA4pSAIC0tPgogIDxnIHN0cm9rZT0iI0M4QTk2RSIgc3Ryb2tlLXdpZHRoPSIwLjciIG9wYWNpdHk9IjAuMjUiPgogICAgPCEtLSAxMiB0aWNrIG1hcmtzIGV2ZXJ5IDMwIGRlZ3JlZXMgLS0+CiAgICA8bGluZSB4MT0iMjAwIiB5MT0iMjQiIHgyPSIyMDAiIHkyPSIzNCIvPgogICAgPGxpbmUgeDE9IjI4OCIgeTE9IjUwIiB4Mj0iMjgzIiB5Mj0iNTkiLz4KICAgIDxsaW5lIHgxPSIzNTAiIHkxPSIxMTIiIHgyPSIzNDEiIHkyPSIxMTciLz4KICAgIDxsaW5lIHgxPSIzNzYiIHkxPSIyMDAiIHgyPSIzNjYiIHkyPSIyMDAiLz4KICAgIDxsaW5lIHgxPSIzNTAiIHkxPSIyODgiIHgyPSIzNDEiIHkyPSIyODMiLz4KICAgIDxsaW5lIHgxPSIyODgiIHkxPSIzNTAiIHgyPSIyODMiIHkyPSIzNDEiLz4KICAgIDxsaW5lIHgxPSIyMDAiIHkxPSIzNzYiIHgyPSIyMDAiIHkyPSIzNjYiLz4KICAgIDxsaW5lIHgxPSIxMTIiIHkxPSIzNTAiIHgyPSIxMTciIHkyPSIzNDEiLz4KICAgIDxsaW5lIHgxPSI1MCIgeTE9IjI4OCIgeDI9IjU5IiB5Mj0iMjgzIi8+CiAgICA8bGluZSB4MT0iMjQiIHkxPSIyMDAiIHgyPSIzNCIgeTI9IjIwMCIvPgogICAgPGxpbmUgeDE9IjUwIiB5MT0iMTEyIiB4Mj0iNTkiIHkyPSIxMTciLz4KICAgIDxsaW5lIHgxPSIxMTIiIHkxPSI1MCIgeDI9IjExNyIgeTI9IjU5Ii8+CiAgPC9nPgoKPC9zdmc+Cg==" width="52" height="52" style="opacity:0.95"/>' if LOGO_B64 else ""

st.markdown(f"""
<div class="prajna-nav">
    <div style="display:flex;align-items:center;gap:16px">
        {logo_html}
        <div>
            <div class="prajna-logo">PRAJNA<span>*</span>Intelligence Suite</div>
            <div class="prajna-meta" style="margin-top:4px">India Innovates 2026 &nbsp;·&nbsp; Domain 02: Digital Democracy &nbsp;·&nbsp; TeamIIMC</div>
        </div>
    </div>
    <div style="text-align:right">
        <div class="prajna-status"><div class="status-dot"></div>GRAPH ACTIVE</div>
        <div class="prajna-meta" style="margin-top:4px">{now_str}</div>
    </div>
</div>
""", unsafe_allow_html=True)
# ── [END: NAV BAR] ──────────────────────────────────────────────


# ── [SECTION: MODULE SELECTOR] ──────────────────────────────────
module = st.radio(
    "",
    ["PRAJNA — Strategic Intelligence", "RAKSHA — Cyber Intelligence", "ARTHA — Financial Intelligence"],
    horizontal=True,
    key="module_selector"
)
st.markdown("<hr style='border:1px solid #1C2A38;margin:0 0 24px 0'>", unsafe_allow_html=True)
# ── [END: MODULE SELECTOR] ──────────────────────────────────────


# ════════════════════════════════════════════════════════════════
# PRAJNA MODULE
# ════════════════════════════════════════════════════════════════
if module == "PRAJNA — Strategic Intelligence":

    # ── [SECTION: STATS ROW] ────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("ARTICLES INGESTED",  articles_n)
    c2.metric("ENTITIES MAPPED",    entities_n)
    c3.metric("CO-OCCURRENCE RELS", rels_n)
    c4.metric("SEMANTIC RELS",      semantic_n)
    c5.metric("GRAPH STATUS",       "● LIVE")
    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)
    # ── [END: STATS ROW] ────────────────────────────────────────────

    # ── [SECTION: TABS] ─────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "INTELLIGENCE BRIEF",
        "TRAJECTORY ANALYSIS",
        "PATH QUERY",
        "SURGE DETECTION",
        "WEEKLY BRIEF"
    ])
    # ── [END: TABS] ─────────────────────────────────────────────────

    # ── [SECTION: TAB 1 — INTELLIGENCE BRIEF] ───────────────────────
    with tab1:
        st.markdown('<div class="section-label">Natural Language Intelligence Query</div>', unsafe_allow_html=True)

        query_input = st.text_input(
            "Intelligence query",
            placeholder="e.g.  India China border tensions  /  Iran nuclear deal  /  BRICS expansion",
            key="query_input"
        )

        run_query = st.button("GENERATE BRIEF", key="run_query")

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
                "Graph context (semantic relationships):\n" + "\n".join(ctx_lines) + "\n\n"
                "Recent headlines:\n" + "\n".join(art_lines) + "\n\n"
                "Generate a structured intelligence brief:\n\n"
                "SITUATION: [2-3 sentences]\n\n"
                "CONNECTIONS: [Key relationships from graph]\n\n"
                "IMPLICATIONS FOR INDIA: [Strategic significance]\n\n"
                "ACTION RECOMMENDED: [One specific action]\n\n"
                "SOURCES: " + "  ".join([f"[{s}]" for _, s in articles]) + "\n\n"
                "Be direct, analytical, India-centric. Max 300 words."
            )

            with st.spinner("Generating brief..."):
                brief = ask_groq(prompt)

            st.markdown(
                '<div class="brief-container"><div class="brief-header">INTELLIGENCE BRIEF — '
                + query_input.upper()[:60]
                + '</div>' + brief.replace("\n", "<br>") + "</div>",
                unsafe_allow_html=True
            )

        # ── [SECTION: TAB 1 — GRAPH CONTROLS] ───────────────────
        st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-label">Interactive Knowledge Graph</div>', unsafe_allow_html=True)

        col_kw, col_gmode, col_gweek = st.columns([2, 1, 2])
        with col_kw:
            graph_keyword = st.text_input(
                "Filter entities (comma-separated)",
                placeholder="e.g. India, China, Iran",
                key="graph_keyword"
            )
        with col_gmode:
            selected_graph_mode = st.selectbox("GRAPH MODE", ["semantic", "co-occurrence"], key="graph_mode_select")
        with col_gweek:
            available_weeks_graph = get_available_weeks()
            week_options_graph    = ["ALL WEEKS"] + available_weeks_graph
            selected_graph_week   = st.selectbox("WEEK FILTER (co-occurrence)", week_options_graph, key="graph_week_select")

        col_gen, _ = st.columns([1, 3])
        with col_gen:
            gen_graph = st.button("GENERATE GRAPH", key="gen_graph")

        if gen_graph:
            week_param = None
            if selected_graph_mode == "co-occurrence" and selected_graph_week != "ALL WEEKS":
                week_param = selected_graph_week.split("  ")[0]

            with st.spinner("Building graph..."):
                graph_html = build_graph_visual(
                    keyword=graph_keyword or None,
                    week=week_param,
                    mode=selected_graph_mode
                )
            components.html(graph_html, height=500, scrolling=False)

            legend_items = [
                ("#C8A96E", "GPE / Country"),
                ("#6B8CAE", "Organisation"),
                ("#A8C5A0", "Person"),
                ("#B8956A", "NORP / Group"),
                ("#8AABBA", "Location"),
                ("#C47B6E", "Event"),
            ]
            legend_html = '<div style="display:flex;gap:16px;flex-wrap:wrap;margin-top:8px">'
            for color, label in legend_items:
                legend_html += (
                    f'<div style="display:flex;align-items:center;gap:6px">'
                    f'<div style="width:10px;height:10px;border-radius:50%;background:{color}"></div>'
                    f'<span style="font-family:IBM Plex Mono;font-size:9px;color:#3A5068;'
                    f'text-transform:uppercase;letter-spacing:0.1em">{label}</span></div>'
                )
            legend_html += "</div>"
            st.markdown(legend_html, unsafe_allow_html=True)
    # ── [END: TAB 1] ────────────────────────────────────────────────


    # ── [SECTION: TAB 2 — TRAJECTORY ANALYSIS] ──────────────────────
    with tab2:
        st.markdown('<div class="section-label">Week-on-Week Relationship Intensity</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-family:IBM Plex Mono;font-size:10px;color:#3A5068;margin-bottom:20px">Track how co-occurrence between any two entities has changed over time — intensifying, cooling, or volatile.</div>', unsafe_allow_html=True)

        col_e1, col_e2 = st.columns(2)
        with col_e1:
            traj_e1 = st.text_input("Entity A", placeholder="India", key="traj_e1")
        with col_e2:
            traj_e2 = st.text_input("Entity B", placeholder="China", key="traj_e2")

        run_traj = st.button("ANALYSE TRAJECTORY", key="run_traj")

        if run_traj:
            if not traj_e1 or not traj_e2:
                st.warning("Enter both entities.")
            else:
                trajectory, total = get_trajectory(traj_e1.strip(), traj_e2.strip())
                if not trajectory:
                    st.info(f"No co-occurrence data found for {traj_e1} ↔ {traj_e2}.")
                else:
                    weeks  = [w for w, _ in trajectory]
                    counts = [c for _, c in trajectory]
                    df_traj = pd.DataFrame({"week": weeks, "co-occurrences": counts})

                    st.markdown(
                        f'<div style="font-family:IBM Plex Mono;font-size:10px;color:#4A6A8A;'
                        f'margin-bottom:12px">{traj_e1.upper()} ↔ {traj_e2.upper()} &nbsp;·&nbsp; '
                        f'{total} total co-mentions across {len(weeks)} weeks</div>',
                        unsafe_allow_html=True
                    )
                    st.bar_chart(df_traj.set_index("week"))

                    with st.spinner("Analysing pattern..."):
                        traj_str = "  ".join([f"{w}:{c}" for w, c in trajectory])
                        prompt = (
                            f"Prajna trajectory analysis.\n"
                            f"Entities: {traj_e1} and {traj_e2}\n"
                            f"Weekly co-occurrence data: {traj_str}\n\n"
                            "PATTERN: Is this relationship intensifying, cooling, or volatile?\n"
                            "EXPLANATION: What likely drove the key peaks or troughs?\n"
                            "INDIA IMPLICATION: What does this trajectory mean for India?\n"
                            "OUTLOOK: What should we watch for next week?\n\n"
                            "Max 200 words. Be direct."
                        )
                        traj_brief = ask_groq(prompt)

                    st.markdown(
                        '<div class="brief-container"><div class="brief-header">TRAJECTORY ANALYSIS — '
                        + traj_e1.upper() + " ↔ " + traj_e2.upper()
                        + '</div>' + traj_brief.replace("\n", "<br>") + "</div>",
                        unsafe_allow_html=True
                    )
    # ── [END: TAB 2] ────────────────────────────────────────────────


    # ── [SECTION: TAB 3 — PATH QUERY & SEMANTIC EXPLORER] ───────────
    with tab3:
        st.markdown('<div class="section-label">Graph Path Query & Semantic Explorer</div>', unsafe_allow_html=True)

        subtab1, subtab2 = st.tabs(["GRAPH PATH QUERY", "ENTITY SEMANTIC PROFILE"])

        # ── Subtab 1: Shortest path via CO_OCCURS_WITH ──
        with subtab1:
            st.markdown('<div style="font-family:IBM Plex Mono;font-size:10px;color:#3A5068;margin-bottom:20px">Find the shortest connection path between any two entities in the knowledge graph — up to 4 hops.</div>', unsafe_allow_html=True)

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                path_e1 = st.text_input("From entity", placeholder="India", key="path_e1")
            with col_p2:
                path_e2 = st.text_input("To entity", placeholder="Taliban", key="path_e2")

            run_path = st.button("FIND PATH", key="run_path")

            if run_path:
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

                        st.markdown(
                            f'<div style="font-family:IBM Plex Mono;font-size:10px;color:#4A6A8A;'
                            f'margin-bottom:16px">PATH FOUND — {hops} hop{"s" if hops > 1 else ""}</div>',
                            unsafe_allow_html=True
                        )

                        for i, node in enumerate(nodes):
                            css_class = "start" if i == 0 else ("end" if i == len(nodes)-1 else "mid")
                            st.markdown(
                                f'<div class="path-node {css_class}">'
                                f'<span style="font-family:IBM Plex Mono;font-size:10px;color:#3A5068">{i+1}</span>'
                                f'<span>{node}</span></div>',
                                unsafe_allow_html=True
                            )
                            if i < len(strengths):
                                st.markdown(
                                    f'<div class="path-connector">↓ &nbsp; co-occurrence strength: {strengths[i]}</div>',
                                    unsafe_allow_html=True
                                )

                        with st.spinner("Interpreting path..."):
                            path_str = " → ".join(nodes)
                            prompt = (
                                f"Prajna path analysis.\n"
                                f"Connection: {path_str}\n"
                                f"This is the shortest path in the knowledge graph between {path_e1} and {path_e2}.\n\n"
                                "INTERPRETATION: What does this connection chain mean geopolitically?\n"
                                "KEY INTERMEDIARY: Which node in the middle is most strategically significant?\n"
                                "INDIA ANGLE: How does India fit into or should respond to this connection?\n\n"
                                "Max 150 words. Be direct."
                            )
                            path_brief = ask_groq(prompt)

                        st.markdown(
                            '<div class="brief-container"><div class="brief-header">PATH INTERPRETATION</div>'
                            + path_brief.replace("\n", "<br>") + "</div>",
                            unsafe_allow_html=True
                        )

        # ── Subtab 2: Entity semantic profile ──
        with subtab2:
            st.markdown('<div style="font-family:IBM Plex Mono;font-size:10px;color:#3A5068;margin-bottom:20px">Full semantic profile of any entity — all typed relationships from the knowledge graph.</div>', unsafe_allow_html=True)

            profile_entity = st.text_input("Entity name", placeholder="Iran", key="profile_entity")
            run_profile    = st.button("BUILD PROFILE", key="run_profile")

            if run_profile and profile_entity:
                with st.spinner("Building semantic profile..."):
                    outgoing, incoming = get_semantic_relations(profile_entity.strip())

                if not outgoing and not incoming:
                    st.info(f"No semantic relationships found for '{profile_entity}'.")
                else:
                    col_out, col_in = st.columns(2)

                    with col_out:
                        st.markdown(
                            f'<div style="font-family:IBM Plex Mono;font-size:9px;color:#C8A96E;'
                            f'letter-spacing:0.15em;margin-bottom:8px">{profile_entity.upper()} ACTS ON →</div>',
                            unsafe_allow_html=True
                        )
                        rows_html = ""
                        for r in outgoing:
                            rows_html += (
                                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                                f'padding:7px 12px;border-bottom:1px solid #1C2A38;font-family:IBM Plex Mono;font-size:11px">'
                                f'<span style="color:#C8D4E0">{r["target"]}</span>'
                                f'<span style="color:{RELATION_COLORS.get(r["rel"],"#4A6A8A")};font-size:9px;'
                                f'letter-spacing:0.1em">{r["rel"].replace("_"," ")}</span>'
                                f'<span style="color:#3A5068;font-size:9px">{r["cnt"]}x</span></div>'
                            )
                        st.markdown('<div style="border:1px solid #1C2A38;background:#0D1117">' + rows_html + '</div>', unsafe_allow_html=True)

                    with col_in:
                        st.markdown(
                            f'<div style="font-family:IBM Plex Mono;font-size:9px;color:#6B8CAE;'
                            f'letter-spacing:0.15em;margin-bottom:8px">→ OTHERS ACT ON {profile_entity.upper()}</div>',
                            unsafe_allow_html=True
                        )
                        rows_html = ""
                        for r in incoming:
                            rows_html += (
                                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                                f'padding:7px 12px;border-bottom:1px solid #1C2A38;font-family:IBM Plex Mono;font-size:11px">'
                                f'<span style="color:#C8D4E0">{r["source"]}</span>'
                                f'<span style="color:{RELATION_COLORS.get(r["rel"],"#4A6A8A")};font-size:9px;'
                                f'letter-spacing:0.1em">{r["rel"].replace("_"," ")}</span>'
                                f'<span style="color:#3A5068;font-size:9px">{r["cnt"]}x</span></div>'
                            )
                        st.markdown('<div style="border:1px solid #1C2A38;background:#0D1117">' + rows_html + '</div>', unsafe_allow_html=True)

                    with st.spinner("Generating entity profile brief..."):
                        out_str = ", ".join([f"{r['target']} ({r['rel']})" for r in outgoing[:6]])
                        in_str  = ", ".join([f"{r['source']} ({r['rel']})" for r in incoming[:6]])
                        prompt = (
                            f"Prajna entity profile.\n"
                            f"Entity: {profile_entity}\n\n"
                            f"Acts on: {out_str}\n"
                            f"Others act on it: {in_str}\n\n"
                            "PROFILE SUMMARY: Who/what is this entity in the current global context?\n"
                            "KEY RELATIONSHIPS: Most strategically significant connections\n"
                            "INDIA RELEVANCE: How does this entity affect India's strategic interests?\n\n"
                            "Max 200 words."
                        )
                        profile_brief = ask_groq(prompt)

                    st.markdown(
                        '<div class="brief-container"><div class="brief-header">ENTITY PROFILE — '
                        + profile_entity.upper()
                        + '</div>' + profile_brief.replace("\n", "<br>") + "</div>",
                        unsafe_allow_html=True
                    )
    # ── [END: TAB 3] ────────────────────────────────────────────────


    # ── [SECTION: TAB 4 — SURGE DETECTION] ──────────────────────────
    with tab4:
        st.markdown('<div class="section-label">Entity Surge Detection</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-family:IBM Plex Mono;font-size:10px;color:#3A5068;margin-bottom:20px">Automatically detects entities whose mention frequency has exceeded their historical baseline — early warning for emerging developments.</div>', unsafe_allow_html=True)

        col_thresh, col_topn, col_run4 = st.columns([2, 2, 1])
        with col_thresh:
            threshold = st.slider("SURGE THRESHOLD (x baseline)", 1.2, 5.0, 1.5, 0.1, key="surge_threshold")
        with col_topn:
            top_n = st.slider("MAX RESULTS", 1, 10, 5, 1, key="surge_topn")
        with col_run4:
            st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
            run_surge = st.button("DETECT SURGES", key="run_surge")

        if run_surge:
            with st.spinner("Scanning graph for surges..."):
                surges = detect_surges(threshold=threshold, top_n=top_n)

            if not surges:
                top = []
                with driver.session() as session:
                    result = session.run("""
                        MATCH (e:Entity)
                        WHERE e.type IN ["GPE","ORG","PERSON","NORP"]
                        WITH e, COUNT{(e)--()} as conn
                        ORDER BY conn DESC LIMIT 10
                        RETURN e.name as name, e.type as type, conn
                    """).data()
                    top = result

                st.markdown(
                    '<div style="font-family:IBM Plex Mono;font-size:10px;color:#4A6A8A;'
                    'border:1px solid #1C2A38;padding:10px 16px;background:#0D1117;margin-bottom:16px">'
                    'No surges detected above threshold this week. Top entities by connectivity:</div>',
                    unsafe_allow_html=True
                )
                rows_html = ""
                for r in top:
                    if len(r["name"]) < 35:
                        rows_html += (
                            f'<div style="display:flex;justify-content:space-between;padding:7px 12px;'
                            f'border-bottom:1px solid #1C2A38;font-family:IBM Plex Mono;font-size:11px">'
                            f'<span style="color:#C8D4E0">{r["name"]}</span>'
                            f'<span style="color:#3A5068">{r["type"]}</span>'
                            f'<span style="color:#3A5068">{r["conn"]} connections</span></div>'
                        )
                st.markdown('<div style="border:1px solid #1C2A38;background:#0D1117">' + rows_html + '</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="font-family:IBM Plex Mono;font-size:10px;color:#C87B6A;border:1px solid #2A1A1A;padding:10px 16px;background:#0D0A0A;margin-bottom:16px">' + str(len(surges)) + ' ENTITIES FLAGGED ABOVE ' + str(threshold) + 'x BASELINE</div>', unsafe_allow_html=True)
                for surge in surges:
                    st.markdown('<div class="surge-card"><div class="surge-entity">' + surge["entity"] + '</div><div class="surge-ratio">' + str(surge["ratio"]) + 'x baseline &nbsp;·&nbsp; ' + str(surge["latest"]) + ' this week &nbsp;·&nbsp; baseline: ' + str(surge["baseline"]) + '/week</div></div>', unsafe_allow_html=True)
                    prompt = (
                        "Prajna surge alert:\n"
                        "Entity: " + surge["entity"] + " (" + surge["type"] + ")\n"
                        "This week: " + str(surge["latest"]) + " co-occurrences\n"
                        "Baseline: " + str(surge["baseline"]) + " per week\n"
                        "Surge ratio: " + str(surge["ratio"]) + "x\n\n"
                        "SURGE EXPLANATION — why is this entity surging?\n"
                        "INDIA RISK/OPPORTUNITY — strategic implications for India?\n"
                        "URGENCY — Immediate / Days / Weeks\n"
                        "RECOMMENDED ACTION — one specific action\n\n"
                        "Max 130 words. Be direct."
                    )
                    with st.spinner(""):
                        brief = ask_groq(prompt)
                    st.markdown('<div class="brief-container" style="border-left-color:#8A4A3A;margin-bottom:20px"><div class="brief-header" style="color:#C87B6A">SURGE BRIEF — ' + surge["entity"].upper() + '</div>' + brief.replace("\n", "<br>") + '</div>', unsafe_allow_html=True)
    # ── [END: TAB 4] ────────────────────────────────────────────────


    # ── [SECTION: TAB 5 — WEEKLY BRIEF] ─────────────────────────────
    with tab5:
        st.markdown('<div class="section-label">Automated Weekly Intelligence Brief</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-family:IBM Plex Mono;font-size:10px;color:#3A5068;margin-bottom:20px">Prajna automatically identifies the 5 most strategically significant developments India should monitor — zero user input required.</div>', unsafe_allow_html=True)

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
                        headlines[p["e1"] + " and " + p["e2"]] = arts

                    sem_context = session.run(
                        "MATCH (e1:Entity)-[r:RELATES_TO]->(e2:Entity) "
                        "WHERE e1.name IN $names AND e2.name IN $names "
                        "RETURN e1.name AS e1, r.type AS rel, e2.name AS e2, r.count AS cnt "
                        "ORDER BY cnt DESC LIMIT 20",
                        {"names": names}
                    ).data()

                pairs_lines = ["Most active relationships this week:"]
                for p in top_pairs:
                    pairs_lines.append("  " + p["e1"] + " and " + p["e2"] + ": " + str(p["co_count"]) + " co-mentions")
                hl_lines = ["Supporting headlines:"]
                for key, arts in headlines.items():
                    hl_lines.append(key + ":")
                    for a in arts:
                        hl_lines.append("  [" + a["source"] + "] " + a["title"])
                sem_lines = ["Semantic relationships:"]
                for r in sem_context:
                    sem_lines.append("  " + r["e1"] + " -[" + r["rel"] + "]-> " + r["e2"] + " (" + str(r["cnt"]) + "x)")

                prompt = (
                    "You are Prajna, India's strategic intelligence engine.\n"
                    "Week: " + brief_week + "\n\n"
                    + "\n".join(pairs_lines) + "\n\n"
                    + "\n".join(hl_lines) + "\n\n"
                    + "\n".join(sem_lines) + "\n\n"
                    "Generate a WEEKLY INTELLIGENCE BRIEF for Indian policymakers.\n\n"
                    "WEEK " + brief_week + " - STRATEGIC INTELLIGENCE BRIEF\n\n"
                    "STORY 1: [headline]\n[2-3 sentences on why this matters for India]\n\n"
                    "STORY 2: [headline]\n[2-3 sentences]\n\n"
                    "STORY 3: [headline]\n[2-3 sentences]\n\n"
                    "STORY 4: [headline]\n[2-3 sentences]\n\n"
                    "STORY 5: [headline]\n[2-3 sentences]\n\n"
                    "BOTTOM LINE FOR INDIA: One sentence strategic summary.\n\n"
                    "Be direct, analytical, India-centric. Max 400 words."
                )
                brief_text = ask_groq(prompt, max_tokens=800)

            all_sources = []
            for arts in headlines.values():
                for a in arts:
                    if a["source"] not in all_sources:
                        all_sources.append(a["source"])
            src_str = "  ".join(["[" + s + "]" for s in all_sources[:8]])
            header  = "WEEKLY BRIEF - " + brief_week + " - " + str(len(top_pairs)) + " signal pairs - " + str(len(names)) + " entities"
            st.markdown(
                '<div class="brief-container"><div class="brief-header">' + header + '</div>'
                + brief_text.replace("\n", "<br>")
                + '<div style="margin-top:12px;padding-top:12px;border-top:1px solid #1C2A38;font-family:IBM Plex Mono;font-size:9px;color:#3A5068">' + src_str + '</div></div>',
                unsafe_allow_html=True
            )

            with st.spinner("Generating PDF..."):
                detailed_prompt = (
                    "You are Prajna, India's strategic intelligence engine.\n"
                    "Week: " + brief_week + "\n\n"
                    + "\n".join(pairs_lines) + "\n\n"
                    + "\n".join(hl_lines) + "\n\n"
                    + "\n".join(sem_lines) + "\n\n"
                    "Generate a DETAILED WEEKLY INTELLIGENCE BRIEF for Indian policymakers.\n\n"
                    "WEEK " + brief_week + " - STRATEGIC INTELLIGENCE BRIEF\n\n"
                    "EXECUTIVE SUMMARY\n"
                    "[3-4 sentence overview of the most critical developments]\n\n"
                    "STORY 1: [headline]\n[4-5 sentences: what happened, why it matters, India's exposure]\n\n"
                    "STORY 2: [headline]\n[4-5 sentences]\n\n"
                    "STORY 3: [headline]\n[4-5 sentences]\n\n"
                    "STORY 4: [headline]\n[4-5 sentences]\n\n"
                    "STORY 5: [headline]\n[4-5 sentences]\n\n"
                    "STRATEGIC RISK MATRIX\n"
                    "HIGH RISK: [one line]\n"
                    "MEDIUM RISK: [one line]\n"
                    "OPPORTUNITY: [one line]\n\n"
                    "BOTTOM LINE FOR INDIA: Two sentence strategic summary.\n\n"
                    "Be direct, analytical, India-centric. Max 700 words."
                )
                detailed_brief = ask_groq(detailed_prompt, max_tokens=1200)
                pdf_bytes = generate_pdf_brief(brief_week, top_pairs, headlines, detailed_brief, names)

            st.download_button(
                label="DOWNLOAD DETAILED BRIEF (PDF)",
                data=pdf_bytes,
                file_name="Prajna_Brief_" + brief_week + ".pdf",
                mime="application/pdf"
            )
    # ── [END: TAB 5] ────────────────────────────────────────────────


# ════════════════════════════════════════════════════════════════
# RAKSHA MODULE
# ════════════════════════════════════════════════════════════════
elif module == "RAKSHA — Cyber Intelligence":

    st.markdown("""
        <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                    letter-spacing:0.2em;color:#4A6A8A;margin-bottom:4px">
            PRAJNA INTELLIGENCE SUITE
        </div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:22px;
                    font-weight:700;color:#E8D5A3;letter-spacing:0.05em;margin-bottom:2px">
            RAKSHA
        </div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                    color:#4A6A8A;letter-spacing:0.15em;margin-bottom:20px">
            CYBERSECURITY INTELLIGENCE · INDIA-CENTRIC THREAT ANALYSIS
        </div>
    """, unsafe_allow_html=True)

    if not driver_2:
        st.warning("Raksha graph not connected. Add NEO4J_URI_2 / NEO4J_USERNAME_2 / NEO4J_PASSWORD_2 to Streamlit secrets.")
        st.stop()

    with driver_2.session() as s:
        n_cart  = s.run("MATCH (a:CyberArticle)  RETURN count(a) AS c").single()["c"]
        n_cent  = s.run("MATCH (e:CyberEntity)   RETURN count(e) AS c").single()["c"]
        n_crels = s.run("MATCH ()-[r:CYBER_CO_OCCURS]-() RETURN count(r) AS c").single()["c"]

    c1, c2, c3 = st.columns(3)
    for col, label, val in [
        (c1, "CYBER ARTICLES", n_cart),
        (c2, "THREAT ENTITIES", n_cent),
        (c3, "SIGNAL PAIRS",   n_crels),
    ]:
        col.markdown(
            f'<div style="background:#0D1117;border:1px solid #1C2A38;border-radius:6px;'
            f'padding:14px;text-align:center">'
            f'<div style="font-family:IBM Plex Mono;font-size:9px;color:#4A6A8A;'
            f'letter-spacing:0.15em">{label}</div>'
            f'<div style="font-family:IBM Plex Mono;font-size:22px;font-weight:700;'
            f'color:#E8D5A3">{val}</div></div>',
            unsafe_allow_html=True
        )
    st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)

    rtab1, rtab2, rtab3 = st.tabs(["THREAT BRIEF", "SECTOR EXPOSURE", "CVE TRACKER"])

    with rtab1:
        st.markdown(
            '<div style="font-family:IBM Plex Mono;font-size:10px;color:#4A6A8A;'
            'letter-spacing:0.15em;margin-bottom:16px">'
            'QUERY THE CYBER THREAT GRAPH · GROQ-POWERED ANALYSIS</div>',
            unsafe_allow_html=True
        )
        query = st.text_input(
            "Enter threat query",
            placeholder="e.g. APT attacks on Indian banking sector",
            key="raksha_query"
        )
        if st.button("GENERATE THREAT BRIEF", key="raksha_brief_btn"):
            if not query:
                st.warning("Enter a query first.")
            else:
                with st.spinner("Querying cyber graph..."):
                    with driver_2.session() as s:
                        context_rows = s.run("""
                            MATCH (e:CyberEntity)
                            WHERE toLower(e.name) CONTAINS toLower($kw)
                            WITH e LIMIT 5
                            MATCH (e)-[r:CYBER_CO_OCCURS]-(other:CyberEntity)
                            RETURN e.name AS e1, other.name AS e2,
                                   r.count AS count, other.type AS type
                            ORDER BY r.count DESC LIMIT 20
                        """, {"kw": query.split()[0]}).data()

                        headlines = s.run("""
                            MATCH (e:CyberEntity)
                            WHERE toLower(e.name) CONTAINS toLower($kw)
                            WITH e LIMIT 3
                            MATCH (a:CyberArticle)-[:CYBER_MENTIONS]->(e)
                            RETURN a.title AS title, a.source AS source
                            ORDER BY a.published DESC LIMIT 10
                        """, {"kw": query.split()[0]}).data()

                    ctx_lines = [f"- {r['e1']} <-> {r['e2']} (strength: {r['count']}, type: {r['type']})"
                                 for r in context_rows]
                    hl_lines  = [f"[{h['source']}] {h['title']}" for h in headlines]

                    prompt = (
                        f"You are Raksha, India's cybersecurity intelligence engine.\n"
                        f"Query: {query}\n\n"
                        f"CYBER GRAPH CONTEXT:\n" + "\n".join(ctx_lines) + "\n\n"
                        f"RECENT HEADLINES:\n" + "\n".join(hl_lines) + "\n\n"
                        "Generate a structured CYBER THREAT BRIEF:\n\n"
                        "SITUATION: [2-3 sentences on current threat landscape]\n\n"
                        "THREAT ACTORS: [Who is behind this — APT groups, nation-state actors]\n\n"
                        "INDIA EXPOSURE: [Specific sectors, systems, organisations at risk in India]\n\n"
                        "RECOMMENDED ACTIONS: [2-3 concrete defensive steps]\n\n"
                        "SOURCES: [List the headlines used]\n\n"
                        "Be direct, technical, India-centric. Max 350 words."
                    )
                    brief = ask_groq(prompt, max_tokens=700)

                st.markdown(
                    '<div class="brief-container"><div class="brief-header">CYBER THREAT BRIEF — '
                    + query.upper()[:60] + '</div>'
                    + brief.replace("\n", "<br>") + "</div>",
                    unsafe_allow_html=True
                )

                if context_rows:
                    st.markdown(
                        '<div style="font-family:IBM Plex Mono;font-size:9px;color:#4A6A8A;'
                        'letter-spacing:0.15em;margin:20px 0 8px">CYBER ENTITY GRAPH</div>',
                        unsafe_allow_html=True
                    )
                    CYBER_COLORS = {
                        "THREAT_ACTOR": "#C47B6E", "CVE": "#E8D5A3",
                        "MALWARE": "#B8476E", "CYBER_ORG": "#6B8CAE",
                        "SECTOR": "#A8C5A0", "ORG": "#6B8CAE", "GPE": "#C8A96E",
                    }
                    net = Network(height="420px", width="100%", bgcolor="#0A0C0F",
                                  font_color="#8A9BB0", notebook=True, cdn_resources="in_line")
                    net.set_options('{"physics":{"forceAtlas2Based":{"gravitationalConstant":-50,"springLength":130},"solver":"forceAtlas2Based"},"edges":{"smooth":{"type":"continuous"},"color":{"opacity":0.4}}}')
                    nodes_seen = set()
                    for r in context_rows:
                        for name, ntype in [(r["e1"], "ORG"), (r["e2"], r["type"])]:
                            if name not in nodes_seen:
                                nodes_seen.add(name)
                                color = CYBER_COLORS.get(ntype, "#5A6A7A")
                                net.add_node(name, label=name,
                                             color={"background": color, "border": color},
                                             size=20, font={"size": 11, "color": "#C8D4E0"})
                        net.add_edge(r["e1"], r["e2"], value=min(r["count"]*0.4, 4),
                                     color={"color": "#2A3A4A", "highlight": "#C8A96E"})
                    net.save_graph("raksha_graph.html")
                    with open("raksha_graph.html", "r", encoding="utf-8") as f:
                        html = f.read()
                    components.html(html, height=430, scrolling=False)

    with rtab2:
        st.markdown(
            '<div style="font-family:IBM Plex Mono;font-size:10px;color:#4A6A8A;'
            'letter-spacing:0.15em;margin-bottom:16px">'
            'SECTOR TARGETING ANALYSIS · WHICH SECTORS ARE MOST EXPOSED THIS WEEK</div>',
            unsafe_allow_html=True
        )
        with st.spinner("Loading sector exposure data..."):
            with driver_2.session() as s:
                sector_rows = s.run("""
                    MATCH (s:CyberEntity {type:'SECTOR'})
                    WITH s, COUNT{(s)-[:CYBER_CO_OCCURS]-()} AS exposure
                    ORDER BY exposure DESC
                    RETURN s.name AS sector, exposure
                """).data()
                actor_rows = s.run("""
                    MATCH (t:CyberEntity {type:'THREAT_ACTOR'})
                    WITH t, COUNT{(t)-[:CYBER_CO_OCCURS]-()} AS activity
                    ORDER BY activity DESC LIMIT 10
                    RETURN t.name AS actor, activity
                """).data()

        if sector_rows:
            df_sectors = pd.DataFrame(sector_rows)
            st.markdown(
                '<div style="font-family:IBM Plex Mono;font-size:9px;color:#4A6A8A;'
                'letter-spacing:0.15em;margin-bottom:8px">SECTOR EXPOSURE SCORE</div>',
                unsafe_allow_html=True
            )
            st.bar_chart(df_sectors.set_index("sector")["exposure"])

            with st.spinner("Generating sector risk brief..."):
                sector_str = ", ".join([f"{r['sector']} ({r['exposure']})" for r in sector_rows[:8]])
                actor_str  = ", ".join([f"{r['actor']} ({r['activity']})" for r in actor_rows[:5]])
                prompt = (
                    f"You are Raksha, India's cybersecurity intelligence engine.\n"
                    f"Sector exposure this week: {sector_str}\n"
                    f"Most active threat actors: {actor_str}\n\n"
                    "HIGHEST RISK SECTORS: [Top 3 sectors and why]\n\n"
                    "RESPONSIBLE THREAT ACTORS: [Which actors target which sectors]\n\n"
                    "INDIA-SPECIFIC RISK: [Why these sectors matter for India's critical infrastructure]\n\n"
                    "PRIORITY ACTION: [What should CERT-In / NCIIPC prioritise this week]\n\n"
                    "Max 250 words."
                )
                brief = ask_groq(prompt, max_tokens=500)

            st.markdown(
                '<div class="brief-container"><div class="brief-header">SECTOR RISK ASSESSMENT</div>'
                + brief.replace("\n", "<br>") + "</div>",
                unsafe_allow_html=True
            )
        else:
            st.info("No sector data yet — run the ingestion notebook first.")

        if actor_rows:
            st.markdown(
                '<div style="font-family:IBM Plex Mono;font-size:9px;color:#4A6A8A;'
                'letter-spacing:0.15em;margin:20px 0 8px">ACTIVE THREAT ACTORS</div>',
                unsafe_allow_html=True
            )
            df_actors = pd.DataFrame(actor_rows)
            st.dataframe(
                df_actors.rename(columns={"actor": "Threat Actor", "activity": "Activity Score"}),
                use_container_width=True, hide_index=True
            )

    with rtab3:
        st.markdown(
            '<div style="font-family:IBM Plex Mono;font-size:10px;color:#4A6A8A;'
            'letter-spacing:0.15em;margin-bottom:16px">'
            'ACTIVE CVE TRACKER · CISA KEV · FILTERED FOR INDIA-RELEVANT VENDORS</div>',
            unsafe_allow_html=True
        )
        with driver_2.session() as s:
            cve_rows = s.run("""
                MATCH (c:CyberEntity {type:'CVE'})
                WITH c, COUNT{(c)-[:CYBER_CO_OCCURS]-()} AS signals
                ORDER BY c.last_seen DESC, signals DESC
                RETURN c.name AS cve, c.last_seen AS date, signals
                LIMIT 50
            """).data()
            enriched = []
            for row in cve_rows:
                actors = s.run("""
                    MATCH (c:CyberEntity {name: $cve, type:'CVE'})
                    MATCH (c)-[:CYBER_CO_OCCURS]-(t:CyberEntity {type:'THREAT_ACTOR'})
                    RETURN t.name AS actor LIMIT 3
                """, {"cve": row["cve"]}).data()
                enriched.append({
                    "CVE ID":          row["cve"],
                    "Date Added":      row["date"],
                    "Signal Strength": row["signals"],
                    "Linked Actors":   ", ".join([a["actor"] for a in actors]) or "—",
                })

        if enriched:
            df_cve = pd.DataFrame(enriched)
            st.dataframe(df_cve, use_container_width=True, hide_index=True)
            st.markdown(
                f'<div style="font-family:IBM Plex Mono;font-size:9px;color:#4A6A8A;margin-top:8px">'
                f'{len(enriched)} CVEs tracked · Source: CISA Known Exploited Vulnerabilities</div>',
                unsafe_allow_html=True
            )
        else:
            st.info("No CVE data yet — run the ingestion notebook first.")


# ════════════════════════════════════════════════════════════════
# ARTHA MODULE
# ════════════════════════════════════════════════════════════════
elif module == "ARTHA — Financial Intelligence":

    st.markdown("""
        <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                    letter-spacing:0.2em;color:#4A6A8A;margin-bottom:4px">
            PRAJNA INTELLIGENCE SUITE
        </div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:22px;
                    font-weight:700;color:#E8D5A3;letter-spacing:0.05em;margin-bottom:2px">
            ARTHA
        </div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                    color:#4A6A8A;letter-spacing:0.15em;margin-bottom:20px">
            FINANCIAL INTELLIGENCE · SANCTIONS · SHELL NETWORKS · INDIA RISK
        </div>
    """, unsafe_allow_html=True)

    if not driver_2:
        st.warning("Artha graph not connected. Add NEO4J_URI_2 / NEO4J_USERNAME_2 / NEO4J_PASSWORD_2 to Streamlit secrets.")
        st.stop()

    with driver_2.session() as s:
        n_fart  = s.run("MATCH (a:FinancialArticle) RETURN count(a) AS c").single()["c"]
        n_fent  = s.run("MATCH (e:FinancialEntity)  RETURN count(e) AS c").single()["c"]
        n_cross = s.run("MATCH ()-[r:CROSS_DOMAIN]-() RETURN count(r) AS c").single()["c"]

    c1, c2, c3 = st.columns(3)
    for col, label, val in [
        (c1, "SANCTIONS ENTRIES",  n_fart),
        (c2, "FINANCIAL ENTITIES", n_fent),
        (c3, "CROSS-DOMAIN LINKS", n_cross),
    ]:
        col.markdown(
            f'<div style="background:#0D1117;border:1px solid #1C2A38;border-radius:6px;'
            f'padding:14px;text-align:center">'
            f'<div style="font-family:IBM Plex Mono;font-size:9px;color:#4A6A8A;'
            f'letter-spacing:0.15em">{label}</div>'
            f'<div style="font-family:IBM Plex Mono;font-size:22px;font-weight:700;'
            f'color:#E8D5A3">{val}</div></div>',
            unsafe_allow_html=True
        )
    st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)

    atab1, atab2, atab3 = st.tabs(["SANCTIONS QUERY", "SHELL NETWORK", "INDIA RISK EXPOSURE"])

    with atab1:
        st.markdown(
            '<div style="font-family:IBM Plex Mono;font-size:10px;color:#4A6A8A;'
            'letter-spacing:0.15em;margin-bottom:16px">'
            'SEARCH 800+ SANCTIONS ENTRIES · OPENSANCTIONS + OFAC SDN</div>',
            unsafe_allow_html=True
        )
        entity_query = st.text_input(
            "Entity name",
            placeholder="e.g. Rostec, Sberbank, IRGC",
            key="artha_sanctions_query"
        )
        if st.button("SEARCH SANCTIONS GRAPH", key="artha_search_btn"):
            if not entity_query:
                st.warning("Enter an entity name.")
            else:
                with driver_2.session() as s:
                    results = s.run("""
                        MATCH (e:FinancialEntity)
                        WHERE toLower(e.name) CONTAINS toLower($q)
                        RETURN e.name AS name, e.type AS type,
                               e.source_list AS lists,
                               e.first_seen AS first_seen,
                               e.last_seen AS last_seen
                        ORDER BY e.last_seen DESC LIMIT 20
                    """, {"q": entity_query}).data()

                    co_occurs = s.run("""
                        MATCH (e:FinancialEntity)
                        WHERE toLower(e.name) CONTAINS toLower($q)
                        WITH e LIMIT 3
                        MATCH (e)-[r:FIN_CO_OCCURS]-(other:FinancialEntity)
                        RETURN e.name AS e1, other.name AS e2, r.count AS count
                        ORDER BY r.count DESC LIMIT 15
                    """, {"q": entity_query}).data()

                    cross = s.run("""
                        MATCH (f:FinancialEntity)
                        WHERE toLower(f.name) CONTAINS toLower($q)
                        WITH f LIMIT 3
                        MATCH (c:CyberEntity)-[:CROSS_DOMAIN]->(f)
                        RETURN c.name AS cyber_entity, c.type AS cyber_type
                        LIMIT 5
                    """, {"q": entity_query}).data()

                if results:
                    df_res = pd.DataFrame(results)
                    st.dataframe(
                        df_res.rename(columns={
                            "name": "Entity", "type": "Type",
                            "lists": "Sanctions Lists",
                            "first_seen": "First Sanctioned",
                            "last_seen": "Last Updated"
                        }),
                        use_container_width=True, hide_index=True
                    )

                    if cross:
                        st.markdown(
                            '<div style="font-family:IBM Plex Mono;font-size:9px;color:#C47B6E;'
                            'letter-spacing:0.15em;margin:12px 0 4px">'
                            '⚠ CROSS-DOMAIN ALERT — ALSO APPEARS IN CYBER GRAPH</div>',
                            unsafe_allow_html=True
                        )
                        for c in cross:
                            st.markdown(
                                f'<div style="font-family:IBM Plex Mono;font-size:10px;color:#E8D5A3">'
                                f'→ {c["cyber_entity"]} ({c["cyber_type"]})</div>',
                                unsafe_allow_html=True
                            )

                    with st.spinner("Generating sanctions intelligence brief..."):
                        entities_str  = ", ".join([r["name"] for r in results[:5]])
                        lists_str     = results[0]["lists"] if results else ""
                        co_occurs_str = ", ".join([f"{r['e2']} ({r['count']})" for r in co_occurs[:8]])
                        cross_str     = ", ".join([c["cyber_entity"] for c in cross]) or "None"

                        prompt = (
                            f"You are Artha, India's financial intelligence engine.\n"
                            f"Query: {entity_query}\n\n"
                            f"Matched entities: {entities_str}\n"
                            f"Sanctions lists: {lists_str}\n"
                            f"Co-occurring financial entities: {co_occurs_str}\n"
                            f"Cross-domain cyber linkages: {cross_str}\n\n"
                            "ENTITY PROFILE: [Who/what is this entity, why sanctioned]\n\n"
                            "SANCTIONS EXPOSURE: [Which lists, what programs, since when]\n\n"
                            "INDIA EXPOSURE: [Compliance risk for Indian banks/companies]\n\n"
                            "CROSS-DOMAIN RISK: [Any cyber threat actor linkages?]\n\n"
                            "Max 300 words."
                        )
                        brief = ask_groq(prompt, max_tokens=600)

                    st.markdown(
                        '<div class="brief-container"><div class="brief-header">SANCTIONS INTELLIGENCE BRIEF — '
                        + entity_query.upper()[:50] + '</div>'
                        + brief.replace("\n", "<br>") + "</div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.info(f"No results found for '{entity_query}' in the sanctions graph.")

    with atab2:
        st.markdown(
            '<div style="font-family:IBM Plex Mono;font-size:10px;color:#4A6A8A;'
            'letter-spacing:0.15em;margin-bottom:16px">'
            'FINANCIAL ENTITY NETWORK · PATH QUERY · MAX 4 HOPS</div>',
            unsafe_allow_html=True
        )
        col_a, col_b = st.columns(2)
        with col_a:
            node_a = st.text_input("Entity A", placeholder="e.g. Rostec", key="shell_a")
        with col_b:
            node_b = st.text_input("Entity B", placeholder="e.g. OFAC", key="shell_b")

        if st.button("FIND NETWORK PATH", key="shell_btn"):
            if not node_a or not node_b:
                st.warning("Enter both entities.")
            else:
                with driver_2.session() as s:
                    path_result = s.run("""
                        MATCH (a:FinancialEntity), (b:FinancialEntity)
                        WHERE toLower(a.name) CONTAINS toLower($a)
                          AND toLower(b.name) CONTAINS toLower($b)
                        WITH a, b LIMIT 1
                        MATCH path = shortestPath((a)-[:FIN_CO_OCCURS*..4]-(b))
                        RETURN [n IN nodes(path) | n.name] AS nodes,
                               length(path) AS hops
                        LIMIT 1
                    """, {"a": node_a, "b": node_b}).data()

                    neighbourhood = s.run("""
                        MATCH (e:FinancialEntity)
                        WHERE toLower(e.name) CONTAINS toLower($a)
                        WITH e LIMIT 1
                        MATCH (e)-[r:FIN_CO_OCCURS]-(other:FinancialEntity)
                        RETURN e.name AS e1, other.name AS e2,
                               r.count AS count, other.type AS type
                        ORDER BY r.count DESC LIMIT 25
                    """, {"a": node_a}).data()

                if path_result:
                    path = path_result[0]
                    st.markdown(
                        f'<div style="font-family:IBM Plex Mono;font-size:10px;color:#A8C5A0;margin-bottom:12px">'
                        f'PATH FOUND — {path["hops"]} hops: '
                        + " → ".join([f'<span style="color:#E8D5A3">{n}</span>' for n in path["nodes"]])
                        + "</div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.info("No direct path found within 4 hops.")

                if neighbourhood:
                    ARTHA_COLORS = {
                        "SANCTIONED_PERSON": "#C47B6E", "SANCTIONED_ORG": "#E8D5A3",
                        "SANCTIONS_BODY": "#6B8CAE", "JURISDICTION": "#A8C5A0",
                        "FINANCIAL_CRIME": "#B8476E", "ORG": "#6B8CAE",
                        "GPE": "#C8A96E", "PERSON": "#A8C5A0",
                    }
                    net = Network(height="450px", width="100%", bgcolor="#0A0C0F",
                                  font_color="#8A9BB0", notebook=True, cdn_resources="in_line")
                    net.set_options('{"physics":{"forceAtlas2Based":{"gravitationalConstant":-50,"springLength":130},"solver":"forceAtlas2Based"},"edges":{"smooth":{"type":"continuous"},"color":{"opacity":0.4}}}')
                    nodes_seen = set()
                    for r in neighbourhood:
                        for name, ntype in [(r["e1"], "SANCTIONED_ORG"), (r["e2"], r["type"])]:
                            if name not in nodes_seen:
                                nodes_seen.add(name)
                                color = ARTHA_COLORS.get(ntype, "#5A6A7A")
                                size  = 30 if name == r["e1"] else 16
                                net.add_node(name, label=name,
                                             color={"background": color, "border": color},
                                             size=size, font={"size": 11, "color": "#C8D4E0"})
                        net.add_edge(r["e1"], r["e2"], value=min(r["count"]*0.4, 4),
                                     color={"color": "#2A3A4A", "highlight": "#E8D5A3"})
                    net.save_graph("artha_graph.html")
                    with open("artha_graph.html", "r", encoding="utf-8") as f:
                        html = f.read()
                    components.html(html, height=460, scrolling=False)

    with atab3:
        st.markdown(
            '<div style="font-family:IBM Plex Mono;font-size:10px;color:#4A6A8A;'
            'letter-spacing:0.15em;margin-bottom:16px">'
            'CROSS-DOMAIN INDIA RISK · ENTITIES IN BOTH GEOPOLITICAL + SANCTIONS GRAPH</div>',
            unsafe_allow_html=True
        )
        with st.spinner("Computing India risk exposure..."):
            with driver_2.session() as s:
                india_exposed = s.run("""
                    MATCH (f:FinancialEntity)
                    WHERE f.source_list CONTAINS 'India'
                       OR f.source_list CONTAINS 'IN'
                    WITH f, COUNT{(f)--()} AS conn
                    ORDER BY conn DESC LIMIT 30
                    RETURN f.name AS name, f.type AS type,
                           f.source_list AS lists, conn
                """).data()

                cross_domain = s.run("""
                    MATCH (c:CyberEntity)-[r:CROSS_DOMAIN]->(f:FinancialEntity)
                    RETURN c.name AS cyber_name, c.type AS cyber_type,
                           f.name AS fin_name, f.type AS fin_type,
                           f.source_list AS lists
                    LIMIT 20
                """).data()

            if india_exposed:
                st.markdown(
                    '<div style="font-family:IBM Plex Mono;font-size:9px;color:#4A6A8A;'
                    'letter-spacing:0.15em;margin-bottom:8px">INDIA-LINKED SANCTIONED ENTITIES</div>',
                    unsafe_allow_html=True
                )
                df_india = pd.DataFrame(india_exposed)
                st.dataframe(
                    df_india.rename(columns={
                        "name": "Entity", "type": "Type",
                        "lists": "Sanctions Lists", "conn": "Graph Connections"
                    }),
                    use_container_width=True, hide_index=True
                )

            if cross_domain:
                st.markdown(
                    '<div style="font-family:IBM Plex Mono;font-size:9px;color:#C47B6E;'
                    'letter-spacing:0.15em;margin:20px 0 8px">'
                    '⚠ CROSS-DOMAIN ENTITIES — APPEAR IN BOTH CYBER + FINANCIAL GRAPHS</div>',
                    unsafe_allow_html=True
                )
                df_cross = pd.DataFrame(cross_domain)
                st.dataframe(
                    df_cross.rename(columns={
                        "cyber_name": "Cyber Entity", "cyber_type": "Cyber Type",
                        "fin_name": "Financial Entity", "fin_type": "Financial Type",
                        "lists": "Sanctions Lists"
                    }),
                    use_container_width=True, hide_index=True
                )

            with st.spinner("Generating India risk brief..."):
                india_str = ", ".join([r["name"] for r in india_exposed[:8]]) or "None found"
                cross_str = ", ".join([
                    f"{r['cyber_name']} / {r['fin_name']}" for r in cross_domain[:5]
                ]) or "None found"

                prompt = (
                    "You are Artha, India's financial intelligence engine.\n\n"
                    f"India-linked sanctioned entities (top): {india_str}\n"
                    f"Cross-domain entities (cyber + financial): {cross_str}\n\n"
                    "TOP 3 INDIA EXPOSURE RISKS:\n"
                    "1. [Entity/network — why it matters for India]\n"
                    "2. [Entity/network — why it matters for India]\n"
                    "3. [Entity/network — why it matters for India]\n\n"
                    "CROSS-DOMAIN ALERT: [Entities appearing in both cyber + financial graphs]\n\n"
                    "COMPLIANCE IMPLICATIONS: [What Indian banks, PSUs, corporates should watch for]\n\n"
                    "Max 300 words. India-centric, direct, actionable."
                )
                risk_brief = ask_groq(prompt, max_tokens=600)

            st.markdown(
                '<div class="brief-container"><div class="brief-header">INDIA RISK EXPOSURE BRIEF — '
                + get_week_key() + '</div>'
                + risk_brief.replace("\n", "<br>") + "</div>",
                unsafe_allow_html=True
            )
# ── [END: RAKSHA + ARTHA MODULES] ───────────────────────────────
