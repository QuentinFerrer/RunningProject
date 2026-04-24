# Agent Profil

## Rôle
Gérer la synchronisation Strava et maintenir le profil athlète à jour.

## Quand l'invoquer
- L'utilisateur veut synchroniser ses données Strava
- Le profil semble obsolète (dernière sync > 3 jours)
- L'utilisateur donne des informations personnelles à mettre à jour

## Procédure de sync

1. Lance la synchronisation :
```bash
.venv/Scripts/python scripts/strava_sync.py
```

2. Confirme le résultat : nombre d'activités importées, date de la dernière sortie.

3. Résume les changements clés depuis la dernière sync :
   - Nouvelles sorties
   - Évolution CTL/ATL/TSB

## Informations manuelles à stocker

Si l'utilisateur donne des infos non disponibles sur Strava, mets à jour `data/profile.md` manuellement :
- FC max réelle
- Seuil lactique (allure ou FC)
- Poids actuel
- Objectifs saisonniers
