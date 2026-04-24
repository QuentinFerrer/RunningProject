# Agent Vues

## Rôle
Afficher des données de course sous forme de tableaux ou graphiques : calendrier, activités récentes, stats, charge d'entraînement, records personnels, détail d'une course, ou toute requête multi-critères sur l'historique.

## Déclenchement
Quand l'utilisateur dit : "montre", "affiche", "je veux voir", "stats", "graphique", "calendrier", "records", "PRs", "mon historique", "ma charge", "mes courses", "entre le... et le...", "toutes mes sorties de...".

---

## Mapping des demandes simples

| L'utilisateur veut... | Commande |
|---|---|
| Voir le calendrier des prochaines courses | `calendar` |
| Voir les dernières sorties | `recent [N]` |
| Statistiques du mois / semaine / année | `stats [week\|month\|year\|all]` |
| Graphique CTL/ATL/TSB | `load [jours]` |
| Trouver une course par nom | `race "nom"` |
| Records personnels par distance | `prs` |
| Requête avec critères (dates, distance, type...) | `filter [options]` |

---

## Commande `filter` — critères disponibles

```
--from  YYYY-MM-DD     date de début
--to    YYYY-MM-DD     date de fin
--min-dist KM          distance minimale en km
--max-dist KM          distance maximale en km
--type  Run|TrailRun|All   type (défaut : toutes courses)
--name  "texte"        filtre sur le nom (partiel)
--races-only           seulement les courses ciblées au calendrier
--has-feedback         seulement les activités avec un feedback
--order date|dist|time|tss  tri des résultats (défaut : date)
--limit N              nombre max de résultats (défaut : 50)
```

### Traduction langage naturel → flags

| L'utilisateur dit... | Commande à construire |
|---|---|
| "mes courses du 1er au 10 janvier" | `filter --from 2026-01-01 --to 2026-01-10` |
| "mes semi-marathons cette année" | `filter --from 2026-01-01 --min-dist 19 --max-dist 22` |
| "mes sorties trail de plus de 30 km" | `filter --type TrailRun --min-dist 30` |
| "toutes mes courses avec un feedback" | `filter --has-feedback` |
| "mes 5 courses les plus longues" | `filter --order dist --limit 5` |
| "mes marathons" | `filter --min-dist 40 --max-dist 44` |
| "mes courses de mars 2025" | `filter --from 2025-03-01 --to 2025-03-31` |
| "mes courses ciblées cette saison" | `filter --races-only --from 2025-09-01` |
| "sorties trail entre 20 et 30 km" | `filter --type TrailRun --min-dist 20 --max-dist 30` |
| "mes 10 km les plus rapides" | `filter --min-dist 9 --max-dist 11 --order time --limit 5` |

Les critères se combinent librement. Si l'utilisateur mentionne plusieurs filtres, les empiler tous dans la même commande.

---

## Exécution

```bash
# Exemples concrets
.venv/Scripts/python scripts/views.py filter --from 2026-01-01 --to 2026-01-10
.venv/Scripts/python scripts/views.py filter --min-dist 19 --max-dist 22 --order time
.venv/Scripts/python scripts/views.py filter --type TrailRun --min-dist 30 --has-feedback
.venv/Scripts/python scripts/views.py filter --races-only --from 2025-01-01

# Vues simples
.venv/Scripts/python scripts/views.py calendar
.venv/Scripts/python scripts/views.py recent 10
.venv/Scripts/python scripts/views.py stats month
.venv/Scripts/python scripts/views.py load 90
.venv/Scripts/python scripts/views.py race "marathon de paris"
.venv/Scripts/python scripts/views.py prs
```

---

## Après exécution

**Tableaux** — afficher le résultat et commenter les points notables :
- Meilleure performance sur la période
- Progression ou régression visible
- Activités avec ou sans feedback (signaler si un bilan manque sur une course ciblée)

**Graphique `load`** — si matplotlib est installé, le script sauvegarde `data/load_chart.png`. Lire l'image et commenter :
- CTL vs ATL : surcharge ou bonne forme ?
- TSB : positif = frais, négatif = fatigué, < -30 = surcharge
- Tendance des 2 dernières semaines

**Si aucun résultat** — proposer d'élargir les critères (plage de dates, distance, type).
