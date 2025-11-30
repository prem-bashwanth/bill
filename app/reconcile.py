# app/reconcile.py
from typing import List, Dict, Any
import re

TOTAL_KEYS = ["total", "grand total", "amount payable", "net payable", "balance"]

def compute_final_total(unique_items: List[Dict[str, Any]]) -> float:
    return round(sum([float(it['item_amount']) for it in unique_items]), 2)

def find_totals_in_text(words: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Search tokens for lines that contain keywords like 'subtotal' or 'total' and a numeric value.
    Returns mapping keyword->value for first hits.
    """
    text_rows = {}
    # build simple lines by grouping tokens by similar cy
    if not words:
        return {}
    # group by cy (rudimentary)
    rows = {}
    for w in words:
        key = int(w['cy'] // 10)
        rows.setdefault(key, []).append(w)
    found = {}
    for _, toks in rows.items():
        line_text = " ".join([t['text'] for t in sorted(toks, key=lambda x: x['left'])])
        lower = line_text.lower()
        for k in TOTAL_KEYS + ["subtotal", "sub total", "sub-total"]:
            if k in lower:
                # find numeric in line
                m = re.findall(r'[-+]?[0-9]+(?:[,\.][0-9]{1,2})*', line_text)
                if m:
                    # pick last numeric token
                    val = m[-1].replace(',', '')
                    try:
                        found[k] = float(val)
                    except:
                        pass
    return found
