"""Détection des changements entre deux jours."""

from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest

from tests.outils import JOUR2, dispo, etat_fixture
from veille_ruptures.diff import appliquer, comparer, type_changement
from veille_ruptures.modeles import Statut, TypeEvenement, indexer


def test_scenario_complet_entre_deux_jours() -> None:
    evenements = comparer(indexer(etat_fixture("jour1")), indexer(etat_fixture("jour2")), JOUR2)
    par_cis = {e.disponibilite.cis: e.type for e in evenements}

    assert par_cis == {
        "60000001": TypeEvenement.REMISE_A_DISPOSITION,
        "60000002": TypeEvenement.AGGRAVATION,
        "60000003": TypeEvenement.SORTIE_DE_LISTE,
        "60000005": TypeEvenement.NOUVELLE_RUPTURE,
        "60000006": TypeEvenement.NOUVELLE_TENSION,
    }
    assert "60000004" not in par_cis  # inchangé
    assert all(e.date == JOUR2 for e in evenements)
    # Tri : dans l'ordre des types d'événements
    ordre = list(TypeEvenement)
    assert [ordre.index(e.type) for e in evenements] == sorted(ordre.index(e.type) for e in evenements)


@pytest.mark.parametrize(
    ("avant", "apres", "attendu"),
    [
        (Statut.TENSION, Statut.RUPTURE, TypeEvenement.AGGRAVATION),
        (Statut.RUPTURE, Statut.TENSION, TypeEvenement.AMELIORATION),
        (Statut.RUPTURE, Statut.REMISE, TypeEvenement.REMISE_A_DISPOSITION),
        (Statut.TENSION, Statut.ARRET, TypeEvenement.ARRET_COMMERCIALISATION),
        (Statut.REMISE, Statut.RUPTURE, TypeEvenement.NOUVELLE_RUPTURE),
        (Statut.ARRET, Statut.TENSION, TypeEvenement.NOUVELLE_TENSION),
        (Statut.RUPTURE, Statut.INCONNU, TypeEvenement.CHANGEMENT_STATUT),
    ],
)
def test_types_de_changement(avant: Statut, apres: Statut, attendu: TypeEvenement) -> None:
    assert type_changement(avant, apres) is attendu


def test_mises_a_jour_ignorees_par_defaut() -> None:
    a = dispo("1", date_maj=date(2026, 9, 1))
    b = replace(a, date_maj=date(2026, 9, 2))
    assert comparer(indexer([a]), indexer([b])) == []
    evenements = comparer(indexer([a]), indexer([b]), avec_mises_a_jour=True)
    assert [e.type for e in evenements] == [TypeEvenement.MISE_A_JOUR]


def test_appliquer_reconstruit_l_etat_d_arrivee() -> None:
    avant, apres = indexer(etat_fixture("jour1")), indexer(etat_fixture("jour2"))
    assert appliquer(avant, comparer(avant, apres, avec_mises_a_jour=True)) == apres


def test_comparer_un_etat_avec_lui_meme() -> None:
    etat = indexer(etat_fixture("jour2"))
    assert comparer(etat, etat) == []
