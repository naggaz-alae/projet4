"""Conversion en DataFrame pandas (dépendance optionnelle : pip install veille-ruptures[pandas])."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from veille_ruptures.modeles import Disponibilite


def vers_dataframe(disponibilites: list[Disponibilite]) -> Any:
    """Renvoie un pandas.DataFrame (une ligne par présentation)."""
    try:
        import pandas as pd
    except ImportError as err:  # pragma: no cover - dépend de l'environnement
        raise ImportError("pandas n'est pas installé : pip install 'veille-ruptures[pandas]'") from err
    lignes = []
    for d in disponibilites:
        ligne = asdict(d)
        ligne["statut"] = d.statut.value
        ligne["cle"] = d.cle
        lignes.append(ligne)
    return pd.DataFrame(lignes)
