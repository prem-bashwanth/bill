# app/lineitem_extractor.py
import re
from typing import List, Dict, Any

NUM_RE = re.compile(r"[+-]?\d+(?:\.\d+)?")

DATE_RE = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b")
TIME_RE = re.compile(r"\b\d{1,2}:\d{2}\b")

def is_valid_number(x):
    try:
        float(x)
        return True
    except:
        return False

def parse_num(x):
    try:
        return float(x.replace(",", ""))
    except:
        return None

def group_rows(words: List[dict], y_tol=12):
    words = sorted(words, key=lambda w: w["cy"])
    rows = []
    for w in words:
        placed = False
        for r in rows:
            if abs(r["cy"] - w["cy"]) < y_tol:
                r["words"].append(w)
                r["cy"] = sum(x["cy"] for x in r["words"]) / len(r["words"])
                placed = True
                break
        if not placed:
            rows.append({"cy": w["cy"], "words": [w]})
    for r in rows:
        r["words"] = sorted(r["words"], key=lambda w: w["left"])
    return rows


def clean_text(s):
    return s.replace("”", "").replace("“", "").replace("\"", "").strip()


def extract_items_from_page(words: List[dict]) -> List[Dict[str, Any]]:
    rows = group_rows(words)
    output = []

    for row in rows:
        texts = [w["text"] for w in row["words"]]
        line = " ".join(texts).strip()

        # Remove lines that are clearly dates or times
        if DATE_RE.search(line) or TIME_RE.search(line):
            continue
        
        # Extract numeric tokens
        numeric_tokens = [t for t in texts if is_valid_number(t.replace(",", ""))]

        # We need at least qty, rate, amount → minimum 2 numbers
        if len(numeric_tokens) < 2:
            continue

        # Last number must be amount
        amount = parse_num(numeric_tokens[-1])
        if amount is None or amount <= 0:
            continue
        
        # Filter unrealistic amounts
        if amount > 50000:
            continue

        # Try to assign rate and quantity
        rate = parse_num(numeric_tokens[-2]) if len(numeric_tokens) >= 2 else None
        qty = parse_num(numeric_tokens[-3]) if len(numeric_tokens) >= 3 else None

        # Remove garbage quantities/rates
        if qty and qty > 100:
            qty = None
        if rate and rate > 100000:
            rate = None

        # Amount consistency check (if qty & rate exists)
        if qty and rate:
            if abs((qty * rate) - amount) > (0.20 * amount):  # 20% tolerance
                continue

        # Extract name (tokens before numbers)
        first_num_index = 0
        for i, t in enumerate(texts):
            if is_valid_number(t.replace(",", "")):
                first_num_index = i
                break

        name_tokens = texts[:first_num_index]
        name = clean_text(" ".join(name_tokens))

        # Ignore garbage names
        if len(name) < 2:
            continue
        if name.lower() in ["inr", "pm", "am", "dr", "mr", "ms"]:
            continue
        if name.isdigit():
            continue

        item = {
            "item_name": name,
            "item_amount": float(amount),
            "item_rate": float(rate) if rate else None,
            "item_quantity": float(qty) if qty else None
        }

        output.append(item)

    # Dedupe
    seen = set()
    unique_items = []
    for it in output:
        key = (it["item_name"].lower(), round(it["item_amount"], 2))
        if key not in seen:
            seen.add(key)
            unique_items.append(it)

    return unique_items
