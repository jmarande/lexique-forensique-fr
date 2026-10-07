# Distribution des mises à jour

Le projet utilise **un seul dépôt GitHub** pour le code source et les versions publiées.

## Publication d’une version

1. Mettre à jour le numéro de version dans :
   - `extension/description.xml`
   - `CURRENT_VERSION` dans `extension/Scripts/python/lexique_forensique.py`
2. Vérifier que `data/lexique.json` et `extension/data/lexique.json` sont synchronisés.
3. Fusionner la version validée dans `main`.
4. Publier la version :
   - soit en poussant un tag `vX.Y.Z` ;
   - soit avec **Actions > Build and publish LibreOffice extension > Run workflow** en indiquant la version.
5. GitHub Actions construit `lexique-forensique-fr.oxt`.
6. Une GitHub Release portant le même tag est créée ou mise à jour avec l’OXT en pièce jointe.

## Mise à jour depuis LibreOffice

Le menu **Lexique forensique > Mettre à jour…** consulte la dernière GitHub Release du dépôt.

L’extension :

- lit le numéro de la dernière version ;
- compare ce numéro à la version installée ;
- affiche les notes de version disponibles ;
- cherche l’asset **`lexique-forensique-fr.oxt`** ;
- télécharge l’OXT dans un répertoire temporaire en conservant exactement ce nom ;
- contrôle le SHA-256 lorsque GitHub fournit le digest de l’asset ;
- ouvre ensuite l’OXT pour lancer l’installation.

Aucun token GitHub n’est embarqué dans l’extension.

## Contrainte importante

Le fichier distribué doit rester nommé exactement :

`lexique-forensique-fr.oxt`

Les URL de scripts LibreOffice définies dans `extension/Addons.xcu` dépendent de ce nom.
