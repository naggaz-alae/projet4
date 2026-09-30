# Contribuer

Merci de votre intérêt ! Les contributions sont bienvenues : signalement de bug, idée, code, documentation.

## Installer l'environnement de développement

```bash
git clone https://github.com/naggaz-alae/projet4.git
cd projet4
python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -e ".[dev,pandas]"
pre-commit install                 # vérifications automatiques avant chaque commit
```

## Avant d'ouvrir une pull request

```bash
ruff check .            # style et bugs probables
ruff format .           # formatage
mypy                    # typage strict
pytest --cov            # tests + couverture (minimum 90 %)
```

La CI relance ces vérifications sur Python 3.10 à 3.13 pour chaque pull request.

## Conventions

- Code, noms et messages en français, comme le domaine (ANSM, données publiques françaises).
- Messages de commit au format [Conventional Commits](https://www.conventionalcommits.org/fr/) :
  `feat: …`, `fix: …`, `docs: …`, `test: …`, `chore: …`.
- Toute nouvelle fonctionnalité est accompagnée de tests et d'une ligne dans `CHANGELOG.md`.
- Les données de test (`tests/donnees/`) utilisent des médicaments **fictifs**.

## Publier une version (mainteneur)

1. Mettre à jour `__version__` dans `src/veille_ruptures/__init__.py` et `CHANGELOG.md`.
2. Créer une Release GitHub avec le tag `vX.Y.Z` (identique à la version).
3. Le workflow `release.yml` construit le paquet et le publie sur PyPI (Trusted Publishing).
