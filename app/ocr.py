# app/ocr.py
from typing import List
from PIL import Image
import io
import numpy as np
import pytesseract
from pdf2image import convert_from_bytes
import cv2

from app.utils import detect_file_type_from_bytes

def get_images_from_bytes(file_bytes: bytes, dpi: int = 300) -> List[Image.Image]:
    """
    Convert file bytes into a list of PIL.Image pages (RGB).
    """
    ftype = detect_file_type_from_bytes(file_bytes)
    if ftype == "pdf":
        images = convert_from_bytes(file_bytes, dpi=dpi)
        return [img.convert("RGB") for img in images]
    elif ftype == "image":
        img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        return [img]
    else:
        # fallback try open as image
        img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        return [img]

def pil_to_cv2(img: Image.Image):
    arr = np.array(img)
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

def cv2_to_pil(arr) -> Image.Image:
    rgb = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)

def preprocess_image(img: Image.Image,
                     resize_height: int = 1600,
                     denoise: bool = True,
                     binarize: bool = True,
                     deskew: bool = True) -> Image.Image:
    """
    Preprocess to improve OCR.
    Returns PIL Image (L mode if binarized).
    """
    w, h = img.size
    if h != resize_height:
        new_w = int((resize_height / float(h)) * w)
        img = img.resize((new_w, resize_height), Image.LANCZOS)
    img_cv = pil_to_cv2(img)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    if deskew:
        coords = np.column_stack(np.where(gray > gray.mean()))
        if coords.size > 0:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            if abs(angle) > 0.1:
                (h_g, w_g) = gray.shape[:2]
                center = (w_g // 2, h_g // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                gray = cv2.warpAffine(gray, M, (w_g, h_g),
                                      flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    if denoise:
        gray = cv2.fastNlMeansDenoising(gray, h=10)
    if binarize:
        gray = cv2.adaptiveThreshold(gray, 255,
                                     cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 31, 10)
    pil_out = Image.fromarray(gray)
    if pil_out.mode != "L":
        pil_out = pil_out.convert("L")
    return pil_out

def ocr_words(image: Image.Image, lang: str = "eng") -> list:
    """
    Use pytesseract to extract word-level tokens with bounding boxes.
    Returns list of dicts: text, left, top, width, height, conf, cx, cy
    """
    data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
    words = []
    n = len(data.get("text", []))
    for i in range(n):
        txt = (data.get("text")[i] or "").strip()
        if not txt:
            continue
        try:
            conf = float(data.get("conf")[i])
        except Exception:
            conf = -1.0
        left = int(data.get("left")[i])
        top = int(data.get("top")[i])
        width = int(data.get("width")[i])
        height = int(data.get("height")[i])
        words.append({
            "text": txt,
            "left": left,
            "top": top,
            "width": width,
            "height": height,
            "conf": conf,
            "cx": left + width / 2.0,
            "cy": top + height / 2.0
        })
    return words
