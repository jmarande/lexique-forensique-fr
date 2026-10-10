# Référentiel documentaire — Lexique forensique FR

État initial : 10 octobre 2026. Références documentaires proposées pour vérifier et enrichir les entrées ; **aucune autorisation de reproduction intégrale n'est présumée**.

| ID | Organisme / ressource | Périmètre | Accès et référence | Politique d'intégration |
| --- | --- | --- | --- | --- |
| CLARUS-D32 | CLARUS — D3.2, *A searchable web-based common lexicon* | Terminologie de criminalistique numérique | [Document initial](CLARUS.md) | Conserver les références existantes ; recontrôler les notions et les droits de réutilisation |
| SWGDE-GLOSSARY | Scientific Working Group on Digital Evidence — *Digital & Multimedia Evidence Glossary* | Preuves numériques, informatique, multimédia | https://www.swgde.org/documents/published-complete-listing/05-f-001-swgde-digital-multimedia-evidence-glossary/ | Source de comparaison, **pas d'import massif** ; droits des documents à vérifier |
| NIST-CSRC-GLOSSARY | NIST Computer Security Resource Center — Glossary | Terminologie cybersécurité, digital forensics, provenance des définitions | https://csrc.nist.gov/glossary | Vérifier le document primaire cité par chaque définition ; ne pas attribuer systématiquement au NIST une définition agrégée |
| ANSSI-CYBERDICO | ANSSI — CyberDico | Traductions techniques français / anglais et cybersécurité | https://cyber.gouv.fr/cyberdico/ | Comparer les équivalents français ; contrôler les droits de reproduction avant tout import |
| FRANCE-TERME | Commission d'enrichissement de la langue française — FranceTerme | Terminologie française officielle | https://www.culture.fr/franceterme | Vérifier l'entrée, son domaine et sa publication ; indiquer le statut officiel lorsqu'il est établi |
| ISO-IEC-27037 | ISO/IEC 27037 — Guidelines for identification, collection, acquisition and preservation of digital evidence | Collecte, acquisition, préservation | https://www.iso.org/search.html?q=ISO%2FIEC%2027037 | Référence normative : consultation selon accès autorisé, sans reproduction des clauses |
| ISO-IEC-27042 | ISO/IEC 27042 — Guidelines for the analysis and interpretation of digital evidence | Analyse, interprétation | https://www.iso.org/search.html?q=ISO%2FIEC%2027042 | Référence normative : consultation selon accès autorisé, sans reproduction des clauses |
| INTERPOL-DF | INTERPOL — ressources de criminalistique numérique | Intervention et méthodes forensiques | https://www.interpol.int/ | Identifier d'abord le guide exact, son édition et ses conditions |
| ENFSI-DF | ENFSI — Best Practice Manuals | Qualité et pratiques forensiques | https://enfsi.eu/documents/best-practice-manuals/ | Identifier l'édition exacte avant de s'en servir pour valider une fiche |

## Règles éditoriales

1. Une **source** atteste un concept, et non nécessairement la phrase française produite pour le lexique.
2. Une **traduction recommandée** doit être distinguée d'une définition scientifique et d'une **formulation de rapport** rédigée par le projet.
3. Chaque proposition d'évolution consigne : ID de la fiche, terme concerné, source primaire, URL, version/date de la source si identifiable, observation et décision.
4. Une divergence entre plusieurs sources est documentée ; ne pas remplacer silencieusement une définition existante.
5. Les textes de normes, logos, tableaux et glossaires ne sont pas copiés automatiquement ; vérifier les licences et éventuelles autorisations de réutilisation, même si Lexique FR est sous GPL-3.0.
6. Les sources ne cautionnent pas automatiquement le projet et les formulations produites ne sont pas des citations des organismes.
7. Toute évolution des fichiers de données officiels doit synchroniser `data/` et `extension/data/`.

## Première vague de contrôle

