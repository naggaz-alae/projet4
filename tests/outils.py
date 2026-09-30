"""Données et constructeurs partagés par les tests (médicaments fictifs)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from veille_ruptures.modeles import Disponibilite, Statut
from veille_ruptures.veille import etat_du_jour

DONNEES = Path(__file__).parent / "donnees"
JOUR1, JOUR2 = date(2026, 9, 28), date(2026, 9, 29)


def etat_fixture(nom: str) -> list[Disponibilite]:
    etat, _ = etat_du_jour(dossier_sources=DONNEES / nom)
    return etat


def dispo(cis: str = "1", statut: Statut = Statut.RUPTURE, **autres: object) -> Disponibilite:
    """Construit une disponibilité minimale pour un test."""
    valeurs: dict[str, object] = {
        "cis": cis,
        "cip13": f"34009{cis.zfill(8)}",
        "code_statut": "1",
        "libelle_statut": statut.libelle_court,
        "statut": statut,
    }
    valeurs.update(autres)
    return Disponibilite(**valeurs)  # type: ignore[arg-type]
