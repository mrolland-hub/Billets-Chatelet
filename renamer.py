
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
    Traite tous les PDF d'un dossier (et de ses sous-dossiers).

    Retourne :
        dossier_sortie, nb_ok, nb_erreurs
    """

    dossier_source = Path(dossier_source)
    dossier_sortie = dossier_source.parent / f"{dossier_source.name} - renommés"

    if dossier_sortie.exists():
        shutil.rmtree(dossier_sortie)

    dossier_sortie.mkdir()

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
            rang = info["rang"]
            place = info["place"]

            dossier_rang = dossier_sortie / zone / f"Rang {rang}"
            dossier_rang.mkdir(parents=True, exist_ok=True)

            nom = f"{zone}_Rang_{rang}_Place_{place}.pdf"
            destination = dossier_rang / nom

            compteur = 2
            while destination.exists():
                destination = dossier_rang / (
                    f"{zone}_Rang_{rang}_Place_{place}_{compteur}.pdf"
                )
                compteur += 1

            shutil.copy2(pdf, destination)
            nb_ok += 1

        except Exception as e:
            erreurs.append(f"{pdf.name} : {e}")

        if callback_progress:
            callback_progress(i, total)

    if erreurs:
        (dossier_sortie / "erreurs.txt").write_text(
            "\n".join(erreurs),
            encoding="utf-8"
        )

    return dossier_sortie, nb_ok, len(erreurs)
