# Lexique forensique FR

Lexique français collaboratif de **criminalistique numérique**, accompagné d’une extension **LibreOffice Writer** destinée à la recherche terminologique, au contrôle de cohérence d’un rapport et à l’insertion de formulations rédactionnelles.

## Objectifs

Le projet vise à :

- proposer un vocabulaire français cohérent pour la criminalistique numérique ;
- rapprocher les termes français de leurs équivalents anglais ;
- fournir des définitions courtes, techniques et opérationnelles ;
- conserver les synonymes et, dans les données, les termes déconseillés ainsi que les sources ;
- proposer plusieurs formulations de rapport lorsque le contexte le justifie ;
- détecter dans un document Writer certains termes déconseillés et proposer leur remplacement ;
- conserver le lexique dans un format JSON réutilisable par d’autres outils.

## Extension LibreOffice Writer

L’extension permet actuellement de :

- rechercher un terme dans le lexique ;
- afficher sa fiche sans quitter le document ;
- vérifier le document actif et afficher les alertes terminologiques ;
- sélectionner une occurrence détectée et la remplacer individuellement ;
- afficher plusieurs formulations de rapport directement dans la fiche ;
- sélectionner une formulation dans la zone de droite et l’insérer dans Writer ;
- vérifier les mises à jour depuis GitHub et installer une nouvelle version.

La fenêtre est **non modale** : elle peut rester ouverte pendant la rédaction du rapport.

## Installation

Télécharger le fichier **`lexique-forensique-fr.oxt`** depuis la dernière GitHub Release, puis l’ouvrir avec LibreOffice.

> Le nom du fichier OXT doit rester exactement `lexique-forensique-fr.oxt`.

Après installation, redémarrer complètement LibreOffice si le menu **Lexique forensique** n’apparaît pas immédiatement.

## Données du lexique

Le lexique est conservé dans :

- `data/lexique.json` : source de données du dépôt ;
- `extension/data/lexique.json` : copie embarquée dans l’extension.

Ces deux fichiers doivent rester synchronisés.

Une entrée peut notamment contenir :

```json
{
  "id": "acquisition-forensique",
  "terme": "Acquisition forensique",
  "anglais": "Forensic acquisition",
  "categorie": "Méthode de criminalistique numérique",
  "definition": "…",
  "synonymes": ["Extraction"],
  "termes_deconseilles": [],
  "sources": ["CLARUS D3.2 — Forensic acquisition"],
  "formulations_rapport": [
    {
      "type": "Acquisition réalisée",
      "texte": "…"
    },
    {
      "type": "Acquisition partielle",
      "texte": "…"
    }
  ]
}
```

Les **termes déconseillés** et les **sources** restent présents dans les données même lorsqu’ils ne sont pas affichés dans la fiche de l’extension.

## Sources

Le projet s’appuie notamment sur le livrable européen **CLARUS D3.2 — A searchable web-based common lexicon**.

Les entrées françaises ne sont pas conçues comme une traduction littérale. Elles sont adaptées aux usages professionnels francophones tout en conservant, lorsque cela est pertinent, la correspondance avec la terminologie internationale et la traçabilité de la source.

Voir `sources/CLARUS.md`.

## Structure

```text
lexique-forensique-fr/
├── .github/workflows/release-oxt.yml
├── README.md
├── CONTRIBUTING.md
├── data/
│   └── lexique.json
├── extension/
│   ├── Addons.xcu
│   ├── META-INF/manifest.xml
│   ├── Scripts/python/lexique_forensique.py
│   ├── data/lexique.json
│   ├── description.xml
│   └── README.txt
├── release/
│   └── README.md
└── sources/
    └── CLARUS.md
```

## Version actuelle

**v0.7.15**

La distribution de l’extension est assurée par GitHub Actions et GitHub Releases.
