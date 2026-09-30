# veille-ruptures

**Surveiller les ruptures et tensions d'approvisionnement de médicaments en France.**

L'ANSM publie chaque jour l'état de disponibilité des médicaments, mais **pas son historique**.
`veille-ruptures` photographie cet état quotidiennement, détecte les changements et reconstruit
l'historique : nouvelles ruptures, aggravations, remises à disposition, durée des épisodes,
médicaments d'intérêt thérapeutique majeur (MITM) touchés.

```bash
pip install veille-ruptures
veille-ruptures etat --mitm --statut rupture
```

- [Démarrage](demarrage.md) : installation et premiers pas
- [Ligne de commande](cli.md) : toutes les commandes
- [Veille automatique](veille-automatique.md) : une photo par jour avec GitHub Actions
- [Méthodologie](methodologie.md) : sources, événements, épisodes, limites
- [Référence de l'API](api.md) : utilisation en Python

!!! warning "Avertissement"
    Outil d'information indépendant, non affilié à l'ANSM. La référence officielle reste le
    [site de l'ANSM](https://ansm.sante.fr/disponibilites-des-produits-de-sante/medicaments).
    Données : ANSM, Base de données publique des médicaments, licence Etalab 2.0.
