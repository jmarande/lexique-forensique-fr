# Extension LibreOffice

Extension Writer du **Lexique forensique FR**.

## Version 0.4.0 — branche de test

Cette version part de la v0.3.0 validée et ajoute le traitement ciblé des alertes terminologiques.

### Contrôle terminologique

Le bouton **Vérifier document** :

- recherche les termes présents dans `termes_deconseilles` ;
- compte les occurrences ;
- affiche le terme détecté et le terme recommandé.

### Navigation dans le document

Quand l'opérateur sélectionne une alerte, Writer sélectionne automatiquement la première occurrence correspondante dans le document.

Exemple :

`cryptage → Chiffrement`

L'occurrence de `cryptage` est sélectionnée directement dans Writer.

### Remplacement ciblé

Le bouton **Remplacer occurrence** remplace uniquement l'occurrence actuellement sélectionnée par le terme recommandé.

Il n'existe volontairement pas encore de remplacement global : l'opérateur garde la maîtrise de chaque correction.

Après un remplacement, le document est analysé à nouveau et le nombre d'occurrences restantes est actualisé.
