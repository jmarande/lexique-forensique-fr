# Extension LibreOffice

Extension Writer du **Lexique forensique FR**.

## Version 0.3.0 — branche de test

Cette version part de la v0.2.1 validée et ajoute un premier **contrôle terminologique du document**.

### Fonctionnement

Le bouton **Vérifier document** :

- parcourt le texte du document Writer actif ;
- recherche les entrées présentes dans `termes_deconseilles` du lexique ;
- compte les occurrences ;
- affiche la forme détectée et le terme français recommandé ;
- conserve la fenêtre non modale pour permettre de continuer à modifier le document.

Exemple actuel :

`cryptage → chiffrement`

Le contrôle est alimenté directement par `data/lexique.json` : les futurs termes déconseillés ajoutés au lexique seront donc pris en compte sans modifier le moteur de vérification.

## Limites de cette première version

- aucune modification automatique du document ;
- pas encore de surlignage ni de navigation vers l'occurrence ;
- l'opérateur reste maître de la rédaction.

Ces fonctions seront étudiées après validation de cette première détection.