- **SWGDE / CLARUS / NIST** : acquisition forensique, extraction, copie, image forensique, intégrité, empreinte numérique, traçabilité.
- **ANSSI / FranceTerme** : équivalents français courants et libellés techniques anglais.
- **ISO/IEC / ENFSI / INTERPOL** : vérifier les nuances entre constatation, collecte, acquisition, analyse et interprétation.

Une source supplémentaire n'est ajoutée dans `sources` d'une fiche qu'après examen humain du terme correspondant.

## Contrôle initial des conditions de réutilisation (10 octobre 2026)

**Portée :** examen des conditions générales publiées par les organismes ; ce contrôle ne dispense pas de vérifier la notice attachée à chaque document/édition et à chaque entrée. Ce tableau ne constitue pas un avis juridique.

| Source | Statut pour l'enrichissement distribué sous GPL-3.0 | Constat et document de référence |
| --- | --- | --- |
| FranceTerme (jeu de données officiel) | **Réutilisation possible avec attribution** | Licence Ouverte / Open Licence explicitement attachée au jeu de données : https://www.data.gouv.fr/datasets/base-franceterme-termes-scientifiques-et-techniques-1 ; https://www.culture.fr/franceterme/Mentions-legales . Conserver la mention du ministère, la licence et les modifications. |
| NIST (documents rédigés par son personnel) | **Réutilisation possible sous réserve des notices individuelles** | Le NIST accorde des droits mondiaux sur la plupart des productions concernées ; exceptions : contenus tiers, Standard Reference Data et autres mentions spécifiques. Citer le document original, pas seulement la page du glossaire : https://www.nist.gov/open/copyright-fair-use-and-licensing-statements-srd-data-software-and-technical-series-publications et https://csrc.nist.gov/glossary . |
| ANSSI / CyberDico | **Pas d'import libre validé** | Mentions légales : Licence Ouverte v1.0 sauf mention spécifique, mais exploitation commerciale soumise à autorisation préalable. Ne pas affirmer la compatibilité avec la redistribution GPL, qui permet l'usage commercial : https://cyber.gouv.fr/mentions-legales/ . Références et comparaison uniquement dans l'attente d'une clarification. |
| SWGDE | **Référence ; conditions à appliquer document par document** | Redistribution autorisée sous certaines conditions : conservation de la page de garde SWGDE, absence d'approbation implicite, mention du numéro de version/date lors des références ou citations. Ne pas incorporer de passages dans une base GPL sans étude de compatibilité et des conditions applicables au document : https://www.swgde.org/documents/Current%20Documents/ . |
| ISO/IEC 27037 et 27042 | **Référence uniquement ; reproduction exclue sans permission** | L'ISO réserve les droits de reproduction, notamment partielle, aux titulaires d'autorisation : https://www.iso.org/fr/copyright.html . |
| INTERPOL | **Référence uniquement ; import non autorisé par défaut** | Conditions spécifiques, limitations notamment sur les usages commerciaux, l'extraction automatisée et les reproductions nécessitant autorisation : https://www.interpol.int/en/Who-we-are/Terms-of-use . |
| ENFSI | **Référence uniquement ; licence de réutilisation GPL non établie** | Certains manuels permettent la diffusion et la traduction, avec droits d'auteur ENFSI et restrictions ; examiner la notice du manuel exact avant utilisation : https://enfsi.eu/wp-content/uploads/2017/06/Best-Practice-Manual-for-Forensic-Image-and-Video-Enhancement.pdf . |
| CLARUS D3.2 | **Conditions non déterminées** | Le document de référence précis, son éditeur, son dépôt officiel et sa licence doivent être retrouvés avant de réutiliser textuellement des passages. L'homonymie avec d'autres services « CLARUS » ne constitue pas une preuve de droits. |

**Décision provisoire :** commencer les enrichissements à partir de FranceTerme et de publications NIST dont les mentions confirment la réutilisation ; les autres sources sont utilisables pour orienter l'analyse et pour des références bibliographiques, sans reproduction de leur expression protégée. Conserver des attributions spécifiques aux données tierces : la présence d'un fichier LICENSE GPL à la racine ne transforme pas les œuvres de tiers en œuvres GPL.
