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
    nombre.textContent =
        total === 0
            ? "Aucun fichier sélectionné."
            : `${total} fichier${total > 1 ? "s" : ""} sélectionné${total > 1 ? "s" : ""}.`;
});

function normaliser(t) {
    return t.replace(/\u00a0/g, " ").replace(/\s+/g, " ").trim();
}

function nomSecurise(nom) {
    return nom.replace(/[<>:"/\\|?*]/g, "_");
}

function regrouperParLignes(items) {
    const lignes = [];
    const tolerance = 2;

    const tries = [...items].sort((a, b) => b.y - a.y);

    for (const item of tries) {
        let ligne = lignes.find(l => Math.abs(l.y - item.y) <= tolerance);

        if (!ligne) {
            ligne = { y: item.y, mots: [] };
            lignes.push(ligne);
        }

        ligne.mots.push(item);
    }

    lignes.sort((a, b) => b.y - a.y);

    for (const ligne of lignes) {
        ligne.mots.sort((a, b) => a.x - b.x);
    }

    return lignes;
}

function extraireInformations(items) {

    const texteComplet = items.map(i => i.texte).join(" ");

    const etage =
        ETAGES.find(e =>
            texteComplet.toLowerCase().includes(e.toLowerCase())
        );

    if (!etage) {
        throw new Error("Étage introuvable.");
    }

    const lignes = regrouperParLignes(items);

    const index = lignes.findIndex(l => {
        const texte = l.mots.map(m => m.texte).join(" ");
        return texte.includes("Porte")
            && texte.includes("Rang")
            && texte.includes("Num");
    });

    if (index === -1) {
        throw new Error("Ligne Porte/Rang/Numéro introuvable.");
    }

    const valeurs = lignes[index + 1];

    if (!valeurs || valeurs.mots.length < 3) {
        throw new Error("Valeurs Porte/Rang/Place introuvables.");
    }

    const [v1, v2, v3] = valeurs.mots.map(m => m.texte);

    if (!/^\d+$/.test(v1) || Number(v1) > 23) {
        throw new Error(`Porte invalide : ${v1}`);
    }

    if (!/^[A-Za-z]{1,2}$/.test(v2)) {
        throw new Error(`Rang invalide : ${v2}`);
    }

    if (!/^\d+[A-Za-z]?$/.test(v3)) {
        throw new Error(`Place invalide : ${v3}`);
    }

    return {
        etage,
        porte: v1,
        rang: v2.toUpperCase(),
        place: v3
    };
}

async function analyserPDF(fichier) {

    const buffer = await fichier.arrayBuffer();

    const pdf = await pdfjsLib.getDocument({
        data: buffer
    }).promise;

    const page = await pdf.getPage(1);

    const contenu = await page.getTextContent();

    const items = contenu.items
        .map(i => ({
            texte: normaliser(i.str),
            x: i.transform[4],
            y: i.transform[5]
        }))
        .filter(i => i.texte);

    return {
        infos: extraireInformations(items),
        buffer
    };
}

traiter.addEventListener("click", async () => {

    if (!fichiers.files.length) {
        resultat.textContent = "Veuillez sélectionner au moins un PDF.";
        return;
    }

    traiter.disabled = true;

    const zip = new JSZip();

    const erreurs = [];

    let ok = 0;

    try {

        for (let i = 0; i < fichiers.files.length; i++) {

            const fichier = fichiers.files[i];

            resultat.innerHTML =
                `Analyse ${i + 1}/${fichiers.files.length}<br><strong>${fichier.name}</strong>`;

            try {

                const { infos, buffer } = await analyserPDF(fichier);

                const chemin =
                    `${nomSecurise(infos.etage)}/` +
                    `Rang ${infos.rang}/` +
                    `${nomSecurise(infos.etage)}_Porte_${infos.porte}_Rang_${infos.rang}_Place_${infos.place}.pdf`;

                zip.file(chemin, buffer);

                ok++;

            } catch (e) {

                erreurs.push(`${fichier.name} : ${e.message}`);
            }
        }

        if (erreurs.length) {
            zip.file("erreurs.txt", erreurs.join("\n"));
        }

        const blob = await zip.generateAsync({ type: "blob" });

        const lien = document.createElement("a");
        lien.href = URL.createObjectURL(blob);
        lien.download = "Billets-renommes.zip";
        lien.textContent = "Télécharger le ZIP";
        lien.style.display = "inline-block";
        lien.style.marginTop = "15px";

        resultat.innerHTML =
            `<strong>${ok}</strong> billet(s) traité(s)<br>` +
            `<strong>${erreurs.length}</strong> erreur(s)<br><br>`;

        resultat.appendChild(lien);

    } finally {

        traiter.disabled = false;
    }
});
