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

    const texteNormalise =
        normaliser(texte).toLowerCase();

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

        /*
         * Dans les coordonnées PDF utilisées ici,
         * une valeur située sous le libellé possède
         * une coordonnée Y plus petite.
         */

        if (mot.y >= label.y) {
            continue;
        }


        const distanceY =
            label.y - mot.y;


        /*
         * On limite la recherche verticalement
         * pour éviter de prendre un autre texte
         * éloigné du champ.
         */

        if (distanceY > 100) {
            continue;
        }


        const distanceX =
            Math.abs(mot.x - label.x);


        /*
         * Même principe horizontalement.
         */

        if (distanceX > 100) {
            continue;
        }


        const texte =
            mot.texte;


        /*
         * PORTE
         *
         * Nombre entier compris entre 1 et 23.
         */

        if (type === "porte") {

            if (
                !/^\d+$/.test(texte)
            ) {
                continue;
            }

            const valeur =
                Number(texte);

            if (
                valeur < 1 ||
                valeur > 23
            ) {
                continue;
            }
        }


        /*
         * RANG
         *
         * Une ou deux lettres maximum.
         *
         * Exemples :
         * A
         * B
         * LG
         */

        if (type === "rang") {

            if (
                !/^[A-Za-z]{1,2}$/.test(texte)
            ) {
                continue;
            }
        }


        /*
         * PLACE
         *
         * Un ou plusieurs chiffres,
         * éventuellement suivis d'une lettre.
         *
         * Exemples :
         * 16
         * 16A
         * 125
         * 125B
         */

        if (type === "place") {

            if (
                !/^\d+[A-Za-z]?$/.test(texte)
            ) {
                continue;
            }
        }


        /*
         * Score :
         *
         * On privilégie d'abord la proximité
         * verticale, puis la proximité horizontale.
         */

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
        (a, b) =>
            a.score - b.score
    );


    return candidats[0].texte;
}


function extraireInformations(mots) {

    const etage =
        trouverEtage(mots);


    const labelPorte =
        trouverMot(
            mots,
            "Porte"
        );


    const labelRang =
        trouverMot(
            mots,
            "Rang"
        );


    let labelNumero =
        trouverMot(
            mots,
            "Numéro"
        );


    if (!labelNumero) {

        labelNumero =
            trouverMot(
                mots,
                "Numero"
            );
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


    const porte =
        trouverValeurSousLabel(
            mots,
            labelPorte,
            "porte"
        );


    const rang =
        trouverValeurSousLabel(
            mots,
            labelRang,
            "rang"
        );


    const place =
        trouverValeurSousLabel(
            mots,
            labelNumero,
            "place"
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

        rang:
            rang.toUpperCase(),

        place
    };
}


function nomSecurise(nom) {

    return nom.replace(
        /[<>:"/\\|?*]/g,
        "_"
    );
}


async function analyserPDF(fichier) {

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

                texte:
                    normaliser(
                        item.str
                    ),

                x:
                    item.transform[4],

                y:
                    item.transform[5]

            }))

            .filter(
                mot =>
                    mot.texte
            );


    return extraireInformations(
        mots
    );
}


traiter.addEventListener(
    "click",
    async () => {

        if (
            fichiers.files.length === 0
        ) {

            resultat.textContent =
                "Veuillez sélectionner au moins un PDF.";

            return;
        }


        traiter.disabled = true;


        const total =
            fichiers.files.length;


        let nbOK = 0;

        let nbErreurs = 0;


        const erreurs = [];


        try {

            const zip =
                new JSZip();


            for (
                let i = 0;
                i < total;
                i++
            ) {

                const fichier =
                    fichiers.files[i];


                resultat.innerHTML =

                    `Analyse du billet ${i + 1} / ${total}<br>` +

                    `<strong>${fichier.name}</strong>`;


                try {

                    const infos =
                        await analyserPDF(
                            fichier
                        );


                    if (!infos.etage) {

                        throw new Error(
                            "Étage introuvable."
                        );
                    }


                    const dossier =

                        `${nomSecurise(infos.etage)}/` +

                        `Rang ${nomSecurise(infos.rang)}/`;


                    const nom =

                        `${nomSecurise(infos.etage)}` +

                        `_Porte_${nomSecurise(infos.porte)}` +

                        `_Rang_${nomSecurise(infos.rang)}` +

                        `_Place_${nomSecurise(infos.place)}` +

                        `.pdf`;


                    const chemin =
                        dossier + nom;


                    const donnees =
                        await fichier.arrayBuffer();


                    zip.file(
                        chemin,
                        donnees
                    );


                    nbOK++;

                }
                catch (erreur) {

                    nbErreurs++;


                    erreurs.push(

                        `${fichier.name} : ${erreur.message}`

                    );
                }
            }


            resultat.innerHTML =

                `Traitement terminé.<br><br>` +

                `<strong>${nbOK}</strong> billet(s) traité(s).<br>` +

                `<strong>${nbErreurs}</strong> erreur(s).`;


            if (
                erreurs.length > 0
            ) {

                zip.file(
                    "erreurs.txt",
                    erreurs.join("\n")
                );
            }


            if (nbOK > 0) {

                resultat.innerHTML +=
                    "<br><br>Création du fichier ZIP...";


                const contenuZIP =
                    await zip.generateAsync({
                        type: "blob"
                    });


                const url =
                    URL.createObjectURL(
                        contenuZIP
                    );


                const lien =
                    document.createElement("a");


                lien.href =
                    url;


                lien.download =
                    "Billets-renommes.zip";


                lien.textContent =
                    "Télécharger le ZIP";


                lien.style.display =
                    "inline-block";


                lien.style.marginTop =
                    "15px";


                lien.style.padding =
                    "12px 20px";


                lien.style.background =
                    "#222";


                lien.style.color =
                    "white";


                lien.style.textDecoration =
                    "none";


                lien.style.borderRadius =
                    "6px";


                resultat.appendChild(
                    document.createElement("br")
                );


                resultat.appendChild(
                    lien
                );
            }

        }
        catch (erreur) {

            console.error(
                erreur
            );


            resultat.innerHTML =

                "<strong>Erreur :</strong><br>" +

                erreur.message;
        }


        traiter.disabled = false;
    }
);
