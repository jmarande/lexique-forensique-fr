# Extension LibreOffice Writer

Extension du projet **Lexique forensique FR**.

## Fonctions actuelles

La fenêtre principale reste ouverte pendant la rédaction et permet de :

- rechercher un terme dans le lexique ;
- consulter sa définition, son équivalent anglais, sa catégorie et ses synonymes ;
- vérifier le document Writer actif ;
- afficher séparément les alertes terminologiques ;
- sélectionner une occurrence et la remplacer individuellement ;
- afficher les formulations de rapport directement dans la fiche ;
- sélectionner une formulation dans la zone de droite ;
- insérer la formulation sélectionnée dans le document ;
- rechercher et installer les mises à jour publiées sur GitHub.

Les sources et les termes déconseillés restent conservés dans le JSON mais ne sont plus affichés dans la fiche principale afin de garder l’interface lisible.

## Interface

Le panneau de gauche conserve en permanence :

- **Lexique** : liste des termes disponibles ;
- **Alertes du document** : termes déconseillés détectés dans le document actif.

La zone de droite affiche la fiche du terme et, lorsqu’elles existent, les différentes **formulations pour rapport**.

La fenêtre est **non modale**.

## Installation

Le paquet doit impérativement conserver le nom :

`lexique-forensique-fr.oxt`

Installer l’extension pour l’utilisateur actif puis redémarrer complètement LibreOffice si nécessaire.

Version de la source actuelle : **0.7.15**.
