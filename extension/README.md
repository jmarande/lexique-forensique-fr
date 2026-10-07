# Extension LibreOffice

Extension Writer du **Lexique forensique FR**.

## Version 0.4.1 — branche de test

Cette version corrige l'ergonomie du contrôle terminologique.

### Séparation du lexique et des alertes

Le panneau de gauche est maintenant divisé en deux zones :

- **Lexique** : conserve en permanence la liste des termes disponibles ;
- **Alertes du document** : affiche uniquement les termes déconseillés détectés dans le document actif.

Le bouton **Vérifier document** ne remplace donc plus la liste du lexique par les alertes.

### Comportement

- rechercher un terme continue d'afficher sa définition ;
- vérifier le document remplit uniquement la zone d'alertes ;
- sélectionner une alerte affiche la fiche du terme recommandé et sélectionne l'occurrence dans Writer ;
- **Remplacer occurrence** corrige uniquement l'occurrence sélectionnée ;
- après correction, la liste d'alertes est actualisée sans effacer le lexique.

La fenêtre reste non modale afin de permettre la modification du document pendant son utilisation.
