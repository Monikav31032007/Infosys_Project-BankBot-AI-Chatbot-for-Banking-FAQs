import streamlit as st
import datetime
import io
import pandas as pd
import altair as alt

from dialogue_manager.dialogue_handler import DialogueHandler
from database.db import init_db
from database import bank_crud
from database import db as database_db

# -------------------------
# Page Configuration
# -------------------------
st.set_page_config(page_title="Bankbot Ultra", page_icon="🏦", layout="wide")

# -------------------------
# Core Logic Helpers (PRESERVED)
# -------------------------
def try_rerun():
    """Try to rerun in a cross-version safe way."""
    try:
        if hasattr(st, "rerun"):
            st.rerun()
            return
    except Exception:
        pass
    st.session_state._needs_rerun = True
    st.stop()

def set_page_no_rerun(page_name: str):
    """Set page in session state without forcing a rerun from the callback."""
    st.session_state.page = page_name

# -------------------------
# Init DB and session
# -------------------------
init_db()
if "handler" not in st.session_state:
    st.session_state.handler = DialogueHandler()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "pending_control" not in st.session_state:
    st.session_state.pending_control = None
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "debug" not in st.session_state:
    st.session_state.debug = False

# -------------------------
# Enhanced UI Styling (VIBRANT & MODERN)
# -------------------------
st.markdown(
    """
<style>
/* --- GLOBAL FONTS & RESET --- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Outfit:wght@400;500;700&display=swap');

html, body, [class*="css"]  {
    font-family: 'Outfit', sans-serif;
}

/* --- BACKGROUNDS --- */
/* Main App Background */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
    /* Alternative colorful bg: */
    background: linear-gradient(to top, #fff1eb 0%, #ace0f9 100%);
}

/* Sidebar Background */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1A2980 0%, #c31432 100%); /* Wisteria to Red gradient */
    border-right: 1px solid rgba(255,255,255,0.1);
}

/* --- SIDEBAR STYLING --- */
.stSidebar h1 {
    color: #Ffffff !important;
    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}
.stSidebar p {
    color: black !important;
}
.stSidebar .stButton>button {
    background: rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(5px);
    color: #ffffff;
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 12px;
    padding: 12px 15px;
    text-align: left;
    width: 100%;
    margin-bottom: 8px;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    font-weight: 500;
}
.stSidebar .stButton>button:hover {
    background: linear-gradient(90deg, #FFD700, #FFA500);
    color: #240b36;
    font-weight: 700;
    box-shadow: 0 5px 15px rgba(255, 215, 0, 0.4);
    transform: translateX(5px) scale(1.02);
    border-color: transparent;
}

/* --- CHAT INTERFACE (WhatsApp Style) --- */
/* Remove old container limits */
.chat-wrapper {
    display: flex;
    flex-direction: column;
    padding-bottom: 150px; /* Space for sticky footer */
}

/* Bot Bubble */
.bot-bubble {
    background: linear-gradient(135deg, #ff9a9e 0%, #f3f4f6 100%);
    color: #333;
    padding: 15px 20px;
    border-radius: 24px 24px 24px 4px;
    margin: 12px 0;
    width: fit-content;
    max-width: 80%;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    border-left: 6px solid #4facfe;
    font-size: 16px;
    position: relative;
    animation: fadeIn 0.4s ease-out;
}

/* User Bubble */
.user-row {
    display: flex;
    justify-content: flex-end;
    margin: 12px 0;
}
.user-bubble {
    background: linear-gradient(135deg, #dda0dd 0%, #F7F1ED 100%);
    color: #1f2937;
    padding: 15px 20px;
    border-radius: 24px 24px 4px 24px;
    width: fit-content;
    max-width: 80%;
    box-shadow: 0 8px 20px rgba(118, 7239, 125, 0.3);
    font-size: 16px;
    text-align: left;
    animation: slideIn 0.4s ease-out;
}

@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@keyframes slideIn { from { opacity: 0; transform: translateX(20px); } to { opacity: 1; transform: translateX(0); } }

.timestamp { font-size: 11px; margin-top: 8px; display: block; opacity: 0.7; font-style: italic; }
.user-bubble .timestamp { color: #E0E7FF; text-align: right; }
.bot-bubble .timestamp { color: #666; }

/* --- STICKY FOOTER INPUT --- */
.sticky-footer-container {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    z-index: 1000;
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(15px);
    border-top: 1px solid rgba(255,255,255,0.5);
    padding: 20px 0;
    box-shadow: 0 -5px 20px rgba(0,0,0,0.05);
}
/* Adjust main content block to not overlap sidebar */
[data-testid="stSidebarNav"] { display: none; } /* Hide default nav if any */

/* Override Text Input for Sticky Footer */
.stTextInput input {
    border-radius: 30px !important;
    border: 2px solid #e0e0e0;
    padding: 12px 20px;
    transition: all 0.3s;
    background: white;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
}
.stTextInput input:focus {
    border-color: #764ba2;
    box-shadow: 0 0 0 3px rgba(118, 75, 162, 0.2);
}

/* --- CARDS & METRICS --- */
.account-card {
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.6);
    padding: 25px;
    border-radius: 20px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.05);
    margin-bottom: 20px;
    transition: transform 0.3s, box-shadow 0.3s;
    overflow: hidden;
    position: relative;
}
.account-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; width: 6px; height: 100%;
    background: linear-gradient(to bottom, #43e97b 0%, #38f9d7 100%);
}
.account-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
}

/* Hero Section */
.section-hero {
    background: linear-gradient(120deg, #c026 0%, #66a6ff 100%);
    padding: 40px;
    border-radius: 25px;
    box-shadow: 0 15px 35px rgba(102, 166, 255, 0.3);
    color: #1a2980;
    position: relative;
    overflow: hidden;
}

/* Buttons in Main Area */
div.stButton > button:first-child {
    background: linear-gradient(90deg, #00FFFF, #fecfcc);
    color: black;
    border: none;
    border-radius: 30px;
    padding: 10px 24px;
    font-weight: 600;
    box-shadow: 0 4px 15px rgba(17, 153, 142, 0.3);
    transition: all 0.3s ease;
}
div.stButton > button:first-child:hover {
    box-shadow: 0 8px 25px rgba(17, 153, 142, 0.5);
    transform: translateY(-2px);
}

/* --- DATAFRAME STYLING --- */
[data-testid="stDataFrame"] {
    background: white;
    border-radius: 15px;
    padding: 10px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.05);
}

</style>
""",
    unsafe_allow_html=True,
)

