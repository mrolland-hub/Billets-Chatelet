import re
import fitz  # PyMuPDF


ETAGES = [
    "Orchestre",
    "Corbeille",
    "1er balcon",
    "2ème balcon",
    "Amphithéâtre Bas",
    "Amphithéâtre Haut",
]


def _normaliser(texte):
    texte = texte.replace("\xa0", " ")
    return " ".join(texte.split()).strip()


def _extraire_zone(page):
    """
    Recherche l'un des six étages possibles.
    """

    texte = page.get_text("text")

    for etage in ETAGES:
        if re.search(
            rf"\b{re.escape(etage)}\b",
            texte,
            re.IGNORECASE
        ):
            return etage

    raise ValueError("Étage introuvable.")


def _extraire_porte_rang_place(page):
    """
    Recherche les trois valeurs sous les intitulés :

        Porte    Rang    Numéro
        11       A       41

    Résultat :
        porte = 11
        rang = A
        place = 41
    """

    texte = page.get_text("text")

    lignes = [
        _normaliser(ligne)
        for ligne in texte.splitlines()
        if _normaliser(ligne)
    ]

    # ---------------------------------------------------------
    # CAS PRINCIPAL
    # ---------------------------------------------------------
    # On cherche une ligne contenant Porte / Rang / Numéro,
    # puis les lignes suivantes.
    # ---------------------------------------------------------

    for i, ligne in enumerate(lignes):

        ligne_min = ligne.lower()

        if (
            "porte" in ligne_min
            and "rang" in ligne_min
            and "num" in ligne_min
        ):

            # On examine les 5 lignes suivantes.
            for j in range(i + 1, min(i + 6, len(lignes))):

                valeurs = lignes[j]

                # Cas idéal : "11 A 41"
                m = re.fullmatch(
                    r"(\d+)\s+([A-Za-z])\s+(\d+)",
                    valeurs
                )

                if m:
                    porte, rang, place = m.groups()

                    return {
                        "porte": porte,
                        "rang": rang.upper(),
                        "place": place,
                    }

    # ---------------------------------------------------------
    # CAS où PyMuPDF sépare les valeurs
    # ---------------------------------------------------------
    #
    # Exemple :
    #
    # Porte
    # Rang
    # Numéro
    # 11
    # A
    # 41
    #
    # ---------------------------------------------------------

    for i, ligne in enumerate(lignes):

        if ligne.lower() == "porte":

            for j in range(i + 1, min(i + 6, len(lignes))):

                if lignes[j].lower() == "rang":

                    for k in range(j + 1, min(j + 6, len(lignes))):

                        if "num" in lignes[k].lower():

                            valeurs = []

                            for n in range(
                                k + 1,
                                min(k + 7, len(lignes))
                            ):
                                valeur = lignes[n]

                                if re.fullmatch(r"\d+", valeur):
                                    valeurs.append(valeur)

                                elif re.fullmatch(
                                    r"[A-Za-z]",
                                    valeur
                                ):
                                    valeurs.append(
                                        valeur.upper()
                                    )

                            if len(valeurs) >= 3:

                                # On vérifie bien :
                                # nombre / lettre / nombre

                                if (
                                    re.fullmatch(r"\d+", valeurs[0])
                                    and
                                    re.fullmatch(
                                        r"[A-Z]",
                                        valeurs[1]
                                    )
                                    and
                                    re.fullmatch(r"\d+", valeurs[2])
                                ):
                                    return {
                                        "porte": valeurs[0],
                                        "rang": valeurs[1],
                                        "place": valeurs[2],
                                    }

    raise ValueError("Porte/Rang/Place introuvable.")


def lire_billet(pdf_path):
    doc = fitz.open(pdf_path)

    try:
        page = doc[0]

        zone = _extraire_zone(page)
        infos = _extraire_porte_rang_place(page)

        return {
            "zone": zone,
            "porte": infos["porte"],
            "rang": infos["rang"],
            "place": infos["place"],
        }

    finally:
        doc.close()
