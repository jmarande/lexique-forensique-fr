# Lexique forensique FR

Lexique français collaboratif de **criminalistique numérique** accompagné d’une extension **LibreOffice Writer** destinée à la recherche terminologique, à la normalisation des rapports et à la francisation de libellés issus d’exports de logiciels forensiques.

## Objectifs

Le projet vise à :

- proposer un vocabulaire français cohérent pour la criminalistique numérique ;
- rapprocher les termes français de leurs équivalents anglais ;
- fournir des définitions courtes, techniques et opérationnelles ;
- conserver synonymes, termes déconseillés, sources et points d’attention ;
- proposer plusieurs formulations de rapport lorsque le contexte le justifie ;
- détecter dans Writer des termes déconseillés ou des libellés anglais à franciser ;
- permettre à l’utilisateur d’enrichir ses propres termes, scénarios et occurrences ;
- conserver les données dans des formats JSON simples et réutilisables.

## Extension LibreOffice Writer

L’extension propose actuellement :

- **Recherche terminologique** avec recherche insensible à la casse et aux accents ;
- **Filtre par catégorie** ;
- **Fiches de termes** avec définition, anglais, catégorie, synonymes et formulations pour rapport ;
- **Insertion d’une formulation** dans le document Writer ;
- **Vérification du document** dans une fenêtre dédiée ;
- détection des **termes déconseillés** ;
- détection et francisation de **libellés anglais** d’exports forensiques ;
- remplacement d’une occurrence détectée ;
- **Occurrences utilisateur** : création, modification et suppression de règles personnelles ;
- **Scénarios de rédaction** composés de plusieurs formulations du lexique ;
- création, duplication, modification et suppression de scénarios utilisateur ;
- **Gestion des termes utilisateur** avec catégories et formulations personnalisées ;
- **Export / import** de toutes les données utilisateur dans un fichier JSON unique ;
- import avec choix entre **fusionner** et **remplacer** la base utilisateur ;
- vérification et installation des mises à jour depuis GitHub.

Les fenêtres principales de travail sont non modales lorsque cela est utile afin de pouvoir continuer à rédiger dans Writer.

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

## Installation

Télécharger **`lexique-forensique-fr.oxt`** depuis la dernière GitHub Release puis l’ouvrir avec LibreOffice.

> Le nom du fichier OXT doit rester exactement `lexique-forensique-fr.oxt`, car les URL de scripts de `extension/Addons.xcu` dépendent de ce nom.

Après installation, redémarrer complètement LibreOffice si le menu **Lexique forensique** n’apparaît pas immédiatement.

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
  "sources": ["CLARUS D3.2 — Forensic acquisition"],
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

## Sources

Le projet s’appuie notamment sur **CLARUS D3.2 — A searchable web-based common lexicon**.

Les entrées françaises ne sont pas nécessairement des traductions littérales : elles sont adaptées à l’usage professionnel francophone, tout en conservant la terminologie internationale et la traçabilité de la source lorsqu’elles sont disponibles.

Voir `sources/CLARUS.md`.

## Structure du dépôt

```text
lexique-forensique-fr/
├── .github/workflows/release-oxt.yml
├── README.md
├── CONTRIBUTING.md
├── ROADMAP.md
├── data/
│   ├── lexique.json
│   ├── scenarios.json
│   └── traductions.json
├── extension/
│   ├── Addons.xcu
│   ├── META-INF/manifest.xml
│   ├── Scripts/python/lexique_forensique.py
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
    └── CLARUS.md
```

## Version

Dernière version publiée au 9 octobre 2026 : **v0.8.1**.

La distribution est construite automatiquement par GitHub Actions et publiée dans GitHub Releases.
