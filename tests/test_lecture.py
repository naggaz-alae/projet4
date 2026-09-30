"""Lecture des fichiers officiels : format sans en-tête, encodages, dates, lignes invalides."""

from __future__ import annotations

from datetime import date

import pytest

from tests.outils import DONNEES, etat_fixture
from veille_ruptures.lecture import (
    ErreurFormat,
    decoder,
    lire_disponibilites,
    lire_mitm,
    lire_specialites,
    parser_date,
)
from veille_ruptures.modeles import Statut


@pytest.mark.parametrize(
    ("libelle", "attendu"),
    [
        ("Rupture de stock", Statut.RUPTURE),
        ("Tension d'approvisionnement", Statut.TENSION),
        ("Arrêt de commercialisation", Statut.ARRET),
        ("ARRET DE COMMERCIALISATION", Statut.ARRET),
        ("Remise à disposition", Statut.REMISE),
        ("Nouveau statut inventé", Statut.INCONNU),
    ],
)
def test_statut_depuis_libelle(libelle: str, attendu: Statut) -> None:
    assert Statut.depuis_libelle(libelle) is attendu


def test_decodage_utf8_windows_et_bom() -> None:
    assert decoder("Arrêt".encode()) == "Arrêt"
    assert decoder("Arrêt".encode("cp1252")) == "Arrêt"
    assert decoder(b"\xef\xbb\xbfRupture") == "Rupture"


def test_dates() -> None:
    assert parser_date("29/09/2026") == date(2026, 9, 29)
    assert parser_date("20260929") == date(2026, 9, 29)
    assert parser_date("  ") is None
    with pytest.raises(ErreurFormat):
        parser_date("32/13/2026")


def test_lecture_disponibilites_et_rapport() -> None:
    texte = (DONNEES / "jour2" / "CIS_CIP_Dispo_Spec.txt").read_text(encoding="utf-8")
    dispos, rapport = lire_disponibilites(texte)

    assert rapport.lignes_lues == 6
    assert rapport.lignes_ignorees == 1  # ligne tronquée
    assert len(dispos) == 5
    remise = dispos[0]
    assert (remise.cis, remise.cip13, remise.statut) == ("60000001", "3400900000011", Statut.REMISE)
    assert remise.date_remise == date(2026, 9, 29)
    # La date invalide est signalée mais la ligne est conservée
    invalide = next(d for d in dispos if d.cis == "60000006")
    assert invalide.date_debut is None
    assert any("date_debut" in a for a in rapport.avertissements)


def test_statut_inconnu_signale_sans_planter() -> None:
    dispos, rapport = lire_disponibilites("1\t2\t9\tStatut futur\t\t\t\t\n")
    assert dispos[0].statut is Statut.INCONNU
    assert any("statut inconnu" in a for a in rapport.avertissements)


def test_lignes_courtes_completees_et_vides_ignorees() -> None:
    dispos, rapport = lire_disponibilites("\n1\t2\t1\tRupture de stock\n\n")
    assert rapport.lignes_lues == 1
    assert dispos[0].lien == ""
    assert dispos[0].date_debut is None


def test_lecture_mitm_et_specialites() -> None:
    mitm = lire_mitm((DONNEES / "jour1" / "CIS_MITM.txt").read_text(encoding="utf-8"))
    assert mitm["60000005"].code_atc == "N02BE01"
    specialites = lire_specialites((DONNEES / "jour1" / "CIS_bdpm.txt").read_text(encoding="utf-8"))
    assert specialites["60000002"].titulaire == "LABORATOIRE BETA"
    assert lire_specialites("99\tNOM SEUL\n")["99"].titulaire is None


def test_enrichissement_complet() -> None:
    etat = {d.cis: d for d in etat_fixture("jour2")}
    antalgique = etat["60000005"]
    assert antalgique.denomination == "ANTALFICTIF 1 g, comprimé"
    assert antalgique.titulaire == "LABORATOIRE BETA"
    assert antalgique.est_mitm
    assert antalgique.code_atc == "N02BE01"
    assert not etat["60000001"].est_mitm
    assert etat["60000001"].code_atc is None
