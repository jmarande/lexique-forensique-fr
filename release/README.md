# Distribution publique des mises à jour

L'extension LibreOffice consulte un dépôt public séparé :

`jmarande/lexique-forensique-fr-releases`

Le dépôt public doit contenir à la racine :

- `update.json`
- `lexique-forensique-fr-latest.oxt`

## update.json

```json
{
  "version": "0.5.0",
  "download_url": "https://raw.githubusercontent.com/jmarande/lexique-forensique-fr-releases/main/lexique-forensique-fr-latest.oxt",
  "sha256": "<empreinte SHA-256 du fichier OXT>"
}
```

## Fonctionnement

Le menu **Lexique forensique > Mettre à jour…** :

1. télécharge `update.json` ;
2. compare la version publiée à la version installée ;
3. télécharge le nouvel OXT lorsqu'une version plus récente existe ;
4. vérifie son SHA-256 ;
5. ouvre le fichier OXT dans le gestionnaire d'extensions LibreOffice.

Aucun token GitHub n'est embarqué dans l'extension.
Le dépôt de développement peut donc rester privé.
