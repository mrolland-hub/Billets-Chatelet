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
    } else if (total === 1) {
        nombre.textContent = "1 fichier sélectionné.";
    } else {
        nombre.textContent = `${total} fichiers sélectionnés.`;
    }
});

function normaliser(texte) {
    return texte
        .replace(/\u00a0/g, " ")
        .replace(/\s+/g, " ")
        .trim();
}

function nomSecurise(nom) {
    return nom.replace(/[<>:"/\\|?*]/g, "_");
}

function trouverEtage(mots) {
    const texte = mots.map(m => m.texte).join(" ").toLowerCase();

    return ETAGES.find(etage =>
        texte.includes(etage.toLowerCase())
    );
}

function trouverMot(mots, recherche) {
    return mots.find(
        mot => mot.texte.toLowerCase() === recherche.toLowerCase()
    );
}

function extrairePorteRangPlace(mots) {

    const porteLabel = trouverMot(mots, "Porte");
    const rangLabel = trouverMot(mots, "Rang");
    const numeroLabel =
        trouverMot(mots, "Numéro") ||
        trouverMot(mots, "Numero");

    if (!porteLabel || !rangLabel || !numeroLabel) {
        throw new Error("Libellés Porte/Rang/Numéro introuvables.");
    }

    // Ligne des libellés
    const yLibelles = Math.max(
        porteLabel.y,
        rangLabel.y,
        numeroLabel.y
    );

    // Toutes les lignes situées sous les libellés
    const ys = [...new Set(
        mots
            .filter(m => m.y < yLibelles - 2)
            .map(m => m.y)
    )];

    if (ys.length === 0) {
        throw new Error("Ligne des valeurs introuvable.");
    }

    // Première ligne située juste sous les libellés
    const yValeurs = Math.max(...ys);

    const ligne = mots.filter(
        m => Math.abs(m.y - yValeurs) <= 2
    );

    if (ligne.length < 3) {
        throw new Error("Valeurs Porte/Rang/Place introuvables.");
    }

    const colonnes = [
        { nom: "porte", x: porteLabel.x },
        { nom: "rang", x: rangLabel.x },
        { nom: "place", x: numeroLabel.x }
    ];

    const resultat = {};

    for (const mot of ligne) {

        let meilleure = colonnes[0];
        let distance = Math.abs(mot.x - meilleure.x);

        for (const col of colonnes.slice(1)) {

            const d = Math.abs(mot.x - col.x);

            if (d < distance) {
                meilleure = col;
                distance = d;
            }
        }

        resultat[meilleure.nom] = mot.texte;
    }

    // Vérifications métier

    const porte = Number(resultat.porte);

    if (!(porte >= 1 && porte <= 23)) {
        throw new Error(`Porte invalide : ${resultat.porte}`);
    }

    if (!/^[A-Za-z]{1,2}$/.test(resultat.rang)) {
        throw new Error(`Rang invalide : ${resultat.rang}`);
    }

    if (!/^\d+[A-Za-z]?$/.test(resultat.place)) {
        throw new Error(`Place invalide : ${resultat.place}`);
    }

    return {
        porte: String(porte),
        rang: resultat.rang.toUpperCase(),
        place: resultat.place
    };
}

function extraireInformations(mots) {

    const etage = trouverEtage(mots);

    if (!etage) {
        throw new Error("Étage introuvable.");
    }

    return {
        etage,
        ...extrairePorteRangPlace(mots)
    };
}

async function analyserPDF(fichier) {

    const donnees = await fichier.arrayBuffer();

    const pdf = await pdfjsLib.getDocument({
        data: donnees
    }).promise;

    const page = await pdf.getPage(1);

    const contenu = await page.getTextContent();

    const mots = contenu.items
        .map(item => ({
            texte: normaliser(item.str),
            x: item.transform[4],
            y: item.transform[5]
        }))
        .filter(m => m.texte);

    return {
        infos: extraireInformations(mots),
        donnees
    };
}

traiter.addEventListener("click", async () => {

    if (fichiers.files.length === 0) {
        resultat.textContent =
            "Veuillez sélectionner au moins un PDF.";
        return;
    }

    traiter.disabled = true;

    const zip = new JSZip();

    let nbOK = 0;
    const erreurs = [];

    try {

        for (let i = 0; i < fichiers.files.length; i++) {

            const fichier = fichiers.files[i];

            resultat.innerHTML =
                `Analyse ${i + 1}/${fichiers.files.length}<br><strong>${fichier.name}</strong>`;

            try {

                const { infos, donnees } =
                    await analyserPDF(fichier);

                const chemin =
                    `${nomSecurise(infos.etage)}/` +
                    `Rang ${infos.rang}/` +
                    `${nomSecurise(infos.etage)}_Porte_${infos.porte}_Rang_${infos.rang}_Place_${infos.place}.pdf`;

                zip.file(chemin, donnees);

                nbOK++;

            } catch (e) {

                erreurs.push(`${fichier.name} : ${e.message}`);
            }
        }

        if (erreurs.length) {
            zip.file("erreurs.txt", erreurs.join("\n"));
        }

        const blob = await zip.generateAsync({
            type: "blob"
        });

        resultat.innerHTML =
            `<strong>${nbOK}</strong> billet(s) traité(s)<br>` +
            `<strong>${erreurs.length}</strong> erreur(s)<br><br>`;

        const lien = document.createElement("a");

        lien.href = URL.createObjectURL(blob);
        lien.download = "Billets-renommes.zip";
        lien.textContent = "Télécharger le ZIP";

        lien.style.display = "inline-block";
        lien.style.marginTop = "15px";
        lien.style.padding = "12px 20px";
        lien.style.background = "#222";
        lien.style.color = "white";
        lien.style.textDecoration = "none";
        lien.style.borderRadius = "6px";

        resultat.appendChild(lien);

    } finally {

        traiter.disabled = false;
    }
});
