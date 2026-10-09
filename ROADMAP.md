# Roadmap

État au 9 octobre 2026.

## Socle actuel

Le projet dispose désormais d’un socle fonctionnel comprenant :

- lexique officiel et termes utilisateur ;
- catégories et recherche ;
- formulations de rapport ;
- scénarios officiels et scénarios utilisateur ;
- vérification terminologique du document ;
- francisation de libellés d’exports forensiques ;
- occurrences officielles et occurrences utilisateur ;
- export / import global des données utilisateur ;
- mise à jour automatisée par GitHub Releases.

## Priorités courtes

### Vérification du document

- proposer le choix entre plusieurs remplacements lorsqu’une occurrence en possède plusieurs ;
- ajouter **Remplacer toutes les occurrences** avec confirmation ;
- améliorer l’affichage du contexte autour de l’occurrence détectée ;
- enrichir progressivement la base de libellés issus d’exports Cellebrite, AXIOM, XRY, GrayKey et autres outils, en évitant les faux positifs.

### Données utilisateur

- améliorer la gestion des conflits lors d’un import fusionné ;
- afficher un résumé détaillé avant validation d’un remplacement de base ;
- conserver un format d’export versionné et rétrocompatible.

### Lexique

- simplifier les définitions trop longues ;
- clarifier les recouvrements entre notions proches ;
- conserver les conseils opérationnels dans les points d’attention plutôt que dans la définition ;
- poursuivre l’enrichissement des formulations situationnelles.

## Qualité et stabilité

- privilégier des fenêtres UNO simples et isolées ;
- éviter les modifications simultanées de plusieurs composants d’interface ;
- tester systématiquement ouverture, fermeture, sélection, insertion et persistance ;
- maintenir la compatibilité avec LibreOffice 7.4 ou supérieur ;
- garantir la synchronisation des données source et embarquées.

## Documentation

Maintenir à jour à chaque évolution significative :

- `README.md` ;
- `extension/README.md` et `README.txt` ;
- `CONTRIBUTING.md` ;
- `release/README.md` ;
- la présente roadmap.
