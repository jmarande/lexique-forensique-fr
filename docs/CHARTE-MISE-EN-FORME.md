# Charte de mise en forme des rapports Writer

Cette charte est la référence de présentation pour les **contenus insérés par Lexique forensique FR** dans les rapports. Elle n'impose pas de modification à la totalité du document Writer existant.

## Typographie

- **Police : Times New Roman** pour les formulations classiques, les titres, les introductions et le contenu de toutes les cellules des tableaux générés par l'extension.
- **Titres de sections :** texte noir, en gras.
- **Introductions :** texte noir, graisse normale, paragraphe séparé du titre et du tableau.
- Les styles existants et le contenu déjà présent dans le rapport ne sont pas modifiés.

## Tableaux

| Élément | Propriété | Valeur |
| --- | --- | --- |
| Ligne d'en-tête | Fond | Gris moyen `#B2B2B2` |
| Ligne d'en-tête | Texte | Noir `#000000`, gras, centré |
| Lignes de données impaires | Fond | Blanc `#FFFFFF` |
| Lignes de données paires | Fond | Gris clair `#EEEEEE` |
| Lignes de données | Texte | Noir `#000000`, Times New Roman, aligné à gauche |
| Bordures | Couleur | Gris `#808080` |
| Bordures | Épaisseur | 0,20 mm |

Les tableaux doivent être de **vrais objets TextTable de LibreOffice Writer**, avec cellules modifiables et nombre de lignes adapté à la fiche. Les valeurs fournies dans les exemples sont des espaces réservés, à remplacer par les informations constatées dans chaque dossier.

## Exemple de référence

La formulation « Comptes utilisateurs et services identifiés sur le support — tableau » de la fiche `compte-utilisateur` sert de référence initiale :

**Les comptes utilisateurs**

L'examen des données extraites du support permet d'identifier plusieurs comptes utilisateurs ou comptes associés à des services. Les informations relevées sont présentées dans le tableau suivant :

| Nom du compte ou service | Nom du compte | Informations complémentaires |
| --- | --- | --- |
|  |  |  |
|  |  |  |
|  |  |  |

## Contrôles de non-régression

1. La formulation avec tableau insère le titre en gras, puis le paragraphe d'introduction.
2. Les trois colonnes sont présentes et les contenus des cellules restent modifiables.
3. Les couleurs suivent le motif gris / blanc / gris clair / blanc.
4. Les bordures et la police restent identiques, y compris après sauvegarde puis réouverture d'un document ODT.
5. Les formulations purement textuelles et les scénarios continuent de s'insérer en Times New Roman sans modification du contenu du document préexistant.
