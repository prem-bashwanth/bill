# app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any
from app.utils import download_file_bytes
from app.ocr import get_images_from_bytes, preprocess_image, ocr_words
from app.lineitem_extractor import extract_items_from_page
from app.reconcile import compute_final_total, find_totals_in_text

app = FastAPI(title="Bill Extractor API")

class Req(BaseModel):
    document: str

@app.post("/extract-bill-data")
async def extract_bill_data(req: Req):
    # Download
    try:
        content = download_file_bytes(req.document)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not download document: {e}")

    # Convert to pages
    try:
        pages = get_images_from_bytes(content, dpi=300)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not process document into pages: {e}")

    pagewise_line_items = []
    all_items = []
    all_words = []  # for totals search
    for pno, pg in enumerate(pages, start=1):
        try:
            pre = preprocess_image(pg, resize_height=1500)
        except Exception:
            pre = pg
        words = ocr_words(pre)
        print("===== OCR PAGE", pno, "=====")
        for w in words:
            print(w["text"], end=" ")
        print("\n============================")

        
        all_words.extend(words)
        items = extract_items_from_page(words)
        # attach page-level items
        page_obj = {
            "page_no": str(pno),
            "page_type": "Bill Detail",
            "bill_items": []
        }
        for it in items:
            # map None to null in JSON automatically
            page_obj["bill_items"].append({
                "item_name": it["item_name"],
                "item_amount": float(it["item_amount"]),
                "item_rate": float(it["item_rate"]) if it.get("item_rate") is not None else None,
                "item_quantity": float(it["item_quantity"]) if it.get("item_quantity") is not None else None
            })
        pagewise_line_items.append(page_obj)
        all_items.extend(items)

    # deduplicate across pages (exact heuristic)
    unique = []
    seen = set()
    for it in all_items:
        key = (it['item_name'].strip().lower(), round(float(it['item_amount']), 2))
        if key in seen:
            continue
        seen.add(key)
        unique.append(it)

    final_total = compute_final_total(unique)
    totals_found = find_totals_in_text(all_words)

    response = {
        "is_success": True,
        "token_usage": {
            "total_tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0
        },
        "data": {
            "pagewise_line_items": pagewise_line_items,
            "total_item_count": len(unique),
            "final_total_extracted": float(final_total),
            "totals_detected_in_text": totals_found
        }
    }
    return response
