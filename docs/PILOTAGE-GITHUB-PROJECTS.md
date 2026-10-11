# Synchronisation GitHub Projects — Lexique

Ce workflow ajoute automatiquement les nouvelles issues et PR ouvertes au Project personnel
`jmarande/1` et synchronise le champ `Priority` quand un préfixe P0/P1/P2 figure
dans le titre ou dans les labels. Il **ne modifie pas Status** : les workflows natifs
du Project conservent la responsabilité de la transition de statut.

## Autorisation préalable

1. Créer de préférence un jeton à droits restreints disposant de l'accès
   nécessaire au **Project personnel** et à la lecture des issues/PR du dépôt.
   Vérifier les autorisations supportées par le type de jeton choisi ;
   un jeton classique avec les portées `project` et, pour un dépôt privé,
   `repo` peut être nécessaire.
2. Ajouter ce jeton uniquement dans **Settings → Secrets and variables → Actions**
   du dépôt Lexique avec le nom exact `PROJECT_SYNC_TOKEN`.
3. Ne jamais placer le jeton dans le code, les issues, les logs ni la conversation.
4. Fusionner la PR seulement après vérification du workflow et du secret.
5. Pour le tester, ouvrir ou modifier une issue Lexique puis contrôler la carte
   dans le Project. Les éléments historiques peuvent être ajoutés manuellement.

## Règles
- Sans P0/P1/P2 explicite, ne modifie pas le champ Priority existant.
- Ne change pas les statuts ni les éléments fermés.
- Un jeton absent entraîne un échec explicite (pas de faux succès).
- Aucun changement de dépôt ConstatBox ni d'autres projets.
- Les événements issus de PR de forks ne reçoivent pas le secret.

## Limites

L'API GraphQL de Projects peut nécessiter d'ajuster les permissions du jeton ;
le workflow n'est pas opérationnel avant configuration et essai réel. Pour éviter
les permissions excessives, privilégier un jeton dédié et révocable.
