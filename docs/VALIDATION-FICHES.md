# Validation éditoriale des fiches

Le lexique distingue **deux états** :

- **En attente de relecture** : fiche publiée pour travail, sans validation terminologique définitive.
- **Validée** : fiche relue et explicitement approuvée après confrontation des sources pertinentes.

**Aucune fiche historique n'est présumée validée.** Toute fiche non mentionnée dans `data/validation_fiches.json` est *en attente de relecture*.

## Cycle de travail

1. Modifier la fiche dans `data/lexique.json` et synchroniser `extension/data/lexique.json`.
2. Croiser les sources pertinentes (NIST, SWGDE, FranceTerme, ANSSI, CLARUS, ISO, etc.) et documenter les concordances, divergences, références précises et droits de réutilisation.
3. Soumettre les modifications à la relecture via une PR.
4. Après approbation explicite, ajouter une entrée dans `data/validation_fiches.json` avec `statut: validee`, `date`, `validateur` et `reference` (numéro de PR ou lien vers la décision).
5. Régénérer les fiches : `python3 scripts/generate_fiches.py`. Le workflow automatique actualise le catalogue après une modification sur `main`.
6. Si le contenu substantiel d'une fiche validée change, **retirer son entrée de validation dans la même PR** et la repasser en attente de relecture jusqu'à nouvelle approbation.

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
