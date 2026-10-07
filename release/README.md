# Distribution des mises à jour

Le projet utilise désormais **un seul dépôt GitHub**.

## Publication d'une version

1. Mettre à jour la version dans `extension/description.xml` et dans `CURRENT_VERSION`.
2. Fusionner la version validée dans `main`.
3. Créer puis pousser un tag de version, par exemple `v0.5.0`.
4. Le workflow GitHub Actions construit automatiquement `lexique-forensique-fr.oxt`.
5. Une GitHub Release portant le même tag est créée avec l'OXT en pièce jointe.

## Mise à jour dans LibreOffice

Le menu **Lexique forensique > Mettre à jour…** appelle :

`https://api.github.com/repos/jmarande/lexique-forensique-fr/releases/latest`

L'extension :

- lit le numéro de la dernière release ;
- compare ce numéro à la version installée ;
- cherche l'asset `lexique-forensique-fr.oxt` ;
- télécharge le nouvel OXT lorsqu'une version plus récente existe ;
- contrôle le SHA-256 si GitHub fournit un digest pour l'asset ;
- ouvre ensuite le fichier OXT pour lancer son installation.

Aucun token GitHub n'est embarqué dans l'extension.
