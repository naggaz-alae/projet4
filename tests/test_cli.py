"""Ligne de commande, testée avec le CliRunner de Click (fichiers locaux, aucun réseau)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from tests.outils import DONNEES
from veille_ruptures import __version__
from veille_ruptures.cli import main
from veille_ruptures.sources import ErreurSource

J1, J2 = "2026-09-28", "2026-09-29"


def lancer(*args: str) -> str:
    """Sortie standard uniquement : les avertissements vont sur la sortie d'erreur,
    pour qu'un `veille-ruptures etat --format json > fichier.json` reste un JSON valide."""
    resultat = CliRunner().invoke(main, list(args), catch_exceptions=False)
    assert resultat.exit_code == 0, resultat.output
    return resultat.stdout


def preparer_photos(dossier: Path) -> None:
    lancer("instantane", "--dossier", str(dossier), "--jour", J1, "--sources", str(DONNEES / "jour1"))
    lancer("instantane", "--dossier", str(dossier), "--jour", J2, "--sources", str(DONNEES / "jour2"))


def test_version() -> None:
    assert __version__ in lancer("--version")


def test_etat_table_et_filtres() -> None:
    sortie = lancer("etat", "--sources", str(DONNEES / "jour2"))
    assert "ANTALFICTIF" in sortie
    assert "5 présentation(s)" in sortie
    assert "Etalab 2.0" in sortie

    mitm = lancer("etat", "--sources", str(DONNEES / "jour2"), "--mitm", "--statut", "rupture")
    assert "2 présentation(s)" in mitm
    assert "CARDIOFICTIF" not in mitm

    assert "1 présentation(s)" in lancer("etat", "--sources", str(DONNEES / "jour2"), "--atc", "n02")
    assert "GASTROFICTIF" in lancer("etat", "--sources", str(DONNEES / "jour2"), "--labo", "beta")
    assert "affichée(s)" in lancer("etat", "--sources", str(DONNEES / "jour2"), "--limite", "2")


def test_etat_json_et_csv() -> None:
    doc = json.loads(lancer("etat", "--sources", str(DONNEES / "jour2"), "--format", "json"))
    assert len(doc["disponibilites"]) == 5
    csv_texte = lancer("etat", "--sources", str(DONNEES / "jour2"), "--format", "csv")
    assert csv_texte.splitlines()[0].startswith("cis,cip13,statut")
    assert len(csv_texte.splitlines()) == 6


def test_diff_tous_formats(tmp_path: Path) -> None:
    preparer_photos(tmp_path)
    table = lancer("diff", "--dossier", str(tmp_path))
    assert "5 changement(s)" in table
    assert "Aggravation" in table
    doc = json.loads(lancer("diff", J1, J2, "--dossier", str(tmp_path), "--format", "json"))
    assert len(doc["evenements"]) == 5
    assert "Nouvelle rupture" in lancer("diff", "--dossier", str(tmp_path), "--format", "markdown")


def test_diff_sans_assez_de_photos(tmp_path: Path) -> None:
    resultat = CliRunner().invoke(main, ["diff", "--dossier", str(tmp_path)])
    assert resultat.exit_code != 0
    assert "deux photos" in resultat.output


def test_historique_stats_rapport_flux(tmp_path: Path) -> None:
    preparer_photos(tmp_path)
    assert "GASTROFICTIF" in lancer("historique", "--dossier", str(tmp_path), "--nom", "gastro")
    assert "Aucun épisode" in lancer("historique", "--dossier", str(tmp_path), "--cis", "00000000")

    stats = lancer("stats", "--dossier", str(tmp_path))
    assert "Présentations en rupture" in stats
    assert "LABORATOIRE BETA" in stats
    assert json.loads(lancer("stats", "--dossier", str(tmp_path), "--format", "json"))["indicateurs"]

    rapport = tmp_path / "sortie" / "rapport.md"
    lancer("rapport", "--dossier", str(tmp_path), "--sortie", str(rapport))
    assert "Aggravation" in rapport.read_text(encoding="utf-8")
    assert "# Veille" in lancer("rapport", "--dossier", str(tmp_path))

    flux = tmp_path / "flux.xml"
    assert "5 événement(s)" in lancer("flux", "--dossier", str(tmp_path), "--sortie", str(flux))
    assert flux.read_text(encoding="utf-8").startswith("<?xml")
    flux_json = tmp_path / "flux.json"
    lancer("flux", "--dossier", str(tmp_path), "--sortie", str(flux_json), "--format", "json")
    assert json.loads(flux_json.read_text(encoding="utf-8"))["evenements"]


def test_stats_sans_photo_utilise_l_etat_du_jour(tmp_path: Path) -> None:
    sortie = lancer("stats", "--dossier", str(tmp_path / "vide"), "--sources", str(DONNEES / "jour2"))
    assert "Présentations en rupture" in sortie


def test_source_indisponible_message_clair() -> None:
    with patch("veille_ruptures.cli.etat_du_jour", side_effect=ErreurSource("serveur ANSM injoignable")):
        resultat = CliRunner().invoke(main, ["etat"])
    assert resultat.exit_code != 0
    assert "serveur ANSM injoignable" in resultat.output


def test_diff_photo_absente(tmp_path: Path) -> None:
    preparer_photos(tmp_path)
    resultat = CliRunner().invoke(main, ["diff", "2020-01-01", J2, "--dossier", str(tmp_path)])
    assert resultat.exit_code != 0
    assert "Aucune photo" in resultat.output


def test_commandes_sans_photo(tmp_path: Path) -> None:
    for commande in (["rapport"], ["historique"], ["flux", "--sortie", str(tmp_path / "f.xml")]):
        resultat = CliRunner().invoke(main, [*commande, "--dossier", str(tmp_path / "vide")])
        assert resultat.exit_code != 0
        assert "Aucune photo" in resultat.output
