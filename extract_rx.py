import json, os, sys, re, logging, traceback
from pathlib import Path

# ── Third-party deps ─────────────────────────────────────────────────────────
import cv2
import pytesseract
import numpy as np
from symspellpy import SymSpell, Verbosity

try:
    from pdf2image import convert_from_path     # needs poppler-utils
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

# ── Configuration ────────────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).parent
FREQ_DICT = BASE_DIR / "dictionary/pharmacy_dict.txt"
MED_DICT  = BASE_DIR / "dictionary/medicine_names.txt"

# ── Helpers ──────────────────────────────────────────────────────────────────
def _init_symspell() -> SymSpell:
    sym = SymSpell(max_dictionary_edit_distance=1, prefix_length=7)
    sym.load_dictionary(str(FREQ_DICT), term_index=0, count_index=1)
    return sym

def _load_med_dict() -> set[str]:
    try:
        with open(MED_DICT, encoding="utf8") as f:
            return {ln.strip().lower() for ln in f if ln.strip()}
    except FileNotFoundError:
        return set()

def _pdf_to_gray(path: str) -> np.ndarray:
    if not HAS_PDF:
        raise RuntimeError("pdf2image not installed")
    pages = convert_from_path(path, first_page=1, last_page=1)
    if not pages:
        raise RuntimeError("Empty PDF")
    img_rgb = np.array(pages[0])
    return cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)

def _load_gray(path: str) -> np.ndarray:
    if path.lower().endswith(".pdf"):
        return _pdf_to_gray(path)
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise RuntimeError(f"Could not read file: {path}")
    return img

def _preprocess(path: str) -> np.ndarray:
    gray = _load_gray(path)
    blur = cv2.medianBlur(gray, 3)
    _, bw = cv2.threshold(
        blur, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    return bw

def _ocr(img: np.ndarray) -> str:
    return pytesseract.image_to_string(img, config="--oem 1 --psm 6")

def _correct(text: str, sym: SymSpell) -> str:
    tokens = re.findall(r"\w+|\W+", text)
    out    = []
    unit_re = re.compile(r"\d*\s*(?:mg|g|ml)", re.I)
    for t in tokens:
        if unit_re.fullmatch(t):
            out.append(t)              # leave units untouched
        elif t.isalpha():
            guess = sym.lookup(t, Verbosity.CLOSEST, max_edit_distance=1)
            out.append(guess[0].term if guess else t)
        else:
            out.append(t)
    return "".join(out)

def process_image(path: str) -> dict:
    """Main pipeline used by both CLI & Electron."""
    img   = _preprocess(path)
    raw   = _ocr(img)
    corr  = _correct(raw, _init_symspell())
    meds  = _load_med_dict()

    # *For now* we only surface the plain text – keeps UI unchanged.
    # Feel free to add meds/dose parsing later; UI will ignore extras.
    return {"text": corr.strip()}

# ── CLI entrypoint: *always* emit ONE JSON line ──────────────────────────────
def _emit(obj: dict):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    sys.stdout.flush()

if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            raise RuntimeError("Usage: extract_rx.py <imageOrPdfPath>")
        _emit(process_image(sys.argv[1]))
    except Exception as e:
        _emit({"error": str(e), "trace": traceback.format_exc()})
        sys.exit(2)