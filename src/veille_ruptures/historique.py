"""Reconstruction des épisodes de rupture ou de tension à partir des photos quotidiennes.

Un épisode = une période continue pendant laquelle une présentation est indisponible
(rupture ou tension). Son début est la date de début DÉCLARÉE à l'ANSM quand elle
existe (on peut donc mesurer des durées dès la première photo), sinon le premier jour observé.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from veille_ruptures.modeles import Disponibilite, Statut


@dataclass
class Episode:
    cle: str
    cis: str
    denomination: str | None
    titulaire: str | None
    est_mitm: bool
    code_atc: str | None
    debut: date
    fin: date | None = None
    pire_statut: Statut = Statut.TENSION
    jours_observes: int = 0

    @property
    def en_cours(self) -> bool:
        return self.fin is None

    def duree_jours(self, reference: date) -> int:
        """Durée en jours ; pour un épisode en cours, jusqu'à la date de référence."""
        return ((self.fin or reference) - self.debut).days

    def _observer(self, d: Disponibilite) -> None:
        self.jours_observes += 1
        if d.statut is Statut.RUPTURE:
            self.pire_statut = Statut.RUPTURE
        self.denomination = d.denomination or self.denomination
        self.titulaire = d.titulaire or self.titulaire
        self.est_mitm = d.est_mitm
        self.code_atc = d.code_atc or self.code_atc


def reconstruire_episodes(photos: list[tuple[date, list[Disponibilite]]]) -> list[Episode]:
    """`photos` : liste de (jour, disponibilités). Renvoie les épisodes clos puis en cours."""
    ouverts: dict[str, Episode] = {}
    clos: list[Episode] = []

    for jour, disponibilites in sorted(photos, key=lambda p: p[0]):
        indisponibles = {d.cle: d for d in disponibilites if d.statut.est_indisponible}

        for cle, d in indisponibles.items():
            episode = ouverts.get(cle)
            if episode is None:
                debut = min(d.date_debut, jour) if d.date_debut else jour
                episode = Episode(
                    cle=cle,
                    cis=d.cis,
                    denomination=d.denomination,
                    titulaire=d.titulaire,
                    est_mitm=d.est_mitm,
                    code_atc=d.code_atc,
                    debut=debut,
                    pire_statut=d.statut,
                )
                ouverts[cle] = episode
            episode._observer(d)

        for cle in [c for c in ouverts if c not in indisponibles]:
            episode = ouverts.pop(cle)
            episode.fin = jour
            clos.append(episode)

    return clos + list(ouverts.values())
