# Contribuer

Merci de contribuer au **Lexique forensique FR**.

## Principes

Une proposition doit privilégier :

- la précision technique ;
- un français clair et professionnel ;
- la cohérence avec les usages de la criminalistique numérique ;
- la distinction entre traduction, définition, occurrence à détecter et recommandation rédactionnelle ;
- la traçabilité des sources ;
- une rédaction prudente lorsque l’identification ou l’interprétation n’est que probable.

## Lexique

Chaque entrée officielle doit comporter au minimum :

- un identifiant stable ;
- le terme français ;
- l’équivalent anglais lorsqu’il existe ;
- une catégorie ;
- une définition ;
- les synonymes éventuels ;
- les termes déconseillés éventuels ;
- la ou les sources.

Pour les phrases de rapport, utiliser `formulations_rapport` et privilégier des formulations **situationnelles** plutôt que plusieurs variantes stylistiques de la même phrase.

```json
"formulations_rapport": [
  {
    "type": "Acquisition réalisée",
    "texte": "Nous procédons à l’acquisition forensique du support…"
  },
  {
    "type": "Acquisition partielle",
    "texte": "Nos moyens techniques ne nous permettent de procéder qu’à une acquisition partielle…"
  }
]
```

## Scénarios

Un scénario doit référencer des formulations existantes par identifiant de terme et type de formulation. Éviter de recopier les phrases elles-mêmes afin que les corrections du lexique se répercutent automatiquement.

## Occurrences et traductions

La base officielle de francisation se trouve dans `data/traductions.json`.

N’ajouter que des correspondances apportant une réelle normalisation ou francisation. Éviter les pseudo-traductions sans valeur ajoutée, par exemple un terme anglais identique au terme français.

Une règle doit être suffisamment précise pour limiter les faux positifs dans les exports.

## Données utilisateur

Les données créées depuis l’extension sont stockées hors du dépôt dans :

- `lexique-utilisateur.json` ;
- `scenarios-utilisateur.json` ;
- `occurrences-utilisateur.json`.

Elles ne doivent jamais être ajoutées au dépôt ni embarquées dans l’OXT.

## Synchronisation des données officielles

Toute modification d’un fichier de données officiel doit être répercutée dans sa copie embarquée :

- `data/lexique.json` ↔ `extension/data/lexique.json`
- `data/scenarios.json` ↔ `extension/data/scenarios.json`
- `data/traductions.json` ↔ `extension/data/traductions.json`

Les paires doivent rester strictement synchronisées.

## Prudence terminologique

Les formulations ne doivent pas transformer une hypothèse technique en certitude. Lorsque le niveau d’information ne permet qu’une identification probable, la rédaction doit le refléter explicitement.

## Pull requests

Pour une modification terminologique, indiquer :

1. l’élément concerné ;
2. la modification proposée ;
3. sa justification ;
4. la ou les sources utilisées.

Pour une évolution de l’extension, privilégier une modification isolée et testable. La stabilité de LibreOffice/UNO prime sur l’ajout de fonctionnalités.
