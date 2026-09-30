# Démarrage

## Installation

```bash
pip install veille-ruptures             # ligne de commande + bibliothèque
pip install "veille-ruptures[pandas]"   # + conversion en DataFrame
```

Python 3.10 ou plus récent. Seule dépendance obligatoire : `click`.

## En ligne de commande

```bash
veille-ruptures etat                                # ruptures et tensions du jour
veille-ruptures etat --mitm --statut rupture        # ruptures des médicaments majeurs
veille-ruptures etat --format csv > ruptures.csv    # export
```

Les fichiers officiels sont téléchargés puis mis en cache dans `~/.cache/veille-ruptures`
(modifiable avec la variable d'environnement `VEILLE_RUPTURES_CACHE`). Aux appels suivants,
ils ne sont retéléchargés que s'ils ont changé.

## En Python

```python
from veille_ruptures import Statut, etat_du_jour

etat, rapport = etat_du_jour()
ruptures_majeures = [d for d in etat if d.est_mitm and d.statut is Statut.RUPTURE]

for d in ruptures_majeures:
    print(d.nom, d.titulaire, d.code_atc, d.date_debut)

print(len(rapport.avertissements), "ligne(s) problématique(s) dans le fichier source")
```

Avec pandas :

```python
from veille_ruptures.tableau import vers_dataframe

df = vers_dataframe(etat)
df.groupby("titulaire").size().sort_values(ascending=False).head(10)
```

## Suivre les changements

```bash
veille-ruptures instantane        # à lancer une fois par jour
veille-ruptures diff              # changements entre les deux dernières photos
veille-ruptures stats             # indicateurs
```

Pour automatiser la photo quotidienne, voir [Veille automatique](veille-automatique.md).
