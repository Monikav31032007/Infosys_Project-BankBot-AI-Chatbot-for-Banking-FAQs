# dialogue_manager/dialogue_handler.py

from typing import Dict, Any, List, Optional
from nlu_engine.nlu_router import NLUProcessor
from database import bank_crud

CANCEL_WORDS = {"cancel", "abort", "stop", "exit"}
RESTART_WORDS = {"restart", "reset", "start over"}

# Confidence thresholds
INTENT_SWITCH_CONF_THRESHOLD = 0.80
UNKNOWN_CONF_THRESHOLD = 0.80 

BANK_INTENTS = {"transfer_money", "check_balance", "card_block", "find_atm"}

EXPLICIT_INTENT_PHRASES = {
    "transfer_money": {"transfer money", "send money"},
    "check_balance": {"check balance", "balance", "view balance"},
    "card_block": {"block card", "card block"},
    "find_atm": {"find atm", "nearest atm", "atm"},
}

# Lightweight domain lexicon to gate banking vs general questions
BANKING_LEXICON = {
    "transfer_money": {"transfer", "send", "pay", "to account", "recipient", "amount", "money"},
    "check_balance": {"balance", "view balance", "account balance", "how much", "available"},
    "card_block": {"block card", "card block", "block", "deactivate", "lost card", "stolen"},
    "find_atm": {"atm", "nearest atm", "cash machine", "cash withdrawal"},
}
# Patterns that strongly indicate general knowledge questions (force non-banking)
NON_BANK_QUESTION_PATTERNS = {"what is", "who is", "define", "explain", "how does", "difference between", "data scientist", "machine learning", "python", "programming"}

def _is_yes(s: str) -> bool:
    return s.strip().lower() in {"yes", "y", "confirm", "ok", "okay"}

def _valid_pin(pin: str) -> bool:
    return pin.isdigit() and len(pin) == 4

def _parse_amount(text: str) -> Optional[int]:
    t = text.strip().replace(",", "")
    try:
        return int(float(t))
    except Exception:
        return None

def _account_names_for_user(user_name: str) -> List[str]:
    accs = bank_crud.list_user_accounts(user_name)
    return [a[1] for a in accs]

def _resolve_account_by_name(user_name: str, account_name: str) -> Optional[str]:
    accs = bank_crud.list_user_accounts(user_name)
    for a in accs:
        if a[1].strip().lower() == account_name.strip().lower():
            return a[0]
    return None

def _account_name_by_number(acc_no: str) -> Optional[str]:
    acc = bank_crud.get_account(acc_no)
    if not acc:
        return None
    user = acc[1]
    accs = bank_crud.list_user_accounts(user)
    for a in accs:
        if a[0] == acc_no:
            return a[1]
    return None

def _text_has_any(text: str, phrases: set) -> bool:
    low = text.lower()
    return any(p in low for p in phrases)

def _is_banking_like(text: str, intent: Optional[str]) -> bool:
    # If an intent is proposed, check its lexicon; otherwise check any banking words
    low = text.lower()
    if intent in BANKING_LEXICON:
        return any(w in low for w in BANKING_LEXICON[intent])
    # Fallback: any lexicon word from any banking intent
    merged = set().union(*BANKING_LEXICON.values())
    return any(w in low for w in merged)

