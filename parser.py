import re
import fitz  # PyMuPDF


def _extraire_zone(page):
    """
    Extrait la zone (Corbeille, 1er Balcon, etc.) en utilisant
    la position des blocs de texte sur la page.
    """

    blocs = page.get_text("blocks")

    candidats = []

    for bloc in blocs:
        x0, y0, x1, y1, texte = bloc[:5]

        texte = " ".join(texte.split()).strip()

        if not texte:
            continue

        # Bande verticale où apparaît la zone sur les billets SecuTix.
        if 150 <= y0 <= 280:

            # On élimine les textes techniques.
            if texte.lower().startswith("porte rang"):
                continue

            if texte.lower() == "grande salle":
                continue

            if "catégorie" in texte.lower():
                continue

            if "gratuit" in texte.lower():
                continue

            candidats.append((y0, texte))

    if not candidats:
        raise ValueError("Zone introuvable.")

    # On prend le candidat le plus bas dans cette bande,
    # ce qui correspond au libellé de zone.
    candidats.sort(key=lambda c: c[0])

    return candidats[-1][1]


def lire_billet(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc[0]

    texte = page.get_text("text")
    zone = _extraire_zone(page)

    m = re.search(
        r"Porte\s+Rang\s+Num[ée]ro\s+(\d+)\s+([A-Z])\s+(\d+)",
        texte,
        re.IGNORECASE,
    )

    if not m:
        doc.close()
        raise ValueError("Porte/Rang/Place introuvable.")

    porte, rang, place = m.groups()

    doc.close()

    return {
        "zone": zone,
        "porte": porte,
        "rang": rang,
        "place": place,
    }
