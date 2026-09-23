
import re
import fitz  # PyMuPDF


def _extraire_zone(texte):
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

    for i, ligne in enumerate(lignes):
        l = ligne.lower()
        if "catégorie" in l or "gratuit" in l:
            if i + 1 < len(lignes):
                return lignes[i + 1]

    return "Inconnu"


def lire_billet(pdf_path):
    doc = fitz.open(pdf_path)
    texte = doc[0].get_text("text")

    zone = _extraire_zone(texte)

    m = re.search(
        r"Porte\s+Rang\s+Num[ée]ro\s+(\d+)\s+([A-Z])\s+(\d+)",
        texte,
        re.IGNORECASE,
    )

    if not m:
        raise ValueError("Impossible de trouver Porte/Rang/Place.")

    porte, rang, place = m.groups()

    return {
        "zone": zone,
        "porte": porte,
        "rang": rang,
        "place": place,
    }
