const fichiers = document.getElementById("fichiers");
const nombre = document.getElementById("nombre");
const traiter = document.getElementById("traiter");
const resultat = document.getElementById("resultat");

fichiers.addEventListener("change", () => {
    const total = fichiers.files.length;

    if (total === 0) {
        nombre.textContent = "Aucun fichier sélectionné.";
    } else if (total === 1) {
        nombre.textContent = "1 fichier sélectionné.";
    } else {
        nombre.textContent = total + " fichiers sélectionnés.";
    }
});


traiter.addEventListener("click", async () => {

    if (fichiers.files.length === 0) {
        resultat.textContent =
            "Veuillez sélectionner au moins un PDF.";
        return;
    }

    resultat.textContent = "Lecture du PDF en cours...";

    const fichier = fichiers.files[0];

    try {

        const donnees = await fichier.arrayBuffer();

        const pdf = await pdfjsLib.getDocument({
            data: donnees
        }).promise;

        const page = await pdf.getPage(1);

        const contenu = await page.getTextContent();

        const mots = contenu.items.map(item => ({
            texte: item.str,
            x: item.transform[4],
            y: item.transform[5]
        }));

        console.log("Mots trouvés :", mots);

        resultat.innerHTML =
            "<strong>PDF lu avec succès.</strong><br>" +
            "Nombre d'éléments de texte trouvés : " +
            mots.length +
            "<br><br>" +
            "Ouvre la console du navigateur avec F12 " +
            "pour voir les éléments détectés.";

    } catch (erreur) {

        console.error(erreur);

        resultat.textContent =
            "Erreur lors de la lecture du PDF : " +
            erreur.message;
    }
});
