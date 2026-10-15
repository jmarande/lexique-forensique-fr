# Extension LibreOffice Writer

Extension du projet **Lexique forensique FR**.

## Fonctions

Une seule fenêtre regroupe trois modules accessibles en haut : **Lexique**, **Vérification du document** et **Scénarios**. Chaque module conserve sa sélection lors du passage à un autre. Les entrées du menu Writer ouvrent le module demandé dans cette même fenêtre.

Dans **Lexique**, les filtres **Catégorie** puis **Sous-catégorie** affinent la liste des fiches. « Toutes » retire le filtre correspondant. La recherche couvre notamment les termes, synonymes et termes proches. Toutes les formulations sont affichées ensemble dans la fiche. Cliquer sur le texte souhaité puis sur **Insérer la formulation**.

Le bouton **Mes fiches** ouvre la gestion des fiches personnelles. La vérification conserve sa gestion des occurrences et les scénarios leurs commandes de création, modification et insertion. Le bouton **Aide** donne accès à l'aide hors ligne.

Les données officielles restent protégées. Les données utilisateur sont enregistrées dans `~/.lexique-forensique-fr/`.

## Présentation des formulations dans les rapports

L'insertion applique **Times New Roman** aux textes ajoutés depuis les modules Lexique et Scénarios. Les formulations structurées peuvent contenir un titre en gras et un véritable tableau Writer. Les tableaux suivent la [charte de mise en forme](../docs/CHARTE-MISE-EN-FORME.md) : en-tête gris moyen, texte noir et alternance des lignes blanches/gris clair.

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

## Classification hiérarchique

Les catégories et sous-catégories reposent sur `data/taxonomie.json`. Une fiche personnelle sans classement hiérarchique reste accessible sous sa catégorie habituelle. Le filtre de sous-catégorie est désactivé lorsqu'aucune sous-catégorie n'est disponible.
