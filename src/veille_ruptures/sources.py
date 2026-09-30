"""Téléchargement des fichiers officiels, avec cache et requêtes conditionnelles.

Avant de retélécharger, on demande au serveur si le fichier a changé
(en-têtes If-None-Match / If-Modified-Since). S'il répond 304, on réutilise
le cache : plus rapide, et plus respectueux d'un service public.
En cas de panne réseau, la dernière version en cache est utilisée (mode dégradé).
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

URL_BASE = "https://base-donnees-publique.medicaments.gouv.fr/download/file/"
FICHIERS = {
    "disponibilites": "CIS_CIP_Dispo_Spec.txt",
    "mitm": "CIS_MITM.txt",
    "specialites": "CIS_bdpm.txt",
}
USER_AGENT = "veille-ruptures (+https://pypi.org/project/veille-ruptures/)"

Ouvreur = Callable[..., Any]


class ErreurSource(RuntimeError):
    """Fichier source indisponible et absent du cache."""


def dossier_cache() -> Path:
    """Dossier de cache : $VEILLE_RUPTURES_CACHE, sinon ~/.cache/veille-ruptures."""
    return Path(os.environ.get("VEILLE_RUPTURES_CACHE", Path.home() / ".cache" / "veille-ruptures"))


def telecharger(
    nom: str,
    cache: Path | None = None,
    timeout: float = 60,
    ouvrir: Ouvreur = urllib.request.urlopen,
) -> bytes:
    """Renvoie le contenu du fichier `nom` (clé de FICHIERS), à jour si possible."""
    if nom not in FICHIERS:
        raise ValueError(f"Fichier inconnu : {nom} (attendu : {', '.join(FICHIERS)})")
    cache = cache or dossier_cache()
    cache.mkdir(parents=True, exist_ok=True)
    chemin = cache / FICHIERS[nom]
    chemin_meta = chemin.with_suffix(".meta.json")
    meta: dict[str, str] = json.loads(chemin_meta.read_text(encoding="utf-8")) if chemin_meta.exists() else {}

    entetes = {"User-Agent": USER_AGENT}
    if chemin.exists():
        if "etag" in meta:
            entetes["If-None-Match"] = meta["etag"]
        if "last_modified" in meta:
            entetes["If-Modified-Since"] = meta["last_modified"]

    requete = urllib.request.Request(URL_BASE + FICHIERS[nom], headers=entetes)
    try:
        with ouvrir(requete, timeout=timeout) as reponse:
            contenu: bytes = reponse.read()
            nouvelles_meta = {
                cle: valeur
                for cle, valeur in (
                    ("etag", reponse.headers.get("ETag")),
                    ("last_modified", reponse.headers.get("Last-Modified")),
                )
                if valeur
            }
    except urllib.error.HTTPError as err:
        if err.code == 304 and chemin.exists():
            logger.info("%s : inchangé depuis le dernier téléchargement", FICHIERS[nom])
            return chemin.read_bytes()
        return _mode_degrade(chemin, f"HTTP {err.code}")
    except (urllib.error.URLError, TimeoutError, OSError) as err:
        return _mode_degrade(chemin, str(err))

    chemin.write_bytes(contenu)
    chemin_meta.write_text(json.dumps(nouvelles_meta), encoding="utf-8")
    logger.info("%s : %s octets téléchargés", FICHIERS[nom], len(contenu))
    return contenu


def _mode_degrade(chemin: Path, raison: str) -> bytes:
    if chemin.exists():
        logger.warning("%s indisponible (%s) : utilisation du cache", chemin.name, raison)
        return chemin.read_bytes()
    raise ErreurSource(f"{chemin.name} indisponible ({raison}) et absent du cache")
