"""Flux RSS 2.0 des événements, pour s'abonner à la veille."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import date, datetime, time, timezone
from email.utils import format_datetime

from veille_ruptures.modeles import Evenement
from veille_ruptures.sorties import AVERTISSEMENT, attribution


def _date_rfc822(jour: date) -> str:
    return format_datetime(datetime.combine(jour, time(6, 0), tzinfo=timezone.utc))


def flux(evenements: list[Evenement], jour: date, lien_site: str) -> str:
    rss = ET.Element("rss", version="2.0")
    canal = ET.SubElement(rss, "channel")
    ET.SubElement(canal, "title").text = "Veille des ruptures de médicaments"
    ET.SubElement(canal, "link").text = lien_site
    ET.SubElement(canal, "description").text = f"{attribution(jour)} {AVERTISSEMENT}"
    ET.SubElement(canal, "language").text = "fr-fr"
    ET.SubElement(canal, "lastBuildDate").text = _date_rfc822(jour)

    for e in evenements:
        d = e.disponibilite
        item = ET.SubElement(canal, "item")
        majeur = " [MITM]" if d.est_mitm else ""
        ET.SubElement(item, "title").text = f"{e.type.icone} {e.type.libelle} : {d.nom}{majeur}"
        ET.SubElement(item, "link").text = d.lien or lien_site
        details = [f"Statut : {e.apres.statut.libelle_court if e.apres else 'retiré de la liste'}"]
        if d.titulaire:
            details.append(f"Laboratoire : {d.titulaire}")
        ET.SubElement(item, "description").text = " — ".join(details)
        ET.SubElement(item, "pubDate").text = _date_rfc822(e.date)
        ET.SubElement(item, "guid", isPermaLink="false").text = f"{e.date.isoformat()}:{e.type.value}:{e.cle}"

    ET.indent(rss)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(rss, encoding="unicode") + "\n"
