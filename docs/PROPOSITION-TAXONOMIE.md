# Proposition de classification du lexique (phase 1)

Objectif : navigation claire, sans confondre la nature d'une notion et ses domaines d'application.

- **Classement principal obligatoire** : famille > sous-catégorie, selon `data/taxonomie-proposition.json`.
- **Domaines complémentaires facultatifs** : téléphonie, informatique, réseaux, multiplateforme. Les plateformes (iOS, Android, Windows, Linux, macOS) seront des filtres et ne doivent pas être imposées aux notions transversales.
- **Application** : WhatsApp et Snapchat restent des applications, avec des domaines possibles ; on évite de les ranger sous iOS uniquement.
- **Acquisition forensique** : Méthodologie forensique > Acquisition et extraction ; domaines téléphonie et informatique.
- **Extraction logique** : Méthodologie forensique > Acquisition et extraction.

## Garantie de migration

La proposition classe **63 fiches sur 63**, une seule fois chacune. Elle ne modifie **ni** les identifiants **ni** `categorie` sur les fiches officielles et personnelles. Les anciennes catégories ne sont pas supprimées. Avant la migration définitive : valider la nomenclature, prévoir une correspondance des catégories personnalisées, ajouter un repli dans l'interface Writer, et tester filtres, recherche, import/export et mises à jour.

## Prochaine étape

Après validation du classement : générer les chemins de navigation GitHub et la sélection hiérarchique dans Writer à partir du JSON, sans recopier les familles dans plusieurs fichiers. Ensuite reprendre la relecture des définitions PR #57.

## Repères visuels

- 🔬 **Méthodologie forensique**
- 🧩 **Données et traces**
- 💾 **Équipements et supports**
- 📱 **Téléphonie mobile**
- 💻 **Informatique**
- 🌐 **Réseaux**
- ☁️ **Services numériques**
- 💬 **Applications**

Les pictogrammes sont des repères légers ; ils ne remplacent jamais les noms de catégories. Ils ne modifient pas les termes personnels.