# -------------------------
# Auto-Scroll JavaScript (WhatsApp Style)
# -------------------------
# This script forces the window to scroll to the bottom whenever the page loads or updates
_AUTO_SCROLL_JS = """
<script>
    function scrollWindowDown() {
        // Scroll the main window to the bottom
        window.scrollTo({
            top: document.body.scrollHeight,
            behavior: 'smooth'
        });
        
        // Also try scrolling the main streamlit container just in case
        const mainContainer = window.parent.document.querySelector('.main .block-container');
        if (mainContainer) {
            mainContainer.scrollTop = mainContainer.scrollHeight;
        }
    }
    
    // Run on load
    setTimeout(scrollWindowDown, 300); // Slight delay to allow render
    
    // Observe DOM changes (new messages)
    const observer = new MutationObserver(() => {
        setTimeout(scrollWindowDown, 100);
    });
    observer.observe(document.body, { childList: true, subtree: true });
</script>
"""

# -------------------------
# Sidebar
# -------------------------
with st.sidebar:
    st.markdown("<h1 style='margin-bottom:0;'>🏦 Bankbot<span style='color:#FFD700;'>.</span></h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:13px; margin-bottom:30px; letter-spacing:1px; text-transform:uppercase;'>Premium Banking AI</p>", unsafe_allow_html=True)
    
    st.button("🏠 Dashboard Home", key="btn_home", on_click=set_page_no_rerun, args=("Home",))
    st.button("💬 Chatbot", key="btn_chat", on_click=set_page_no_rerun, args=("Chat",))
    st.button("💳 My Accounts", key="btn_accounts", on_click=set_page_no_rerun, args=("Accounts",))
    st.button("📜 Transactions", key="btn_tx", on_click=set_page_no_rerun, args=("Transactions",))
    st.button("🔐 Cards & Security", key="btn_cards", on_click=set_page_no_rerun, args=("Cards",))
    st.button("📈 Analytics", key="btn_dash", on_click=set_page_no_rerun, args=("Dashboard",))
    st.button("⚙ Admin Panel", key="btn_admin", on_click=set_page_no_rerun, args=("Admin",))

    st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
    if st.session_state.logged_in:
        st.markdown(
            f"""
            <div style='background:rgba(255,255,255,0.1); padding:15px; border-radius:12px; text-align:center;'>
                <div style='font-size:12px; color:#ddd;'>Logged in as</div>
                <div style='font-size:18px; font-weight:bold; color:white;'>{st.session_state.user}</div>
            </div>
            """, unsafe_allow_html=True
        )

