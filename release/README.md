# Distribution des mises à jour

Le projet utilise **un seul dépôt GitHub** pour le code source et les versions publiées.

## Publication d’une version

Le workflow `.github/workflows/release-oxt.yml` peut être lancé :

- automatiquement par un tag `vX.Y.Z` ;
- manuellement via **Actions > Build and publish LibreOffice extension > Run workflow**.

Lors du build, le workflow synchronise automatiquement la version indiquée dans :

- `CURRENT_VERSION` de `extension/Scripts/python/lexique_forensique.py` ;
- `extension/description.xml`.

Il n’est donc plus nécessaire de modifier ces deux fichiers manuellement avant une publication.

### Vérifications avant publication

1. Valider les changements sur une branche puis les fusionner dans `main`.
2. Vérifier la synchronisation des paires :
   - `data/lexique.json` / `extension/data/lexique.json`
   - `data/scenarios.json` / `extension/data/scenarios.json`
   - `data/traductions.json` / `extension/data/traductions.json`
3. Lancer le workflow avec une nouvelle version.
4. Vérifier la GitHub Release et l’asset `lexique-forensique-fr.oxt`.

## Construction

GitHub Actions :

- synchronise la version interne ;
- vérifie la cohérence de la version ;
- construit le contenu de `extension/` en ZIP/OXT ;
- conserve exactement le nom `lexique-forensique-fr.oxt` ;
- crée ou met à jour la GitHub Release correspondante.

## Mise à jour depuis LibreOffice

Le menu **Lexique forensique > Mettre à jour…** :

- interroge la dernière GitHub Release ;
- compare la version publiée à la version installée ;
- affiche les notes de version ;
- recherche l’asset `lexique-forensique-fr.oxt` ;
- télécharge le paquet dans un répertoire temporaire ;
- vérifie le SHA-256 lorsque GitHub fournit le digest ;
- utilise des en-têtes anti-cache et une seconde URL lorsque nécessaire ;
- ouvre ensuite l’OXT pour lancer l’installation.

Aucun token GitHub n’est embarqué dans l’extension.

## Données utilisateur

Les mises à jour du paquet ne modifient pas les fichiers situés dans `~/.lexique-forensique-fr/`.

L’utilisateur peut également les sauvegarder via **Exporter / Importer…**.

## Contrainte importante

Le fichier distribué doit rester nommé exactement :

`lexique-forensique-fr.oxt`

Les URL de scripts LibreOffice définies dans `extension/Addons.xcu` dépendent de ce nom.
