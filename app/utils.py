# app/utils.py
import requests
import imghdr
import io

class DownloadError(Exception):
    pass

def download_file_bytes(url: str, timeout: int = 30) -> bytes:
    """
    Download a file from a URL and return its bytes.
    Raises DownloadError on failure.
    """
    headers = {
        "User-Agent": "bill-extractor/1.0"
    }
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
    except requests.RequestException as e:
        raise DownloadError(f"Failed to download file: {e}")
    content = r.content
    if not content:
        raise DownloadError("Downloaded file is empty")
    return content

def detect_file_type_from_bytes(b: bytes) -> str:
    """
    Return 'pdf' or 'image' or 'unknown'
    """
    if len(b) >= 4 and b[:4] == b'%PDF':
        return "pdf"
    img_type = imghdr.what(None, h=b)
    if img_type:
        return "image"
    return "unknown"

def save_bytes_to_file(b: bytes, path: str):
    with open(path, "wb") as f:
        f.write(b)