# -------------------------
# Helpers
# -------------------------
def add_chat(role: str, text: str, indicator: str = "none"):
    st.session_state.chat_history.append((role, text, indicator, datetime.datetime.now()))

def render_chat():
    # We remove the fixed height container. Just a wrapper class.
    st.markdown("<div class='chat-wrapper'>", unsafe_allow_html=True)
    
    for role, text, indicator, ts in st.session_state.chat_history:
        safe_text = str(text).replace("<", "&lt;").replace(">", "&gt;")
        time_str = ts.strftime("%I:%M %p")
        
        if role == "bot":
            st.markdown(
                f"""
                <div class='bot-bubble'>
                    <div style='display:flex; align-items:center; margin-bottom:5px;'>
                        <span style='font-size:20px; margin-right:8px;'>🤖</span>
                        <strong style='color:#005bea;'>Bankbot</strong>
                    </div>
                    {safe_text}
                    <span class='timestamp'>{time_str}</span>
                </div>
                """, 
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div class='user-row'>
                    <div class='user-bubble'>
                        {safe_text}
                        <span class='timestamp'>{time_str}</span>
                    </div>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
    st.markdown("</div>", unsafe_allow_html=True)
    # Inject the scroll script
    st.components.v1.html(_AUTO_SCROLL_JS, height=0)

def transactions_to_dataframe(txns):
    if not txns:
        return pd.DataFrame(columns=["ID", "From", "To", "Amount", "Date", "Type"])
    rows = [list(t)[:6] for t in txns]
    df = pd.DataFrame(rows, columns=["ID", "From", "To", "Amount", "Date", "Type"])
    try:
        df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
        df["Amount"] = pd.to_numeric(df["Amount"], errors='coerce').fillna(0)
    except Exception:
        pass
    try:
        df["_ts"] = df["Date"].dt.round('S')
        group_cols = ["From", "To", "Amount", "_ts"]
        to_drop = []
        for _, grp in df.groupby(group_cols):
            types = set(grp["Type"].astype(str).str.lower().tolist())
            if "debit" in types and "credit" in types and len(grp) >= 2:
                credits = grp[grp["Type"].astype(str).str.lower() == "credit"].index.tolist()
                to_drop.extend(credits)
        if to_drop:
            df = df.drop(index=to_drop).reset_index(drop=True)
        df = df.drop(columns=["_ts"], errors='ignore')
    except Exception:
        pass
    return df

def get_account_card_info(account_no: str):
    try:
        conn = database_db.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT card_number, expiry FROM cards WHERE account_no=? ORDER BY id DESC LIMIT 1", (account_no,))
        crow = cur.fetchone()
        if crow:
            card_number, expiry = crow
            conn.close()
            return (card_number or "", "active", True)
        cur.execute("SELECT card_number, card_status FROM accounts WHERE account_no=?", (account_no,))
        row = cur.fetchone()
        conn.close()
        if row:
            card_number, card_status = row
            return (card_number or "", card_status or "active", bool(card_number))
    except Exception:
        pass
    return ("", "unknown", False)

# -------------------------
# Page Logic
# -------------------------

# --- HOME ---
if st.session_state.page == "Home":
    # Hero Section
    st.markdown("""
    <div class='section-hero'>
        <h1 style='color:black; font-size: 3rem; margin-bottom:10px;'>Welcome to Bankbot Chatbot</h1>
        <p style='font-size:1.2rem; opacity:0.9;'>Experience the future of banking with our AI-powered financial assistant.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if not st.session_state.logged_in:
        c1, c2, c3 = st.columns([1,1,1])
        with c2:
            st.info("👋 Please Login via the Chat tab to access your dashboard.")
            if st.button("Go to Login", use_container_width=True):
                 set_page_no_rerun("Chat")
                 try_rerun()
    else:
        st.markdown(f"<h2 style='color:#333;'>Overview for {st.session_state.user}</h2>", unsafe_allow_html=True)
        txns = bank_crud.list_transactions_for_user(st.session_state.user)
        df = transactions_to_dataframe(txns)
        
        # Styled Metrics
        m1, m2, m3 = st.columns(3)
        total_tx = len(df)
        credits = df[df["Type"].astype(str).str.lower() == "credit"]["Amount"].sum()
        debits = df[df["Type"].astype(str).str.lower() == "debit"]["Amount"].sum()
        
        def metric_card(title, val, color_grad):
            st.markdown(f"""
            <div style='background: {color_grad}; padding: 20px; border-radius: 15px; color: white; box-shadow: 0 10px 20px rgba(0,0,0,0.1); text-align: center;'>
                <div style='font-size: 14px; opacity: 0.8; text-transform: uppercase;'>{title}</div>
                <div style='font-size: 32px; font-weight: bold;'>{val}</div>
            </div>
            """, unsafe_allow_html=True)

        with m1: metric_card("Total Transactions", total_tx, "linear-gradient(135deg, #667eea 0%, #764ba2 100%)")
        with m2: metric_card("Total Inflow", f"₹{credits:,.0f}", "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)")
        with m3: metric_card("Total Outflow", f"₹{debits:,.0f}", "linear-gradient(135deg, #ff9a9e 0%, #fecfef 99%, #fecfef 100%)")

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Quick Actions")
        qa1, qa2, qa3, qa4 = st.columns(4)
        with qa1: 
            if st.button("💸 Transfer Money"): 
                set_page_no_rerun("Chat")
                try_rerun()
        with qa2: 
            if st.button("📊 View Analysis"):
                set_page_no_rerun("Dashboard")
                try_rerun()
        with qa3:
            if st.button("🔒 Block Card"):
                set_page_no_rerun("Cards")
                try_rerun()
        with qa4:
             if st.button("🧾 History"):
                set_page_no_rerun("Transactions")
                try_rerun()

# --- CHATBOT ---
elif st.session_state.page == "Chat":
    
    # Login Screen
    if not st.session_state.logged_in:
        st.markdown("<br><br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown(
                """
                <div style='background:white; padding:40px; border-radius:20px; box-shadow:0 20px 50px rgba(0,0,0,0.1); text-align:center;'>
                    <h2 style='color:#240b36;'>🔐 Secure Login</h2>
                    <p style='color:#666;'>Access your Bankbot account</p>
                </div>
                """, unsafe_allow_html=True
            )
            st.markdown("<br>", unsafe_allow_html=True)
            uname = st.text_input("Username", key="login_user")
            upwd = st.text_input("Password", type="password", key="login_pwd")
            if st.button("Authenticate & Enter", use_container_width=True):
                if bank_crud.verify_user_login(uname, upwd):
                    st.session_state.logged_in = True
                    st.session_state.user = uname
                    set_page_no_rerun("Chat")
                    try_rerun()
                else:
                    st.error("Invalid credentials")
        st.stop()

    # Initial Greeting
    if not st.session_state.chat_history:
        add_chat("bot", f"Hello {st.session_state.user}! I am Bankbot.How can I help you today", "none")

    # Render Chat (No fixed container, flows naturally)
    render_chat()

    # Pending Controls (Popups inline)
    pending = st.session_state.pending_control
    if pending:
        # Create a visually distinct card for required actions
        st.markdown("""
        <div style='background: #fff8e1; border-left: 5px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 8px;'>
            <strong style='color:#d39e00;'>⚠ Action Required:</strong> Please respond below.
        </div>
        """, unsafe_allow_html=True)
        
        ptype = pending.get("type")
        
        if ptype == "select_account":
            opts = pending.get("options", [])
            choice = st.selectbox("Select Account", ["-- Choose --"] + opts)
            if st.button("Confirm Selection"):
                if choice != "-- Choose --":
                    add_chat("user", choice)
                    resp = st.session_state.handler.handle_message(choice, current_user=st.session_state.user, from_control=True)
                    add_chat("bot", resp.get("message", ""), resp.get("indicator", "none"))
                    st.session_state.pending_control = None
                    try_rerun()
        
        elif ptype == "password":
            pin = st.text_input("Enter 4-Digit PIN", type="password")
            if st.button("Verify PIN"):
                add_chat("user", "") # Don't show PIN in chat history text clearly
                resp = st.session_state.handler.handle_message(pin, current_user=st.session_state.user, from_control=True)
                add_chat("bot", resp.get("message", ""), resp.get("indicator", "none"))
                st.session_state.pending_control = None
                try_rerun()
                
        elif ptype == "amount":
            amt = st.text_input("Enter Amount (₹)")
            if st.button("Confirm Amount"):
                add_chat("user", amt)
                resp = st.session_state.handler.handle_message(amt, current_user=st.session_state.user, from_control=True)
                add_chat("bot", resp.get("message", ""), resp.get("indicator", "none"))
                st.session_state.pending_control = None
                try_rerun()
                
        elif ptype == "confirm":
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Yes, Proceed", use_container_width=True):
                    add_chat("user", "yes")
                    resp = st.session_state.handler.handle_message("yes", current_user=st.session_state.user, from_control=True)
                    add_chat("bot", resp.get("message", ""), resp.get("indicator", "none"))
                    st.session_state.pending_control = None
                    try_rerun()
            with c2:
                if st.button("❌ No, Cancel", use_container_width=True):
                    add_chat("user", "no")
                    resp = st.session_state.handler.handle_message("no", current_user=st.session_state.user, from_control=True)
                    add_chat("bot", resp.get("message", ""), resp.get("indicator", "none"))
                    st.session_state.pending_control = None
                    try_rerun()
        
        # Add space so footer doesn't hide controls
        st.markdown("<div style='height: 150px;'></div>", unsafe_allow_html=True)
        st.stop()

    # --- STICKY FOOTER INPUT AREA ---
    # We use a container that is technically at the bottom of the script, 
    # but the CSS .sticky-footer-container pins it visually.
    
    # Placeholder to ensure content doesn't get hidden behind footer
    st.markdown("<div style='height: 120px;'></div>", unsafe_allow_html=True)

    footer_container = st.container()
    with footer_container:
        st.markdown('<div class="sticky-footer-container">', unsafe_allow_html=True)
        
        # We need a layout column inside the footer to center it nicely
        col_main, col_btn = st.columns([8, 1])
        
        with col_main:
            user_input = st.text_input(
                "Message", 
                key="input_text", 
                label_visibility="collapsed", 
                placeholder="Type a message to Bankbot..."
            )
            
        with col_btn:
            # We use a button. In Streamlit, this triggers a rerun.
            send_clicked = st.button("➤", key="send_btn", use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # Logic for handling input
    if send_clicked and user_input and user_input.strip():
        add_chat("user", user_input.strip())
        resp = st.session_state.handler.handle_message(user_input.strip(), current_user=st.session_state.user)
        add_chat("bot", resp.get("message", ""), resp.get("indicator", "none"))
        if resp.get("controls"):
            st.session_state.pending_control = resp["controls"]
        try_rerun()


# --- ACCOUNTS ---
elif st.session_state.page == "Accounts":
    st.markdown("<h2 style='color:#240b36;'>💳 Your Accounts</h2>", unsafe_allow_html=True)
    if not st.session_state.logged_in:
        st.warning("Please login to view accounts.")
    else:
        accs = bank_crud.list_user_accounts(st.session_state.user)
        if not accs:
            st.info("No accounts found.")
        else:
            for a in accs:
                acc_no, acc_name, acc_type, _ = a
                card_num, card_status, has_card = get_account_card_info(acc_no)
                masked_balance = "••••••"  # keep balances hidden
                
                # Visual logic
                status_color = "#10B981" if str(card_status).lower() in ("active","ok","1") else "#EF4444"
                card_label = f"Blocked" if str(card_status).lower() in ("blocked","0","deleted") else "Active"
                
                st.markdown(
                    f"""
                    <div class='account-card'>
                        <div style='display:flex; justify-content:space-between; align-items:start;'>
                            <div>
                                <h3 style='margin:0; color:#2c3e50; font-weight:800;'>{acc_name}</h3>
                                <span style='background:rgba(0,0,0,0.05); padding:4px 8px; border-radius:6px; font-size:12px; color:#555;'>{str(acc_type).upper()}</span>
                            </div>
                            <div style='text-align:right;'>
                                <div style='font-family:"Courier New", monospace; font-size:18px; letter-spacing:1px; color:#333; font-weight:bold;'>{acc_no}</div>
                            </div>
                        </div>
                        <hr style='border:0; border-top:1px dashed #ccc; margin:15px 0;'>
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <div>
                                <div style='font-size:12px; color:#888; text-transform:uppercase;'>Balance</div>
                                <div style='font-size:20px; font-weight:bold; color:#240b36;'>₹ {masked_balance}</div>
                            </div>
                            <div style='text-align:right;'>
                                <div style='font-size:12px; color:#888; text-transform:uppercase;'>Card Status</div>
                                <span style='background:{status_color}; color:white; padding:5px 12px; border-radius:12px; font-size:12px; font-weight:bold;'>{card_label}</span>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            st.caption("🔒 Balances are hidden for privacy. Ask Bankbot in the Chat to view balance.")

# --- TRANSACTIONS ---
elif st.session_state.page == "Transactions":
    st.markdown("<h2 style='color:#240b36;'>📜 Transaction History</h2>", unsafe_allow_html=True)
    if not st.session_state.logged_in:
        st.warning("Please login to view transactions.")
    else:
        txns = bank_crud.list_transactions_for_user(st.session_state.user)
        if not txns:
            st.info("No transactions found for this user.")
        else:
            df = transactions_to_dataframe(txns)
            if not df.empty and "Date" in df.columns:
                df["Date"] = df["Date"].dt.strftime('%Y-%m-%d %H:%M')

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Amount": st.column_config.NumberColumn(format="₹%d"),
                    "Type": st.column_config.TextColumn("Type"),
                    "Date": st.column_config.TextColumn("Timestamp"),
                }
            )

