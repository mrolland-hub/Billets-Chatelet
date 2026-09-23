const fichiers = document.getElementById("fichiers");
const nombre = document.getElementById("nombre");
const traiter = document.getElementById("traiter");
const resultat = document.getElementById("resultat");


const ETAGES = [
    "Orchestre",
    "Corbeille",
    "1er balcon",
    "2ème balcon",
    "Amphithéâtre Bas",
    "Amphithéâtre Haut"
];


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


function trouverEtage(mots) {

    const texte = mots
        .map(mot => mot.texte)
        .join(" ");

    const texteNormalise = normaliser(texte).toLowerCase();

    for (const etage of ETAGES) {

        if (
            texteNormalise.includes(
                etage.toLowerCase()
            )
        ) {
            return etage;
        }
    }

    return null;
}


function trouverMot(mots, recherche) {

    const rechercheMin =
        recherche.toLowerCase();

    return mots.find(
        mot =>
            mot.texte.toLowerCase() ===
            rechercheMin
    );
}


function trouverValeurSousLabel(
    mots,
    label,
    type
) {

    const candidats = [];

    for (const mot of mots) {

        // Le mot doit être situé sous le label.
        if (mot.y >= label.y) {
            continue;
        }

        const distanceY =
            label.y - mot.y;

        // Trop éloigné verticalement.
        if (distanceY > 100) {
            continue;
        }

        const distanceX =
            Math.abs(mot.x - label.x);

        // Trop éloigné horizontalement.
        if (distanceX > 100) {
            continue;
        }

        const texte = mot.texte;

        if (
            type === "nombre" &&
            !/^\d+$/.test(texte)
        ) {
            continue;
        }

        if (
            type === "lettre" &&
            !/^[A-Za-z]$/.test(texte)
        ) {
            continue;
        }

        const score =
            distanceY +
            distanceX * 0.5;

        candidats.push({
            score,
            texte
        });
    }

    if (candidats.length === 0) {
        return null;
    }

    candidats.sort(
        (a, b) => a.score - b.score
    );

    return candidats[0].texte;
}


function extraireInformations(mots) {

    const etage =
        trouverEtage(mots);

    const labelPorte =
        trouverMot(mots, "Porte");

    const labelRang =
        trouverMot(mots, "Rang");

    let labelNumero =
        trouverMot(mots, "Numéro");

    if (!labelNumero) {
        labelNumero =
            trouverMot(mots, "Numero");
    }

    if (!labelPorte) {
        throw new Error(
            "Libellé « Porte » introuvable."
        );
    }

    if (!labelRang) {
        throw new Error(
            "Libellé « Rang » introuvable."
        );
    }

    if (!labelNumero) {
        throw new Error(
            "Libellé « Numéro » introuvable."
        );
    }


    /*
     * IMPORTANT :
     *
     * PDF.js utilise un axe Y qui augmente
     * vers le haut dans les coordonnées
     * du texte.
     *
     * Les valeurs du billet sont donc
     * recherchées sous les intitulés.
     */


    const porte =
        trouverValeurSousLabel(
            mots,
            labelPorte,
            "nombre"
        );

    const rang =
        trouverValeurSousLabel(
            mots,
            labelRang,
            "lettre"
        );

    const place =
        trouverValeurSousLabel(
            mots,
            labelNumero,
            "nombre"
        );


    if (!porte) {
        throw new Error(
            "Porte introuvable."
        );
    }

    if (!rang) {
        throw new Error(
            "Rang introuvable."
        );
    }

    if (!place) {
        throw new Error(
            "Place introuvable."
        );
    }


    return {
        etage,
        porte,
        rang: rang.toUpperCase(),
        place
    };
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
            "Analyse du billet en cours...";


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
                    .map(item => ({

                        texte: normaliser(
                            item.str
                        ),

                        x: item.transform[4],

                        y: item.transform[5]

                    }))
                    .filter(
                        mot => mot.texte
                    );


            console.log(
                "Mots détectés :",
                mots
            );


            const infos =
                extraireInformations(
                    mots
                );


            resultat.innerHTML = `

                <strong>Billet analysé</strong>

                <br><br>

                Étage :
                <strong>${infos.etage}</strong>

                <br>

                Porte :
                <strong>${infos.porte}</strong>

                <br>

                Rang :
                <strong>${infos.rang}</strong>

                <br>

                Place :
                <strong>${infos.place}</strong>

            `;


        }
        catch (erreur) {

            console.error(erreur);

            resultat.innerHTML =

                "<strong>Erreur :</strong><br>" +
                erreur.message;
        }

    }
);
