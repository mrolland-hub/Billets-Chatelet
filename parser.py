
import re
import fitz  # PyMuPDF
from PIL import Image
import pytesseract

ETAGES = [
    "Orchestre",
    "Corbeille",
    "Balcon",
    "Amphithéâtre Bas",
    "Amphithéâtre Haut"
]

def _normaliser_etage(texte):
    t = texte.lower().replace("é", "e").replace("è", "e")

    if "amphitheatre bas" in t:
        return "Amphithéâtre Bas"

    if "amphitheatre haut" in t:
        return "Amphithéâtre Haut"

    if "orchestre" in t:
        return "Orchestre"

    if "corbeille" in t:
        return "Corbeille"

    if "balcon" in t:
        return "Balcon"

    return "Inconnu"


def _extraire(texte):
    etage = _normaliser_etage(texte)

    # Cas normal SecuTix
    m = re.search(
        r"Porte\s+Rang\s+Num[ée]ro\s+(\d+)\s+([A-Z])\s+(\d+)",
        texte,
        re.IGNORECASE,
    )

    # Cas OCR
    if not m:
        m = re.search(
            r"(\d+)\s+([A-Z])\s+(\d+)\s+[- ]*CONTROLE",
            texte,
            re.IGNORECASE,
        )

    if not m:
        return None

    porte, rang, place = m.groups()

    return {
        "etage": etage,
        "porte": porte,
        "rang": rang,
        "place": place,
    }


def lire_billet(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc[0]

    # Lecture directe du texte
    texte = page.get_text("text")
    info = _extraire(texte)

    if info:
        return info

    # Secours OCR
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    texte = pytesseract.image_to_string(
        image,
        lang="fra+eng",
        config="--psm 6"
    )

    return _extraire(texte)
