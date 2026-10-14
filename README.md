<p align="center">
  <img src="docs/images/logo.png" alt="Logo Lexique forensique FR" width="150">
</p>

<h1 align="center">Lexique forensique FR</h1>

<p align="center">
  <strong>Le vocabulaire de la criminalistique numérique, au service de vos rapports.</strong><br>
  Un lexique français collaboratif et une extension pour LibreOffice Writer.
</p>

<p align="center">
  <a href="https://github.com/jmarande/lexique-forensique-fr/releases/latest"><img src="https://img.shields.io/github/v/release/jmarande/lexique-forensique-fr?label=version&amp;color=17365d" alt="Dernière version publiée"></a>
  <a href="extension/README.md"><img src="https://img.shields.io/badge/LibreOffice-7.4%2B-187443" alt="LibreOffice 7.4 ou supérieur"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/licence-GPL--3.0--only-52647a" alt="Licence GPL-3.0-only"></a>
</p>

<p align="center">
  <a href="https://github.com/jmarande/lexique-forensique-fr/releases/latest/download/lexique-forensique-fr.oxt"><strong>Télécharger l’extension</strong></a> ·
  <a href="fiches/README.md"><strong>Consulter les fiches</strong></a> ·
  <a href="docs/AIDE.md">Guide d’utilisation</a> ·
  <a href="CONTRIBUTING.md">Contribuer</a>
</p>

---

## Un vocabulaire commun pour des rapports précis

**Lexique forensique FR** accompagne les professionnels de la criminalistique numérique dans la recherche d’un terme, la compréhension d’une notion et la rédaction en français. Il rassemble des définitions, des équivalents anglais, des synonymes, des termes proches et des formulations adaptées à différentes situations d’examen.

Le [catalogue des fiches](fiches/README.md) se consulte directement sur GitHub. L’extension intègre ces ressources à **LibreOffice Writer** pour les utiliser pendant la rédaction.

## Le lexique en chiffres

| Ressource disponible | Nombre |
| --- | ---: |
| [Fiches terminologiques](fiches/README.md) | **89** |
| Formulations de rapport | **429** |
| Scénarios de rédaction | **5** |
| Règles de francisation des libellés | **18** |

*Chiffres calculés à partir de la base officielle du dépôt au 14 octobre 2026, hors données personnelles. Le catalogue évolue au fil des relectures ; le contenu installé dépend de la version de l’extension.*

## Ce que permet l’extension

| Usage | Fonctionnalités |
| --- | --- |
| **Rechercher un terme** | Recherche insensible à la casse et aux accents, recherche par synonymes et filtre par catégorie. |
| **Rédiger un rapport** | Consultation des fiches et insertion d’une formulation correspondant à la situation rencontrée. |
| **Préparer un scénario** | Assemblage de plusieurs formulations ; création, duplication et modification de scénarios personnels. |
| **Vérifier un document** | Repérage de termes déconseillés et de libellés anglais d’exports forensiques, avec remplacement d’une occurrence. |
| **Enrichir ses ressources** | Création de termes, de formulations et de règles de détection personnelles. |
| **Sauvegarder et partager** | Export et import de la base personnelle ; proposition d’une ou plusieurs fiches au projet depuis l’extension. |

La consultation du lexique, la rédaction et l’aide intégrée fonctionnent **hors ligne**. Le téléchargement des mises à jour et la proposition de fiches sur GitHub nécessitent une connexion.

## Aperçu dans LibreOffice Writer

### Rechercher, comprendre et insérer une formulation

<p align="center">
  <a href="docs/images/capture-lexique.jpg"><img src="docs/images/capture-lexique.jpg" alt="Recherche d’un terme et sélection d’une formulation de rapport dans Writer" width="620"></a>
</p>

### Assembler plusieurs formulations dans un scénario

<p align="center">
  <a href="docs/images/capture-scenarios.jpg"><img src="docs/images/capture-scenarios.jpg" alt="Scénario de rédaction composé de plusieurs formulations du lexique" width="700"></a>
</p>

*Captures d’une version antérieure : certains libellés et la disposition des commandes peuvent différer de la version actuelle.*

## Installer et commencer

**Prérequis : LibreOffice 7.4 ou supérieur, avec Writer.**

