import re
import fitz  # PyMuPDF


def _normaliser(texte):
    texte = texte.replace("\xa0", " ")
    return " ".join(texte.split()).strip()


def _extraire_zone(page):
    blocs = page.get_text("blocks")
    candidats = []

    for bloc in blocs:
        x0, y0, x1, y1, texte = bloc[:5]
        texte = _normaliser(texte)

        if not texte:
            continue

        if 150 <= y0 <= 280:
            t = texte.lower()

            if "porte" in t and "rang" in t and "num" in t:
                continue

            if t == "grande salle":
                continue

            if "catégorie" in t:
                continue

            if "gratuit" in t:
                continue

            candidats.append((y0, texte))

    if not candidats:
        raise ValueError("Zone introuvable.")

    candidats.sort(key=lambda x: x[0])
    return candidats[-1][1]


def _extraire_porte_rang_place(page):
    """
    Cherche une ligne contenant :
        Porte    Rang    Numéro

    puis la ligne suivante contenant :
        11       A       41

    La position exacte des espaces n'a pas d'importance.
    """

    texte = page.get_text("text")

    # Normalisation des fins de lignes
    lignes = [
        _normaliser(ligne)
        for ligne in texte.splitlines()
        if _normaliser(ligne)
    ]

    for i, ligne in enumerate(lignes):

        ligne_min = ligne.lower()

        # On cherche la ligne des intitulés.
        if (
            "porte" in ligne_min
            and "rang" in ligne_min
            and "num" in ligne_min
        ):

            # On regarde les quelques lignes suivantes.
            for j in range(i + 1, min(i + 4, len(lignes))):

                valeurs = lignes[j]

                # Format attendu :
                # 11 A 41
                m = re.fullmatch(
                    r"(\d+)\s+([A-Za-z])\s+(\d+)",
                    valeurs
                )

                if m:
                    porte, rang, place = m.groups()

                    return porte, rang.upper(), place

    # Deuxième possibilité :
    # PyMuPDF peut avoir séparé les trois intitulés
    # et les trois valeurs.
    for i, ligne in enumerate(lignes):

        if ligne.lower() == "porte":

            # Cherche "Rang" puis "Numéro" dans les lignes suivantes.
            for j in range(i + 1, min(i + 6, len(lignes))):
                if lignes[j].lower() == "rang":

                    for k in range(j + 1, min(j + 6, len(lignes))):
                        if "num" in lignes[k].lower():

                            # Les trois valeurs peuvent être juste
                            # après les intitulés.
                            valeurs = []

                            for n in range(k + 1, min(k + 6, len(lignes))):
                                v = lignes[n]

                                if re.fullmatch(r"\d+", v):
                                    valeurs.append(v)

                                elif re.fullmatch(r"[A-Za-z]", v):
                                    valeurs.append(v.upper())

                            if len(valeurs) >= 3:
                                return (
                                    valeurs[0],
                                    valeurs[1],
                                    valeurs[2],
                                )

    raise ValueError("Porte/Rang/Place introuvable.")


def lire_billet(pdf_path):
    doc = fitz.open(pdf_path)

    try:
        page = doc[0]

        zone = _extraire_zone(page)

        porte, rang, place = _extraire_porte_rang_place(page)

        return {
            "zone": zone,
            "porte": porte,
            "rang": rang,
            "place": place,
        }

    finally:
        doc.close()
