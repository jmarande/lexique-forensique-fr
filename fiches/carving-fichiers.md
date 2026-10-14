# Carving de fichiers

**Classification :** 🔬 Méthodologie forensique → Examen et analyse

**Équivalent anglais :** File carving / Data carving

## Définition

Technique de récupération consistant à rechercher et, lorsque cela est possible, à reconstituer des fichiers à partir de leur contenu binaire, notamment de leurs signatures, de leurs structures internes ou d'autres caractéristiques propres à leur format, sans nécessiter les métadonnées d'allocation du système de fichiers. Cette méthode peut être employée sur des données brutes accessibles, notamment dans les espaces non alloués, et permet éventuellement de retrouver des fichiers dont les références d'origine sont absentes ou inexploitables. Les fichiers obtenus peuvent être complets ou partiels, et leur récupération ne démontre pas nécessairement qu'ils ont été supprimés.

## Synonymes

- File carving
- Data carving
- Extraction par signature

## Formulations pour rapport

### Recherche par carving réalisée

Nous procédons à une recherche de fichiers par carving à partir des données accessibles du support examiné.

### Fichiers identifiés par carving

Les opérations de carving permettent d'identifier et de reconstituer des fichiers à partir des données examinées, sans nécessairement permettre de retrouver leur nom ou leur emplacement d'origine.

### Récupération partielle

Les opérations de carving permettent de récupérer partiellement certains fichiers, dont le contenu demeure incomplet.

### Absence de résultat exploitable

Les opérations de carving réalisées ne permettent pas d'identifier de fichiers exploitables dans les données examinées.

### Limites d'interprétation

Les fichiers récupérés par carving peuvent être incomplets ou dépourvus de certaines métadonnées. Leur présence ne permet pas, à elle seule, de déterminer les circonstances de leur création, de leur utilisation ou de leur éventuelle suppression.

> Ces fiches sont des documents de travail du projet : les définitions restent soumises à la revue terminologique et documentaire.

[← Retour à l’index](README.md)
