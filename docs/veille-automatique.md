# Veille automatique avec GitHub Actions

Le workflow `.github/workflows/veille.yml` tourne **chaque matin** et :

1. télécharge l'état du jour et enregistre la photo `donnees/instantanes/AAAA-MM-JJ.csv` ;
2. génère `donnees/RAPPORT.md` (changements + indicateurs), lisible directement sur GitHub ;
3. génère `donnees/flux.xml` (RSS) et `donnees/evenements.json` ;
4. commite le tout dans le dépôt.

L'historique Git **devient** l'historique des ruptures : c'est la technique du *git scraping*.

## Mise en place

1. Dans le dépôt : **Settings → Actions → General → Workflow permissions** :
   choisir *Read and write permissions* (pour que l'action puisse commiter).
2. Onglet **Actions** → *Veille quotidienne* → **Run workflow** pour un premier lancement.
3. Ensuite, le workflow tourne tout seul chaque jour.

!!! tip "Démarrer tôt"
    L'historique commence le jour de la première photo : le passé ne peut pas être reconstruit.
    Les durées de rupture restent calculables dès le premier jour grâce à la date de début
    déclarée à l'ANSM, mais les événements et les épisodes terminés s'accumulent avec le temps.

!!! note "Bon à savoir"
    - Chaque photo pèse quelques centaines de Ko : prévoir quelques dizaines de Mo par an.
    - GitHub peut suspendre les workflows planifiés d'un dépôt public resté longtemps sans
      activité : un simple commit ou un lancement manuel les réactive.
