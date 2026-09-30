"""Formats de sortie : JSON, Markdown, RSS. Tous incluent la mention de source exigée par la licence."""

from __future__ import annotations

from datetime import date

AVERTISSEMENT = (
    "Outil d'information indépendant, non affilié à l'ANSM. La référence officielle reste le site de l'ANSM."
)


def attribution(jour: date) -> str:
    """Mention obligatoire de la licence Etalab 2.0 (source + date des données)."""
    return (
        "Source : ANSM, Base de données publique des médicaments "
        f"(licence Etalab 2.0), données du {jour.strftime('%d/%m/%Y')}."
    )
