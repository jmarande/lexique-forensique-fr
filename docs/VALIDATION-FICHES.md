# Validation éditoriale des fiches

Le projet distingue **trois états éditoriaux** et sépare les fiches personnelles des propositions destinées à la communauté :

- **Proposée** : contribution d'un utilisateur soumise à examen, qui n'entre pas encore dans la base officielle.


- **En attente de relecture** : fiche publiée pour travail, sans validation terminologique définitive.
- **Validée** : fiche relue et explicitement approuvée après confrontation des sources pertinentes.

Une fiche personnelle reste dans le profil LibreOffice de son auteur ; elle n'est pas publiée ni proposée automatiquement. La proposition à la communauté est une action volontaire. Elle doit passer par un canal de contribution (par exemple une issue GitHub avec les champs nécessaires) et faire l'objet d'une première sélection avant d'être ajoutée à la base officielle.

**Aucune fiche historique n'est présumée validée.** Toute fiche non mentionnée dans `data/validation_fiches.json` est *en attente de relecture*.

## Contenu d'une fiche proposée

Toute proposition comprend : **terme français**, **équivalent anglais** (si applicable), **catégorie**, **définition**, **synonymes**, **références documentaires** et **formulations pour rapport**. Les formulations constituent une liste de variantes, chacune avec un **intitulé de situation** (`type`) et un **texte prêt à utiliser** (`texte`). L'utilisateur peut proposer plusieurs variantes, les modifier et en laisser aucune si le terme ne s'y prête pas. Elles restent **à relire**, comme la définition, et ne sont jamais approuvées automatiquement.

Exemples de situations : « Opération réalisée », « Résultat partiel », « Opération impossible », « Limite d'interprétation ». La rédaction doit rester factuelle et ne pas conclure au-delà des observations.

## Cycle de travail

1. Pour une contribution utilisateur, conserver la fiche personnelle localement et soumettre volontairement une proposition via le canal de contribution. Après première sélection, intégrer la fiche dans le lexique avec le statut « En attente de relecture ».
2. Modifier la fiche dans `data/lexique.json` et synchroniser `extension/data/lexique.json`.
3. Croiser les sources pertinentes (NIST, SWGDE, FranceTerme, ANSSI, CLARUS, ISO, etc.) et documenter les concordances, divergences, références précises et droits de réutilisation.
4. Soumettre les modifications à la relecture via une PR.
5. Après approbation explicite, ajouter une entrée dans `data/validation_fiches.json` avec `statut: validee`, `date`, `validateur` et `reference` (numéro de PR ou lien vers la décision).
6. Régénérer les fiches : `python3 scripts/generate_fiches.py`. Le workflow automatique actualise le catalogue après une modification sur `main`.
7. Si le contenu substantiel d'une fiche validée change, **retirer son entrée de validation dans la même PR** et la repasser en attente de relecture jusqu'à nouvelle approbation.

Exemple de validation à renseigner seulement après décision humaine :

```json
{
  "acquisition-forensique": {
    "statut": "validee",
    "date": "AAAA-MM-JJ",
    "validateur": "Identifiant du relecteur",
    "reference": "Lien vers la revue ou PR approuvée"
  }
}
```

Les statuts indiquent une **validation éditoriale du projet**, pas une homologation par les organismes cités ni une garantie juridique. Les fiches demeurent consultables même en attente de relecture. La version de l'extension LibreOffice existante n'affiche pas encore ces statuts.
