"""Photos quotidiennes, reconstruction des épisodes et indicateurs."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from tests.outils import JOUR1, JOUR2, dispo, etat_fixture
from veille_ruptures import instantanes
from veille_ruptures.historique import reconstruire_episodes
from veille_ruptures.indicateurs import NON_CLASSE, calculer, classe_atc
from veille_ruptures.modeles import Statut


def test_photo_aller_retour_sans_perte(tmp_path: Path) -> None:
    etat = etat_fixture("jour2")
    chemin = instantanes.enregistrer(etat, tmp_path, JOUR2)
    assert chemin.name == "2026-09-29.csv"
    relu = instantanes.charger(tmp_path, JOUR2)
    assert sorted(relu, key=lambda d: d.cle) == sorted(etat, key=lambda d: d.cle)


def test_liste_des_jours_et_jour_precedent(tmp_path: Path) -> None:
    instantanes.enregistrer(etat_fixture("jour1"), tmp_path, JOUR1)
    instantanes.enregistrer(etat_fixture("jour2"), tmp_path, JOUR2)
    (tmp_path / "notes.csv").write_text("pas une date", encoding="utf-8")
    assert instantanes.lister_jours(tmp_path) == [JOUR1, JOUR2]
    assert instantanes.jour_precedent(tmp_path, JOUR2) == JOUR1
    assert instantanes.jour_precedent(tmp_path, JOUR1) is None
    assert instantanes.lister_jours(tmp_path / "absent") == []
    with pytest.raises(FileNotFoundError):
        instantanes.charger(tmp_path, date(2020, 1, 1))


def test_episodes_ouverts_fermes_et_pire_statut() -> None:
    j1, j2, j3 = date(2026, 9, 1), date(2026, 9, 2), date(2026, 9, 3)
    tension = dispo("1", Statut.TENSION, date_debut=date(2026, 8, 20))
    rupture = replace(tension, statut=Statut.RUPTURE)
    autre = dispo("2", Statut.RUPTURE)
    photos = [(j1, [tension, autre]), (j2, [rupture, autre]), (j3, [autre])]

    episodes = {e.cis: e for e in reconstruire_episodes(photos)}
    premier = episodes["1"]
    assert premier.debut == date(2026, 8, 20)  # date déclarée, antérieure à la 1re photo
    assert premier.fin == j3
    assert premier.pire_statut is Statut.RUPTURE
    assert premier.jours_observes == 2
    assert premier.duree_jours(j3) == 14
    assert episodes["2"].en_cours
    assert episodes["2"].debut == j1  # pas de date déclarée : premier jour observé


def test_classes_atc() -> None:
    assert classe_atc("N02BE01") == "Système nerveux"
    assert classe_atc(None) == NON_CLASSE
    assert classe_atc("Z99") == "Code ATC Z99"


def test_indicateurs_du_jour() -> None:
    etat = etat_fixture("jour2")
    ind = calculer(etat, JOUR2)
    assert (ind.nb_ruptures, ind.nb_tensions, ind.nb_mitm_indisponibles) == (2, 1, 2)
    assert dict(ind.par_titulaire)["LABORATOIRE BETA"] == 2
    assert dict(ind.par_classe)["Système nerveux"] == 1
    # Anciennetés connues : 60000002 (14 j) et 60000005 (1 j) ; 60000006 a une date invalide
    assert ind.anciennete_mediane_jours == 7.5
    assert ind.duree_mediane_episodes_clos is None


def test_indicateurs_avec_historique() -> None:
    photos = [(JOUR1, etat_fixture("jour1")), (JOUR2, etat_fixture("jour2"))]
    ind = calculer(photos[-1][1], JOUR2, reconstruire_episodes(photos))
    assert ind.nb_episodes_clos == 2  # 60000001 (remise) et 60000003 (sortie de liste)
    assert ind.duree_mediane_episodes_clos is not None
