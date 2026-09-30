"""Ligne de commande : veille-ruptures --help"""

from __future__ import annotations

import csv
import io
import logging
from collections.abc import Sequence
from datetime import date, datetime
from itertools import pairwise
from pathlib import Path

import click

from veille_ruptures import __version__, instantanes
from veille_ruptures.diff import comparer
from veille_ruptures.historique import Episode, reconstruire_episodes
from veille_ruptures.indicateurs import calculer
from veille_ruptures.modeles import Disponibilite, Evenement, Statut, indexer
from veille_ruptures.sorties import attribution, en_json, en_markdown, en_rss
from veille_ruptures.sources import ErreurSource
from veille_ruptures.veille import etat_du_jour

DOSSIER_DEFAUT = Path("donnees/instantanes")
STATUTS = [s.value for s in Statut if s is not Statut.INCONNU]

option_dossier = click.option(
    "--dossier",
    type=click.Path(path_type=Path),
    default=DOSSIER_DEFAUT,
    show_default=True,
    help="Dossier des photos quotidiennes.",
)
option_sources = click.option(
    "--sources",
    "dossier_sources",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Lire les fichiers officiels dans ce dossier au lieu de les télécharger.",
)


def _jour(valeur: datetime | None) -> date | None:
    return valeur.date() if valeur else None


def _tableau(entetes: Sequence[str], lignes: Sequence[Sequence[object]], largeur_max: int = 48) -> str:
    """Tableau texte aligné, sans dépendance."""

    def cellule(v: object) -> str:
        texte = "" if v is None else str(v)
        return texte if len(texte) <= largeur_max else texte[: largeur_max - 1] + "…"

    rangees = [[cellule(v) for v in ligne] for ligne in lignes]
    largeurs = [max([len(e)] + [len(r[i]) for r in rangees]) for i, e in enumerate(entetes)]
    sep = "  "
    sortie = [
        sep.join(e.ljust(larg) for e, larg in zip(entetes, largeurs, strict=True)),
        sep.join("-" * larg for larg in largeurs),
    ]
    sortie += [sep.join(c.ljust(larg) for c, larg in zip(r, largeurs, strict=True)) for r in rangees]
    return "\n".join(sortie)


def _charger_etat(dossier_sources: Path | None) -> list[Disponibilite]:
    try:
        etat, rapport = etat_du_jour(dossier_sources=dossier_sources)
    except ErreurSource as err:
        raise click.ClickException(str(err)) from err
    if rapport.avertissements:
        click.echo(
            f"⚠️  {len(rapport.avertissements)} avertissement(s) de lecture (relancer avec -v pour le détail)",
            err=True,
        )
    return etat


def _photos(dossier: Path) -> list[tuple[date, list[Disponibilite]]]:
    return [(j, instantanes.charger(dossier, j)) for j in instantanes.lister_jours(dossier)]


def _evenements_du_dernier_jour(dossier: Path) -> tuple[date, date | None, list[Evenement]]:
    jours = instantanes.lister_jours(dossier)
    if not jours:
        raise click.ClickException(
            f"Aucune photo dans {dossier} : lancer d'abord `veille-ruptures instantane`"
        )
    jour = jours[-1]
    precedent = jours[-2] if len(jours) > 1 else None
    if precedent is None:
        return jour, None, []
    evenements = comparer(
        indexer(instantanes.charger(dossier, precedent)),
        indexer(instantanes.charger(dossier, jour)),
        date_evenements=jour,
    )
    return jour, precedent, evenements


@click.group()
@click.version_option(__version__, prog_name="veille-ruptures")
@click.option("-v", "--verbeux", is_flag=True, help="Afficher les messages détaillés.")
def main(verbeux: bool) -> None:
    """Veille des ruptures et tensions d'approvisionnement de médicaments en France.

    Données : ANSM, Base de données publique des médicaments (licence Etalab 2.0).
    """
    logging.basicConfig(
        level=logging.INFO if verbeux else logging.ERROR, format="%(levelname)s | %(message)s"
    )


