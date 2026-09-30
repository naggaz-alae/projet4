"""veille-ruptures : surveiller les ruptures et tensions d'approvisionnement de médicaments en France.

Source : ANSM, Base de données publique des médicaments (licence Etalab 2.0).

Exemple :
    >>> from veille_ruptures import etat_du_jour, Statut
    >>> etat, rapport = etat_du_jour()                                  # doctest: +SKIP
    >>> majeurs = [d for d in etat if d.est_mitm and d.statut is Statut.RUPTURE]  # doctest: +SKIP
"""

from veille_ruptures.diff import appliquer, comparer
from veille_ruptures.historique import Episode, reconstruire_episodes
from veille_ruptures.indicateurs import Indicateurs, calculer
from veille_ruptures.modeles import (
    Disponibilite,
    Etat,
    Evenement,
    Statut,
    TypeEvenement,
    indexer,
)
from veille_ruptures.veille import etat_du_jour

__version__ = "0.1.0"

__all__ = [
    "Disponibilite",
    "Episode",
    "Etat",
    "Evenement",
    "Indicateurs",
    "Statut",
    "TypeEvenement",
    "__version__",
    "appliquer",
    "calculer",
    "comparer",
    "etat_du_jour",
    "indexer",
    "reconstruire_episodes",
]
