import re
import fitz  # PyMuPDF


def _normaliser(texte):
    """Nettoie un morceau de texte extrait du PDF."""
    return " ".join(texte.split()).strip()


def _extraire_zone(page):
    """
    Extrait la zone (Corbeille, 1er Balcon, etc.)
    en utilisant la position des blocs de texte.
    """
    blocs = page.get_text("blocks")
    candidats = []

    for bloc in blocs:
        x0, y0, x1, y1, texte = bloc[:5]
        texte = _normaliser(texte)

        if not texte:
            continue

        if 150 <= y0 <= 280:
            texte_min = texte.lower()

            if texte_min.startswith("porte rang"):
                continue

            if texte_min == "grande salle":
                continue

            if "catégorie" in texte_min:
                continue

            if "gratuit" in texte_min:
                continue

            candidats.append((y0, texte))

    if not candidats:
        raise ValueError("Zone introuvable.")

    candidats.sort(key=lambda c: c[0])
    return candidats[-1][1]


def _trouver_mot(mots, recherche):
    """Trouve le premier mot correspondant à recherche."""
    recherche = recherche.lower()

    for mot in mots:
        texte = _normaliser(mot[4])
        if texte.lower() == recherche:
            return mot

    return None


def _trouver_valeur_sous(mots, libelle, type_valeur):
    """
    Cherche une valeur placée sous un libellé.

    Le libellé et la valeur peuvent être dans des blocs
    de texte différents.
    """

    x0, y0, x1, y1, texte = libelle[:5]

    candidats = []

    for mot in mots:
        mx0, my0, mx1, my1, mtexte = mot[:5]
        mtexte = _normaliser(mtexte)

        if not mtexte:
            continue

        # On ne cherche que sous le libellé.
        if my0 <= y1:
            continue

        # Le centre horizontal de la valeur doit être
        # raisonnablement aligné avec celui du libellé.
        centre_libelle = (x0 + x1) / 2
        centre_valeur = (mx0 + mx1) / 2

        largeur_libelle = max(x1 - x0, 1)
        tolerance_x = max(30, largeur_libelle * 1.5)

        if abs(centre_valeur - centre_libelle) > tolerance_x:
            continue

        # Distance verticale.
        distance_y = my0 - y1

        # On privilégie les éléments juste en dessous.
        if distance_y > 150:
            continue

        # Vérification du type attendu.
        if type_valeur == "porte":
            if not re.fullmatch(r"[A-Za-z0-9]+", mtexte):
                continue

        elif type_valeur == "rang":
            if not re.fullmatch(r"\d+", mtexte):
                continue

        elif type_valeur == "place":
            if not re.fullmatch(r"\d+", mtexte):
                continue

        candidats.append((distance_y, abs(centre_valeur - centre_libelle), mtexte))

    if not candidats:
        return None

    candidats.sort(key=lambda x: (x[0], x[1]))

    return candidats[0][2]


def lire_billet(pdf_path):
    doc = fitz.open(pdf_path)

    try:
        page = doc[0]

        zone = _extraire_zone(page)

        # On récupère les blocs de texte avec leurs coordonnées.
        blocs = page.get_text("blocks")

        porte_libelle = _trouver_mot(blocs, "Porte")
        rang_libelle = _trouver_mot(blocs, "Rang")
        numero_libelle = _trouver_mot(blocs, "Numéro")

        # Certains PDF peuvent extraire "Numero" sans accent.
        if numero_libelle is None:
            numero_libelle = _trouver_mot(blocs, "Numero")

        if porte_libelle is None:
            raise ValueError("Libellé 'Porte' introuvable.")

        if rang_libelle is None:
            raise ValueError("Libellé 'Rang' introuvable.")

        if numero_libelle is None:
            raise ValueError("Libellé 'Numéro' introuvable.")

        porte = _trouver_valeur_sous(
            blocs,
            porte_libelle,
            "porte"
        )

        rang = _trouver_valeur_sous(
            blocs,
            rang_libelle,
            "rang"
        )

        place = _trouver_valeur_sous(
            blocs,
            numero_libelle,
            "place"
        )

        if porte is None or rang is None or place is None:
            details = []

            if porte is None:
                details.append("Porte")

            if rang is None:
                details.append("Rang")

            if place is None:
                details.append("Numéro")

            raise ValueError(
                "Valeur introuvable sous : " + ", ".join(details)
            )

        return {
            "zone": zone,
            "porte": porte,
            "rang": rang,
            "place": place,
        }

    finally:
        doc.close()