@main.command()
@click.option("--mitm", is_flag=True, help="Seulement les médicaments d'intérêt thérapeutique majeur.")
@click.option("--statut", type=click.Choice(STATUTS), help="Filtrer par statut.")
@click.option("--atc", help="Préfixe de code ATC (ex. N02). Connu seulement pour les MITM.")
@click.option("--labo", help="Filtrer sur le nom du laboratoire titulaire (contient).")
@click.option(
    "--format", "format_", type=click.Choice(["table", "json", "csv"]), default="table", show_default=True
)
@click.option(
    "--limite", type=int, default=50, show_default=True, help="Nombre de lignes en format table (0 = toutes)."
)
@option_sources
def etat(
    mitm: bool,
    statut: str | None,
    atc: str | None,
    labo: str | None,
    format_: str,
    limite: int,
    dossier_sources: Path | None,
) -> None:
    """État du jour des ruptures et tensions."""
    selection = [
        d
        for d in _charger_etat(dossier_sources)
        if (not mitm or d.est_mitm)
        and (statut is None or d.statut.value == statut)
        and (atc is None or (d.code_atc or "").upper().startswith(atc.upper()))
        and (labo is None or labo.lower() in (d.titulaire or "").lower())
    ]
    selection.sort(key=lambda d: (d.statut.value, d.nom))
    aujourd_hui = date.today()

    if format_ == "json":
        click.echo(en_json.document(aujourd_hui, disponibilites=selection))
        return
    if format_ == "csv":
        tampon = io.StringIO()
        ecrivain = csv.writer(tampon, lineterminator="\n")
        ecrivain.writerow(
            ["cis", "cip13", "statut", "denomination", "titulaire", "mitm", "atc", "date_debut"]
        )
        for d in selection:
            ecrivain.writerow(
                [
                    d.cis,
                    d.cip13,
                    d.statut.value,
                    d.nom,
                    d.titulaire or "",
                    int(d.est_mitm),
                    d.code_atc or "",
                    d.date_debut or "",
                ]
            )
        click.echo(tampon.getvalue(), nl=False)
        return

    affichees = selection if limite == 0 else selection[:limite]
    click.echo(
        _tableau(
            ["Statut", "Médicament", "Laboratoire", "MITM", "Depuis"],
            [
                [
                    d.statut.libelle_court,
                    d.nom,
                    d.titulaire,
                    "oui" if d.est_mitm else "",
                    d.date_debut.strftime("%d/%m/%Y") if d.date_debut else "",
                ]
                for d in affichees
            ],
        )
    )
    click.echo(
        f"\n{len(selection)} présentation(s)"
        + (f", {len(affichees)} affichée(s)" if len(affichees) < len(selection) else "")
    )
    click.echo(attribution(aujourd_hui))


@main.command()
@option_dossier
@click.option(
    "--jour", type=click.DateTime(formats=["%Y-%m-%d"]), help="Date de la photo (défaut : aujourd'hui)."
)
@option_sources
def instantane(dossier: Path, jour: datetime | None, dossier_sources: Path | None) -> None:
    """Enregistre la photo du jour (à lancer une fois par jour)."""
    jour_photo = _jour(jour) or date.today()
    chemin = instantanes.enregistrer(_charger_etat(dossier_sources), dossier, jour_photo)
    click.echo(f"Photo enregistrée : {chemin}")


@main.command()
@click.argument("avant", type=click.DateTime(formats=["%Y-%m-%d"]), required=False)
@click.argument("apres", type=click.DateTime(formats=["%Y-%m-%d"]), required=False)
@option_dossier
@click.option(
    "--format",
    "format_",
    type=click.Choice(["table", "json", "markdown"]),
    default="table",
    show_default=True,
)
@click.option("--mises-a-jour", is_flag=True, help="Inclure les simples mises à jour (même statut).")
def diff(
    avant: datetime | None, apres: datetime | None, dossier: Path, format_: str, mises_a_jour: bool
) -> None:
    """Changements entre deux photos (par défaut : les deux dernières)."""
    jours = instantanes.lister_jours(dossier)
    jour_apres = _jour(apres) or (jours[-1] if jours else None)
    jour_avant = _jour(avant) or (instantanes.jour_precedent(dossier, jour_apres) if jour_apres else None)
    if jour_avant is None or jour_apres is None:
        raise click.ClickException("Il faut au moins deux photos pour comparer.")
    try:
        etat_avant = instantanes.charger(dossier, jour_avant)
        etat_apres = instantanes.charger(dossier, jour_apres)
    except FileNotFoundError as err:
        raise click.ClickException(str(err)) from err
    evenements = comparer(
        indexer(etat_avant), indexer(etat_apres), date_evenements=jour_apres, avec_mises_a_jour=mises_a_jour
    )

    if format_ == "json":
        click.echo(en_json.document(jour_apres, evenements=evenements))
    elif format_ == "markdown":
        click.echo(en_markdown.rapport(jour_apres, evenements, calculer(etat_apres, jour_apres), jour_avant))
    else:
        click.echo(f"Du {jour_avant:%d/%m/%Y} au {jour_apres:%d/%m/%Y} : {len(evenements)} changement(s)\n")
        if evenements:
            click.echo(
                _tableau(
                    ["Événement", "Médicament", "Laboratoire", "MITM"],
                    [
                        [
                            f"{e.type.icone} {e.type.libelle}",
                            e.disponibilite.nom,
                            e.disponibilite.titulaire,
                            "oui" if e.disponibilite.est_mitm else "",
                        ]
                        for e in evenements
                    ],
                )
            )


def _lignes_episodes(episodes: list[Episode], reference: date) -> list[list[object]]:
    return [
        [
            e.denomination or e.cis,
            e.pire_statut.libelle_court,
            f"{e.debut:%d/%m/%Y}",
            f"{e.fin:%d/%m/%Y}" if e.fin else "en cours",
            e.duree_jours(reference),
        ]
        for e in episodes
    ]


