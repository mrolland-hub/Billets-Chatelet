const fichiers = document.getElementById("fichiers");
const nombre = document.getElementById("nombre");
const traiter = document.getElementById("traiter");
const resultat = document.getElementById("resultat");


fichiers.addEventListener("change", () => {

    const total = fichiers.files.length;

    if (total === 0) {
        nombre.textContent = "Aucun fichier sélectionné.";
    }
    else if (total === 1) {
        nombre.textContent = "1 fichier sélectionné.";
    }
    else {
        nombre.textContent =
            total + " fichiers sélectionnés.";
    }
});


function normaliser(texte) {

    return texte
        .replace(/\u00a0/g, " ")
        .replace(/\s+/g, " ")
        .trim();
}


traiter.addEventListener(
    "click",
    async () => {

        if (fichiers.files.length === 0) {

            resultat.textContent =
                "Veuillez sélectionner au moins un PDF.";

            return;
        }


        const fichier =
            fichiers.files[0];


        resultat.textContent =
            "Lecture du billet en cours...";


        try {

            const donnees =
                await fichier.arrayBuffer();


            const pdf =
                await pdfjsLib.getDocument({
                    data: donnees
                }).promise;


            const page =
                await pdf.getPage(1);


            const contenu =
                await page.getTextContent();


            const mots =
                contenu.items
                    .map(item =>
                        normaliser(item.str)
                    )
                    .filter(
                        texte => texte
                    );


            console.log(
                "Texte extrait dans l'ordre :"
            );

            console.log(mots);


            resultat.innerHTML =
                "<strong>Texte extrait dans l'ordre :</strong>" +
                "<br><br>" +
                mots.join("<br>");


        }
        catch (erreur) {

            console.error(erreur);


            resultat.innerHTML =
                "<strong>Erreur :</strong><br>" +
                erreur.message;
        }

    }
);
