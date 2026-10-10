# Mettre à jour les fiches du lexique

Le fichier **`data/lexique.json` est la source de vérité**. Les pages du dossier `fiches/` sont **générées automatiquement** : ne les modifiez pas directement, car vos changements seraient écrasés à la prochaine génération.

## Méthode simple, depuis GitHub

1. Ouvrir [`data/lexique.json`](../data/lexique.json) et cliquer sur le crayon **Edit this file**.
2. Rechercher l'identifiant stable (`id`) ou le terme (`terme`) de la fiche.
3. Modifier les champs nécessaires : `definition`, `anglais`, `synonymes`, `categorie`, `formulations_rapport`, etc. Conserver un JSON valide et un `id` unique. Pour ajouter une formulation, respecter les propriétés `type` et `texte`.
4. Enregistrer via **Commit changes**, de préférence dans une branche / pull request pour permettre la revue terminologique.
5. **Synchroniser également `extension/data/lexique.json` avec le contenu exact de `data/lexique.json`** : l'extension LibreOffice utilise la copie embarquée. Sans cette étape, le catalogue GitHub et l'extension peuvent diverger.
6. Après intégration sur `main`, le workflow **Catalogue des fiches Markdown** régénère automatiquement l'index et les fiches, puis crée un commit si elles ont changé. Vérifier son exécution dans l'onglet **Actions** et le résultat dans [le catalogue](../fiches/README.md).

> Si le workflow ne peut pas pousser (permissions GitHub Actions, protections de branche, exécution désactivée), la génération devra être lancée localement et les fichiers produits seront à committer manuellement.

## Méthode locale

Depuis la racine du dépôt :

```bash
python3 -m json.tool data/lexique.json > /dev/null
cp data/lexique.json extension/data/lexique.json
python3 scripts/generate_fiches.py
git add data/lexique.json extension/data/lexique.json fiches/
git commit -m "Mettre à jour les fiches du lexique"
git push
```

Ne lancez `git push` qu'après avoir vérifié le diff, les droits de réutilisation et le contenu des formulations.

## Ajouter une nouvelle fiche

Insérer un nouvel objet dans le tableau `data/lexique.json`, avec au minimum un `id` unique et stable, un `terme`, une `categorie`, une `definition` et une liste `sources`. Exemple fictif :

```json
{
  "id": "terme-exemple",
  "terme": "Terme exemple",
  "anglais": "Example term",
  "categorie": "Méthode de criminalistique numérique",
  "definition": "Définition originale à valider.",
  "synonymes": [],
  "termes_deconseilles": [],
  "sources": ["Référence à contrôler"],
  "formulations_rapport": []
}
```

## Contrôles avant validation

- Vérifier la précision technique, les synonymes, les limites d'interprétation et les formulations.
- Citer les références exactes et vérifier les droits de réutilisation : **la présence d'une source ne donne pas le droit d'en recopier le texte**.
- Vérifier la validité du JSON et l'unicité des identifiants.
- Vérifier que `data/lexique.json` et `extension/data/lexique.json` sont identiques.
- Vérifier le résultat dans le catalogue et dans l'extension lors de la prochaine version distribuée.

Le catalogue ne modifie pas automatiquement une extension **déjà installée** : la copie embarquée est prise en compte lors de la construction et de l'installation de la nouvelle version OXT.
