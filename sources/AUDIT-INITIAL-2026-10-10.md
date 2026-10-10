# Audit terminologique initial — 10 octobre 2026

## Inventaire du dépôt

Inspection des bases sources sur `main` :
- `data/lexique.json` : **63** fiches ;
- `data/traductions.json` : **18** correspondances de francisation ;
- `data/scenarios.json` : **5** scénarios.

Les bases sont distinctes : ne pas confondre traduction d'un libellé d'export et définition d'un terme forensique. Les copies embarquées dans `extension/data/` doivent rester identiques aux sources en cas de modification.

## Premiers points de vigilance

- La fiche « Acquisition forensique » référence **CLARUS D3.2 — Forensic acquisition** et utilise « Extraction » comme synonyme : examiner si la synonymie est pertinente dans tous les contextes (image physique, extraction logique ou accès partiel).
- Les phrases de rapport ne doivent pas revendiquer une fidélité littérale à CLARUS ou à d'autres référentiels.
- Les traductions courtes comme « Missed Call » → « Appel manqué » nécessitent un contexte de détection approprié, pour éviter les remplacements abusifs.
- Avant tout apport externe : contrôler la provenance, la portée de la définition et les droits applicables.

## Méthode d'examen à appliquer aux 63 fiches

| Champ de revue | Valeurs proposées |
| --- | --- |
| ID de fiche | ID stable de `lexique.json` |
| Statut | Non examinée / À clarifier / Conforme / À corriger |
| Source examinée | Identifiant du référentiel, URL, édition |
| Type d'écart | Définition / Synonyme / Traduction / Formulation / Aucun |
| Proposition | Texte original du projet, sans copie non autorisée |
| Validation | Décision explicite avant modification des données |

## Limite de cet audit initial

Ce document **n'affirme pas** que les 63 définitions ont été confrontées une par une à tous les référentiels. Il établit l'inventaire, les sources et les premiers sujets de contrôle. Aucune fiche fonctionnelle n'est modifiée dans cette étape.
