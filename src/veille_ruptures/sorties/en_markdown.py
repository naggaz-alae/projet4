"""Rapport quotidien en Markdown (lisible directement sur GitHub)."""

from __future__ import annotations

from datetime import date

from veille_ruptures.indicateurs import Indicateurs
from veille_ruptures.modeles import Evenement, TypeEvenement
from veille_ruptures.sorties import AVERTISSEMENT, attribution


def _echapper(texte: str) -> str:
    return texte.replace("|", "\\|")


def rapport(
    jour: date,
    evenements: list[Evenement],
    indicateurs: Indicateurs,
    jour_precedent: date | None,
) -> str:
    i = indicateurs
    lignes = [
        f"# Veille des ruptures de médicaments — {jour.strftime('%d/%m/%Y')}",
        "",
        "| Indicateur | Valeur |",
        "|---|---|",
        f"| Présentations en rupture | {i.nb_ruptures} |",
        f"| Présentations en tension | {i.nb_tensions} |",
        f"| dont médicaments d'intérêt thérapeutique majeur | {i.nb_mitm_indisponibles} |",
    ]
    if i.anciennete_mediane_jours is not None:
        lignes.append(f"| Ancienneté médiane des indisponibilités | {i.anciennete_mediane_jours:.0f} jours |")
    if i.duree_mediane_episodes_clos is not None:
        lignes.append(
            f"| Durée médiane des épisodes terminés ({i.nb_episodes_clos}) "
            f"| {i.duree_mediane_episodes_clos:.0f} jours |"
        )

    lignes += ["", "## Changements"]
    if jour_precedent is None:
        lignes += ["", "_Première photo : aucun jour précédent pour comparer._"]
    elif not evenements:
        lignes += ["", f"_Aucun changement depuis le {jour_precedent.strftime('%d/%m/%Y')}._"]
    else:
        lignes += [
            "",
            f"Depuis le {jour_precedent.strftime('%d/%m/%Y')} : {len(evenements)} changement(s).",
            "",
        ]
        for type_ in TypeEvenement:
            du_type = [e for e in evenements if e.type is type_]
            if not du_type:
                continue
            lignes += [f"### {type_.icone} {type_.libelle} ({len(du_type)})", ""]
            for e in du_type:
                d = e.disponibilite
                majeur = " — **MITM**" if d.est_mitm else ""
                labo = f" ({_echapper(d.titulaire)})" if d.titulaire else ""
                lien = f" — [fiche ANSM]({d.lien})" if d.lien else ""
                lignes.append(f"- {_echapper(d.nom)}{labo}{majeur}{lien}")
            lignes.append("")

    if i.par_classe:
        lignes += ["", "## Indisponibilités par classe thérapeutique", "", "| Classe | Nombre |", "|---|---|"]
        lignes += [f"| {_echapper(classe)} | {nb} |" for classe, nb in i.par_classe]
    if i.par_titulaire:
        lignes += ["", "## Laboratoires les plus concernés", "", "| Titulaire | Nombre |", "|---|---|"]
        lignes += [f"| {_echapper(t)} | {nb} |" for t, nb in i.par_titulaire]

    lignes += ["", "---", "", f"_{attribution(jour)} {AVERTISSEMENT}_", ""]
    return "\n".join(lignes)
