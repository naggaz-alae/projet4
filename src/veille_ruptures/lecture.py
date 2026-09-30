"""Lecture des fichiers de la Base de données publique des médicaments.

Format officiel : texte, valeurs séparées par des tabulations, SANS en-tête,
dates au format JJ/MM/AAAA (ou AAAAMMJJ dans certains fichiers).
Selon les fichiers et les époques, l'encodage est UTF-8 ou Windows-1252.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import date, datetime

from veille_ruptures.modeles import Disponibilite, Statut

logger = logging.getLogger(__name__)

COLONNES_DISPONIBILITE = (
    "cis",
    "cip13",
    "code_statut",
    "libelle_statut",
    "date_debut",
    "date_maj",
    "date_remise",
    "lien",
)
INDEX_TITULAIRE_SPECIALITES = 10  # CIS_bdpm.txt : 11e colonne = titulaire(s)


class ErreurFormat(ValueError):
    """Valeur illisible dans un fichier source."""


@dataclass
class RapportLecture:
    """Bilan d'une lecture : les lignes problématiques sont signalées, pas fatales."""

    lignes_lues: int = 0
    lignes_ignorees: int = 0
    avertissements: list[str] = field(default_factory=list)

    def signaler(self, message: str) -> None:
        self.avertissements.append(message)
        logger.warning(message)


def decoder(contenu: bytes) -> str:
    """Décode en UTF-8 (BOM éventuel retiré), sinon en Windows-1252."""
    try:
        return contenu.decode("utf-8-sig")
    except UnicodeDecodeError:
        return contenu.decode("cp1252")


def lignes_tsv(texte: str) -> Iterator[tuple[int, list[str]]]:
    """(numéro de ligne, cellules) pour chaque ligne non vide."""
    for numero, ligne in enumerate(texte.splitlines(), start=1):
        if ligne.strip():
            yield numero, [cellule.strip() for cellule in ligne.split("\t")]


def parser_date(valeur: str) -> date | None:
    """« 29/09/2026 » ou « 20260929 » -> date ; chaîne vide -> None."""
    valeur = valeur.strip()
    if not valeur:
        return None
    for fmt in ("%d/%m/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(valeur, fmt).date()
        except ValueError:
            continue
    raise ErreurFormat(f"date illisible : {valeur!r}")


def lire_disponibilites(texte: str) -> tuple[list[Disponibilite], RapportLecture]:
    """Lit CIS_CIP_Dispo_Spec.txt."""
    rapport = RapportLecture()
    resultat: list[Disponibilite] = []
    nb_colonnes = len(COLONNES_DISPONIBILITE)

    for numero, cellules in lignes_tsv(texte):
        rapport.lignes_lues += 1
        if len(cellules) < 4 or not cellules[0]:
            rapport.lignes_ignorees += 1
            rapport.signaler(f"ligne {numero} ignorée : {len(cellules)} colonne(s) au lieu de {nb_colonnes}")
            continue
        cellules = (cellules + [""] * nb_colonnes)[:nb_colonnes]
        valeurs = dict(zip(COLONNES_DISPONIBILITE, cellules, strict=True))

        dates: dict[str, date | None] = {}
        for nom in ("date_debut", "date_maj", "date_remise"):
            try:
                dates[nom] = parser_date(valeurs[nom])
            except ErreurFormat as err:
                rapport.signaler(f"ligne {numero}, {nom} : {err}")
                dates[nom] = None

        statut = Statut.depuis_libelle(valeurs["libelle_statut"])
        if statut is Statut.INCONNU:
            rapport.signaler(f"ligne {numero} : statut inconnu {valeurs['libelle_statut']!r}")

        resultat.append(
            Disponibilite(
                cis=valeurs["cis"],
                cip13=valeurs["cip13"],
                code_statut=valeurs["code_statut"],
                libelle_statut=valeurs["libelle_statut"],
                statut=statut,
                date_debut=dates["date_debut"],
                date_maj=dates["date_maj"],
                date_remise=dates["date_remise"],
                lien=valeurs["lien"],
            )
        )
    return resultat, rapport


@dataclass(frozen=True)
class InfoMitm:
    code_atc: str
    denomination: str


def lire_mitm(texte: str) -> dict[str, InfoMitm]:
    """Lit CIS_MITM.txt : code CIS -> (code ATC, dénomination)."""
    resultat: dict[str, InfoMitm] = {}
    for _, cellules in lignes_tsv(texte):
        if len(cellules) >= 3 and cellules[0]:
            resultat[cellules[0]] = InfoMitm(code_atc=cellules[1], denomination=cellules[2])
    return resultat


@dataclass(frozen=True)
class InfoSpecialite:
    denomination: str
    titulaire: str | None


def lire_specialites(texte: str) -> dict[str, InfoSpecialite]:
    """Lit CIS_bdpm.txt : code CIS -> (dénomination, titulaire)."""
    resultat: dict[str, InfoSpecialite] = {}
    for _, cellules in lignes_tsv(texte):
        if len(cellules) >= 2 and cellules[0]:
            titulaire = (
                cellules[INDEX_TITULAIRE_SPECIALITES] if len(cellules) > INDEX_TITULAIRE_SPECIALITES else None
            )
            resultat[cellules[0]] = InfoSpecialite(denomination=cellules[1], titulaire=titulaire or None)
    return resultat
