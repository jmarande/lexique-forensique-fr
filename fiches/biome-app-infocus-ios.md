# Biome — activité applicative (App.InFocus)

**Classification :** 📱 Téléphonie mobile → Artefacts système

**Statut :** En attente de relecture

**Domaines d’application :** Téléphonie

**Équivalent anglais :** App.InFocus

## Définition

Flux d’événements Biome susceptible d’enregistrer les transitions de certaines applications vers ou hors de l’état de premier plan. Les enregistrements peuvent comporter un horodatage, un identifiant d’application (bundle ID) et un état de transition. Leur rapprochement aide à reconstituer une chronologie d’activité applicative, sous réserve de la disponibilité et de l’interprétation correcte des événements.

## Synonymes

- _DKEvent.App.InFocus

## Formulations pour rapport

### Événements identifiés

L’analyse du flux Biome relatif à l’activité applicative met en évidence des événements horodatés de passage de certaines applications au premier plan.

### Application au premier plan

Un événement enregistré dans le flux App.InFocus indique que l’application identifiée par son identifiant technique était signalée au premier plan à l’horodatage considéré.

### Chronologie d’activité

Le rapprochement des événements d’activité applicative permet de proposer une chronologie partielle des applications signalées au premier plan sur le terminal examiné.

### Limite d’interprétation

Ces événements ne permettent pas, à eux seuls, de déterminer si une personne a effectivement interagi avec l’application, ni d’établir son identité ou le contenu consulté.

> Ces fiches sont des documents de travail du projet : les définitions restent soumises à la revue terminologique et documentaire.

[← Retour à l’index](README.md)
