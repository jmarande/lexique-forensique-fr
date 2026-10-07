# Contribuer

Merci de contribuer au **Lexique forensique FR**.

## Principes

Une proposition doit privilégier :

- la précision technique ;
- un français clair et professionnel ;
- la cohérence avec les usages de la criminalistique numérique ;
- la distinction entre traduction, définition et recommandation rédactionnelle ;
- la traçabilité des sources ;
- une rédaction prudente lorsque l’identification ou l’interprétation n’est que probable.

## Format recommandé

Chaque entrée doit comporter au minimum :

- un identifiant stable ;
- le terme français ;
- l’équivalent anglais lorsqu’il existe ;
- une catégorie ;
- une définition ;
- les synonymes éventuels ;
- les termes déconseillés éventuels ;
- la ou les sources.

Lorsqu’une entrée peut être utilisée dans un rapport, privilégier `formulations_rapport` avec des formulations **situationnelles** plutôt que plusieurs variantes stylistiques d’une même phrase.

Exemple :

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

## Prudence terminologique

Les formulations ne doivent pas transformer une hypothèse technique en certitude. Lorsque le niveau d’information ne permet qu’une identification probable, la rédaction doit le refléter explicitement.

## Synchronisation des données

Toute modification du lexique doit être répercutée dans les deux fichiers :

- `data/lexique.json`
- `extension/data/lexique.json`

Ils doivent rester strictement synchronisés.

## Proposer une modification

Créer une issue ou une pull request en indiquant :

1. le terme concerné ;
2. la modification proposée ;
3. sa justification ;
4. la ou les sources utilisées.
