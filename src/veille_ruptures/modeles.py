"""Modèles de données : disponibilité d'une présentation de médicament et événements."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from datetime import date
from enum import Enum


def _sans_accents(texte: str) -> str:
    decompose = unicodedata.normalize("NFKD", texte)
    return "".join(c for c in decompose if not unicodedata.combining(c)).lower()


class Statut(str, Enum):
    """Statut de disponibilité, déduit du LIBELLÉ fourni par l'ANSM.

    On ne code pas en dur la correspondance « code -> statut » : si l'ANSM
    ajoute un nouveau statut, il devient ``INCONNU`` au lieu de faire planter l'outil.
    """

    RUPTURE = "rupture"
    TENSION = "tension"
    ARRET = "arret_commercialisation"
    REMISE = "remise_a_disposition"
    INCONNU = "inconnu"

    @classmethod
    def depuis_libelle(cls, libelle: str) -> Statut:
        texte = _sans_accents(libelle)
        if "rupture" in texte:
            return cls.RUPTURE
        if "tension" in texte:
            return cls.TENSION
        if "arret" in texte:
            return cls.ARRET
        if "remise" in texte:
            return cls.REMISE
        return cls.INCONNU

    @property
    def est_indisponible(self) -> bool:
        """Vrai pour une rupture ou une tension d'approvisionnement."""
        return self in (Statut.RUPTURE, Statut.TENSION)

    @property
    def libelle_court(self) -> str:
        return {
            Statut.RUPTURE: "Rupture",
            Statut.TENSION: "Tension",
            Statut.ARRET: "Arrêt de commercialisation",
            Statut.REMISE: "Remise à disposition",
            Statut.INCONNU: "Inconnu",
        }[self]


@dataclass(frozen=True)
class Disponibilite:
    """Une ligne du fichier de disponibilité : une présentation (code CIP13) d'un médicament."""

    cis: str
    cip13: str
    code_statut: str
    libelle_statut: str
    statut: Statut
    date_debut: date | None = None
    date_maj: date | None = None
    date_remise: date | None = None
    lien: str = ""
    # Enrichissement (autres fichiers de la base)
    denomination: str | None = None
    titulaire: str | None = None
    est_mitm: bool = False
    code_atc: str | None = None

    @property
    def cle(self) -> str:
        """Identifiant stable d'une présentation, utilisé pour comparer deux jours."""
        return f"{self.cis}:{self.cip13}"

    @property
    def nom(self) -> str:
        return self.denomination or f"CIS {self.cis}"


Etat = dict[str, Disponibilite]
"""État d'un jour : présentations indexées par leur clé."""


def indexer(disponibilites: list[Disponibilite]) -> Etat:
    """Indexe une liste par clé (en cas de doublon, la dernière ligne l'emporte)."""
    return {d.cle: d for d in disponibilites}


class TypeEvenement(str, Enum):
    NOUVELLE_RUPTURE = "nouvelle_rupture"
    NOUVELLE_TENSION = "nouvelle_tension"
    AGGRAVATION = "aggravation"
    AMELIORATION = "amelioration"
    REMISE_A_DISPOSITION = "remise_a_disposition"
    ARRET_COMMERCIALISATION = "arret_commercialisation"
    SORTIE_DE_LISTE = "sortie_de_liste"
    CHANGEMENT_STATUT = "changement_statut"
    MISE_A_JOUR = "mise_a_jour"

    @property
    def icone(self) -> str:
        return {
            TypeEvenement.NOUVELLE_RUPTURE: "🔴",
            TypeEvenement.NOUVELLE_TENSION: "🟠",
            TypeEvenement.AGGRAVATION: "⬆️",
            TypeEvenement.AMELIORATION: "⬇️",
            TypeEvenement.REMISE_A_DISPOSITION: "🟢",
            TypeEvenement.ARRET_COMMERCIALISATION: "⚫",
            TypeEvenement.SORTIE_DE_LISTE: "🟢",
            TypeEvenement.CHANGEMENT_STATUT: "🔁",
            TypeEvenement.MISE_A_JOUR: "✏️",
        }[self]

    @property
    def libelle(self) -> str:
        return {
            TypeEvenement.NOUVELLE_RUPTURE: "Nouvelle rupture",
            TypeEvenement.NOUVELLE_TENSION: "Nouvelle tension",
            TypeEvenement.AGGRAVATION: "Aggravation (tension → rupture)",
            TypeEvenement.AMELIORATION: "Amélioration (rupture → tension)",
            TypeEvenement.REMISE_A_DISPOSITION: "Remise à disposition",
            TypeEvenement.ARRET_COMMERCIALISATION: "Arrêt de commercialisation",
            TypeEvenement.SORTIE_DE_LISTE: "Sortie de la liste",
            TypeEvenement.CHANGEMENT_STATUT: "Changement de statut",
            TypeEvenement.MISE_A_JOUR: "Mise à jour",
        }[self]


@dataclass(frozen=True)
class Evenement:
    """Changement détecté pour une présentation entre deux jours."""

    type: TypeEvenement
    cle: str
    date: date
    avant: Disponibilite | None
    apres: Disponibilite | None

    @property
    def disponibilite(self) -> Disponibilite:
        """La version la plus récente connue de la présentation."""
        courante = self.apres or self.avant
        assert courante is not None, "un événement a toujours un avant ou un après"
        return courante
