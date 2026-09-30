# Ligne de commande

`veille-ruptures --help` et `veille-ruptures <commande> --help` décrivent toutes les options.
L'option globale `-v` affiche les messages détaillés (téléchargements, lignes ignorées).

| Commande | Rôle |
|---|---|
| `etat` | État du jour, filtrable (`--mitm`, `--statut`, `--atc`, `--labo`) ; formats `table`, `json`, `csv` |
| `instantane` | Enregistre la photo du jour dans `--dossier` (défaut `donnees/instantanes`) |
| `diff [AVANT] [APRES]` | Événements entre deux photos (défaut : les deux dernières) ; formats `table`, `json`, `markdown` |
| `historique` | Épisodes de rupture/tension reconstruits (`--cis`, `--cip`, `--nom`) |
| `stats` | Indicateurs : volumes, ancienneté, classes thérapeutiques, laboratoires |
| `rapport` | Rapport Markdown du dernier jour (`--sortie` pour écrire un fichier) |
| `flux` | Flux RSS ou JSON des changements des N derniers jours |

## Exemples

```bash
# Ruptures d'antalgiques (classe ATC N02, connue pour les MITM)
veille-ruptures etat --atc N02 --statut rupture

# Présentations d'un laboratoire
veille-ruptures etat --labo "sanofi" --format csv > labo.csv

# Changements entre deux dates précises
veille-ruptures diff 2026-09-01 2026-09-30 --format markdown > septembre.md

# Historique d'un médicament
veille-ruptures historique --nom amoxicilline

# Flux RSS des 30 derniers jours
veille-ruptures flux --jours 30 --sortie flux.xml
```

## Travailler hors ligne

L'option `--sources DOSSIER` (commandes `etat`, `instantane`, `stats`) lit les fichiers
officiels (`CIS_CIP_Dispo_Spec.txt`, `CIS_MITM.txt`, `CIS_bdpm.txt`) dans un dossier local
au lieu de les télécharger.
