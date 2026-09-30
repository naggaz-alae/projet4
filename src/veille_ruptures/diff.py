"""Comparaison de deux états : quels changements entre hier et aujourd'hui ?

Règles, pour chaque présentation (clé CIS:CIP13) :

    absente -> présente     nouvelle rupture / tension, arrêt, remise à disposition
    présente -> absente     sortie de la liste
    tension -> rupture      aggravation
    rupture -> tension      amélioration
    même statut, autre champ modifié : mise à jour (ignorée par défaut)

Propriétés garanties (vérifiées par des tests Hypothesis) :
    comparer(A, A) == []
    appliquer(A, comparer(A, B, avec_mises_a_jour=True)) == B
"""

from __future__ import annotations

from datetime import date

from veille_ruptures.modeles import Disponibilite, Etat, Evenement, Statut, TypeEvenement

_APPARITION = {
    Statut.RUPTURE: TypeEvenement.NOUVELLE_RUPTURE,
    Statut.TENSION: TypeEvenement.NOUVELLE_TENSION,
    Statut.ARRET: TypeEvenement.ARRET_COMMERCIALISATION,
    Statut.REMISE: TypeEvenement.REMISE_A_DISPOSITION,
    Statut.INCONNU: TypeEvenement.CHANGEMENT_STATUT,
}


def type_changement(avant: Statut, apres: Statut) -> TypeEvenement:
    """Type d'événement quand le statut d'une présentation change."""
    if (avant, apres) == (Statut.TENSION, Statut.RUPTURE):
        return TypeEvenement.AGGRAVATION
    if (avant, apres) == (Statut.RUPTURE, Statut.TENSION):
        return TypeEvenement.AMELIORATION
    return _APPARITION[apres]


def comparer(
    avant: Etat,
    apres: Etat,
    date_evenements: date | None = None,
    avec_mises_a_jour: bool = False,
) -> list[Evenement]:
    """Liste des événements pour passer de `avant` à `apres`, triés par type puis par nom."""
    jour = date_evenements or date.today()
    evenements: list[Evenement] = []

    for cle in sorted(avant.keys() | apres.keys()):
        a, b = avant.get(cle), apres.get(cle)
        if a == b:
            continue
        if a is None and b is not None:
            type_ = _APPARITION[b.statut]
        elif b is None:
            type_ = TypeEvenement.SORTIE_DE_LISTE
        elif a is not None and a.statut != b.statut:
            type_ = type_changement(a.statut, b.statut)
        else:
            if not avec_mises_a_jour:
                continue
            type_ = TypeEvenement.MISE_A_JOUR
        evenements.append(Evenement(type=type_, cle=cle, date=jour, avant=a, apres=b))

    ordre = list(TypeEvenement)
    return sorted(evenements, key=lambda e: (ordre.index(e.type), e.disponibilite.nom))


def appliquer(etat: Etat, evenements: list[Evenement]) -> Etat:
    """Rejoue des événements sur un état (utilisé pour vérifier la cohérence du diff)."""
    resultat: dict[str, Disponibilite] = dict(etat)
    for e in evenements:
        if e.apres is None:
            resultat.pop(e.cle, None)
        else:
            resultat[e.cle] = e.apres
    return resultat
