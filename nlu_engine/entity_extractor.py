# nlu_engine/entity_extractor.py
import re
import json
import os


class EntityExtractor:
    def __init__(self, entities_file="nlu_engine/entities.json"):
        self.patterns = []
        self.regex_patterns = []

        if os.path.exists(entities_file):
            with open(entities_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.patterns = data.get("patterns", [])

            for rp in data.get("regex_patterns", []):
                flags = re.IGNORECASE if str(rp.get("flags", "")).lower() == "i" else 0
                self.regex_patterns.append({
                    "label": rp["label"],
                    "pattern": re.compile(rp["pattern"], flags)
                })

        self.used_spans = []

    # -----------------------
    # Avoid overlapping spans
    # -----------------------
    def _reserve(self, start, end):
        for s, e in self.used_spans:
            if not (end <= s or start >= e):
                return False
        self.used_spans.append((start, end))
        return True

    # -----------------------
    # Normalize values
    # -----------------------
    def _normalize_amount(self, value):
        value = value.replace(",", "").strip()
        if value.lower().endswith("k"):
            return str(int(float(value[:-1]) * 1000))
        return value

    # -----------------------
    # Main extraction
    # -----------------------
    def extract(self, text):
        self.used_spans = []
        results = []

        text = str(text)
        lower = text.lower()

        # ✅ 1. REGEX FIRST 
        for rp in self.regex_patterns:
            label = rp["label"]
            pattern = rp["pattern"]

            for match in pattern.finditer(text):
                start, end = match.span()
                if not self._reserve(start, end):
                    continue

                value = match.group(1) if match.groups() else match.group()

                if label == "AMOUNT":
                    value = self._normalize_amount(value)

                results.append({
                    "entity": label,
                    "value": value,
                    "start": start,
                    "end": end
                })

        # ✅ 2. TOKEN-BASED TYPES
        for p in self.patterns:
            label = p["label"]
            keyword = p["pattern"][0]["LOWER"]

            for m in re.finditer(rf"\b{keyword}\b", lower):
                if self._reserve(m.start(), m.end()):
                    results.append({
                        "entity": label,
                        "value": text[m.start():m.end()],
                        "start": m.start(),
                        "end": m.end()
                    })

        return results


# -----------------------
# Wrapper
# -----------------------
def extract(text):
    return EntityExtractor().extract(text)


# -----------------------
# Manual test
# -----------------------
if __name__ == "__main__":
    ee = EntityExtractor()

    tests = [
        "Move funds to account ending 4321",
        "Block card number ending 4321",
        "Transfer 5k from my savings",
        "Pay 4500 to account 99887766",
        "Get balance for account ending 1234",
        "Where is the nearest ATM?"
    ]

    for t in tests:
        print("\nTEXT:", t)
        print(ee.extract(t))