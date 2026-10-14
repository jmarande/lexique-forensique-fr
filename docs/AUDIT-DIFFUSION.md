# Audit de diffusion du lexique — 14 octobre 2026

## Périmètre et méthode

Examen des 91 entrées de `data/lexique.json`, de leurs définitions, champs complémentaires et formulations de rapport. Les fiches présentant des informations techniques suffisamment précises pour établir une cartographie ciblée d'artefacts iOS ont été exclues du catalogue public, par précaution. Les concepts courants, sans procédure de contournement ni information interne, demeurent publics.

## Décision

- 87 fiches maintenues dans le catalogue public.
- 4 fiches retirées des sources publiques et des fichiers Markdown générés : `biome-ios`, `biome-app-infocus-ios`, `knowledgec-ios`, `notification-and-suggestion-db-ios`.
- Les fiches génériques AFU/BFU, extraction, authentification, chiffrement et force brute restent diffusables : elles ne décrivent pas de procédure opérationnelle permettant de neutraliser une protection.
- Les futures contributions détaillant des chemins d'artefacts, tables, schémas, événements propriétaires, commandes d'exploitation ou limites opérationnelles particulières nécessitent une validation de diffusion avant intégration au dépôt public.

## Contrôle de publication

Le dépôt public est destiné aux seules fiches autorisées à la diffusion. Aucune fiche sensible ne doit être stockée dans `data/`, `fiches/`, les tests, les exemples, les releases ou un autre chemin public. Les contenus exclus doivent être conservés, s'ils sont nécessaires, dans un espace privé indépendant, avant toute éventuelle distribution contrôlée.

**Limite de cette mesure :** supprimer les fichiers de la branche principale ne supprime ni leur historique Git, ni d'éventuels clones, caches, archives, forks ou versions déjà téléchargées. Une suppression effective de l'historique demande une intervention spécifique et ne permet pas de rappeler les copies diffusées.
