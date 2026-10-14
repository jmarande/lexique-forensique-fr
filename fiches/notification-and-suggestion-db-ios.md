# notificationAndSuggestionDB.db (iOS)

**Classification :** 📱 Téléphonie mobile → Artefacts système

**Statut :** Validée

**Validation éditoriale :** 2026-10-14 — jmarande (https://github.com/jmarande/lexique-forensique-fr/pull/95)

**Domaines d’application :** Téléphonie

**Équivalent anglais :** Notification and Suggestion Database

## Définition

Base de données SQLite du sous-système DuetExpertCenter d'Apple qui conserve des métadonnées relatives aux notifications enregistrées sur un appareil iOS. Elle peut contenir des horodatages, des identifiants d'applications, de conversations ou de correspondants et des indicateurs relatifs au traitement des notifications. Son exploitation permet de rechercher des événements de notification et de contribuer à leur contextualisation chronologique. Les travaux examinés n'ont pas mis en évidence la conservation du contenu textuel des notifications dans cette base.

## Synonymes

- Base des métadonnées de notifications

## Formulations pour rapport

### Présentation de la base

Le système iOS conserve, au sein de la base notificationAndSuggestionDB.db, des métadonnées relatives aux notifications associées aux applications du terminal.

### Base identifiée

Nous identifions dans les données extraites la base notificationAndSuggestionDB.db, contenant des enregistrements relatifs aux notifications du terminal.

### Notifications identifiées

L'analyse de cette base met en évidence plusieurs événements de notification horodatés associés à différentes applications.

### Notification associée à une application

Nous identifions un enregistrement de notification associé à l'application concernée, accompagné d'un horodatage de réception.

### Correspondant identifié

L'examen des métadonnées de notification met en évidence un identifiant susceptible de correspondre à un numéro de téléphone associé à une communication.

### Conversation identifiée

Les données analysées comportent un identifiant de conversation associé à une notification provenant de l'application concernée.

### Reconstitution chronologique

Le rapprochement des horodatages de notification contribue à établir une chronologie partielle des événements enregistrés par le système.

### Corrélation des données

Les métadonnées de notification ont été rapprochées des autres données accessibles afin de rechercher des correspondances avec les communications identifiées sur le terminal.

### Limites d'interprétation

Les enregistrements identifiés correspondent à des métadonnées de notification et ne permettent pas, à eux seuls, d'établir la consultation des notifications par l'utilisateur ni de déterminer leur contenu.

### Données insuffisantes

Les données accessibles dans cette base ne permettent pas de reconstituer de manière exhaustive l'historique des notifications du terminal.

> Ces fiches sont des documents de travail du projet : les définitions restent soumises à la revue terminologique et documentaire.

[← Retour à l’index](README.md)
