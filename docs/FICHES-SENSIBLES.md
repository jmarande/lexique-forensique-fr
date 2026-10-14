# Fiches sensibles : import et scénarios

Les fiches classées sensibles ne sont pas intégrées à la distribution publique. Le fichier d'import est remis séparément, sans être publié dans le dépôt, une release ou une issue publique.

## Import manuel

Depuis Writer, ouvrir **Lexique forensique > Exporter / Importer…**, sélectionner un fichier au format `lexique-forensique-fr-user-data` (version 1) puis choisir **Fusionner**. Les fiches ainsi ajoutées sont conservées dans le profil utilisateur. Une sauvegarde de la base locale précède l'import.

Chaque fiche sensible doit contenir `"sensible": true`. L'extension affiche **FICHE SENSIBLE — MERCI DE NE PAS DIFFUSER** dans la fiche et **⚠ [SENSIBLE]** dans les listes. Ce marquage est informatif : il ne chiffre pas les données et n'en interdit pas l'export.

## Scénarios sensibles

Si une étape référence une fiche sensible, le scénario est automatiquement signalé **Scénarios sensibles**, même lorsque ses autres étapes sont ordinaires. La classification est calculée à partir de l'état des fiches, sans imposer de modification de leur contenu. Si toutes les références sensibles sont retirées, il revient dans la rubrique ordinaire. Dans les listes, les scénarios sensibles sont regroupés et signalés visuellement.

## Prévention de publication accidentelle

La commande « Proposer les fiches sélectionnées » refuse désormais toute sélection contenant une fiche marquée sensible. Le fichier de sauvegarde/export local peut en revanche contenir ces fiches : il doit être conservé et partagé avec précaution.

**Attention :** le marquage « sensible » ne constitue pas un dispositif de contrôle d'accès. Les copies déjà diffusées, anciens commits et releases doivent être traités séparément.
