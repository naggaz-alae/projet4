"""Photos quotidiennes de l'état des disponibilités.

Chaque jour est enregistré dans un CSV nommé AAAA-MM-JJ.csv, trié par clé :
dans un dépôt Git, le diff entre deux jours reste ainsi lisible ligne à ligne
(technique dite de « git scraping »).
"""

from __future__ import annotations

import csv
from dataclasses import fields
from datetime import date
from pathlib import Path

from veille_ruptures.modeles import Disponibilite, Statut

COLONNES = [f.name for f in fields(Disponibilite)]
_DATES = {"date_debut", "date_maj", "date_remise"}


def _vers_texte(d: Disponibilite) -> dict[str, str]:
    ligne: dict[str, str] = {}
    for nom in COLONNES:
        valeur = getattr(d, nom)
        if valeur is None:
            ligne[nom] = ""
        elif isinstance(valeur, Statut):
            ligne[nom] = valeur.value
        elif isinstance(valeur, bool):
            ligne[nom] = "1" if valeur else "0"
        elif isinstance(valeur, date):
            ligne[nom] = valeur.isoformat()
        else:
            ligne[nom] = str(valeur)
    return ligne


def _depuis_texte(ligne: dict[str, str]) -> Disponibilite:
    def date_ou_none(nom: str) -> date | None:
        return date.fromisoformat(ligne[nom]) if ligne.get(nom) else None

    def texte_ou_none(nom: str) -> str | None:
        return ligne.get(nom) or None

    return Disponibilite(
        cis=ligne["cis"],
        cip13=ligne["cip13"],
        code_statut=ligne["code_statut"],
        libelle_statut=ligne["libelle_statut"],
        statut=Statut(ligne["statut"]),
        date_debut=date_ou_none("date_debut"),
        date_maj=date_ou_none("date_maj"),
        date_remise=date_ou_none("date_remise"),
        lien=ligne.get("lien", ""),
        denomination=texte_ou_none("denomination"),
        titulaire=texte_ou_none("titulaire"),
        est_mitm=ligne.get("est_mitm") == "1",
        code_atc=texte_ou_none("code_atc"),
    )


def chemin_instantane(dossier: Path, jour: date) -> Path:
    return dossier / f"{jour.isoformat()}.csv"


def enregistrer(disponibilites: list[Disponibilite], dossier: Path, jour: date) -> Path:
    """Enregistre la photo du jour (écrase une photo existante du même jour)."""
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = chemin_instantane(dossier, jour)
    with chemin.open("w", encoding="utf-8", newline="") as f:
        ecrivain = csv.DictWriter(f, fieldnames=COLONNES, lineterminator="\n")
        ecrivain.writeheader()
        for d in sorted(disponibilites, key=lambda x: x.cle):
            ecrivain.writerow(_vers_texte(d))
    return chemin


def charger(dossier: Path, jour: date) -> list[Disponibilite]:
    chemin = chemin_instantane(dossier, jour)
    if not chemin.exists():
        raise FileNotFoundError(f"Aucune photo pour le {jour.isoformat()} dans {dossier}")
    with chemin.open(encoding="utf-8", newline="") as f:
        return [_depuis_texte(ligne) for ligne in csv.DictReader(f)]


def lister_jours(dossier: Path) -> list[date]:
    """Jours disponibles, du plus ancien au plus récent."""
    if not dossier.exists():
        return []
    jours = []
    for chemin in dossier.glob("*.csv"):
        try:
            jours.append(date.fromisoformat(chemin.stem))
        except ValueError:
            continue
    return sorted(jours)


def jour_precedent(dossier: Path, jour: date) -> date | None:
    """Dernière photo strictement antérieure à `jour`."""
    anterieurs = [j for j in lister_jours(dossier) if j < jour]
    return anterieurs[-1] if anterieurs else None
