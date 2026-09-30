"""Tests par propriétés (Hypothesis) : des milliers d'états aléatoires, des règles toujours vraies.

1. comparer(A, A) ne produit aucun événement ;
2. appliquer(A, comparer(A, B)) redonne exactement B ;
3. chaque présentation modifiée produit exactement un événement.
"""

from __future__ import annotations

from datetime import date

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from veille_ruptures.diff import appliquer, comparer  # noqa: E402
from veille_ruptures.modeles import Disponibilite, Etat, Statut, indexer  # noqa: E402

JOURS = st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31))

disponibilites = st.builds(
    Disponibilite,
    cis=st.sampled_from([f"6{n:07d}" for n in range(12)]),  # peu de clés -> beaucoup de collisions
    cip13=st.sampled_from(["3400900000011", "3400900000028"]),
    code_statut=st.sampled_from(["1", "2", "3", "4"]),
    libelle_statut=st.just(""),
    statut=st.sampled_from(list(Statut)),
    date_debut=st.none() | JOURS,
    date_maj=st.none() | JOURS,
    est_mitm=st.booleans(),
)
etats = st.lists(disponibilites, max_size=20).map(indexer)


@given(etats)
def test_un_etat_compare_a_lui_meme_ne_change_pas(etat: Etat) -> None:
    assert comparer(etat, etat, avec_mises_a_jour=True) == []


@given(etats, etats)
def test_appliquer_le_diff_redonne_l_etat_d_arrivee(avant: Etat, apres: Etat) -> None:
    assert appliquer(avant, comparer(avant, apres, avec_mises_a_jour=True)) == apres


@given(etats, etats)
def test_un_evenement_par_presentation_modifiee(avant: Etat, apres: Etat) -> None:
    evenements = comparer(avant, apres, avec_mises_a_jour=True)
    modifiees = {c for c in avant.keys() | apres.keys() if avant.get(c) != apres.get(c)}
    assert sorted(e.cle for e in evenements) == sorted(modifiees)


def _statut_de(d: Disponibilite | None) -> Statut | None:
    return d.statut if d else None


@given(etats, etats)
def test_sans_mises_a_jour_seuls_les_changements_de_presence_ou_statut(avant: Etat, apres: Etat) -> None:
    for e in comparer(avant, apres):
        assert _statut_de(e.avant) != _statut_de(e.apres)
