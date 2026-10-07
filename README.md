# Lexique forensique FR

Lexique français collaboratif de criminalistique numérique, avec une extension LibreOffice destinée à la recherche terminologique et à l'aide à la rédaction de rapports.

## Objectifs

Le projet vise à :

- proposer un vocabulaire français cohérent pour la criminalistique numérique ;
- rapprocher les termes français de leurs équivalents anglais ;
- distinguer les termes recommandés, admis et déconseillés ;
- fournir des définitions courtes et opérationnelles ;
- proposer des exemples de formulation utilisables dans des rapports ;
- alimenter une extension LibreOffice Writer ;
- conserver le lexique dans un format JSON réutilisable par d'autres outils.

## Sources

Le projet s'appuie notamment sur le livrable européen **CLARUS D3.2 — A searchable web-based common lexicon**.

Les entrées françaises ne sont pas conçues comme une traduction littérale : elles doivent être adaptées aux usages professionnels francophones tout en conservant la correspondance avec la terminologie internationale.

## Structure

```text
lexique-forensique-fr/
├── README.md
├── CONTRIBUTING.md
├── data/
│   └── lexique.json
├── extension/
│   └── README.md
└── sources/
    └── CLARUS.md
```

## Format d'une entrée

```json
{
  "terme": "Chiffrement",
  "anglais": "Encryption",
  "categorie": "Cryptographie",
  "definition": "Procédé cryptographique transformant des données afin de les rendre inintelligibles sans la clé appropriée.",
  "synonymes": [],
  "termes_deconseilles": ["Cryptage"],
  "exemple_rapport": "Les données présentes sur le support sont protégées par chiffrement.",
  "sources": ["CLARUS D3.2"]
}
```

## Extension LibreOffice

La première cible est une extension **LibreOffice Writer** permettant de :

1. rechercher un terme ;
2. afficher sa fiche ;
3. insérer une formulation recommandée dans le document.

Les versions suivantes pourront ajouter l'analyse terminologique d'un document et des propositions de remplacement.

## État du projet

Version initiale : **v0.1.0 — démarrage du projet**.
