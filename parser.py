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

    texte = _normaliser(page.get_text("text"))

    for etage in ETAGES:
        if re.search(
            rf"\b{re.escape(etage)}\b",
            texte,
            re.IGNORECASE
        ):
            return etage

    raise ValueError("Étage introuvable.")


def _recuperer_mots(page):
    """
    Récupère les mots avec leur position sur la page.

    Chaque élément contient :
        x0, y0, x1, y1, texte
    """

    mots = []

    for mot in page.get_text("words"):
        x0, y0, x1, y1, texte = mot[:5]

        texte = _normaliser(texte)

        if texte:
            mots.append({
                "x0": x0,
                "y0": y0,
                "x1": x1,
                "y1": y1,
                "x": (x0 + x1) / 2,
                "y": (y0 + y1) / 2,
                "texte": texte,
            })

    return mots


def _trouver_mot(mots, recherche):
    """
    Trouve le mot correspondant à un intitulé.
    """

    recherche = recherche.lower()

    for mot in mots:
        if mot["texte"].lower() == recherche:
            return mot

    return None


def _trouver_valeur_sous_label(
    mots,
    label,
    type_valeur
):
    """
    Cherche la valeur située sous un intitulé.

    type_valeur :
        "nombre" -> 11 ou 44
        "lettre" -> A
    """

    candidats = []

    # Centre horizontal du libellé
    centre_label = label["x"]

    for mot in mots:

        # Il faut être sous le libellé
        if mot["y"] <= label["y"]:
            continue

        # Distance verticale raisonnable
        distance_y = mot["y"] - label["y"]

        if distance_y > 100:
            continue

        texte = mot["texte"]

        # Vérification du type de valeur
        if type_valeur == "nombre":
            if not re.fullmatch(r"\d+", texte):
                continue

        elif type_valeur == "lettre":
            if not re.fullmatch(r"[A-Za-z]", texte):
                continue

        # Distance horizontale
        distance_x = abs(mot["x"] - centre_label)

        # On évite les valeurs trop éloignées
        if distance_x > 100:
            continue

        # Score :
        # on privilégie d'abord la proximité verticale,
        # puis la proximité horizontale.
        score = distance_y + distance_x * 0.5

        candidats.append((score, mot))

    if not candidats:
        return None

    candidats.sort(key=lambda x: x[0])

    return candidats[0][1]["texte"]


def _extraire_porte_rang_place(page):
    """
    Recherche :

        Porte       Rang       Numéro
         11          A           44

    en utilisant les positions des éléments sur le PDF.
    """

    mots = _recuperer_mots(page)

    label_porte = _trouver_mot(mots, "Porte")
    label_rang = _trouver_mot(mots, "Rang")
    label_numero = _trouver_mot(mots, "Numéro")

    # Certains PDF peuvent avoir "Numero" sans accent.
    if label_numero is None:
        label_numero = _trouver_mot(mots, "Numero")

    if label_porte is None:
        raise ValueError("Libellé 'Porte' introuvable.")

    if label_rang is None:
        raise ValueError("Libellé 'Rang' introuvable.")

    if label_numero is None:
        raise ValueError("Libellé 'Numéro' introuvable.")

    porte = _trouver_valeur_sous_label(
        mots,
        label_porte,
        "nombre"
    )

    rang = _trouver_valeur_sous_label(
        mots,
        label_rang,
        "lettre"
    )

    place = _trouver_valeur_sous_label(
        mots,
        label_numero,
        "nombre"
    )

    if porte is None:
        raise ValueError("Porte introuvable.")

    if rang is None:
        raise ValueError("Rang introuvable.")

    if place is None:
        raise ValueError("Place introuvable.")

    return {
        "porte": porte,
        "rang": rang.upper(),
        "place": place,
    }


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
