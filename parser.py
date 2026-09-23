import re
import unicodedata
import fitz  # PyMuPDF


ETAGES = [
    "Orchestre",
    "Corbeille",
    "2ème balcon",
    "1er balcon",
    "Amphithéâtre Bas",
    "Amphithéâtre Haut",
]


def normaliser(texte):
    """Normalise un texte extrait du PDF."""
    texte = texte.replace("\xa0", " ")
    texte = " ".join(texte.split())
    return texte.strip()


def sans_accents(texte):
    """Supprime les accents pour faciliter les comparaisons."""
    return "".join(
        c
        for c in unicodedata.normalize("NFD", texte)
        if unicodedata.category(c) != "Mn"
    )


def trouver_etage(texte):
    """
    Cherche explicitement l'un des six étages possibles.
    """

    texte_normalise = sans_accents(texte).lower()

    # On teste les plus longs en premier.
    etages = sorted(ETAGES, key=len, reverse=True)

    for etage in etages:
        recherche = sans_accents(etage).lower()

        if recherche in texte_normalise:
            return etage

    raise ValueError("Étage introuvable.")


def trouver_place(page):
    """
    Recherche la structure :

        Porte        Rang        Numéro
        12           A           66

    et retourne :
        porte = 12
        rang = A
        place = 66
    """

    texte = page.get_text("text")

    lignes = [
        normaliser(ligne)
        for ligne in texte.splitlines()
        if normaliser(ligne)
    ]

    # ---------------------------------------------------------
    # CAS 1 :
    #
    # Porte Rang Numéro
    # 12 A 66
    # ---------------------------------------------------------

    for i, ligne in enumerate(lignes):

        ligne_test = sans_accents(ligne).lower()

        if (
            "porte" in ligne_test
            and "rang" in ligne_test
            and "numero" in ligne_test
        ):

            # Cherche la ligne de valeurs juste après.
            for j in range(i + 1, min(i + 4, len(lignes))):

                valeurs = lignes[j]

                match = re.fullmatch(
                    r"(\d+)\s+([A-Za-z])\s+(\d+)",
                    valeurs,
                )

                if match:
                    porte, rang, place = match.groups()

                    return porte, rang.upper(), place

    # ---------------------------------------------------------
    # CAS 2 :
    #
    # PyMuPDF peut avoir séparé les éléments différemment.
    # On recherche donc n'importe où une séquence :
    #
    # nombre + lettre + nombre
    #
    # à proximité de "Porte / Rang / Numéro".
    # ---------------------------------------------------------

    for i, ligne in enumerate(lignes):

        ligne_test = sans_accents(ligne).lower()

        if (
            "porte" in ligne_test
            or "rang" in ligne_test
            or "numero" in ligne_test
        ):

            for j in range(i + 1, min(i + 5, len(lignes))):

                valeurs = lignes[j]

                match = re.fullmatch(
                    r"(\d+)\s+([A-Za-z])\s+(\d+)",
                    valeurs,
                )

                if match:
                    porte, rang, place = match.groups()

                    return porte, rang.upper(), place

    # ---------------------------------------------------------
    # CAS 3 :
    #
    # Les valeurs peuvent être extraites chacune sur une ligne :
    #
    # Porte
    # Rang
    # Numéro
    # 12
    # A
    # 66
    # ---------------------------------------------------------

    for i, ligne in enumerate(lignes):

        if sans_accents(ligne).lower() != "porte":
            continue

        # Cherche Rang puis Numéro dans les lignes suivantes.
        rang_index = None
        numero_index = None

        for j in range(i + 1, min(i + 8, len(lignes))):

            test = sans_accents(lignes[j]).lower()

            if test == "rang" and rang_index is None:
                rang_index = j

            if test == "numero" and numero_index is None:
                numero_index = j

        if rang_index is None or numero_index is None:
            continue

        # Les valeurs doivent apparaître après les intitulés.
        valeurs = []

        debut = max(rang_index, numero_index) + 1

        for j in range(debut, min(debut + 8, len(lignes))):

            valeur = lignes[j]

            if re.fullmatch(r"\d+", valeur):
                valeurs.append(valeur)

            elif re.fullmatch(r"[A-Za-z]", valeur):
                valeurs.append(valeur.upper())

        if len(valeurs) >= 3:
            return valeurs[0], valeurs[1], valeurs[2]

    raise ValueError("Porte/Rang/Place introuvable.")


def lire_billet(pdf_path):

    doc = fitz.open(pdf_path)

    try:
        if len(doc) == 0:
            raise ValueError("PDF vide.")

        page = doc[0]

        texte = page.get_text("text")

        if not texte.strip():
            raise ValueError("Aucun texte détecté dans le PDF.")

        # -----------------------------------------------------
        # ÉTAGE
        # -----------------------------------------------------

        zone = trouver_etage(texte)

        # -----------------------------------------------------
        # PORTE / RANG / PLACE
        # -----------------------------------------------------

        porte, rang, place = trouver_place(page)

        return {
            "zone": zone,
            "porte": porte,
            "rang": rang,
            "place": place,
        }

    finally:
        doc.close()
