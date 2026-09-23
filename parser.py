import re
import fitz  # PyMuPDF

IGNORER = {
    "grande salle",
    "contrôle",
    "controle",
    "catégorie",
    "gratuit",
    "porte rang numéro",
    "porte rang numero",
}


def _est_a_ignorer(texte):
    t = texte.lower().strip()

    if not t:
        return True

    for mot in IGNORER:
        if mot in t:
            return True

    if t.startswith("dossier :"):
        return True

    if t.startswith("édité le") or t.startswith("edite le"):
        return True

    if t.startswith("numéro fiscal") or t.startswith("numero fiscal"):
        return True

    return False


def _extraire_zone(page):
    """
    Détecte la zone en utilisant la position des blocs de texte.
    """

    blocs = page.get_text("blocks")
    blocs = sorted(blocs, key=lambda b: (b[1], b[0]))  # haut -> bas

    # Cherche le bloc "Dossier :"
    for i, bloc in enumerate(blocs):
        texte = bloc[4].strip()

        if texte.lower().startswith("dossier :"):

            # Remonte jusqu'au premier bloc significatif
            for j in range(i - 1, -1, -1):

                candidat = blocs[j][4].strip()

                if not _est_a_ignorer(candidat):
                    return candidat

    raise ValueError("Zone introuvable.")


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
        raise ValueError("Porte/Rang/Place introuvable.")

    porte, rang, place = m.groups()

    doc.close()

    return {
        "zone": zone,
        "porte": porte,
        "rang": rang,
        "place": place,
    }
