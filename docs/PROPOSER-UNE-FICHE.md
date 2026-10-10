# Proposer une fiche au lexique

Depuis LibreOffice Writer : **Lexique forensique > Gestion des termes**, sélectionner une **fiche personnelle** puis cliquer sur **Proposer au lexique**.

La fiche doit contenir au minimum un **terme** et une **définition**. La proposition reprend le terme français, l'équivalent anglais, la catégorie, la définition, les synonymes, les références documentaires ainsi que les **formulations pour rapport** déjà enregistrées.

L'extension ouvre le navigateur sur une **issue GitHub préremplie**. Aucun envoi n'est effectué par l'extension. **L'utilisateur doit se connecter à GitHub, relire la proposition puis confirmer lui-même sa publication**. Le contenu publié dans une issue est public : **ne pas transmettre de données nominatives, d'extraits de dossiers, d'identifiants ou d'informations confidentielles**.

Seules les fiches personnelles peuvent être proposées depuis ce bouton. Les fiches officielles ne peuvent pas être renvoyées directement ; elles peuvent d'abord être dupliquées et adaptées en fiche personnelle. L'envoi ne modifie pas les données locales.

## Traitement des contributions

1. La proposition arrive dans les *Issues* du dépôt, sans droit d'écriture pour le contributeur sur la base officielle.
2. Le mainteneur élimine spam et doublons et décide de mettre en relecture.
3. Après comparaison des sources, il propose une modification de `data/lexique.json` par PR.
4. Une fiche intégrée reste « En attente de relecture » tant qu'aucune décision explicite n'a été prise.
5. La validation éditoriale est consignée selon [la procédure](VALIDATION-FICHES.md) lorsque celle-ci est intégrée au dépôt.

## Limites de cette première version

- Un compte GitHub est requis et GitHub assure la protection anti-spam à l'entrée.
- Aucun serveur, jeton GitHub ou mail de réception n'est inclus dans l'extension.
- Les formulations sont transmises dans la proposition, sans validation automatique.
- Si le contenu est trop long, l'URL préremplie peut atteindre les limites du navigateur ; réduire alors la proposition.
- Le statut de proposition n'est pas encore synchronisé automatiquement avec l'extension.
