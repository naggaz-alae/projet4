# Journal des modifications

Toutes les modifications notables sont documentées ici.
Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) ·
Versionnage : [Semantic Versioning](https://semver.org/lang/fr/).

## [Non publié]

## [0.1.0] - 2026-09-30

### Ajouté
- Téléchargement conditionnel (ETag / Last-Modified) des fichiers de la Base de données
  publique des médicaments, avec cache local et mode dégradé en cas de panne réseau.
- Lecture robuste des fichiers officiels (sans en-tête, UTF-8 ou Windows-1252, dates françaises),
  avec rapport des lignes problématiques.
- Enrichissement : nom du médicament, laboratoire titulaire, statut MITM, code ATC.
- Photos quotidiennes (CSV triés, adaptés au « git scraping »).
- Détection des événements entre deux jours : nouvelle rupture, nouvelle tension, aggravation,
  amélioration, remise à disposition, arrêt de commercialisation, sortie de liste.
- Reconstruction des épisodes de rupture et indicateurs (volumes, ancienneté, classes, laboratoires).
- Sorties JSON, Markdown et RSS, avec mention de licence Etalab 2.0.
- Ligne de commande : `etat`, `instantane`, `diff`, `historique`, `stats`, `rapport`, `flux`.
- Conversion optionnelle en DataFrame pandas (`veille-ruptures[pandas]`).
- CI (ruff, mypy strict, tests Python 3.10 à 3.13), publication PyPI par Trusted Publishing,
  documentation MkDocs, veille quotidienne automatisée par GitHub Actions.

[Non publié]: https://github.com/naggaz-alae/projet4/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/naggaz-alae/projet4/releases/tag/v0.1.0
