# Méthodologie

## Sources

Base de données publique des médicaments, publiée par l'ANSM sous
[licence Etalab 2.0](https://www.etalab.gouv.fr/licence-ouverte-open-licence/) :

| Fichier | Contenu utilisé |
|---|---|
| `CIS_CIP_Dispo_Spec.txt` | Code CIS, code CIP13, code et libellé du statut, date de début, date de mise à jour, date de remise à disposition, lien ANSM |
| `CIS_MITM.txt` | Médicaments d'intérêt thérapeutique majeur : code CIS, code ATC, dénomination |
| `CIS_bdpm.txt` | Dénomination et laboratoire titulaire de chaque spécialité |

Format officiel : texte, tabulations, sans en-tête ; dates JJ/MM/AAAA.
La mention de source et la date des données sont ajoutées à chaque sortie, comme l'exige la licence.

## Statuts

Le statut est déduit du **libellé** fourni par l'ANSM (rupture, tension, arrêt de
commercialisation, remise à disposition), et non d'une table de codes figée : un statut
nouveau devient `inconnu` et est signalé, sans interrompre le traitement.

## Événements

Une présentation est identifiée par le couple (code CIS, code CIP13). Entre deux photos :

| Situation | Événement |
|---|---|
| Absente → rupture / tension | Nouvelle rupture / nouvelle tension |
| Tension → rupture | Aggravation |
| Rupture → tension | Amélioration |
| → Remise à disposition | Remise à disposition |
| → Arrêt de commercialisation | Arrêt de commercialisation |
| Présente → absente | Sortie de la liste |
| Même statut, autre champ modifié | Mise à jour (masquée par défaut) |

Propriétés vérifiées par des tests Hypothesis sur des milliers d'états aléatoires :
comparer un état avec lui-même ne produit aucun événement, et rejouer les événements
sur l'état de départ redonne exactement l'état d'arrivée.

## Épisodes

Un épisode est une période continue d'indisponibilité (rupture ou tension) d'une présentation.
Son début est la **date de début déclarée** à l'ANSM quand elle existe, sinon le premier jour
observé ; sa fin est le premier jour où la présentation n'est plus indisponible.

## Limites

- L'historique commence à la première photo ; une rupture ouverte et refermée entre deux
  photos n'est pas vue.
- Le code ATC (classe thérapeutique) n'est fourni que pour les MITM : les autres
  présentations apparaissent comme « non classées ».
- Les données sont celles déclarées par les industriels à l'ANSM ; l'outil ne les corrige pas.
