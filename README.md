# veille-ruptures

[![CI](https://github.com/naggaz-alae/projet4/actions/workflows/ci.yml/badge.svg)](https://github.com/naggaz-alae/projet4/actions/workflows/ci.yml)
[![Licence MIT](https://img.shields.io/badge/licence-MIT-green)](LICENSE)

Un petit outil en ligne de commande pour suivre les ruptures de stock de médicaments en France.

## Pourquoi

L'ANSM publie tous les jours la liste des médicaments en rupture ou en tension
d'approvisionnement. Le problème, c'est qu'elle ne garde que l'état du jour : impossible de
savoir depuis quand un médicament manque, ni ce qui a changé depuis la veille.

J'ai donc écrit un script qui enregistre cette liste chaque jour et compare les jours entre eux.
Au fil du temps, on obtient un historique : quelles ruptures sont nouvelles, lesquelles se sont
aggravées, lesquelles sont terminées, et combien de temps elles ont duré.

## Installation

Il faut Python 3.10 ou plus récent.

```bash
pip install git+https://github.com/naggaz-alae/projet4.git
```

## Utilisation

Voir les ruptures du jour qui concernent des médicaments d'intérêt thérapeutique majeur (MITM) :

```console
$ veille-ruptures etat --mitm
Statut   Médicament                  Laboratoire       MITM  Depuis
-------  --------------------------  ----------------  ----  ----------
Rupture  ANTALFICTIF 1 g, comprimé   LABORATOIRE BETA  oui   28/09/2026
Rupture  GASTROFICTIF 20 mg, gélule  LABORATOIRE BETA  oui   15/09/2026

2 présentation(s)
Source : ANSM, Base de données publique des médicaments (licence Etalab 2.0), données du 29/09/2026.
```

Voir ce qui a changé depuis la veille :

```console
$ veille-ruptures diff
Du 28/09/2026 au 29/09/2026 : 5 changement(s)

Événement                          Médicament                   Laboratoire        MITM
---------------------------------  ---------------------------  -----------------  ----
🔴 Nouvelle rupture                 ANTALFICTIF 1 g, comprimé    LABORATOIRE BETA   oui
🟠 Nouvelle tension                 CARDIOFICTIF 5 mg, comprimé  LABORATOIRE ALPHA
⬆️ Aggravation (tension → rupture) GASTROFICTIF 20 mg, gélule   LABORATOIRE BETA   oui
🟢 Remise à disposition             FICTIFAMOL 500 mg, comprimé  LABORATOIRE ALPHA
🟢 Sortie de la liste               DERMOFICTIF 1 %, crème       LABORATOIRE ALPHA
```

(Ces exemples tournent sur les données de test du projet, les médicaments sont inventés.)

Les autres commandes :

- `instantane` : enregistre l'état du jour (à lancer une fois par jour)
- `historique` : retrace les ruptures passées d'un médicament (`--nom`, `--cis` ou `--cip`)
- `stats` : quelques chiffres (nombre de ruptures, ancienneté médiane des ruptures, labos les plus touchés…)
- `rapport` : génère un résumé du jour en Markdown
- `flux` : génère un flux RSS ou JSON des derniers changements

`etat` accepte aussi des filtres (`--statut`, `--atc`, `--labo`) et peut sortir du JSON ou du
CSV. `veille-ruptures <commande> --help` donne le détail.

On peut aussi s'en servir depuis Python :

```python
from veille_ruptures import Statut, etat_du_jour

etat, rapport = etat_du_jour()
ruptures_majeures = [d for d in etat if d.est_mitm and d.statut is Statut.RUPTURE]
```

## Comment ça marche

Chaque jour, l'outil télécharge les fichiers de la Base de données publique des médicaments,
les croise pour retrouver le nom du médicament, le laboratoire et sa classe thérapeutique, puis
enregistre le résultat dans un CSV daté. Il suffit ensuite de comparer deux CSV pour savoir ce
qui a changé.

Pour que ça tourne tout seul, une GitHub Action lance l'enregistrement chaque matin et commite
le fichier dans le dépôt. L'historique Git sert donc directement de base de données.

Quelques détails :

- les fichiers ne sont retéléchargés que s'ils ont changé, et si le réseau tombe, l'outil
  repart du cache ;
- les fichiers de l'ANSM ne sont pas toujours propres (encodage, dates, lignes bancales),
  donc les lignes illisibles sont signalées au lieu de faire planter le programme ;
- seule `click` est obligatoire, pandas est optionnel.

## Développement

```bash
git clone https://github.com/naggaz-alae/projet4.git && cd projet4
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,pandas]"
pytest
```

Le code est vérifié avec ruff et mypy, et les tests utilisent pytest et Hypothesis.
Plus de détails dans [CONTRIBUTING.md](CONTRIBUTING.md).

## Données

Les données viennent de l'ANSM (Base de données publique des médicaments, licence
[Etalab 2.0](https://www.etalab.gouv.fr/licence-ouverte-open-licence/)). Ce projet est
personnel et n'a aucun lien avec l'ANSM : pour une information officielle, il faut consulter
[leur site](https://ansm.sante.fr/disponibilites-des-produits-de-sante/medicaments), et pour
toute question sur un traitement, demander à un pharmacien ou un médecin.

Le code est sous licence [MIT](LICENSE).
