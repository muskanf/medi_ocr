# ── Locate bundled Tesseract at runtime ─────────────────────────────────────
import sys, os, pytesseract
import re, traceback, json
from pathlib import Path

def _find_tessdir() -> Path:
    """
    Returns Path to windows_tesseract no matter how the binary is launched.
    • dev  -> repo_root/windows_tesseract
    • prod -> .../resources/windows_tesseract          (copied by Forge hook)
    • rare -> inside _MEIPASS if we ever bundle it into the exe
    """
    # 1) during development (`python extract_rx.py …`)
    here = Path(__file__).resolve().parent / "windows_tesseract"
    if here.exists():
        return here

    # 2) packaged: ocr_core.exe lives in resources/python_dist/
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent    # …/python_dist
        cand    = exe_dir.parent / "windows_tesseract"     # …/resources/…
        if cand.exists():
            return cand

        # 3) fallback: inside the PyInstaller temp dir (_MEIPASS)
        mei = Path(getattr(sys, "_MEIPASS", ""))
        if (mei / "windows_tesseract").exists():
            return mei / "windows_tesseract"

    raise FileNotFoundError("windows_tesseract folder not found")

def _find_dictdir() -> Path:
    here = Path(__file__).resolve().parent / "dictionary"
    if here.exists():
        return here
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent      # …\python_dist
        cand    = exe_dir.parent / "dictionary"              # …\resources
        if cand.exists():
            return cand
        mei = Path(getattr(sys, "_MEIPASS", ""))
        if (mei / "dictionary").exists():
            return mei / "dictionary"
    raise FileNotFoundError("dictionary folder not found")


_TESS_DIR = _find_tessdir()
pytesseract.pytesseract.tesseract_cmd = _TESS_DIR / "tesseract.exe"
os.environ["TESSDATA_PREFIX"]        = str(_TESS_DIR / "tessdata")
# ────────────────────────────────────────────────────────────────────────────


import cv2
import numpy as np
from symspellpy import SymSpell, Verbosity

try:
    from pdf2image import convert_from_path     # needs poppler-utils
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

# ── Configuration ────────────────────────────────────────────────────────────
DICT_DIR  = _find_dictdir()
FREQ_DICT = DICT_DIR / "pharmacy_dict.txt"
MED_DICT  = DICT_DIR / "medicine_names.txt"

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