# --- CARDS ---
elif st.session_state.page == "Cards":
    st.markdown("<h2 style='color:#240b36;'>💳 Card Management</h2>", unsafe_allow_html=True)
    if not st.session_state.logged_in:
        st.warning("Please login.")
    else:
        st.markdown("""
        <div style='background:linear-gradient(90deg, #fdfbfb 0%, #ebedee 100%); padding:20px; border-radius:10px; border-left:5px solid #667eea; margin-bottom:20px;'>
            ℹ <b>Security Note:</b> Use the buttons below to instantly block cards. For PIN generation, please use the secure Chatbot.
        </div>
        """, unsafe_allow_html=True)
        
        accs = bank_crud.list_user_accounts(st.session_state.user)
        for a in accs:
            acc_no, acc_name, _, _ = a
            card_num, card_status, has_card = get_account_card_info(acc_no)
            
            with st.container():
                # Card UI imitation
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color:white; padding:25px; border-radius:15px; max-width:500px; box-shadow:0 10px 25px rgba(30, 60, 114, 0.4); margin-bottom:10px;'>
                    <div style='display:flex; justify-content:space-between;'>
                        <span style='font-size:18px; font-weight:bold;'>BANKBOT <span style='color:#FFD700'>GOLD</span></span>
                        <span>{acc_name}</span>
                    </div>
                    <div style='margin-top:25px; font-family:"Courier New", monospace; font-size:22px; letter-spacing:3px; text-shadow:0 2px 2px rgba(0,0,0,0.3);'>
                        {f"**** **** **** {str(card_num)[-4:]}" if card_num else "NO CARD LINKED"}
                    </div>
                    <div style='display:flex; justify-content:space-between; margin-top:20px; align-items:flex-end;'>
                        <div>
                            <div style='font-size:10px; opacity:0.8;'>VALID THRU</div>
                            <div>12/30</div>
                        </div>
                         <div style='font-size:14px; font-weight:bold; color: {"#4ade80" if str(card_status).lower() in ("active","ok") else "#f87171"};'>
                            {str(card_status).upper()}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2 = st.columns([1, 4])
                with c1:
                    if has_card:
                         if st.button(f"Block Card", key=f"block_{acc_no}"):
                            res = bank_crud.block_card_for_account(acc_no)
                            st.success(res)
                    else:
                        if st.button(f"➕ Issue Card", key=f"add_{acc_no}"):
                            bank_crud.add_card(acc_no, f"4000{acc_no[-4:]}", expiry="12/30")
                            st.success("Card added (demo). Refresh page.")
                
                st.markdown("---")

