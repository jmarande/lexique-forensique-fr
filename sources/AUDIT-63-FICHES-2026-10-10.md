# Audit des 63 fiches — revue interne du 10 octobre 2026

## Portée et limites

Revue **exhaustive des 63 enregistrements du fichier `data/lexique.json`** : définition, synonymes, catégorie, cohérence des références et principaux risques rédactionnels. **Ce n'est pas** une confrontation ligne à ligne avec le texte intégral de CLARUS D3.2 ni une expertise juridique de similarité textuelle. Le statut de réutilisation et la proximité littérale avec CLARUS demeurent **à vérifier individuellement** avant toute redistribution de contenu inspiré de cette source.

- 63 fiches, 63 identifiants distincts, aucun champ fondamental absent (id, terme, catégorie, définition, liste de sources).
- 43 fiches citent CLARUS ; 13 mentionnent un usage professionnel interne ; 7 concernent une application et citent l'assistance éditeur.
- 29 fiches comportent des formulations de rapport.
- **22 points de vigilance haute**, **30 moyens**, **11 bas** : priorisation éditoriale, et non mesure de conformité à CLARUS.

## Revue fiche par fiche

| N° | ID | Origine déclarée | Priorité | Observation / action proposée |
|---:|---|---|---|---|
| 1 | `acquisition-forensique` | CLARUS | Haute | « Extraction » ne doit pas être synonyme systématique ; acquisition physique/logique et extraction diffèrent selon contexte. |
| 2 | `adresse-ip` | CLARUS | Haute | Une adresse IP identifie une interface/adressage à un instant, pas nécessairement un équipement ou une personne. |
| 3 | `analyse-donnees` | Interne | Moyenne | Distinguer examen technique, analyse et interprétation. |
| 4 | `artefact-forensique` | Interne | Moyenne | Un artefact ne constitue pas automatiquement une preuve ; préciser indices et interprétation. |
| 5 | `authentification` | CLARUS | Haute | Conflation authentification d’identité, authenticité des données et vérification d’intégrité ; scinder les concepts. |
| 6 | `base-de-donnees` | CLARUS | Basse | Lecture de cohérence sans anomalie manifeste ; contrôle externe et droits de réutilisation restent à effectuer. |
| 7 | `carte-sim` | CLARUS | Moyenne | Préciser carte UICC et configurations eSIM ; données accessibles variables. |
| 8 | `chaine-tracabilite` | CLARUS | Haute | Chain of custody : privilégier chaîne de conservation/chaîne de possession selon contexte, préciser continuité documentée. |
| 9 | `chiffrement` | CLARUS | Haute | Ne pas présenter mot de passe et clé cryptographique comme identiques ; accès parfois conditionné à matériel/état. |
| 10 | `cle-usb` | CLARUS | Basse | Lecture de cohérence sans anomalie manifeste ; contrôle externe et droits de réutilisation restent à effectuer. |
| 11 | `code-deverrouillage` | Interne | Moyenne | Distinguer PIN SIM, code d’écran et clé de déchiffrement. |
| 12 | `copie-forensique` | CLARUS | Haute | « Image forensique » et « copie de travail » ne sont pas nécessairement équivalentes ; préciser copie vérifiée, exhaustive ou partielle. |
| 13 | `criminalistique-numerique` | CLARUS | Basse | Lecture de cohérence sans anomalie manifeste ; contrôle externe et droits de réutilisation restent à effectuer. |
| 14 | `decodage-donnees` | Interne | Basse | Lecture de cohérence sans anomalie manifeste ; contrôle externe et droits de réutilisation restent à effectuer. |
| 15 | `disque-dur` | CLARUS | Moyenne | La définition s’applique à d’autres supports ; souligner stockage magnétique HDD. |
| 16 | `donnee-reconstruite` | Interne | Haute | Reconstruction logicielle ne signifie pas correspondance probante avec l’événement initial. |
| 17 | `donnee-supprimee` | Interne | Moyenne | Ne pas supposer que la suppression prouve l’intention d’un utilisateur. |
| 18 | `donnees-numeriques` | CLARUS | Haute | Ne pas inclure obligation procédurale dans une définition générale des données. |
| 19 | `dossier` | CLARUS | Moyenne | Une arborescence ne suffit pas à attribuer une action à l’utilisateur. |
| 20 | `empreinte-numerique` | CLARUS | Haute | Une valeur de hachage concerne les données, pas directement l’équipement ; éviter « identifiant » unique garanti. |
| 21 | `etat-support` | Interne | Moyenne | Distinguer observation de prise en charge et déduction technique. |
| 22 | `exif` | CLARUS | Moyenne | Date EXIF potentiellement absente, modifiable et dépourvue de fuseau ; ne pas assimiler à preuve de création. |
| 23 | `extraction` | CLARUS | Moyenne | Différencier acquisition, extraction et décodage dans les formulations. |
| 24 | `extraction-systeme-fichiers` | Interne | Haute | Ne pas confondre extraction du système de fichiers avec image complète et privilèges d’accès. |
| 25 | `extraction-logique` | Interne | Moyenne | Clarifier limites de portée ; ne pas confondre avec extraction du système de fichiers. |
| 26 | `fichier-multimedia` | Interne | Basse | Lecture de cohérence sans anomalie manifeste ; contrôle externe et droits de réutilisation restent à effectuer. |
| 27 | `force-brute` | CLARUS | Moyenne | Différencier attaque en ligne/hors ligne, limites de tentative ; catégorie « Méthode de criminalistique » discutable. |
| 28 | `fai` | CLARUS | Moyenne | Garde des données variable selon régime juridique, réseau et acteur. |
| 29 | `hachage` | CLARUS | Basse | Lecture de cohérence sans anomalie manifeste ; contrôle externe et droits de réutilisation restent à effectuer. |
| 30 | `horodatage` | CLARUS | Moyenne | Préciser les limites du fuseau, de la précision et de la fiabilité de l’horloge. |
| 31 | `iccid` | CLARUS | Haute | Longueur variable selon standards/opérateurs ; retirer l’affirmation prescriptive des 19 chiffres. |
| 32 | `imei` | CLARUS | Haute | IMEI ne permet pas à lui seul une identification sûre du modèle et peut être multiple, absent ou altéré. |
| 33 | `instagram-direct` | Aide éditeur | Moyenne | Vérifier libellés et sources d’assistance Meta, variables dans le temps. |
| 34 | `integrite-donnees` | CLARUS | Haute | Une concordance de hash permet un contrôle de concordance de contenu, pas la preuve absolue de toutes les dimensions de l’intégrité. |
| 35 | `investigation-numerique` | CLARUS | Basse | Lecture de cohérence sans anomalie manifeste ; contrôle externe et droits de réutilisation restent à effectuer. |
| 36 | `journaux-systeme` | CLARUS | Moyenne | Ne pas assimiler journal et activité réelle de l’utilisateur sans corroboration. |
| 37 | `memoire` | CLARUS | Haute | Distinguer mémoire vive et stockage persistant ; catégorie « Équipement numérique » impropre. |
| 38 | `memoire-cache` | CLARUS | Haute | Cache logiciel et mémoire cache matérielle différents ; définition contradictoire avec terme anglais. |
| 39 | `messages-apple` | Aide éditeur | Moyenne | iMessage est un service et Messages une application ; éviter synonymie stricte. |
| 40 | `messenger` | Aide éditeur | Moyenne | Préciser portée des messages chiffrés / présents uniquement en ligne. |
| 41 | `metadonnees` | CLARUS | Moyenne | Différencier métadonnées natives, ajoutées et reconstruites. |
| 42 | `mode-avion` | CLARUS | Haute | L’activation du mode avion ne garantit pas la désactivation de toutes les radios ; contrôler Wi-Fi/Bluetooth et état réel. |
| 43 | `msisdn` | CLARUS | Moyenne | Un numéro inscrit sur SIM n’établit pas seul la ligne utilisée ; formulation déjà prudente. |
| 44 | `numero-serie` | CLARUS | Haute | L’unicité n’est pas garantie au-delà du périmètre fabricant/produit ; ne pas généraliser. |
| 45 | `preuve-numerique` | CLARUS | Moyenne | La valeur probatoire dépend du contexte et de l’appréciation judiciaire. |
| 46 | `recuperation-donnees` | CLARUS | Haute | Distinguer récupération de données supprimées, restauration et simple consultation de données. |
| 47 | `remise-resultats` | Interne | Basse | Lecture de cohérence sans anomalie manifeste ; contrôle externe et droits de réutilisation restent à effectuer. |
| 48 | `reparation-support` | Interne | Moyenne | Documenter les effets possibles de la réparation sur l’état du support. |
| 49 | `reseau-communications` | CLARUS | Basse | Lecture de cohérence sans anomalie manifeste ; contrôle externe et droits de réutilisation restent à effectuer. |
| 50 | `reseau-sans-fil` | CLARUS | Moyenne | Bluetooth n’est pas systématiquement un réseau IP ; cadrer les protocoles. |
| 51 | `scelle` | Interne | Haute | Différencier l’objet/scellé judiciaire du dispositif matériel de fermeture et du conditionnement. |
| 52 | `signal` | Aide éditeur | Moyenne | Ambiguïté du terme « Signal » (application vs signal réseau) dans la recherche. |
| 53 | `snapchat` | Aide éditeur | Moyenne | Les politiques de suppression varient selon paramètres ; vérifier version/date des aides. |
| 54 | `source-donnees` | CLARUS | Basse | Lecture de cohérence sans anomalie manifeste ; contrôle externe et droits de réutilisation restent à effectuer. |
| 55 | `stockage-cloud` | CLARUS | Haute | Distinguer accès distant, données synchronisées et présence physique sur le terminal. |
| 56 | `stockage-donnees` | CLARUS | Moyenne | Le stockage ne présume pas la possibilité d’extraire les données. |
| 57 | `support-stockage` | CLARUS | Haute | La définition mélange support matériel et contenu distant ; retirer l’assimilation du cloud au média physique. |
| 58 | `support-numerique` | CLARUS | Moyenne | Champ très large : distinguer dispositif, média de stockage et service distant. |
| 59 | `systeme-exploitation` | CLARUS | Basse | Lecture de cohérence sans anomalie manifeste ; contrôle externe et droits de réutilisation restent à effectuer. |
| 60 | `systeme-fichiers` | CLARUS | Moyenne | Veiller à différencier structure logique et volume physique. |
| 61 | `telegram` | Aide éditeur | Moyenne | Secret Chats et cloud chat ne sont pas stockés ni accessibles de la même manière. |
| 62 | `valeur-hachage` | CLARUS | Haute | « Empreinte numérique » polysémique (tracking/fingerprint matériel) ; borner le contexte et l’algorithme. |
| 63 | `whatsapp` | Aide éditeur | Moyenne | Distinguer accès local, sauvegardes et messages éphémères selon paramètres. |

## Risque de droits CLARUS

Pour les **43 fiches citant CLARUS**, inscrire dans une revue ultérieure : terme et page/entrée CLARUS exacte, extrait limité pour contrôle interne, degré de proximité de l'expression, rédaction indépendante proposée, base juridique/permission applicable, approbation humaine. **Ne pas considérer ces 43 fiches comme validées juridiquement.** La présence de références est une provenance déclarée, pas une autorisation de traduction/reproduction.

## Actions proposées, sans changement de données dans cette PR

1. Corriger d'abord l'authentification, le mode avion, la mémoire cache, les supports de stockage et les confusions acquisition/extraction/copie.
2. Réviser IMEI et ICCID pour éviter les affirmations trop générales ; encadrer valeur de hachage et intégrité.
3. Examiner les synonymes ambigus et la catégorisation, puis les formulations de rapport susceptibles d'affirmer plus que les observations.
4. Confronter séparément les 43 fiches CLARUS au texte original, avec vérification des droits et aucune reprise textuelle sans autorisation.
5. Soumettre les corrections par lots avec tests de synchronisation `data/` ↔ `extension/data/`.
