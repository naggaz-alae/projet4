"""Sortie JSON (pour les programmes et les flux)."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
from enum import Enum
from typing import Any

from veille_ruptures.indicateurs import Indicateurs
from veille_ruptures.modeles import Disponibilite, Evenement
from veille_ruptures.sorties import AVERTISSEMENT, attribution


def _serialisable(valeur: Any) -> Any:
    if isinstance(valeur, Enum):
        return valeur.value
    if isinstance(valeur, date):
        return valeur.isoformat()
    if isinstance(valeur, dict):
        return {cle: _serialisable(v) for cle, v in valeur.items()}
    if isinstance(valeur, (list, tuple)):
        return [_serialisable(v) for v in valeur]
    return valeur


def disponibilite_dict(d: Disponibilite) -> dict[str, Any]:
    return {"cle": d.cle, **_serialisable(asdict(d))}


def evenement_dict(e: Evenement) -> dict[str, Any]:
    d = e.disponibilite
    return {
        "type": e.type.value,
        "libelle": e.type.libelle,
        "date": e.date.isoformat(),
        "cle": e.cle,
        "denomination": d.nom,
        "titulaire": d.titulaire,
        "est_mitm": d.est_mitm,
        "statut_avant": e.avant.statut.value if e.avant else None,
        "statut_apres": e.apres.statut.value if e.apres else None,
        "lien": d.lien,
    }


def document(
    jour: date,
    evenements: list[Evenement] | None = None,
    indicateurs: Indicateurs | None = None,
    disponibilites: list[Disponibilite] | None = None,
) -> str:
    contenu: dict[str, Any] = {
        "date": jour.isoformat(),
        "attribution": attribution(jour),
        "avertissement": AVERTISSEMENT,
    }
    if indicateurs is not None:
        contenu["indicateurs"] = _serialisable(asdict(indicateurs))
    if evenements is not None:
        contenu["evenements"] = [evenement_dict(e) for e in evenements]
    if disponibilites is not None:
        contenu["disponibilites"] = [disponibilite_dict(d) for d in disponibilites]
    return json.dumps(contenu, ensure_ascii=False, indent=2)