class DialogueHandler:
    def __init__(self):
        self.nlu = NLUProcessor()
        self.state: Dict[str, Any] = {"intent": None, "step": 0, "ctx": {}, "intent_lock": False}

    def reset(self):
        self.state = {"intent": None, "step": 0, "ctx": {}, "intent_lock": False}

    def handle_message(self, user_text: str, current_user: Optional[str] = None, from_control: bool = False) -> Dict[str, Any]:
        low = user_text.strip().lower()
        if low in CANCEL_WORDS:
            self.reset()
            return {"message": "🟡 Flow cancelled. What would you like to do next?", "indicator": "none", "end_flow": True}
        if low in RESTART_WORDS:
            self.reset()
            return {"message": "🔄 Flow restarted. Tell me what you want to do.", "indicator": "none", "end_flow": True}

        # Detect strongly general knowledge queries and force non-banking
        if not from_control and _text_has_any(low, NON_BANK_QUESTION_PATTERNS):
            self.reset()
            return {"message": "unknown", "indicator": "none", "end_flow": True}

        if not from_control:
            intent, confidence, entities = self.nlu.process(user_text)
            try:
                confidence = float(confidence)
            except Exception:
                confidence = 1.0
        else:
            intent, confidence, entities = self.state["intent"], 1.0, []


        is_supported_intent = intent in BANK_INTENTS
        looks_banking = _is_banking_like(user_text, intent)

        if (not is_supported_intent) or (confidence < UNKNOWN_CONF_THRESHOLD) or (not looks_banking and confidence < 0.95):
            self.reset()
            return {"message": "unknown", "indicator": "none", "end_flow": True}

        if not self.state["intent"]:
            return self._start_intent(intent, entities, current_user, confidence)

        if not from_control and not self.state["intent_lock"]:
            if intent and intent != self.state["intent"] and confidence >= INTENT_SWITCH_CONF_THRESHOLD:
                phrases = EXPLICIT_INTENT_PHRASES.get(intent, set())
                if any(p in low for p in phrases):
                    self.state["ctx"]["pending_switch"] = {"intent": intent, "confidence": confidence}
                    return {
                        "message": f"⚠ Switch to '{intent.replace('_',' ')}'? Type 'yes' to switch or continue current flow.",
                        "indicator": "none",
                        "end_flow": False,
                        "controls": None,
                    }

        pending = self.state["ctx"].get("pending_switch")
        if pending:
            if _is_yes(user_text):
                new_intent = pending["intent"]
                self.reset()
                self.state["intent"] = new_intent
                self.state["step"] = 1
                self.state["ctx"] = {}
                return self._start_intent(new_intent, [], current_user, pending["confidence"])
            else:
                self.state["ctx"].pop("pending_switch", None)
                return {"message": "👍 Continuing current flow.", "indicator": "none", "end_flow": False, "controls": None}

        return self._continue_intent(user_text, entities, current_user, from_control)

    # -------------------------
    # Start flows
    # -------------------------
    def _start_intent(self, intent: str, entities: List[Dict[str, Any]], current_user: Optional[str], confidence: float = 1.0) -> Dict[str, Any]:
        self.state["intent"] = intent
        self.state["step"] = 1
        self.state["ctx"] = {"entities": entities, "confidence": confidence}
        self.state["intent_lock"] = True 
        users = [u[0] for u in bank_crud.list_users()]

        if intent == "transfer_money":
            if current_user:
                self.state["ctx"]["sender_user"] = current_user
                self.state["step"] = 2
                options = _account_names_for_user(current_user)
                return {
                    "message": "📂 Which of your accounts do you want to transfer from? (select account name)",
                    "indicator": "thinking",
                    "end_flow": False,
                    "controls": {"type": "select_account", "field": "from_acc", "user": current_user, "options": options},
                }
            return {"message": f"📤 From which user’s account do you want to transfer? Users: {', '.join(users)}", "indicator": "thinking", "end_flow": False}

        if intent == "check_balance":
            if current_user:
                self.state["ctx"]["user"] = current_user
                self.state["step"] = 2
                options = _account_names_for_user(current_user)
                return {
                    "message": "📂 Which of your accounts do you want to check? (select account name)",
                    "indicator": "thinking",
                    "end_flow": False,
                    "controls": {"type": "select_account", "field": "account", "user": current_user, "options": options},
                }
            return {"message": f"👀 Which user’s account do you want to check? Users: {', '.join(users)}", "indicator": "thinking", "end_flow": False}

        if intent == "card_block":
            if current_user:
                self.state["ctx"]["user"] = current_user
                self.state["step"] = 2
                options = _account_names_for_user(current_user)
                return {
                    "message": "💳 Which of your accounts' card do you want to block? (select account name)",
                    "indicator": "thinking",
                    "end_flow": False,
                    "controls": {"type": "select_account", "field": "account", "user": current_user, "options": options},
                }
            return {"message": f"💳 For which user do you want to block a card? Users: {', '.join(users)}", "indicator": "thinking", "end_flow": False}

        if intent == "find_atm":
            self.reset()
            return {"message": "🏧 ATM lookup placeholder. We'll add maps later.", "indicator": "none", "end_flow": True}

        self.reset()
        return {"message": "unknown", "indicator": "none", "end_flow": True}

    # -------------------------
    # Continue flows
    # -------------------------
    def _continue_intent(self, user_text: str, entities: List[Dict[str, Any]], current_user: Optional[str], from_control: bool) -> Dict[str, Any]:
        intent = self.state["intent"]
        step = self.state["step"]

        if intent == "transfer_money":
            return self._flow_transfer(user_text, entities, step, current_user)
        if intent == "check_balance":
            return self._flow_balance(user_text, step, current_user)
        if intent == "card_block":
            return self._flow_card_block(user_text, step, current_user)

        self.reset()
        return {"message": "unknown", "indicator": "none", "end_flow": True}

    # -------------------------
    # Transfer pipeline
    # -------------------------
    def _flow_transfer(self, user_text: str, entities: List[Dict[str, Any]], step: int, current_user: Optional[str]) -> Dict[str, Any]:
        ctx = self.state["ctx"]

        if step == 1:
            sender_user = user_text.strip()
            if sender_user not in [u[0] for u in bank_crud.list_users()]:
                return {"message": "❌ Invalid user. Type a valid user name.", "indicator": "error", "end_flow": False}
            ctx["sender_user"] = sender_user
            self.state["step"] = 2
            options = _account_names_for_user(sender_user)
            return {"message": "📂 Which account (select account name)?", "indicator": "thinking", "end_flow": False, "controls": {"type": "select_account", "field": "from_acc", "user": sender_user, "options": options}}

        if step == 2:
            account_name = user_text.strip()
            acc_no = _resolve_account_by_name(ctx["sender_user"], account_name)
            if not acc_no:
                return {"message": "❌ Invalid account name. Choose from the dropdown.", "indicator": "error", "end_flow": False, "controls": {"type": "select_account", "field": "from_acc", "user": ctx["sender_user"], "options": _account_names_for_user(ctx["sender_user"])}}
            ctx["from_acc"] = acc_no
            ctx["from_acc_name"] = account_name
            self.state["step"] = 3
            users = [u[0] for u in bank_crud.list_users()]
            return {"message": f"👤 To which user’s account do you want to transfer? Users: {', '.join(users)}", "indicator": "thinking", "end_flow": False}

        if step == 3:
            recipient_user = user_text.strip()
            if recipient_user not in [u[0] for u in bank_crud.list_users()]:
                return {"message": "❌ Invalid recipient user. Type a valid user name.", "indicator": "error", "end_flow": False}
            ctx["recipient_user"] = recipient_user
            self.state["step"] = 4
            options = _account_names_for_user(recipient_user)
            return {"message": "📥 Which account (select account name)?", "indicator": "thinking", "end_flow": False, "controls": {"type": "select_account", "field": "to_acc", "user": recipient_user, "options": options}}

        if step == 4:
            account_name = user_text.strip()
            to_acc = _resolve_account_by_name(ctx["recipient_user"], account_name)
            if not to_acc:
                return {"message": "❌ Invalid recipient account name. Choose from the dropdown.", "indicator": "error", "end_flow": False, "controls": {"type": "select_account", "field": "to_acc", "user": ctx["recipient_user"], "options": _account_names_for_user(ctx["recipient_user"])}}
            if to_acc == ctx.get("from_acc"):
                return {"message": "❌ Sender and recipient cannot be the same account. Choose a different recipient.", "indicator": "error", "end_flow": False}
            ctx["to_acc"] = to_acc
            ctx["to_acc_name"] = account_name
            self.state["step"] = 5
            return {"message": "🔑 Enter your 4-digit password for the sender account.", "indicator": "thinking", "end_flow": False, "controls": {"type": "password", "field": "password"}}

        if step == 5:
            pwd = user_text.strip()
            if not _valid_pin(pwd):
                return {"message": "🔴 Password must be 4 digits. Try again.", "indicator": "error", "end_flow": False, "controls": {"type": "password", "field": "password"}}
            ok = bank_crud.verify_account_password(ctx["from_acc"], pwd)
            if not ok:
                return {"message": "🔴 Incorrect password. Try again or type 'cancel' to abort.", "indicator": "error", "end_flow": False, "controls": {"type": "password", "field": "password"}}
            ctx["password"] = pwd
            self.state["step"] = 6
            return {"message": "🟢 Password verified. How much do you want to transfer? (enter amount)", "indicator": "success", "end_flow": False, "controls": {"type": "amount", "field": "amount"}}

        if step == 6:
            amt = _parse_amount(user_text)
            if not amt or amt <= 0:
                return {"message": "❌ Invalid amount. Enter a positive number.", "indicator": "error", "end_flow": False, "controls": {"type": "amount", "field": "amount"}}
            ctx["amount"] = amt
            self.state["step"] = 7
            from_name = ctx.get("from_acc_name") or _account_name_by_number(ctx["from_acc"]) or ctx["from_acc"]
            to_name = ctx.get("to_acc_name") or _account_name_by_number(ctx["to_acc"]) or ctx["to_acc"]
            return {"message": f"⚠ Confirm transfer of ₹{amt} from '{from_name}' ({ctx['from_acc']}) to '{to_name}' ({ctx['to_acc']})? Type 'yes' to proceed.", "indicator": "none", "end_flow": False, "controls": {"type": "confirm", "field": "confirm"}}

        if step == 7:
            if not _is_yes(user_text):
                self.reset()
                return {"message": "🟡 Transfer cancelled.", "indicator": "none", "end_flow": True}
            res = bank_crud.transfer_money(ctx["from_acc"], ctx["to_acc"], int(ctx["amount"]), ctx["password"])
            indicator = "success" if res.startswith("✅") else "error"
            self.reset()
            return {"message": res, "indicator": indicator, "end_flow": True}

        self.reset()
        return {"message": "❌ Unexpected error. Restarting.", "indicator": "error", "end_flow": True}

    # -------------------------
    # Check balance pipeline
    # -------------------------
    def _flow_balance(self, user_text: str, step: int, current_user: Optional[str]) -> Dict[str, Any]:
        ctx = self.state["ctx"]

        if step == 1:
            user = user_text.strip()
            if user not in [u[0] for u in bank_crud.list_users()]:
                return {"message": "❌ Invalid user. Type a valid user name.", "indicator": "error", "end_flow": False}
            ctx["user"] = user
            self.state["step"] = 2
            options = _account_names_for_user(user)
            return {"message": "📂 Which account? (select account name)", "indicator": "thinking", "end_flow": False, "controls": {"type": "select_account", "field": "account", "user": user, "options": options}}

        if step == 2:
            account_name = user_text.strip()
            acc_no = _resolve_account_by_name(ctx["user"], account_name)
            if not acc_no:
                return {"message": "❌ Invalid account name. Choose from the dropdown.", "indicator": "error", "end_flow": False, "controls": {"type": "select_account", "field": "account", "user": ctx["user"], "options": _account_names_for_user(ctx["user"])}}
            ctx["account"] = acc_no
            ctx["account_name"] = account_name
            self.state["step"] = 3
            return {"message": "🔑 Enter your 4-digit password to view balance.", "indicator": "thinking", "end_flow": False, "controls": {"type": "password", "field": "password"}}

        if step == 3:
            pwd = user_text.strip()
            if not _valid_pin(pwd):
                return {"message": "🔴 Password must be 4 digits. Try again.", "indicator": "error", "end_flow": False, "controls": {"type": "password", "field": "password"}}
            ok = bank_crud.verify_account_password(ctx["account"], pwd)
            if not ok:
                return {"message": "🔴 Incorrect password. Try again or type 'cancel' to abort.", "indicator": "error", "end_flow": False, "controls": {"type": "password", "field": "password"}}
            self.state["step"] = 4
            acc_name = ctx.get("account_name") or _account_name_by_number(ctx["account"]) or ctx["account"]
            return {"message": f"⚠ Confirm viewing balance for account '{acc_name}' ({ctx['account']})? Type 'yes' to proceed.", "indicator": "none", "end_flow": False, "controls": {"type": "confirm", "field": "confirm"}}

        if step == 4:
            if not _is_yes(user_text):
                self.reset()
                return {"message": "🟡 Balance view cancelled.", "indicator": "none", "end_flow": True}
            acc = bank_crud.get_account(ctx["account"])
            acc_name = ctx.get("account_name") or _account_name_by_number(ctx["account"]) or acc[0]
            balance = acc[3]
            self.reset()
            return {"message": f"🟢 Balance for '{acc_name}': ₹{balance}", "indicator": "success", "end_flow": True}

        self.reset()
        return {"message": "❌ Unexpected error. Restarting.", "indicator": "error", "end_flow": True}

    # -------------------------
    # Card block pipeline
    # -------------------------
    def _flow_card_block(self, user_text: str, step: int, current_user: Optional[str]) -> Dict[str, Any]:
        ctx = self.state["ctx"]

        if step == 1:
            user = user_text.strip()
            if user not in [u[0] for u in bank_crud.list_users()]:
                return {"message": "❌ Invalid user. Type a valid user name.", "indicator": "error", "end_flow": False}
            ctx["user"] = user
            self.state["step"] = 2
            options = _account_names_for_user(user)
            return {"message": "💳 Which account’s card do you want to block? (select account name)", "indicator": "thinking", "end_flow": False, "controls": {"type": "select_account", "field": "account", "user": user, "options": options}}

        if step == 2:
            account_name = user_text.strip()
            acc_no = _resolve_account_by_name(ctx["user"], account_name)
            if not acc_no:
                return {"message": "❌ Invalid account name. Choose from the dropdown.", "indicator": "error", "end_flow": False, "controls": {"type": "select_account", "field": "account", "user": ctx["user"], "options": _account_names_for_user(ctx["user"])}}
            ctx["account"] = acc_no
            ctx["account_name"] = account_name
            self.state["step"] = 3
            return {"message": "🔑 Enter your 4-digit password to confirm card block.", "indicator": "thinking", "end_flow": False, "controls": {"type": "password", "field": "password"}}

        if step == 3:
            pwd = user_text.strip()
            if not _valid_pin(pwd):
                return {"message": "🔴 Password must be 4 digits. Try again.", "indicator": "error", "end_flow": False, "controls": {"type": "password", "field": "password"}}
            ok = bank_crud.verify_account_password(ctx["account"], pwd)
            if not ok:
                return {"message": "🔴 Incorrect password. Try again or type 'cancel' to abort.", "indicator": "error", "end_flow": False, "controls": {"type": "password", "field": "password"}}
            self.state["step"] = 4
            acc_name = ctx.get("account_name") or _account_name_by_number(ctx["account"]) or ctx["account"]
            return {"message": f"⚠ Confirm blocking the card linked to account '{acc_name}' ({ctx['account']})? Type 'yes' to proceed.", "indicator": "none", "end_flow": False, "controls": {"type": "confirm", "field": "confirm"}}

        if step == 4:
            if not _is_yes(user_text):
                self.reset()
                return {"message": "🟡 Card block cancelled.", "indicator": "none", "end_flow": True}
            res = bank_crud.block_card_for_account(ctx["account"])
            indicator = "success" if res.startswith("✅") else "error"
            self.reset()
            return {"message": res, "indicator": indicator, "end_flow": True}

        self.reset()
        return {"message": "❌ Unexpected error. Restarting.", "indicator": "error", "end_flow": True}