@main.command()
@option_dossier
@click.option("--cis", help="Code CIS du médicament.")
@click.option("--cip", help="Code CIP13 de la présentation.")
@click.option("--nom", help="Recherche dans le nom du médicament.")
def historique(dossier: Path, cis: str | None, cip: str | None, nom: str | None) -> None:
    """Épisodes de rupture/tension reconstruits à partir des photos."""
    photos = _photos(dossier)
    if not photos:
        raise click.ClickException(f"Aucune photo dans {dossier}")
    episodes = [
        e
        for e in reconstruire_episodes(photos)
        if (cis is None or e.cis == cis)
        and (cip is None or e.cle.endswith(f":{cip}"))
        and (nom is None or nom.lower() in (e.denomination or "").lower())
    ]
    reference = photos[-1][0]
    if not episodes:
        click.echo("Aucun épisode trouvé.")
        return
    click.echo(
        _tableau(
            ["Médicament", "Pire statut", "Début", "Fin", "Durée (j)"],
            _lignes_episodes(sorted(episodes, key=lambda e: e.debut), reference),
        )
    )
    click.echo(f"\nPhotos du {photos[0][0]:%d/%m/%Y} au {reference:%d/%m/%Y}")


@main.command()
@option_dossier
@click.option("--format", "format_", type=click.Choice(["table", "json"]), default="table", show_default=True)
@option_sources
def stats(dossier: Path, format_: str, dossier_sources: Path | None) -> None:
    """Indicateurs : volumes, ancienneté, classes et laboratoires les plus touchés."""
    photos = _photos(dossier)
    if photos:
        jour, etat = photos[-1]
        episodes = reconstruire_episodes(photos)
    else:
        jour, etat, episodes = date.today(), _charger_etat(dossier_sources), []
    ind = calculer(etat, jour, episodes)

    if format_ == "json":
        click.echo(en_json.document(jour, indicateurs=ind))
        return
    click.echo(f"Indicateurs au {jour:%d/%m/%Y}\n")
    lignes: list[list[object]] = [
        ["Présentations en rupture", ind.nb_ruptures],
        ["Présentations en tension", ind.nb_tensions],
        ["dont médicaments d'intérêt thérapeutique majeur", ind.nb_mitm_indisponibles],
        [
            "Ancienneté médiane (jours)",
            ind.anciennete_mediane_jours if ind.anciennete_mediane_jours is not None else "—",
        ],
        [
            "Durée médiane des épisodes terminés (jours)",
            ind.duree_mediane_episodes_clos if ind.duree_mediane_episodes_clos is not None else "—",
        ],
    ]
    click.echo(_tableau(["Indicateur", "Valeur"], lignes, largeur_max=60))
    if ind.par_classe:
        click.echo("\n" + _tableau(["Classe thérapeutique", "Nombre"], ind.par_classe, largeur_max=60))
    if ind.par_titulaire:
        click.echo("\n" + _tableau(["Laboratoire", "Nombre"], ind.par_titulaire, largeur_max=60))
    click.echo("\n" + attribution(jour))


@main.command()
@option_dossier
@click.option(
    "--sortie", type=click.Path(dir_okay=False, path_type=Path), help="Fichier Markdown (défaut : écran)."
)
def rapport(dossier: Path, sortie: Path | None) -> None:
    """Rapport Markdown du dernier jour : changements + indicateurs."""
    jour, precedent, evenements = _evenements_du_dernier_jour(dossier)
    photos = _photos(dossier)
    texte = en_markdown.rapport(
        jour, evenements, calculer(photos[-1][1], jour, reconstruire_episodes(photos)), precedent
    )
    if sortie:
        sortie.parent.mkdir(parents=True, exist_ok=True)
        sortie.write_text(texte, encoding="utf-8")
        click.echo(f"Rapport écrit : {sortie}")
    else:
        click.echo(texte)


@main.command()
@option_dossier
@click.option(
    "--jours", type=int, default=30, show_default=True, help="Profondeur du flux (en jours de photos)."
)
@click.option(
    "--sortie", type=click.Path(dir_okay=False, path_type=Path), required=True, help="Fichier de sortie."
)
@click.option("--format", "format_", type=click.Choice(["rss", "json"]), default="rss", show_default=True)
@click.option(
    "--lien",
    default="https://pypi.org/project/veille-ruptures/",
    show_default=True,
    help="Lien du site affiché dans le flux.",
)
def flux(dossier: Path, jours: int, sortie: Path, format_: str, lien: str) -> None:
    """Flux RSS ou JSON des changements des derniers jours."""
    liste = instantanes.lister_jours(dossier)[-(jours + 1) :]
    if not liste:
        raise click.ClickException(f"Aucune photo dans {dossier}")
    evenements: list[Evenement] = []
    for avant, apres in pairwise(liste):
        evenements += comparer(
            indexer(instantanes.charger(dossier, avant)),
            indexer(instantanes.charger(dossier, apres)),
            date_evenements=apres,
        )
    evenements.sort(key=lambda e: e.date, reverse=True)
    dernier = liste[-1]
    texte = (
        en_rss.flux(evenements, dernier, lien)
        if format_ == "rss"
        else en_json.document(dernier, evenements=evenements)
    )
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(texte, encoding="utf-8")
    click.echo(f"Flux écrit : {sortie} ({len(evenements)} événement(s))")


if __name__ == "__main__":  # pragma: no cover
    main()