1. Télécharger [**lexique-forensique-fr.oxt**](https://github.com/jmarande/lexique-forensique-fr/releases/latest/download/lexique-forensique-fr.oxt), le paquet de la dernière version publiée.
2. Ouvrir le fichier avec LibreOffice et confirmer l’installation. Redémarrer complètement LibreOffice si nécessaire.
3. Dans Writer, ouvrir **Lexique forensique > Rechercher un terme…**, puis choisir une fiche et une formulation à insérer.

Conserver le nom **`lexique-forensique-fr.oxt`** : il est nécessaire au fonctionnement de l’extension.

**Au quotidien :** le menu **Aide…** ouvre une aide consultable hors ligne. Le menu **Mettre à jour…** recherche la dernière version et présente ses notes de publication.

[Consulter les versions et leurs nouveautés](https://github.com/jmarande/lexique-forensique-fr/releases) · [Ouvrir le guide d’utilisation](docs/AIDE.md)

## Vos ressources personnelles

Vos **termes, scénarios et occurrences** sont enregistrés localement, séparément des données fournies avec l’extension. Ils sont conservés lors des mises à jour.

Le menu **Exporter / Importer…** permet de sauvegarder l’ensemble dans un fichier JSON. L’import propose de **fusionner** les données ou de **remplacer** la base personnelle, avec sauvegarde automatique préalable. Les données officielles ne sont pas écrasées par l’import.

[Comprendre le stockage et les formats de données](docs/DONNEES.md)

## Une démarche documentaire fondée sur plusieurs sources

**Le projet est indépendant.** Il rédige ses propres définitions françaises et formulations de rapport en confrontant, selon le sujet, les références pertinentes : **NIST, SWGDE, CLARUS D3.2, ANSSI, FranceTerme**, ainsi que d’autres guides méthodologiques et documentations techniques. Aucune source ne bénéficie d’une priorité automatique ; les organismes cités ne sont ni éditeurs ni garants du projet.

La relecture des fiches se poursuit progressivement : une fiche disponible n’est pas nécessairement une fiche validée. Le circuit prévoit une analyse documentaire, la comparaison des concepts et une **validation humaine explicite**. Les formulations proposées restent à adapter aux constatations et aux limites de chaque examen.

Les références documentent les notions et leurs usages. Leur citation ne vaut pas autorisation de reproduction ; les conditions de réutilisation de chaque source doivent être respectées.

[Référentiel commun des sources](sources/REFERENTIEL.md) · [Méthode de relecture et de validation](docs/VALIDATION-FICHES.md)

## Participer au projet

Vous pouvez proposer un terme, préciser une définition, enrichir une formulation ou signaler un dysfonctionnement.

- **Depuis Writer :** dans **Exporter / Importer…**, sélectionner une ou plusieurs fiches personnelles et préparer leur proposition au lexique.
- **Depuis GitHub :** suivre le [guide de contribution](CONTRIBUTING.md) ou [ouvrir une issue](https://github.com/jmarande/lexique-forensique-fr/issues/new/choose).

La proposition depuis l’extension ouvre un formulaire prérempli : elle n’est publiée qu’après votre confirmation sur GitHub. Vérifiez son contenu avant publication et retirez toute donnée personnelle, confidentielle ou issue d’une procédure. Les propositions sont relues avant leur éventuelle intégration.

[Comment proposer une fiche](docs/PROPOSER-UNE-FICHE.md) · [Comment mettre à jour une fiche](docs/MISE-A-JOUR-FICHES.md)

## Documentation et suivi

| Ressource | Contenu |
| --- | --- |
| [Catalogue des fiches](fiches/README.md) | Index alphabétique, définitions et formulations de rapport. |
| [Aide utilisateur](docs/AIDE.md) | Prise en main et principaux parcours dans Writer. |
| [Extension Writer](extension/README.md) | Fonctionnement de l’extension et mises à jour. |
| [Données et organisation du dépôt](docs/DONNEES.md) | Stockage local, formats JSON et structure du projet. |
| [Sources et validation](docs/VALIDATION-FICHES.md) | Méthode documentaire et critères de relecture. |
| [Feuille de route](ROADMAP.md) | Priorités et évolutions prévues. |
| [Distribution des versions](release/README.md) | Construction du paquet OXT et publication. |

Les [issues du projet](https://github.com/jmarande/lexique-forensique-fr/issues) détaillent les travaux en cours. Les audits [initial](sources/AUDIT-INITIAL-2026-10-10.md) et [des 63 fiches au 10 octobre 2026](sources/AUDIT-63-FICHES-2026-10-10.md) restent consultables comme états historiques.

## Licence

Lexique forensique FR est distribué sous licence **GNU GPL-3.0-only**. Consulter le fichier [LICENSE](LICENSE) pour le texte intégral.
