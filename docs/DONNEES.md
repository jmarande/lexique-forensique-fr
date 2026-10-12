# Données et organisation du dépôt

[Retour à la présentation du projet](../README.md)

Ce guide décrit le stockage des données, les formats réutilisables et les fichiers du projet. Pour modifier une fiche, suivre le [guide de mise à jour](MISE-A-JOUR-FICHES.md).

## Données officielles et données utilisateur

Les données fournies avec l’extension sont protégées. Les créations personnelles sont stockées dans le profil utilisateur, hors du paquet OXT :

```text
~/.lexique-forensique-fr/
├── lexique-utilisateur.json
├── scenarios-utilisateur.json
├── occurrences-utilisateur.json
└── sauvegardes/
```

Cela permet de mettre à jour l’extension sans perdre les données personnelles.

### Export / import

Le menu **Lexique forensique > Exporter / Importer…** permet d’exporter dans un seul fichier :

- les termes utilisateur ;
- les scénarios utilisateur ;
- les occurrences utilisateur.

À l’import :

- **Fusionner** conserve les données locales déjà présentes et ajoute les éléments absents ;
- **Remplacer** remplace uniquement les données utilisateur ;
- une sauvegarde automatique de la base locale est créée avant import.

Les données officielles embarquées dans l’extension ne sont jamais écrasées par cette opération.

**Contribuer :** [proposer une fiche au lexique](PROPOSER-UNE-FICHE.md).

**Aide :** accessible depuis le menu [Aide…](AIDE.md).

## Données du projet

Les données officielles existent en double : une copie source à la racine et une copie embarquée dans l’extension.

```text
data/
├── lexique.json
├── scenarios.json
└── traductions.json

extension/data/
├── lexique.json
├── scenarios.json
└── traductions.json
```

Les paires correspondantes doivent rester synchronisées.

### Entrée de lexique

```json
{
  "id": "acquisition-forensique",
  "terme": "Acquisition forensique",
  "anglais": "Forensic acquisition",
  "categorie": "Méthode de criminalistique numérique",
  "definition": "…",
  "synonymes": ["Extraction"],
  "termes_deconseilles": [],
  "sources": ["Référence documentaire précise — entrée, édition ou date (exemple fictif)"],
  "formulations_rapport": [
    {
      "type": "Acquisition réalisée",
      "texte": "…"
    }
  ]
}
```

### Scénarios

Les scénarios référencent les identifiants des termes et les types de formulations. Ils ne recopient pas les phrases du lexique : une évolution d’une formulation reste ainsi répercutée dans les scénarios.

### Occurrences et francisation

La base officielle `traductions.json` alimente le vérificateur avec des correspondances du type :

```json
{
  "anglais": "Missed Call",
  "francais": "Appel manqué",
  "note": "Statut d’appel non répondu."
}
```

Les règles utilisateur peuvent contenir une occurrence, plusieurs remplacements possibles et un remplacement préféré.

## Structure du dépôt

```text
lexique-forensique-fr/
├── .github/workflows/release-oxt.yml
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── ROADMAP.md
├── docs/
│   └── images/
│       ├── logo.png
│       ├── capture-lexique.jpg
│       └── capture-scenarios.jpg
├── data/
│   ├── lexique.json
│   ├── scenarios.json
│   └── traductions.json
├── extension/
│   ├── Addons.xcu
│   ├── META-INF/manifest.xml
│   ├── Scripts/python/lexique_forensique.py
│   ├── images/logo.png
│   ├── data/
│   │   ├── lexique.json
│   │   ├── scenarios.json
│   │   └── traductions.json
│   ├── description.xml
│   ├── README.md
│   └── README.txt
├── release/
│   └── README.md
└── sources/
    ├── REFERENTIEL.md
    ├── AUDIT-63-FICHES-2026-10-10.md
    └── AUDIT-INITIAL-2026-10-10.md
```

## Publication

Le paquet OXT est construit par GitHub Actions. Consulter le [guide de distribution](../release/README.md) pour préparer une version et vérifier sa publication.
