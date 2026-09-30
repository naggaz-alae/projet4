"""Formats de sortie : JSON valide, Markdown, RSS, mention de licence, DataFrame."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET

import pytest

from tests.outils import JOUR1, JOUR2, etat_fixture
from veille_ruptures.diff import comparer
from veille_ruptures.indicateurs import calculer
from veille_ruptures.modeles import indexer
from veille_ruptures.sorties import en_json, en_markdown, en_rss


def _evenements():  # type: ignore[no-untyped-def]
    return comparer(indexer(etat_fixture("jour1")), indexer(etat_fixture("jour2")), JOUR2)


def test_json_valide_avec_attribution() -> None:
    etat = etat_fixture("jour2")
    doc = json.loads(en_json.document(JOUR2, _evenements(), calculer(etat, JOUR2), etat))
    assert "Etalab 2.0" in doc["attribution"]
    assert "29/09/2026" in doc["attribution"]
    assert {e["type"] for e in doc["evenements"]} >= {"nouvelle_rupture", "aggravation"}
    assert doc["indicateurs"]["nb_ruptures"] == 2
    assert doc["disponibilites"][0]["cle"]


def test_rapport_markdown() -> None:
    etat = etat_fixture("jour2")
    texte = en_markdown.rapport(JOUR2, _evenements(), calculer(etat, JOUR2), JOUR1)
    assert "# Veille des ruptures de médicaments — 29/09/2026" in texte
    assert "Nouvelle rupture (1)" in texte
    assert "ANTALFICTIF 1 g, comprimé (LABORATOIRE BETA) — **MITM**" in texte
    assert "Etalab 2.0" in texte


def test_rapport_markdown_sans_changement_et_premiere_photo() -> None:
    ind = calculer(etat_fixture("jour1"), JOUR1)
    assert "Aucun changement" in en_markdown.rapport(JOUR2, [], ind, JOUR1)
    assert "Première photo" in en_markdown.rapport(JOUR1, [], ind, None)


def test_flux_rss_valide() -> None:
    texte = en_rss.flux(_evenements(), JOUR2, "https://exemple.org")
    racine = ET.fromstring(texte.split("\n", 1)[1])
    items = racine.findall("./channel/item")
    assert len(items) == 5
    assert all(item.findtext("guid") for item in items)
    assert "Etalab 2.0" in (racine.findtext("./channel/description") or "")


def test_vers_dataframe() -> None:
    pd = pytest.importorskip("pandas")
    from veille_ruptures.tableau import vers_dataframe

    df = vers_dataframe(etat_fixture("jour2"))
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 5
    assert set(df["statut"]) >= {"rupture", "tension"}
