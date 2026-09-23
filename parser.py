
import re
import fitz  # PyMuPDF
from PIL import Image
import pytesseract

# Libellés connus servant uniquement de secours.
ZONES_CONNNUES = [
    "Orchestre",
    "Corbeille",
    "1er Balcon",
    "2ème Balcon",
    "Amphithéâtre Bas",
    "Amphithéâtre Haut",
]


def _zone_exacte(texte):
    """
    Récupère le libellé exact de la zone imprimé sur le billet.
    Exemple :
        Corbeille
        1er Balcon
        2ème Balcon
        Orchestre
        Amphithéâtre Bas
    """

    lignes = [l.strip() for l in texte.splitlines() if l.strip()]

    # Sur les billets SecuTix, le nom de la zone se trouve
    # juste après la catégorie (Catégorie 1, GRATUIT, etc.).
    for i, ligne in enumerate(lignes):
        if "catégorie" in ligne.lower() or "gratuit" in ligne.lower():
            if i + 1 < len(lignes):
                return lignes[i + 1]

    # Secours : recherche de libellés connus
    t = texte.lower()
    t = (t.replace("é", "e")
           .replace("è", "e")
           .replace("ê", "e"))

    for zone in ZONES_CONNNUES:
        z = zone.lower().replace("é", "e").replace("è", "e")
        if z in t:
            return zone

    return "Inconnu"


def _extraire(texte):
    zone = _zone_exacte(texte)

    m = re.search(
        r"Porte\s+Rang\s+Num[ée]ro\s+(\d+)\s+([A-Z])\s+(\d+)",
        texte,
        re.IGNORECASE,
    )

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
        "zone": zone,
        "porte": porte,
        "rang": rang,
        "place": place,
    }


def lire_billet(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc[0]

    texte = page.get_text("text")
    info = _extraire(texte)

    if info:
        return info

    # OCR uniquement en secours
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    texte = pytesseract.image_to_string(
        image,
        lang="fra+eng",
        config="--psm 6"
    )

    return _extraire(texte)
