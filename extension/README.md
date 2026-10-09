# Extension LibreOffice Writer

Extension du projet **Lexique forensique FR**.

## Fonctions

La fenêtre principale permet de rechercher les termes, filtrer par catégorie, consulter les fiches et insérer une formulation dans Writer.

Des fenêtres dédiées gèrent les fonctions plus riches :

- **Vérifier le document** : termes déconseillés, occurrences et francisation de libellés anglais ;
- **Scénarios** : assemblage et insertion de plusieurs formulations ;
- **Gérer les termes** : création et modification de termes utilisateur ;
- **Gérer les occurrences** : création de règles de détection personnelles.

Les données officielles restent protégées. Les données utilisateur sont enregistrées dans `~/.lexique-forensique-fr/`.

## Vérification du document

Le vérificateur distingue notamment :

- **Terminologie** : terme déconseillé à normaliser ;
- **Traduction / normalisation** : occurrence anglaise ou personnalisée à remplacer.

Les occurrences utilisateur peuvent définir plusieurs remplacements possibles et un remplacement préféré.

## Export / import

Le menu **Exporter / Importer…** sauvegarde ensemble :

- les termes utilisateur ;
- les scénarios utilisateur ;
- les occurrences utilisateur.

L’import propose **Fusionner** ou **Remplacer**. Une sauvegarde de la base existante est créée avant import.

## Mise à jour

Le menu **Mettre à jour…** consulte la dernière GitHub Release, vérifie la version et le SHA-256 lorsqu’il est fourni, télécharge `lexique-forensique-fr.oxt` puis lance son installation.

## Installation

Le paquet doit impérativement conserver le nom :

`lexique-forensique-fr.oxt`

Installer l’extension pour l’utilisateur actif puis redémarrer complètement LibreOffice si nécessaire.

Version de référence du dépôt : **0.8.1**.
