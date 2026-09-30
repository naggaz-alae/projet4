"""Indicateurs de synthèse sur un état du jour et sur l'historique des épisodes."""

from __future__ import annotations

import statistics
from collections import Counter
from dataclasses import dataclass, field
from datetime import date

from veille_ruptures.historique import Episode
from veille_ruptures.modeles import Disponibilite, Statut

# Groupes anatomiques principaux de la classification ATC (1re lettre du code)
CLASSES_ATC = {
    "A": "Voies digestives et métabolisme",
    "B": "Sang et organes hématopoïétiques",
    "C": "Système cardiovasculaire",
    "D": "Médicaments dermatologiques",
    "G": "Système génito-urinaire et hormones sexuelles",
    "H": "Hormones systémiques",
    "J": "Anti-infectieux généraux à usage systémique",
    "L": "Antinéoplasiques et immunomodulateurs",
    "M": "Muscle et squelette",
    "N": "Système nerveux",
    "P": "Antiparasitaires, insecticides",
    "R": "Système respiratoire",
    "S": "Organes sensoriels",
    "V": "Divers",
}
NON_CLASSE = "Non classé (hors liste MITM)"


def classe_atc(code_atc: str | None) -> str:
    """Libellé du groupe anatomique ; le code ATC n'est connu que pour les MITM."""
    if not code_atc:
        return NON_CLASSE
    return CLASSES_ATC.get(code_atc[0].upper(), f"Code ATC {code_atc}")


@dataclass
class Indicateurs:
    jour: date
    nb_ruptures: int
    nb_tensions: int
    nb_mitm_indisponibles: int
    anciennete_mediane_jours: float | None
    par_classe: list[tuple[str, int]] = field(default_factory=list)
    par_titulaire: list[tuple[str, int]] = field(default_factory=list)
    duree_mediane_episodes_clos: float | None = None
    nb_episodes_clos: int = 0


def calculer(
    etat: list[Disponibilite],
    jour: date,
    episodes: list[Episode] | None = None,
    top: int = 10,
) -> Indicateurs:
    indisponibles = [d for d in etat if d.statut.est_indisponible]
    anciennetes = [(jour - d.date_debut).days for d in indisponibles if d.date_debut]
    clos = [e for e in (episodes or []) if not e.en_cours]
    return Indicateurs(
        jour=jour,
        nb_ruptures=sum(d.statut is Statut.RUPTURE for d in indisponibles),
        nb_tensions=sum(d.statut is Statut.TENSION for d in indisponibles),
        nb_mitm_indisponibles=sum(d.est_mitm for d in indisponibles),
        anciennete_mediane_jours=statistics.median(anciennetes) if anciennetes else None,
        par_classe=Counter(classe_atc(d.code_atc) for d in indisponibles).most_common(top),
        par_titulaire=Counter(d.titulaire or "Inconnu" for d in indisponibles).most_common(top),
        duree_mediane_episodes_clos=(statistics.median(e.duree_jours(jour) for e in clos) if clos else None),
        nb_episodes_clos=len(clos),
    )
