from pathlib import Path
import shutil

from parser import lire_billet


def _nom_securise(nom):
    """Supprime les caractères interdits dans les noms de fichiers Windows."""
    interdits = '<>:"/\\|?*'

    for c in interdits:
        nom = nom.replace(c, "_")

    return nom.strip()


def traiter_dossier(dossier_source, callback_progress=None):
    """
    Traite tous les PDF d'un dossier et de ses sous-dossiers.

    Les fichiers sont copiés dans une nouvelle arborescence :

        dossier_source - renommés/
            Zone/
                Rang A/
                    Zone_Porte_11_Rang_A_Place_41.pdf

    Retourne :
        dossier_sortie, nb_ok, nb_erreurs
    """

    dossier_source = Path(dossier_source)

    dossier_sortie = (
        dossier_source.parent
        / f"{dossier_source.name} - renommés"
    )

    # Supprime une ancienne version du dossier de sortie
    if dossier_sortie.exists():
        shutil.rmtree(dossier_sortie)

    dossier_sortie.mkdir()

    # Recherche tous les PDF, y compris dans les sous-dossiers
    pdfs = sorted(dossier_source.rglob("*.pdf"))

    erreurs = []
    nb_ok = 0

    total = len(pdfs)

    for i, pdf in enumerate(pdfs, start=1):

        try:
            info = lire_billet(pdf)

            if info is None:
                raise Exception("Lecture impossible")

            zone = _nom_securise(info["zone"])
            porte = info["porte"]
            rang = info["rang"]
            place = info["place"]

            # Création du dossier correspondant au rang
            dossier_rang = (
                dossier_sortie
                / zone
                / f"Rang {rang}"
            )

            dossier_rang.mkdir(
                parents=True,
                exist_ok=True
            )

            # Nom du fichier
            nom = (
                f"{zone}"
                f"_Porte_{porte}"
                f"_Rang_{rang}"
                f"_Place_{place}.pdf"
            )

            destination = dossier_rang / nom

            # Si le fichier existe déjà, ajoute _2, _3, etc.
            compteur = 2

            while destination.exists():

                destination = (
                    dossier_rang
                    /
                    (
                        f"{zone}"
                        f"_Porte_{porte}"
                        f"_Rang_{rang}"
                        f"_Place_{place}"
                        f"_{compteur}.pdf"
                    )
                )

                compteur += 1

            # Copie du PDF original
            shutil.copy2(pdf, destination)

            nb_ok += 1

        except Exception as e:

            erreurs.append(
                f"{pdf.name} : {e}"
            )

        # Mise à jour de la progression
        if callback_progress:
            callback_progress(
                i,
                total
            )

    # Création du fichier d'erreurs s'il y en a
    if erreurs:

        (dossier_sortie / "erreurs.txt").write_text(
            "\n".join(erreurs),
            encoding="utf-8"
        )

    return (
        dossier_sortie,
        nb_ok,
        len(erreurs)
    )
