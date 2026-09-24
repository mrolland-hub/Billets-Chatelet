const fichiers=document.getElementById("fichiers");
const nombre=document.getElementById("nombre");
const traiter=document.getElementById("traiter");
const resultat=document.getElementById("resultat");
const dropzone=document.getElementById("dropzone");

const ETAGES=[
"Orchestre",
"Corbeille",
"1er balcon",
"2ème balcon",
"Amphithéâtre Bas",
"Amphithéâtre Haut"
];

function mettreAJourNombre(){

const total=fichiers.files.length;

if(total===0)
nombre.textContent="Aucun fichier sélectionné.";
else if(total===1)
nombre.textContent="1 fichier sélectionné.";
else
nombre.textContent=`${total} fichiers sélectionnés.`;

}

fichiers.addEventListener("change",mettreAJourNombre);

dropzone.addEventListener("click",()=>fichiers.click());

["dragenter","dragover"].forEach(evt=>{

dropzone.addEventListener(evt,e=>{

e.preventDefault();
dropzone.classList.add("dragover");

});

});

["dragleave","drop"].forEach(evt=>{

dropzone.addEventListener(evt,e=>{

e.preventDefault();
dropzone.classList.remove("dragover");

});

});

dropzone.addEventListener("drop",e=>{

const pdfs=[...e.dataTransfer.files].filter(f=>
f.type==="application/pdf"||
f.name.toLowerCase().endsWith(".pdf")
);

const dt=new DataTransfer();

pdfs.forEach(f=>dt.items.add(f));

fichiers.files=dt.files;

mettreAJourNombre();

});

function normaliser(texte){

return texte
.replace(/\u00a0/g," ")
.replace(/\s+/g," ")
.trim();

}

function trouverEtage(mots){

const texte=mots.map(m=>m.texte).join(" ").toLowerCase();

return ETAGES.find(e=>texte.includes(e.toLowerCase()));

}

function trouverMot(mots,recherche){

return mots.find(m=>
m.texte.toLowerCase()===recherche.toLowerCase()
);

}

function trouverValeurSousLabel(mots,label,type){

const candidats=[];

for(const mot of mots){

if(mot.y>=label.y)
continue;

const distanceY=label.y-mot.y;
const distanceX=Math.abs(mot.x-label.x);

if(distanceY>100)
continue;

if(distanceX>100)
continue;

const texte=mot.texte;

if(type==="porte"){

if(!/^\d+$/.test(texte))
continue;

const n=Number(texte);

if(n<1||n>23)
continue;

}

if(type==="rang"){

if(!/^[A-Za-z]{1,2}$/.test(texte))
continue;

}

if(type==="place"){

if(!/^\d+[A-Za-z]?$/.test(texte))
continue;

}

const score=distanceY+distanceX*.5;

candidats.push({score,texte});

}

if(candidats.length===0)
return null;

candidats.sort((a,b)=>a.score-b.score);

return candidats[0].texte;

}

function extraireInformations(mots){

const etage=trouverEtage(mots);

const labelPorte=trouverMot(mots,"Porte");
const labelRang=trouverMot(mots,"Rang");
let labelNumero=trouverMot(mots,"Numéro")||trouverMot(mots,"Numero");

if(!labelPorte)
throw new Error("Libellé « Porte » introuvable.");

if(!labelRang)
throw new Error("Libellé « Rang » introuvable.");

if(!labelNumero)
throw new Error("Libellé « Numéro » introuvable.");

const porte=trouverValeurSousLabel(mots,labelPorte,"porte");
const rang=trouverValeurSousLabel(mots,labelRang,"rang");
const place=trouverValeurSousLabel(mots,labelNumero,"place");

if(!porte)
throw new Error("Porte introuvable.");

if(!rang)
throw new Error("Rang introuvable.");

if(!place)
throw new Error("Place introuvable.");

if(!etage)
throw new Error("Étage introuvable.");

return{
etage,
porte,
rang:rang.toUpperCase(),
place
};

}

function nomSecurise(nom){

return nom.replace(/[<>:"/\\|?*]/g,"_");

}

async function analyserPDF(fichier){

const donnees=await fichier.arrayBuffer();

const pdf=await pdfjsLib.getDocument({
data:donnees
}).promise;

const page=await pdf.getPage(1);

const contenu=await page.getTextContent();

const mots=contenu.items
.map(item=>({
texte:normaliser(item.str),
x:item.transform[4],
y:item.transform[5]
}))
.filter(m=>m.texte);

const infos=extraireInformations(mots);

return{
infos,
donnees
};

}

traiter.addEventListener("click",async()=>{

if(fichiers.files.length===0){

resultat.textContent="Veuillez sélectionner au moins un PDF.";
return;

}

traiter.disabled=true;

const zip=new JSZip();

let ok=0;
const erreurs=[];

try{

for(let i=0;i<fichiers.files.length;i++){

const fichier=fichiers.files[i];

resultat.innerHTML=
`Analyse du billet ${i+1}/${fichiers.files.length}<br><strong>${fichier.name}</strong>`;

try{

const{infos,donnees}=await analyserPDF(fichier);

const chemin=
`${nomSecurise(infos.etage)}/`+
`Rang ${nomSecurise(infos.rang)}/`+
`${nomSecurise(infos.etage)}_Porte_${infos.porte}_Rang_${infos.rang}_Place_${infos.place}.pdf`;

zip.file(chemin,donnees);

ok++;

}catch(e){

erreurs.push(`${fichier.name} : ${e.message}`);

}

}

if(erreurs.length)
zip.file("erreurs.txt",erreurs.join("\n"));

const blob=await zip.generateAsync({type:"blob"});

resultat.innerHTML=
`Traitement terminé.

${ok} billet(s) traité(s).
${erreurs.length} erreur(s).

`;

const lien=document.createElement("a");

lien.href=URL.createObjectURL(blob);
lien.download="Billets-renommes.zip";
lien.textContent="Télécharger le ZIP";

lien.style.display="inline-block";
lien.style.marginTop="15px";
lien.style.padding="12px 20px";
lien.style.background="#222";
lien.style.color="white";
lien.style.textDecoration="none";
lien.style.borderRadius="8px";

resultat.appendChild(lien);

}catch(e){

console.error(e);

resultat.innerHTML=`Erreur :

${e.message}`;

}finally{

traiter.disabled=false;

}

});
