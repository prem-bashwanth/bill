import requests
from PIL import Image
from io import BytesIO


def download_file_bytes(url: str) -> bytes:
    """
    Download a file (PDF or Image) from a URL and return bytes.
    """
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    return response.content


def is_image_file(file_bytes: bytes) -> bool:
    """
    Detect whether downloaded bytes represent an image.
    Uses Pillow, works in Python 3.10–3.13+
    """
    try:
        Image.open(BytesIO(file_bytes))
        return True
    except Exception:
        return False


def save_temp_file(file_bytes: bytes, filename: str) -> str:
    """
    Save downloaded file bytes to a temporary file.
    Used for OCR / PDF processing.
    """
    import os
    temp_path = f"/tmp/{filename}"
    with open(temp_path, "wb") as f:
        f.write(file_bytes)
    return temp_path
