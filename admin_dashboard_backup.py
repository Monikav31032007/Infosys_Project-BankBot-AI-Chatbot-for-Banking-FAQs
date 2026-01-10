# admin_dashboard.py
import streamlit as st
import pandas as pd
import json
import os
import time
from pathlib import Path
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import re

# ================================
# Paths & setup
# ================================
INTENTS_PATH = "nlu_engine/intents.json"
ENTITIES_FILE = "nlu_engine/entities.json"
MODEL_DIR = "models/intent_model"
LOG_PATH = "logs/query_history.json"
FAQ_PATH = "faq_data.json"

os.makedirs("models", exist_ok=True)
os.makedirs("nlu_engine", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# ================================
# Page config
# ================================
st.set_page_config(page_title="BankBot Admin Panel", layout="wide", initial_sidebar_state="expanded")

# ================================
# Brand palette & theme toggles
# ================================
PALETTE = {
    "primary": "#1f3fd1",
    "accent": "#06b6d4",
    "success": "#10b981",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "ink": "#0f172a",
    "muted": "#6b7280",
    "bg": "#f7fbff",
    "purple": "#7c3aed",
    "pink": "#ec4899",
    "teal": "#14b8a6",
    "indigo": "#4f46e5",
    "cyan": "#22d3ee",
    "amber": "#fbbf24",
    "rose": "#f43f5e",
}

if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = False
if "page" not in st.session_state:
    st.session_state["page"] = "Dashboard"
if "view" not in st.session_state:
    st.session_state["view"] = None
if "selected_intent" not in st.session_state:
    st.session_state["selected_intent"] = None
if "selected_entity" not in st.session_state:
    st.session_state["selected_entity"] = None
with st.sidebar:
    st.session_state["dark_mode"] = st.toggle("🌙 Dark mode", value=st.session_state["dark_mode"])
    st.markdown("<div class='sb-title'>Navigation</div>", unsafe_allow_html=True)

    nav_items = [
        ("🏠 Dashboard", "Dashboard", "linear-gradient(135deg,#4f46e5,#06b6d4)"),
        ("🔎 User Queries", "User Queries", "linear-gradient(135deg,#10b981,#14b8a6)"),
        ("🧪 Training", "Training", "linear-gradient(135deg,#f59e0b,#fbbf24)"),
        ("🗂️ Manage Intents", "Manage Intents", "linear-gradient(135deg,#7c3aed,#ec4899)"),
        ("📚 FAQs", "FAQs", "linear-gradient(135deg,#06b6d4,#4f46e5)"),
        ("📈 Analytics", "Analytics", "linear-gradient(135deg,#14b8a6,#10b981)"),
        ("❓ Help", "Help", "linear-gradient(135deg,#f43f5e,#f59e0b)"),
    ]

    css_rules = ""  

    for i, (label, page, gradient) in enumerate(nav_items):
        if st.button(label, key=f"nav_{page}"):
            st.session_state["page"] = page
            st.session_state["view"] = None

        css_rules += f"""
        div.row-widget.stButton:nth-of-type({i+1}) > button {{
            background: {gradient};
            border-radius: 12px;
            color: white;
            font-weight: 700;
            margin-bottom: 10px;
            padding: 12px;
            text-align: left;
            transition: 0.2s;
            width: 100%;
        }}
        div.row-widget.stButton:nth-of-type({i+1}) > button:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.25);
        }}
        """

    st.markdown(f"<style>{css_rules}</style>", unsafe_allow_html=True)


# ================================
#  CSS
# ================================
bg_light = """
.stApp { background: radial-gradient(1200px 600px at 10% 10%, #8e98a2 20%, #83d5e1 40%, #d8e89f 60%, #d394e5 80%, #db89c4 100%); }
"""
bg_dark = """
.stApp { background: radial-gradient(1200px 600px at 10% 10%, #0b1220 0%, #0f172a 40%, #1f2937 75%, #111827 100%); }
"""
base_css = f"""
<style>
{bg_dark if st.session_state["dark_mode"] else bg_light}

@keyframes gradientShift {{
  0% {{background-position:0% 50%;}}
  50% {{background-position:100% 50%;}}
  100% {{background-position:0% 50%;}}
}}

.sb-title {{
  font-weight:800; margin-bottom:8px; color:{("#7692C9" if st.session_state["dark_mode"] else PALETTE["ink"])};
}}
div.stButton > button {{
  width:100%;
  border:none;
  border-radius:10px;
  padding:10px 12px;
  color:#black;
  font-weight:900;
  box-shadow: 0 6px 18px rgba(15,23,42,0.12);
  background-size: 300% 300%;
  transition: transform .12s ease, box-shadow .12s ease;
}}
#sb_dash {{ background: linear-gradient(135deg,{PALETTE['primary']},{PALETTE['accent']}); animation: gradientShift 12s ease infinite; }}
#sb_queries {{ background: linear-gradient(135deg,{PALETTE['success']},{PALETTE['teal']}); animation: gradientShift 14s ease infinite; }}
#sb_train {{ background: linear-gradient(135deg,{PALETTE['warning']},{PALETTE['amber']}); animation: gradientShift 16s ease infinite; }}
#sb_manage {{ background: linear-gradient(135deg,{PALETTE['indigo']},{PALETTE['purple']}); animation: gradientShift 18s ease infinite; }}
#sb_faq {{ background: linear-gradient(135deg,{PALETTE['pink']},{PALETTE['rose']}); animation: gradientShift 20s ease infinite; }}
#sb_analytics {{ background: linear-gradient(135deg,{PALETTE['accent']},{PALETTE['primary']}); animation: gradientShift 22s ease infinite; }}
#sb_help {{ background: linear-gradient(135deg,{PALETTE['teal']},{PALETTE['success']}); animation: gradientShift 24s ease infinite; }}
div.stButton > button:hover {{ transform: translateY(-3px); box-shadow: 0 12px 30px rgba(15,23,42,0.28); }}

.card {{
  background: {("#0b1220" if st.session_state["dark_mode"] else "#blue")};
  border-radius:14px; padding:14px; margin-bottom:12px;
  box-shadow: 0 10px 30px rgba(15,23,42,0.12);
  border: 1px solid {("#1f2937" if st.session_state["dark_mode"] else "#e5e7eb")};
}}
.metric-title {{ font-size:16px; font-weight:800; color:#black; opacity:0.95; }}
.metric-value {{ font-size:26px; font-weight:900; color:#blue; }}
.metric-info {{ font-size:12px; color:#violet; opacity:0.9; }}

.intent-card {{
  color:white; padding:10px; border-radius:10px; margin-bottom:8px;
  box-shadow: 0 8px 24px rgba(15,23,42,0.20);
  background: linear-gradient(135deg,#4f46e5,#7c3aed,#ec4899,#14b8a6,#f59e0b);
  background-size: 400% 400%; animation: gradientShift 16s ease infinite;
}}

.entity-card {{
  border-radius:12px; padding:12px; margin-bottom:10px; color:white;
  box-shadow: 0 8px 24px rgba(15,23,42,0.16);
}}
.entity-title {{ font-weight:800; font-size:14px; }}
.entity-desc {{ font-size:12px; opacity:0.92; }}

.example-chip {{
  display:inline-block; background:{("#1f2937" if st.session_state["dark_mode"] else "#eef2ff")};
  color:{("#e5e7eb" if st.session_state["dark_mode"] else PALETTE['ink'])};
  padding:6px 10px; border-radius:999px; margin:4px 6px 4px 0;
  font-weight:600; border:{("1px solid #374151" if st.session_state["dark_mode"] else "1px solid #e5e7eb")};
  font-size:12px;
}}
.new-chip {{
  display:inline-block; background:#fff7ed; color:#9a3412; padding:6px 10px; border-radius:999px; margin:4px 6px 4px 0;
  font-weight:700; border:1px solid #fdba74; font-size:12px;
}}

.history-item {{
  background:{("#0b1220" if st.session_state["dark_mode"] else "#ffffff")};
  border:{("1px solid #1f2937" if st.session_state["dark_mode"] else "1px solid #e5e7eb")};
  border-radius:12px; padding:10px 12px; margin-bottom:10px;
  box-shadow: 0 6px 18px rgba(15,23,42,0.10);
  display:flex; align-items:center; justify-content:space-between; gap:10px;
}}
.history-query {{ font-weight:700; }}
.badge {{ display:inline-block; border-radius:999px; padding:6px 10px; font-weight:700; font-size:12px; }}
.badge-intent {{ background:#e0f2fe; color:#0369a1; }}
.badge-conf {{ background:#dcfce7; color:#166534; }}
.badge-date {{ background:#f1f5f9; color:#0f172a; }}
</style>
"""
st.markdown(base_css, unsafe_allow_html=True)

# ================================
# Utilities: load/save
# ================================
def load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Intent helpers with new-example support
def normalize_intent(it):
    norms = []
    for ex in it.get("examples", []):
        if isinstance(ex, dict):
            txt = ex.get("text", "").strip()
            status = ex.get("status", "trained")
        else:
            txt = str(ex).strip()
            status = "trained"
        if txt:
            norms.append({"text": txt, "status": status})
    it["examples"] = norms
    it["new_examples"] = [e for e in it.get("new_examples", []) if isinstance(e, str) and e.strip()]
    return it

def load_intents():
    data = load_json(INTENTS_PATH, {}).get("intents", [])
    cleaned = []
    for it in data:
        name = re.sub(r"[^a-z0-9_]", "", it.get("name", "").lower().strip().replace(" ", "_"))
        if not name:
            continue
        cleaned.append(normalize_intent({"name": name, **it}))
    return cleaned

def save_intents(intents):
    out = []
    seen = set()
    for it in intents:
        name = re.sub(r"[^a-z0-9_]", "", it.get("name", "").lower().strip().replace(" ", "_"))
        if not name or name in seen:
            continue
        seen.add(name)
        it = normalize_intent({"name": name, **it})
        out.append({"name": name, "examples": it["examples"], "new_examples": it["new_examples"]})
    save_json(INTENTS_PATH, {"intents": out})

def load_entities():
    data = load_json(ENTITIES_FILE, {})
    patterns = data.get("patterns", [])
    regex_patterns = data.get("regex_patterns", [])
    out = {}
    for p in patterns:
        label = (p.get("label") or "").strip()
        lower = ""
        try:
            lower = (p.get("pattern", [{}])[0].get("LOWER") or "").strip().lower()
        except Exception:
            lower = ""
        if not label:
            continue
        key = label.lower()
        if key not in out:
            out[key] = {"label": label, "values": [], "has_regex": False}
        if lower:
            if lower not in out[key]["values"]:
                out[key]["values"].append(lower)

    for rp in regex_patterns:
        lab = (rp.get("label") or "").strip()
        if not lab:
            continue
        key = lab.lower()
        if key not in out:
            out[key] = {"label": lab, "values": [], "has_regex": True}
        else:
            out[key]["has_regex"] = True

    return list(out.values())

def load_logs():
    return load_json(LOG_PATH, [])

def save_logs(logs):
    save_json(LOG_PATH, logs)

def dedup_entities(ents):
    uniq = []
    seen = set()
    for e in ents or []:
        key = (e.get("entity", ""), e.get("value", ""))
        if key not in seen:
            uniq.append(e)
            seen.add(key)
    return uniq

def log_query(query, intent, confidence, entities=None):
    entities = dedup_entities(entities or [])
    entry = {
        "query": query,
        "intent": intent,
        "confidence": float(confidence),
        "entities": [f"{e.get('entity','')}: {e.get('value','')}" for e in entities],
        "date": datetime.utcnow().isoformat()
    }
    logs = load_logs()
    if logs:
        last = logs[-1]
        try:
            last_time = datetime.fromisoformat(last.get("date", "").replace("Z",""))
        except Exception:
            last_time = datetime.utcnow() - timedelta(seconds=10)
        now_time = datetime.utcnow()
        is_same = (
            last.get("query") == entry["query"] and
            last.get("intent") == entry["intent"] and
            abs(float(last.get("confidence", 0.0)) - entry["confidence"]) < 1e-6 and
            (now_time - last_time).total_seconds() <= 2
        )
        if is_same:
            return last
    logs.append(entry)
    save_logs(logs)
    return entry

def model_exists():
    return os.path.isdir(MODEL_DIR) and any(Path(MODEL_DIR).iterdir())

# ================================
# Classifier & extractor
# ================================
try:
    from nlu_engine.infer_intent import IntentClassifier
    from nlu_engine.entity_extractor import EntityExtractor
    classifier_available = True
except Exception:
    classifier_available = False
    class IntentClassifier:
        def __init__(self, model_dir=None):
            self.intents = load_intents()
            self.intent_tokens = {}
            for it in self.intents:
                tokens = set()
                for ex in it.get("examples", []):
                    tokens.update(re.findall(r"\w+", ex["text"].lower()))
                self.intent_tokens[it["name"]] = tokens
        def predict(self, text, top_k=3):
            text_tokens = set(re.findall(r"\w+", text.lower()))
            scores = []
            for name, tokens in self.intent_tokens.items():
                overlap = len(tokens & text_tokens)
                score = overlap / (len(tokens) + 1) if tokens else 0.0
                scores.append({"intent": name, "confidence": float(score)})
            scores = sorted(scores, key=lambda x: x["confidence"], reverse=True)
            if scores and scores[0]["confidence"] > 0:
                top = scores[0]["confidence"]
                for s in scores:
                    if abs(s["confidence"] - top) < 1e-12:
                        s["confidence"] = 1.0
                    else:
                        s["confidence"] = s["confidence"] / top if top > 0 else 0.0
            return scores[:top_k]
    class EntityExtractor:
        def __init__(self, entities_file=None):
            self.entities = load_entities()
        def extract(self, text):
            res = []
            for p in self.entities:
                vals = p.get("values", []) or []
                for kw in vals:
                    if kw and kw in text.lower():
                        res.append({"entity": p["label"], "value": kw})
            return res

IC = IntentClassifier(model_dir=MODEL_DIR) if classifier_available else IntentClassifier()
EE = EntityExtractor(ENTITIES_FILE)

# ================================
# Helpers
# ================================
def df_from_logs():
    logs = load_logs()
    if not logs:
        return pd.DataFrame(columns=["query","intent","confidence","date","entities"])
    df = pd.DataFrame(logs)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df

def format_conf(v):
    """Format confidence consistently to 3 decimal places (accurate display).

    Returns strings like '0.999'."""
    try:
        return f"{round(float(v) + 1e-12, 3):.3f}"
    except Exception:
        return "0.000"

def render_cards(items, cols=2, card_fn=None):
    if not items:
        return
    if cols < 1: cols = 1
    for i in range(0, len(items), cols):
        row = st.columns(cols)
        for j, item in enumerate(items[i:i+cols]):
            with row[j]:
                card_fn(item)

def rainbow_style(idx):
    gradients = [
        f"linear-gradient(135deg,{PALETTE['primary']},{PALETTE['accent']})",
        f"linear-gradient(135deg,{PALETTE['success']},{PALETTE['teal']})",
        f"linear-gradient(135deg,{PALETTE['indigo']},{PALETTE['purple']})",
        f"linear-gradient(135deg,{PALETTE['warning']},{PALETTE['amber']})",
        f"linear-gradient(135deg,{PALETTE['pink']},{PALETTE['rose']})",
    ]
    return gradients[idx % len(gradients)]

def entity_color(idx):
    return [
        f"linear-gradient(135deg,{PALETTE['accent']},#3b82f6)",
        f"linear-gradient(135deg,{PALETTE['success']},#22c55e)",
        f"linear-gradient(135deg,{PALETTE['indigo']},#6366f1)",
        f"linear-gradient(135deg,{PALETTE['purple']},#a855f7)",
        f"linear-gradient(135deg,{PALETTE['pink']},#fb7185)",
        f"linear-gradient(135deg,{PALETTE['teal']},#2dd4bf)",
        f"linear-gradient(135deg,{PALETTE['warning']},#f59e0b)",
        f"linear-gradient(135deg,{PALETTE['primary']},#60a5fa)",
    ][idx % 8]

# ================================
# Header
# ================================
st.markdown("<h1 style='margin-bottom:6px; color:#e5e7eb;'>BankBot Admin</h1>" if st.session_state["dark_mode"]
            else "<h1 style='margin-bottom:6px; color:#0b4a6f;'>BankBot Admin</h1>", unsafe_allow_html=True)

# ================================
# Dashboard
# ================================
if st.session_state["page"] == "Dashboard":
    df = df_from_logs()
    total_queries = len(df)
    intents_list = load_intents()
    intents_count = len(intents_list)
    entity_defs = load_entities()
    entities_count = len(entity_defs)
    avg_conf = df["confidence"].mean() if not df.empty else 0.0
    avg_conf_display = format_conf(avg_conf) if not df.empty else "N/A"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        btn = st.button("📊  Total Queries", key="card_total")
        st.markdown(f"<div class='metric-title'>Total queries</div><div class='metric-value'>{total_queries}</div><div class='metric-info'>All user queries logged with filters & export.</div>", unsafe_allow_html=True)
        st.markdown(f"<style>div.row-widget.stButton > button#card_total {{background: {rainbow_style(0)}; border-radius:14px;}}</style>", unsafe_allow_html=True)
        if btn: st.session_state["view"] = "total"
    with c2:
        btn = st.button("🎯  Confidence", key="card_conf")
        st.markdown(f"<div class='metric-title'>Average confidence</div><div class='metric-value'>{avg_conf_display}</div><div class='metric-info'>Browse per-intent confidence and details.</div>", unsafe_allow_html=True)
        st.markdown(f"<style>div.row-widget.stButton > button#card_conf {{background: {rainbow_style(1)}; border-radius:14px;}}</style>", unsafe_allow_html=True)
        if btn: st.session_state["view"] = "confidence"
    with c3:
        btn = st.button("🗂️  Intents", key="card_intents")
        st.markdown(f"<div class='metric-title'>Intents</div><div class='metric-value'>{intents_count}</div><div class='metric-info'>Click to view examples.</div>", unsafe_allow_html=True)
        st.markdown(f"<style>div.row-widget.stButton > button#card_intents {{background: {rainbow_style(2)}; border-radius:14px;}}</style>", unsafe_allow_html=True)
        if btn: st.session_state["view"] = "intents"
    with c4:
        btn = st.button("🏷️  Entities", key="card_entities")
        st.markdown(f"<div class='metric-title'>Entities</div><div class='metric-value'>{entities_count}</div><div class='metric-info'>View entity cards and history drilldowns.</div>", unsafe_allow_html=True)
        st.markdown(f"<style>div.row-widget.stButton > button#card_entities {{background: {rainbow_style(3)}; border-radius:14px;}}</style>", unsafe_allow_html=True)
        if btn: st.session_state["view"] = "entities"

    st.markdown("---")

    view = st.session_state.get("view")
    if view == "total":
        st.markdown("### Query history")
        fcol1, fcol2, fcol3 = st.columns([2,2,1])
        with fcol1:
            start = st.date_input("Start date", value=None)
        with fcol2:
            end = st.date_input("End date", value=None)
        with fcol3:
            min_conf = st.slider("Min confidence", 0.0, 1.0, 0.0, 0.01)

        dff = df.copy()
        if start: dff = dff[dff["date"] >= pd.to_datetime(start)]
        if end: dff = dff[dff["date"] <= pd.to_datetime(end)]
        dff = dff[dff["confidence"] >= min_conf]
        dff = dff.sort_values("date", ascending=False).reset_index(drop=True)

        st.write(f"Records: {len(dff)}")
        if not dff.empty:
            for _, r in dff.head(200).iterrows():
                dt = r["date"].strftime("%Y-%m-%d %H:%M")
                st.markdown(
                    f"<div class='history-item'>"
                    f"<div class='history-query'>{r['query']}</div>"
                    f"<div class='history-meta'>"
                    f"<span class='badge badge-intent'>{r['intent']}</span>"
                    f"<span class='badge badge-conf'>conf {format_conf(r['confidence'])}</span>"
                    f"<span class='badge badge-date'>{dt}</span>"
                    f"</div></div>",
                    unsafe_allow_html=True
                )
            with st.expander("Table view & export"):
                dff_display = dff.copy()
                try:
                    dff_display["confidence"] = dff_display["confidence"].apply(format_conf)
                except Exception:
                    dff_display["confidence"] = dff_display.get("confidence")
                st.dataframe(dff_display, height=380)
                dff_export = dff.copy()
                try:
                    dff_export["confidence"] = dff_export["confidence"].apply(format_conf)
                except Exception:
                    pass
                st.download_button("Download CSV", dff_export.to_csv(index=False).encode("utf-8"), "query_history.csv", "text/csv")
        else:
            st.info("No records match the filters.")

    elif view == "confidence":
        st.markdown("### Confidence — intents")
        if df.empty:
            st.info("No logs yet.")
        else:
            avg_by_intent = df.groupby("intent")["confidence"].mean().reset_index().sort_values("confidence", ascending=False)
            def render_intent_card(row):
                intent_name = row["intent"]
                avg_val = row["confidence"]
                df_int = df[df["intent"] == intent_name]
                st.markdown(
                    f"<div class='intent-card'><div style='font-weight:800'>{intent_name.replace('_',' ').title()}</div><div style='margin-top:6px;'>Avg: <strong>{format_conf(avg_val)}</strong> • {len(df_int)} queries</div></div>",
                    unsafe_allow_html=True
                )
                if st.button(f"Open {intent_name}", key=f"open_conf_{intent_name}"):
                    st.session_state["selected_intent"] = intent_name
                    st.session_state["view"] = "confidence_intent"
            render_cards([r for _, r in avg_by_intent.iterrows()], cols=2, card_fn=render_intent_card)

    elif view == "confidence_intent" and st.session_state.get("selected_intent"):
        sel = st.session_state["selected_intent"]
        st.markdown(f"### {sel.replace('_',' ').title()} — confidence details")
        df_sel = df[df["intent"] == sel].sort_values("date", ascending=False)
        if df_sel.empty:
            st.info("No queries for this intent.")
        else:
            st.markdown("#### Recent queries")
            for _, r in df_sel.head(50).iterrows():
                dt = r["date"].strftime("%Y-%m-%d %H:%M") if not pd.isnull(r["date"]) else ""
                st.markdown(
                    f"<div class='history-item'><div class='history-query'>{r['query']}</div>"
                    f"<div style='display:flex; gap:8px; align-items:center;'>"
                    f"<span class='badge badge-conf'>conf {format_conf(r['confidence'])}</span>"
                    f"<span class='badge badge-date'>{dt}</span></div></div>",
                    unsafe_allow_html=True
                )
            avg_conf_val = df_sel['confidence'].mean()
            st.markdown(f"- Average confidence: **{format_conf(avg_conf_val)}**")
            df_sel["bucket"] = pd.cut(df_sel["confidence"], bins=[0,0.2,0.4,0.6,0.8,1.0],
                                      labels=["0-0.2","0.2-0.4","0.4-0.6","0.6-0.8","0.8-1.0"]) 
            bucket_counts = df_sel["bucket"].value_counts().sort_index()
            fig = px.pie(values=bucket_counts.values, names=bucket_counts.index, title="Confidence buckets",
                         hole=0.35, color_discrete_sequence=["#ef4444", "#f59e0b", "#fbbf24", "#84cc16", "#10b981"])
            st.plotly_chart(fig, use_container_width=True)

    elif view == "intents":
        st.markdown("### Intents")
        intents = intents_list
        if not intents:
            st.info("No intents found.")
        else:
            def render_intent(it):
                name = it["name"]
                examples = it.get("examples", [])
                new_examples = it.get("new_examples", [])
                st.markdown(
                    f"<div class='intent-card'><div style='font-weight:800'>{name.replace('_',' ').title()}</div>"
                    f"<div style='margin-top:6px; opacity:0.95;'>{len(examples)} trained • {len(new_examples)} new</div></div>",
                    unsafe_allow_html=True
                )
                if st.button(f"View {name}", key=f"view_intent_{name}"):
                    st.session_state["selected_intent"] = name
                    st.session_state["view"] = "intent_detail"
            render_cards(intents, cols=2, card_fn=render_intent)

    elif view == "intent_detail" and st.session_state.get("selected_intent"):
        sel = st.session_state["selected_intent"]
        st.markdown(f"### {sel.replace('_',' ').title()} — examples")
        it = next((x for x in intents_list if x["name"] == sel), None)
        if it:
            for ex in it.get("examples", []):
                st.markdown(f"<span class='example-chip'>{ex['text']}</span>", unsafe_allow_html=True)
            if it.get("new_examples"):
                st.markdown("### New examples (pending training)")
                for ex in it.get("new_examples", []):
                    st.markdown(f"<span class='new-chip'>{ex}</span>", unsafe_allow_html=True)
        else:
            st.info("Intent not found.")

    elif view == "entities":
        st.markdown("### Entities")
        entity_defs = load_entities()  
        if not entity_defs:
            st.info("No entity definitions found.")
        else:
            def render_entity_card(idx, ent):
                bg = entity_color(idx)
                vals = ent.get('values', []) or []
                sample = ", ".join(vals[:6]) if vals else "(patterns)"
                regex_note = " — includes regex patterns" if ent.get('has_regex') else ""
                desc = f"Values: {sample}{'...' if len(vals)>6 else ''}{regex_note}"
                st.markdown(
                    f"<div class='entity-card' style='background:{bg};'>"
                    f"<div class='entity-title'>{ent['label']}</div>"
                    f"<div class='entity-desc'>{desc}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
                if st.button(f"Open {ent['label']}", key=f"open_entity_{ent['label']}_{idx}"):
                    st.session_state["selected_entity"] = ent["label"]
                    st.session_state["view"] = "entity_detail"

            render_cards(list(entity_defs), cols=2, card_fn=lambda e, idx=[0]: (render_entity_card(idx[0], e), idx.__setitem__(0, idx[0]+1)))

    elif view == "entity_detail" and st.session_state.get("selected_entity"):
        label = st.session_state["selected_entity"]
        st.markdown(f"### {label} — history & distribution")
        df = df_from_logs()
        if df.empty:
            st.info("No logs yet.")
        else:
            mask = df["entities"].apply(lambda ents: any(str(ents_i).startswith(f"{label}:") for ents_i in (ents or [])))
            df_e = df[mask].sort_values("date", ascending=False)
            if df_e.empty:
                st.info("No queries found for this entity.")
            else:
                for _, r in df_e.head(100).iterrows():
                    dt = r["date"].strftime("%Y-%m-%d %H:%M")
                    st.markdown(
                        f"<div class='history-item'>"
                        f"<div class='history-query'>{r['query']}</div>"
                        f"<div class='history-meta'>"
                        f"<span class='badge badge-intent'>{r['intent']}</span>"
                        f"<span class='badge badge-conf'>conf {format_conf(r['confidence'])}</span>"
                        f"<span class='badge badge-date'>{dt}</span>"
                        f"</div></div>",
                        unsafe_allow_html=True
                    )
                dist = df_e["intent"].value_counts().reset_index()
                dist.columns = ["intent", "count"]
                fig_edonut = px.pie(dist, names="intent", values="count", hole=0.5, title=f"Intent distribution for {label}")
                st.plotly_chart(fig_edonut, use_container_width=True)

# ================================
# User Queries
# ================================
elif st.session_state["page"] == "User Queries":
    st.markdown("## User queries")
    query = st.text_area("User Query", height=120, placeholder="e.g., Transfer ₹1,000 from savings to current")
    top_k = st.slider("Top K intents", 1, 5, 3)
    if st.button("Analyze Query"):
        if not query.strip():
            st.warning("Please enter a query.")
        else:
            try:
                preds = IC.predict(query, top_k=top_k)
                ents = EE.extract(query)
            except Exception as e:
                st.error(f"Error running NLU: {e}")
                preds = []
                ents = []

            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("### Intent predictions")
            for p in preds:
                st.markdown(
                    f"<div style='display:flex; justify-content:space-between; align-items:center; padding:6px 0;'>"
                    f"<div style='font-weight:700'>{p['intent'].replace('_',' ').title()}</div>"
                    f"<div style='background:#dbeafe; color:#1e40af; padding:6px 12px; border-radius:999px;'>{format_conf(p['confidence'])}</div></div>",
                    unsafe_allow_html=True
                )
            st.markdown("---")
            st.markdown("### Entities")
            ents = dedup_entities(ents)
            if ents:
                highlighted = query
                try:
                    ents_sorted = sorted(ents, key=lambda x: x.get("start", 0), reverse=True)
                    for e in ents_sorted:
                        s = e.get("start")
                        en = e.get("end")
                        if isinstance(s, int) and isinstance(en, int) and 0 <= s < en <= len(highlighted):
                            highlighted = highlighted[:s] + f"<span class='highlight-entity'>{highlighted[s:en]} <small style='opacity:0.8'>[{e['entity']}]</small></span>" + highlighted[en:]
                    st.markdown(f"<div style='padding:8px'>{highlighted}</div>", unsafe_allow_html=True)
                except Exception:
                    pass
                st.markdown("**Entity list**")
                for e in ents:
                    st.markdown(f"- **{e.get('entity','')}**: {e.get('value','')}")
            else:
                st.info("No entities found.")
            st.markdown("</div>", unsafe_allow_html=True)

            top = preds[0] if preds else {"intent":"", "confidence":0.0}
            log_query(query, top["intent"], top["confidence"], ents)
            st.success("Analyzed and logged.")

# ================================
# Training 
# ================================
elif st.session_state["page"] == "Training":
    st.markdown("## Training")
    # Check model files and whether there are pending new examples that require retraining
    intents_for_training = load_intents()
    has_untrained = any(it.get("new_examples") for it in intents_for_training)
    if not model_exists():
        st.error("Training model not found: Start training to create a model.")
    else:
        if has_untrained:
            st.warning("Model exists but new examples or intents are pending — please retrain to include them.")
        else:
            st.success("Training model found")

    st.markdown("### Parameters")
    epochs = st.number_input("Epochs", value=50)
    batch = st.number_input("Batch size", value=16)
    lr = st.number_input("Learning rate", value=0.01, format="%.6f")
    if st.button("Start training"):
        st.info("Training started (simulated).")
        progress = st.progress(0)
        status = st.empty()
        for i in range(100):
            time.sleep(0.03)
            progress.progress(i+1)
            status.text(f"Progress: {i+1}% — epochs={epochs}, batch={batch}, lr={lr}")
        st.success("Training completed (simulated)")
        # Create placeholder model files to indicate a trained model exists
        try:
            Path(MODEL_DIR).mkdir(parents=True, exist_ok=True)
            (Path(MODEL_DIR) / "model.bin").write_text("trained-placeholder")
            st.success("Model files created.")
        except Exception as e:
            st.error(f"Failed creating model files: {e}")
        # Promote new examples to trained
        intents = load_intents()
        changed = False
        for it in intents:
            new_ex = it.get("new_examples", [])
            if new_ex:
                it["examples"].extend([{"text": e, "status": "trained"} for e in new_ex])
                it["new_examples"] = []
                changed = True
        if changed:
            save_intents(intents)
            st.info("New examples promoted to trained.")

# ================================
# Manage Intents 
# ================================
elif st.session_state["page"] == "Manage Intents":
    st.markdown("## Manage intents")
    intents = load_intents()

    st.markdown("### Add intent")
    name = st.text_input("Intent name (snake_case, e.g., check_balance)")
    examples = st.text_area("Examples (one per line)")
    if st.button("Create intent"):
        if not name.strip() or not examples.strip():
            st.warning("Provide intent name and examples.")
        else:
            new = {
                "name": name.strip(),
                "examples": [{"text": e.strip(), "status": "trained"} for e in examples.splitlines() if e.strip()],
                "new_examples": []
            }
            intents.append(new)
            save_intents(intents)
            st.success(f"Intent '{name}' added.")
            # Prompt user to train the model after adding new intents
            st.warning("Model not trained: new intents require training to be recognized by the model.")
            if st.button("Go to Training"):
                st.session_state["page"] = "Training"

    st.markdown("---")
    st.markdown("### Existing intents")
    for idx, it in enumerate(intents):
        safe_key = f"{idx}_{it.get('name','') }"
        with st.expander(it["name"]):
            trained = [ex["text"] for ex in it.get("examples", [])]
            for ex in trained:
                st.markdown(f"<span class='example-chip'>{ex}</span>", unsafe_allow_html=True)
            new_ex = st.text_input(f"Add new example to '{it['name']}'", key=f"newex_{safe_key}")
            if st.button(f"Add example to {it['name']}", key=f"btn_add_{safe_key}"):
                if new_ex.strip():
                    it["new_examples"] = it.get("new_examples", [])
                    it["new_examples"].append(new_ex.strip())
                    save_intents(intents)
                    st.success("New example added (pending training).")
            if it.get("new_examples"):
                st.markdown("New examples (pending training):")
                for ex in it["new_examples"]:
                    st.markdown(f"<span class='new-chip'>{ex}</span>", unsafe_allow_html=True)

# ================================
# FAQs
# ================================
elif st.session_state["page"] == "FAQs":
    st.markdown("## FAQs")
    faqs = load_json(FAQ_PATH, {
        "How do I check my account balance?": "Use the chatbot: 'What's my account balance?' or navigate to Accounts > Balance.",
        "How to transfer money?": "Say 'Transfer ₹1,000 from savings to current' or use Transfers in the app.",
        "How to block a lost card?": "Say 'Block my debit card' or go to Cards > Security > Block.",
        "What is the interest rate on savings?": "Currently 7.5%. Check Rates page for updates.",
        "How to locate the nearest ATM?": "Ask 'Where is the nearest ATM?' and allow location access.",
    })
    search = st.text_input("Search FAQs")
    filtered = {q:a for q,a in faqs.items() if search.lower() in q.lower() or search.lower() in a.lower()} if search else faqs
    if filtered:
        for q,a in filtered.items():
            with st.expander(q):
                st.write(a)
    else:
        st.info("No FAQs found.")
    st.markdown("### Add / Edit FAQ")
    q_text = st.text_input("Question")
    a_text = st.text_area("Answer")
    if st.button("Save FAQ"):
        if q_text.strip() and a_text.strip():
            faqs[q_text.strip()] = a_text.strip()
            save_json(FAQ_PATH, faqs)
            st.success("FAQ saved")
        else:
            st.warning("Provide both question and answer")
    col1, col2 = st.columns(2)
    with col1:
        uploaded = st.file_uploader("Import FAQs (JSON)", type=["json"])
        if uploaded:
            try:
                data = json.load(uploaded)
                if isinstance(data, dict):
                    save_json(FAQ_PATH, data)
                    st.success("Imported FAQs")
                else:
                    st.error("Invalid format")
            except Exception as e:
                st.error(f"Import failed: {e}")
    with col2:
        if faqs:
            st.download_button("Export FAQs", json.dumps(faqs, indent=2).encode("utf-8"), "faqs.json", "application/json")

# ================================
# Analytics 
# ================================
elif st.session_state["page"] == "Analytics":
    st.markdown("## Analytics")
    df = df_from_logs()
    if df.empty:
        st.info("No logs yet.")
    else:
        unique_intents = sorted(df["intent"].unique().tolist())
        palette_seq = [PALETTE["primary"], PALETTE["accent"], PALETTE["indigo"], PALETTE["purple"],
                       PALETTE["pink"], PALETTE["teal"], PALETTE["success"], PALETTE["warning"], PALETTE["amber"], PALETTE["rose"]]
        color_map = {i: c for i, c in zip(unique_intents, palette_seq)}

        st.markdown("### Intent distribution (donut)")
        counts = df["intent"].value_counts().reset_index()
        counts.columns = ["intent", "count"]
        fig_donut = px.pie(counts, names="intent", values="count", hole=0.5,
                           color="intent", color_discrete_map=color_map,
                           title="Intents by count")
        st.plotly_chart(fig_donut, use_container_width=True)

        st.markdown("### Queries over time (with rolling averages)")
        ts = df.set_index("date").resample("D").size().reset_index()
        ts.columns = ["date", "count"]
        ts["roll7"] = ts["count"].rolling(7).mean()
        ts["roll30"] = ts["count"].rolling(30).mean()
        fig_ts = go.Figure()
        fig_ts.add_trace(go.Scatter(x=ts["date"], y=ts["count"], mode="lines+markers", name="Daily", line=dict(color=PALETTE["primary"])))
        fig_ts.add_trace(go.Scatter(x=ts["date"], y=ts["roll7"], mode="lines", name="7-day avg", line=dict(color=PALETTE["accent"])))
        fig_ts.add_trace(go.Scatter(x=ts["date"], y=ts["roll30"], mode="lines", name="30-day avg", line=dict(color=PALETTE["teal"])))
        fig_ts.update_layout(legend=dict(orientation="h"))
        st.plotly_chart(fig_ts, use_container_width=True)

        st.markdown("### Confidence distribution")
        try:
            conf_hist = px.histogram(df, x="confidence", nbins=20, title="Confidence histogram",
                                     color="intent", color_discrete_map=color_map, marginal="rug")
            st.plotly_chart(conf_hist, use_container_width=True)
        except Exception:
            st.info("Not enough data for confidence histogram.")

        st.markdown("### Entity extraction frequency")
        entity_series = []
        for row in load_logs():
            for e in row.get("entities", []):
                label = e.split(":")[0].strip()
                if label:
                    entity_series.append(label)
        if entity_series:
            edf = pd.Series(entity_series).value_counts().reset_index()
            edf.columns = ["entity", "count"]
            fig_ent = px.bar(edf, x="entity", y="count", color="entity", title="Entity frequency")
            fig_ent.update_layout(showlegend=False)
            st.plotly_chart(fig_ent, use_container_width=True)
        else:
            st.info("No entities logged yet.")

# ================================
# Help
# ================================
elif st.session_state["page"] == "Help":
    st.markdown("## Help")
    colA, colB = st.columns(2)
    with colA:
        st.markdown(f"<div class='card' style='background: linear-gradient(135deg,{PALETTE['primary']}, #3b82f6); color:#fff;'><strong>Dashboard</strong><div class='metric-info'>Enhanced history view, colorful metrics.</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='card' style='background: linear-gradient(135deg,{PALETTE['success']}, #22c55e); color:#fff;'><strong>User Queries</strong><div class='metric-info'>Analyze queries, dedup entities, log results.</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='card' style='background: linear-gradient(135deg,{PALETTE['warning']}, #f59e0b); color:#fff;'><strong>Training</strong><div class='metric-info'>Simulate progress; promote new examples to trained.</div></div>", unsafe_allow_html=True)
    with colB:
        st.markdown(f"<div class='card' style='background: linear-gradient(135deg,{PALETTE['accent']}, {PALETTE['primary']}); color:#fff;'><strong>Manage Intents</strong><div class='metric-info'>Add intents and new examples; compact spacing.</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='card' style='background: linear-gradient(135deg,{PALETTE['purple']}, {PALETTE['pink']}); color:#fff;'><strong>Entities</strong><div class='metric-info'>Pattern-only, deduped; drilldowns per entity.</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='card' style='background: linear-gradient(135deg,{PALETTE['indigo']}, {PALETTE['teal']}); color:#fff;'><strong>Analytics</strong><div class='metric-info'>Donut distribution, trends, confidence, entity frequency.</div></div>", unsafe_allow_html=True)