# --- DASHBOARD ---
elif st.session_state.page == "Dashboard":
    st.markdown("<h2 style='color:#240b36;'>📊 Financial Analytics</h2>", unsafe_allow_html=True)
    if not st.session_state.logged_in:
        st.warning("Please login.")
    else:
        txns = bank_crud.list_transactions_for_user(st.session_state.user)
        if not txns:
            st.info("No activity to analyze.")
        else:
            df = transactions_to_dataframe(txns)
            
            # Layout
            c_left, c_right = st.columns([2, 1])
            
            with c_left:
                st.subheader("Cash Flow Trend")
                if not df.empty and "Date" in df.columns:
                    chart_data = df.groupby(df["Date"].dt.date)["Amount"].sum().reset_index()
                    c = alt.Chart(chart_data).mark_area(
                        line={'color':'#764ba2'},
                        color=alt.Gradient(
                            gradient='linear',
                            stops=[alt.GradientStop(color='rgba(118, 75, 162, 0.5)', offset=0),
                                   alt.GradientStop(color='rgba(118, 75, 162, 0.0)', offset=1)],
                            x1=1, x2=1, y1=1, y2=0
                        )
                    ).encode(
                        x=alt.X('Date:T', axis=alt.Axis(format='%b %d', title='Date')),
                        y=alt.Y('Amount:Q', title='Volume (₹)'),
                        tooltip=['Date', 'Amount']
                    ).properties(height=350).configure_view(strokeWidth=0)
                    st.altair_chart(c, use_container_width=True)

            with c_right:
                st.subheader("Recent Activity")
                recent = df.sort_values("Date", ascending=False).head(4)
                for _, r in recent.iterrows():
                    typ = str(r["Type"]).upper()
                    amt = r["Amount"]
                    is_credit = "CREDIT" in typ
                    color = "#10B981" if is_credit else "#EF4444"
                    bg = "#ecfdf5" if is_credit else "#fef2f2"
                    icon = "💰" if is_credit else "💸"
                    
                    st.markdown(
                        f"""
                        <div style='background:{bg}; padding:12px; border-radius:12px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center; border:1px solid {color}33;'>
                            <div style='display:flex; align-items:center;'>
                                <span style='font-size:20px; margin-right:10px;'>{icon}</span>
                                <div>
                                    <div style='font-weight:bold; font-size:14px; color:#333;'>{typ}</div>
                                    <div style='font-size:11px; color:#666;'>{r['Date'].strftime('%d %b, %H:%M') if hasattr(r['Date'], 'strftime') else ''}</div>
                                </div>
                            </div>
                            <div style='color:{color}; font-weight:bold;'>{'u002B' if is_credit else '-'}₹{amt}</div>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
            
            st.markdown("---")
            st.subheader("Spending Analysis")
            col1, col2 = st.columns(2)
            
            with col1:
                # Pie chart for credits vs debits
                try:
                    pie_df = df.groupby(df["Type"].astype(str).str.title()).agg({"Amount":"sum"}).reset_index()
                    pie_df.columns = ["Type","Amount"]
                    pie = alt.Chart(pie_df).mark_arc(innerRadius=60, outerRadius=100).encode(
                        theta=alt.Theta(field="Amount", type="quantitative"),
                        color=alt.Color(field="Type", type="nominal", scale=alt.Scale(range=['#10B981','#EF4444']), legend=None),
                        tooltip=['Type','Amount']
                    ).properties(height=300)
                    st.altair_chart(pie, use_container_width=True)
                    st.caption("Green: Credit (In), Red: Debit (Out)")
                except Exception:
                    pass

            with col2:
                # Bar chart for top counterparties
                try:
                    accs = bank_crud.list_user_accounts(st.session_state.user)
                    acc_set = set([a[0] for a in accs])
                    def counterpart(row):
                        f = row.get('From') if isinstance(row, dict) else row['From']
                        t = row.get('To') if isinstance(row, dict) else row['To']
                        if f in acc_set and t not in acc_set: return t
                        if t in acc_set and f not in acc_set: return f
                        return t if f in acc_set else f

                    cp = df.copy()
                    cp['Counterparty'] = cp.apply(lambda r: counterpart(r), axis=1)
                    top_cp = cp.groupby('Counterparty')['Amount'].sum().abs().reset_index().sort_values('Amount', ascending=False).head(5)
                    
                    if not top_cp.empty:
                        bar = alt.Chart(top_cp).mark_bar(cornerRadius=5).encode(
                            x=alt.X('Amount:Q', title='Volume'),
                            y=alt.Y('Counterparty:N', sort='-x'),
                            color=alt.Color('Amount:Q', scale=alt.Scale(scheme='purples')),
                            tooltip=['Counterparty','Amount']
                        ).properties(height=300)
                        st.altair_chart(bar, use_container_width=True)
                except Exception:
                    pass

# --- ADMIN ---
elif st.session_state.page == "Admin":
    st.markdown("<h2 style='color:#240b36;'>⚙ Admin Terminal</h2>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown("<div style='background:white; padding:20px; border-radius:15px; box-shadow:0 5px 15px rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["👤 Create User", "🏦 Create Account"])
        
        with t1:
            c1, c2 = st.columns(2)
            with c1:
                nu = st.text_input("New Username")
            with c2:
                np = st.text_input("New Password", type="password")
            if st.button("Create User"):
                if nu and np:
                    bank_crud.create_user(nu, np)
                    st.success(f"User {nu} created.")
                else:
                    st.error("Missing fields.")
                    
        with t2:
            all_users = [u[0] for u in bank_crud.list_users()]
            sel_u = st.selectbox("Select User", ["--"] + all_users)
            aname = st.text_input("Account Name")
            atype = st.selectbox("Type", ["savings", "current"])
            abal = st.number_input("Opening Balance", value=0, step=500)
            apin = st.text_input("Set PIN (4 digits)")
            
            if st.button("Create Account"):
                if sel_u != "--" and aname and len(apin)==4:
                    count = len(bank_crud.list_user_accounts(sel_u))
                    acc_no = f"AC{100000 + count + 1}"
                    bank_crud.create_account(sel_u, acc_no, aname, atype, int(abal), apin)
                    st.success(f"Account {acc_no} created.")
                else:
                    st.error("Invalid input.")
        st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# Footer / Debug
# -------------------------
st.markdown("<div style='margin-bottom: 100px;'></div>", unsafe_allow_html=True)
if st.session_state.debug:
    st.json(st.session_state)