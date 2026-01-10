#streamlit_app.py
import streamlit as st
import os
import json
from pathlib import Path

# =====================================================
# Paths
# =====================================================
INTENTS_PATH = "nlu_engine/intents.json"
MODEL_DIR = "models/intent_model"
ENTITIES_FILE = "nlu_engine/entities.json"

os.makedirs("models", exist_ok=True)
os.makedirs("nlu_engine", exist_ok=True)

# =====================================================
# Page config
# =====================================================
st.set_page_config(page_title="BankBot NLU", layout="wide")

# =====================================================
# Styles
# =====================================================
st.markdown("""
<style>
/* Multi-color impressive background */
body { 
    background: linear-gradient(135deg, 
        #667eea 0%, 
        #764ba2 25%, 
        #f093fb 50%, 
        #f5576c 75%, 
        #ffa500 100%);
    animation: gradientShift 15s ease infinite;
    background-size: 400% 400%;
}

.stApp {
    background: linear-gradient(135deg, 
        #667eea 0%, 
        #764ba2 25%, 
        #f093fb 50%, 
        #f5576c 75%, 
        #ffa500 100%);
    animation: gradientShift 15s ease infinite;
    background-size: 400% 400%;
}

@keyframes gradientShift {
    0% {
        background-position: 0% 50%;
    }
    50% {
        background-position: 100% 50%;
    }
    100% {
        background-position: 0% 50%;
    }
}

/* Main content wrapper */
.main .block-container {
    padding-top: 2rem;
}

/* Header styling with vibrant gradient */
.title { 
    font-size: 48px; 
    font-weight: 900; 
    background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 50%, #ef4444 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 10px;
    letter-spacing: -1px;
    filter: drop-shadow(0 0 20px rgba(251, 191, 36, 0.3));
}

.subtitle { 
    color: #f1f5f9; 
    margin-bottom: 35px;
    font-size: 20px;
    font-weight: 600;
    letter-spacing: 0.5px;
}

.monika-header {
    color: #fbbf24;
    font-size: 28px;
    font-weight: 800;
    text-shadow: 0 0 20px rgba(251, 191, 36, 0.5);
    margin-bottom: 5px;
}

/* Elevated panel with stronger glass effect for visibility */
.panel {
    background: rgba(15, 23, 42, 0.85);
    padding: 28px;
    border-radius: 24px;
    border: 2px solid rgba(255, 255, 255, 0.25);
    margin-bottom: 24px;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
}

/* Intent row - vibrant and visible */
.intent-row {
    background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
    padding: 16px 20px;
    border-radius: 14px;
    border: none;
    margin-bottom: 12px;
    font-weight: 800;
    font-size: 16px;
    color: #ffffff;
    box-shadow: 0 4px 20px rgba(139, 92, 246, 0.4);
    transition: all 0.3s ease;
}

.intent-row:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 30px rgba(139, 92, 246, 0.6);
}

/* Example items with strong contrast */
.example-item {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    border: 2px solid #60a5fa;
    padding: 12px 16px;
    border-radius: 12px;
    margin-bottom: 10px;
    font-size: 15px;
    color: #ffffff;
    font-weight: 600;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    transition: all 0.2s;
}

.example-item:hover {
    transform: translateX(5px);
    box-shadow: 0 6px 16px rgba(59, 130, 246, 0.5);
}

.example-item-new {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    border: 2px solid #fbbf24;
    padding: 12px 16px;
    border-radius: 12px;
    margin-bottom: 10px;
    font-size: 15px;
    color: #ffffff;
    font-weight: 700;
    box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { 
        opacity: 1;
        transform: scale(1);
    }
    50% { 
        opacity: 0.95;
        transform: scale(0.99);
    }
}

/* Intent result cards - high contrast */
.intent-result {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    padding: 18px 24px;
    border-radius: 16px;
    border: 2px solid #475569;
    margin-bottom: 14px;
    font-weight: 800;
    font-size: 16px;
    color: #f1f5f9;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    transition: all 0.3s;
}

.intent-result:hover {
    transform: translateX(8px);
    border-color: #64748b;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.4);
}

.confidence {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: #ffffff;
    padding: 10px 22px;
    border-radius: 999px;
    font-size: 15px;
    font-weight: 800;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
    letter-spacing: 0.5px;
}

/* Entity cards - vibrant and clear */
.entity-card {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    border: 2px solid #34d399;
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 16px;
    color: #ffffff;
    box-shadow: 0 4px 16px rgba(16, 185, 129, 0.3);
    transition: all 0.3s;
}

.entity-card:hover {
    transform: scale(1.03);
    box-shadow: 0 8px 24px rgba(16, 185, 129, 0.5);
}

.entity-label { 
    font-weight: 800; 
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #d1fae5;
    margin-bottom: 4px;
}

.entity-value { 
    margin-top: 8px; 
    font-size: 19px;
    font-weight: 700;
    color: #ffffff;
}

/* Section headers - vibrant gradient */
.section-header {
    background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 26px;
    font-weight: 900;
    margin-bottom: 18px;
    letter-spacing: -0.5px;
    filter: drop-shadow(0 0 10px rgba(236, 72, 153, 0.3));
}

/* Streamlit native elements */
div[data-testid="stMarkdownContainer"] p {
    color: #e2e8f0;
    font-weight: 500;
}

/* Labels for inputs */
label {
    color: #f1f5f9 !important;
    font-weight: 700 !important;
    font-size: 15px !important;
}

/* Success/Info messages */
.stSuccess {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 16px !important;
    font-weight: 600 !important;
}

.stInfo {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 16px !important;
    font-weight: 600 !important;
}

.stWarning {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 16px !important;
    font-weight: 600 !important;
}

.stError {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 16px !important;
    font-weight: 600 !important;
}

/* Button styling - vibrant */
.stButton>button {
    background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
    color: #ffffff;
    font-weight: 800;
    font-size: 16px;
    border-radius: 14px;
    border: none;
    padding: 14px 32px;
    box-shadow: 0 6px 20px rgba(236, 72, 153, 0.4);
    transition: all 0.3s;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.stButton>button:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 30px rgba(236, 72, 153, 0.6);
    background: linear-gradient(135deg, #db2777 0%, #7c3aed 100%);
}

/* Input fields - high contrast */
.stTextInput>div>div>input,
.stTextArea>div>div>textarea,
.stNumberInput>div>div>input {
    border-radius: 12px;
    border: 2px solid #475569;
    background: #1e293b;
    color: #f1f5f9;
    font-weight: 600;
    transition: all 0.3s;
}

.stTextInput>div>div>input:focus,
.stTextArea>div>div>textarea:focus,
.stNumberInput>div>div>input:focus {
    border-color: #8b5cf6;
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.3);
    background: #0f172a;
}

.stTextInput>div>div>input::placeholder,
.stTextArea>div>div>textarea::placeholder {
    color: #94a3b8;
}

/* Expander styling */
.streamlit-expanderHeader {
    background: linear-gradient(135deg, #334155 0%, #1e293b 100%);
    border-radius: 12px;
    font-weight: 800;
    font-size: 15px;
    color: #f1f5f9;
    border: 2px solid #475569;
    padding: 12px 16px;
}

.streamlit-expanderHeader:hover {
    border-color: #64748b;
    background: linear-gradient(135deg, #475569 0%, #334155 100%);
}

/* Train section - elevated design with dark background */
.train-section {
    background: rgba(15, 23, 42, 0.85);
    padding: 32px;
    border-radius: 24px;
    border: 2px solid rgba(139, 92, 246, 0.5);
    box-shadow: 0 12px 40px rgba(139, 92, 246, 0.3);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
}

/* Horizontal rule */
hr {
    border-color: rgba(255, 255, 255, 0.1);
    margin: 32px 0;
}

/* Number input styling */
.stNumberInput label {
    color: #f1f5f9 !important;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# Header
# =====================================================
st.markdown("<h2 class='monika-header'>🤖 Monika</h2>", unsafe_allow_html=True)
st.markdown("<div class='title'>NLU Engine in Action</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>✨ Intent Classification & Entity Extraction</div>", unsafe_allow_html=True)

# =====================================================
# Utilities
# =====================================================
def load_intents():
    if not os.path.exists(INTENTS_PATH):
        return []
    with open(INTENTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("intents", [])

def save_intents(intents):
    with open(INTENTS_PATH, "w", encoding="utf-8") as f:
        json.dump({"intents": intents}, f, indent=4)

def model_exists():
    return os.path.isdir(MODEL_DIR) and any(Path(MODEL_DIR).iterdir())

# =====================================================
# Layout
# =====================================================
left_col, right_col = st.columns([1, 1.4], gap="large")

# =====================================================
# LEFT COLUMN — INTENTS + CREATE INTENT
# =====================================================
with left_col:
    st.markdown("<h3 class='section-header'>📚 Intents (edit & add)</h3>", unsafe_allow_html=True)
    st.markdown("<div class='panel'>", unsafe_allow_html=True)

    intents = load_intents()

    if not intents:
        st.info("No intents available.")
    else:
        for intent in intents:
            with st.expander(f"🎯 {intent['name']} ({len(intent['examples'])} examples)"):
                # Show trained examples (only text)
                for ex in intent["examples"]:
                    st.markdown(
                        f"<div class='example-item'>💬 {ex['text']}</div>",
                        unsafe_allow_html=True
                    )
                # Show new examples distinctly
                for new_ex in intent.get("new_examples", []):
                    st.markdown(
                        f"<div class='example-item-new'>✨ {new_ex} (new)</div>",
                        unsafe_allow_html=True
                    )

    st.markdown("</div>", unsafe_allow_html=True)

    # ✅ CREATE NEW INTENT
    st.markdown("<h3 class='section-header'>➕ Create new intent</h3>", unsafe_allow_html=True)
    st.markdown("<div class='panel'>", unsafe_allow_html=True)

    intent_name = st.text_input("Intent name", placeholder="e.g., check_balance")
    examples_text = st.text_area("Examples (one per line)", height=120, placeholder="What is my account balance?\nShow me my balance\nCheck balance")

    if st.button("🚀 Create Intent"):
        if not intent_name or not examples_text.strip():
            st.warning("⚠️ Please provide intent name and examples.")
        else:
            new_intent = {
                "name": intent_name.strip(),
                "examples": [{"text": e.strip(), "status": "new"} for e in examples_text.splitlines() if e.strip()],
                "new_examples": []
            }
            intents.append(new_intent)
            save_intents(intents)
            st.success("✅ Intent created successfully! Retrain the model to use it.")

    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# RIGHT COLUMN — NLU VISUALIZER
# =====================================================
with right_col:
    st.markdown("<h3 class='section-header'>🔍 NLU Visualizer</h3>", unsafe_allow_html=True)
    st.markdown("<div class='panel'>", unsafe_allow_html=True)

    query = st.text_area(
        "User Query",
        height=110,
        value="",
        placeholder="Type a user query to analyze..."
    )

    top_k = st.number_input("Top intents to show", 1, 5, 4)
    analyze = st.button("🔬 Analyze Query")

    if analyze:
        try:
            from nlu_engine.infer_intent import IntentClassifier
            from nlu_engine.entity_extractor import EntityExtractor

            # --- Load models ---
            ic = IntentClassifier(model_dir=MODEL_DIR)
            ee = EntityExtractor(ENTITIES_FILE)

            # --- Predict intents ---
            intent_results = ic.predict(query, top_k=top_k)

            # --- Extract entities ---
            entities = ee.extract(query)

            # --- Display side-by-side ---
            intent_col, entity_col = st.columns(2)

            # Intent Recognition
            with intent_col:
                st.markdown("#### 🎯 Intent Recognition")
                for r in intent_results:
                    intent_name = r.get('intent', 'unknown')
                    try:
                        pretty = str(intent_name).replace('_', ' ').title()
                    except Exception:
                        pretty = str(intent_name)
                    st.markdown(
                        f"""
                        <div class="intent-result">
                            <span>🎯 {pretty}</span>
                            <span class="confidence">{r['confidence']:.2f}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            # Entity Extraction
            with entity_col:
                st.markdown("#### 🏷️ Entity Extraction")
                if not entities:
                    st.info("ℹ️ No entities found for this query")
                else:
                    for e in entities:
                        st.markdown(
                            f"""
                            <div class="entity-card">
                                <div class="entity-label">🏷️ {e['entity']}</div>
                                <div class="entity-value">{e['value']}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
        except Exception as ex:
            st.error(f"❌ Error loading model or predicting: {ex}")

    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# TRAIN MODEL
# =====================================================
st.markdown("---")
st.markdown("<div class='train-section'>", unsafe_allow_html=True)
st.markdown("<h3 class='section-header'>🧠 Train Model</h3>", unsafe_allow_html=True)

if model_exists():
    st.success("✅ Trained model found and ready to use!")

epochs = st.number_input("Epochs", value=50)
batch = st.number_input("Batch size", value=8)
lr = st.number_input("Learning rate", value=0.01, format="%.6f")


if st.button("🚀 Start Training"):
    st.info("🔄 Training started...")
    st.success("✅ Training completed (hook your training script here)")

st.markdown("</div>", unsafe_allow_html=True)