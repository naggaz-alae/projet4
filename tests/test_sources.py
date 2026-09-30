"""Téléchargement conditionnel et mode dégradé, avec un faux serveur (aucun accès réseau)."""

from __future__ import annotations

import urllib.error
from email.message import Message
from pathlib import Path
from typing import Any

import pytest

from veille_ruptures.sources import ErreurSource, dossier_cache, telecharger


class FausseReponse:
    def __init__(self, contenu: bytes, entetes: dict[str, str]) -> None:
        self.contenu = contenu
        self.headers = Message()
        for cle, valeur in entetes.items():
            self.headers[cle] = valeur

    def read(self) -> bytes:
        return self.contenu

    def __enter__(self) -> FausseReponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None


class FauxServeur:
    """Renvoie 200 la première fois, puis 304 si l'ETag envoyé correspond."""

    def __init__(self) -> None:
        self.requetes: list[Any] = []
        self.panne = False

    def __call__(self, requete: Any, timeout: float) -> FausseReponse:
        self.requetes.append(requete)
        if self.panne:
            raise urllib.error.URLError("réseau coupé")
        if requete.get_header("If-none-match") == '"v1"':
            raise urllib.error.HTTPError(requete.full_url, 304, "Not Modified", Message(), None)
        entetes = {"ETag": '"v1"', "Last-Modified": "Mon, 28 Sep 2026 06:00:00 GMT"}
        return FausseReponse(b"contenu v1", entetes)


def test_premier_telechargement_puis_304(tmp_path: Path) -> None:
    serveur = FauxServeur()
    assert telecharger("disponibilites", cache=tmp_path, ouvrir=serveur) == b"contenu v1"
    assert serveur.requetes[0].get_header("If-none-match") is None

    # Second appel : requête conditionnelle, le serveur répond 304, on lit le cache
    assert telecharger("disponibilites", cache=tmp_path, ouvrir=serveur) == b"contenu v1"
    assert serveur.requetes[1].get_header("If-none-match") == '"v1"'
    assert serveur.requetes[1].get_header("If-modified-since") is not None


def test_panne_reseau_avec_cache(tmp_path: Path) -> None:
    serveur = FauxServeur()
    telecharger("mitm", cache=tmp_path, ouvrir=serveur)
    serveur.panne = True
    assert telecharger("mitm", cache=tmp_path, ouvrir=serveur) == b"contenu v1"


def test_panne_reseau_sans_cache(tmp_path: Path) -> None:
    serveur = FauxServeur()
    serveur.panne = True
    with pytest.raises(ErreurSource):
        telecharger("specialites", cache=tmp_path, ouvrir=serveur)


def test_erreur_http_sans_cache(tmp_path: Path) -> None:
    def serveur_en_panne(requete: Any, timeout: float) -> FausseReponse:
        raise urllib.error.HTTPError(requete.full_url, 503, "Indisponible", Message(), None)

    with pytest.raises(ErreurSource):
        telecharger("mitm", cache=tmp_path, ouvrir=serveur_en_panne)


def test_fichier_inconnu(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="inconnu"):
        telecharger("autre", cache=tmp_path)


def test_dossier_cache_configurable(tmp_path: Path) -> None:
    import os
    from unittest.mock import patch

    with patch.dict(os.environ, {"VEILLE_RUPTURES_CACHE": str(tmp_path)}):
        assert dossier_cache() == tmp_path
