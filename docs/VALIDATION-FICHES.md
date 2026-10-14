# Relecture et validation des fiches — démarche multi-sources

## Principes

Aucun référentiel n'est la source principale ou une autorité de validation automatique. CLARUS D3.2, NIST, SWGDE, ANSSI, FranceTerme, ISO/IEC, ENFSI, INTERPOL et les documentations techniques éditeurs sont des références à mobiliser **selon la pertinence du sujet**, leur disponibilité et les conditions de réutilisation. Le [référentiel documentaire](../sources/REFERENTIEL.md) centralise les notices et les précautions juridiques.

Le lexique produit ses propres définitions françaises et formulations de rapport. Une source citée documente une notion ou un usage ; elle ne cautionne ni la fiche entière, ni sa rédaction, ni le projet.

## Circuit de traitement

1. **Proposition / à relire** — conserver l'identifiant stable, les synonymes, termes proches, anciens accès de recherche et formulations existantes.
2. **Analyse documentaire** — sélectionner plusieurs références indépendantes pertinentes lorsque disponibles ; relever, pour chacune, le document ou l'entrée exacts, la date/version, l'URL et la portée du terme.
3. **Confrontation** — comparer les définitions, les distinctions de sens, les conditions d'emploi et les éventuelles divergences. Ne pas compter le nombre de références comme preuve de justesse ; préciser quand une seule source a pu être vérifiée.
4. **Rédaction** — produire une définition originale, des synonymes exacts, des termes proches distincts, et des formulations de rapport prudentes et contextualisées, sans reprise protégée non autorisée.
5. **Décision** — statut « à relire », « à corriger » ou « validée » après contrôle humain explicite ; consignation du motif, des références examinées et des limites.
6. **Publication** — modifier `data/lexique.json` puis synchroniser `extension/data/lexique.json` et régénérer le catalogue des fiches selon la procédure de mise à jour.

## Fusion, regroupement et anciens accès

Les fiches qui expriment exactement le même concept peuvent être regroupées **après relecture**. Conserver dans la fiche principale les formulations utiles, les références, les nuances et les termes de recherche antérieurs ; mettre en place des alias/renvois afin qu'une ancienne recherche aboutisse toujours à la fiche retenue. Ne pas fusionner des notions proches mais distinctes, par exemple « carving » et « données supprimées ». Vérifier les renvois depuis les scénarios et les autres fiches avant suppression d'un identifiant.

## Traçabilité minimale de la relecture

Pour chaque fiche revue, consigner : identifiant, terme, références effectivement examinées (nom exact, URL, version/date ou absence), convergences/divergences, limites de réutilisation, changements proposés, statut de validation et décision humaine. Les références non consultées ne doivent pas être présentées comme des sources vérifiées. Les audits datés restent des instantanés historiques et ne sont pas des preuves de validation actuelle.

## Vérifications techniques

- Conserver les clés JSON et les identifiants tant qu'une migration complète n'est pas prévue.
- Vérifier que `data/` et `extension/data/` restent synchronisés.
- Vérifier la recherche par terme, synonymes et anciens accès après fusion.
- Vérifier les scénarios, les liens et les formulations de rapport.
- Soumettre les modifications de contenu à une PR et à la revue humaine avant publication.

## Registre et statuts publiés

Le registre `data/validation_fiches.json` consigne les validations explicites avec les champs `statut: validee`, `date`, `validateur` et `reference`. Une fiche absente du registre apparaît « En attente de relecture » dans le catalogue ; aucune fiche historique n’est validée automatiquement. Les propositions utilisateur restent distinctes des fiches officielles et leur transmission est volontaire.

Après une modification substantielle d’une fiche validée, retirer son entrée jusqu’à nouvelle relecture. Le catalogue affiche la date, le validateur et la référence de la décision. Ces statuts éditoriaux ne constituent pas une certification et ne sont pas encore affichés dans l’extension.
