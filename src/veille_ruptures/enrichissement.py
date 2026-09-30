"""Enrichit les disponibilités avec le nom du médicament, son laboratoire et son statut MITM."""

from __future__ import annotations

from dataclasses import replace

from veille_ruptures.lecture import InfoMitm, InfoSpecialite
from veille_ruptures.modeles import Disponibilite


def enrichir(
    disponibilites: list[Disponibilite],
    specialites: dict[str, InfoSpecialite],
    mitm: dict[str, InfoMitm],
) -> list[Disponibilite]:
    resultat = []
    for d in disponibilites:
        specialite = specialites.get(d.cis)
        info_mitm = mitm.get(d.cis)
        resultat.append(
            replace(
                d,
                denomination=(
                    specialite.denomination if specialite else info_mitm.denomination if info_mitm else None
                ),
                titulaire=specialite.titulaire if specialite else None,
                est_mitm=info_mitm is not None,
                code_atc=info_mitm.code_atc if info_mitm else None,
            )
        )
    return resultat
