"""Point d'entrée de haut niveau : l'état du jour, prêt à l'emploi."""

from __future__ import annotations

from pathlib import Path

from veille_ruptures import sources
from veille_ruptures.enrichissement import enrichir
from veille_ruptures.lecture import (
    RapportLecture,
    decoder,
    lire_disponibilites,
    lire_mitm,
    lire_specialites,
)
from veille_ruptures.modeles import Disponibilite


def _contenu(nom: str, dossier_sources: Path | None, cache: Path | None) -> str:
    if dossier_sources is not None:
        return decoder((dossier_sources / sources.FICHIERS[nom]).read_bytes())
    return decoder(sources.telecharger(nom, cache=cache))


def etat_du_jour(
    dossier_sources: Path | None = None,
    cache: Path | None = None,
) -> tuple[list[Disponibilite], RapportLecture]:
    """Télécharge (ou lit dans `dossier_sources`) les fichiers officiels et renvoie
    les disponibilités enrichies (nom, laboratoire, MITM, code ATC) + un rapport de lecture."""
    disponibilites, rapport = lire_disponibilites(_contenu("disponibilites", dossier_sources, cache))
    specialites = lire_specialites(_contenu("specialites", dossier_sources, cache))
    mitm = lire_mitm(_contenu("mitm", dossier_sources, cache))
    return enrichir(disponibilites, specialites, mitm), rapport
