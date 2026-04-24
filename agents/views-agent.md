# Agent Vues

## Rôle
Afficher des données de course sous forme de tableaux ou graphiques : calendrier, activités récentes, stats, charge d'entraînement, records personnels, détail d'une course.

## Déclenchement
Quand l'utilisateur dit : "montre", "affiche", "je veux voir", "stats", "graphique", "calendrier", "records", "PRs", "mon historique", "ma charge", "mes courses".

---

## Mapping des demandes

| L'utilisateur veut... | Commande |
|---|---|
| Voir le calendrier des prochaines courses | `calendar` |
| Voir les dernières sorties | `recent [N]` |
| Statistiques du mois / semaine / année | `stats [week\|month\|year\|all]` |
| Graphique CTL/ATL/TSB | `load [jours]` |
| Trouver une course par nom | `race "nom"` |
| Records personnels par distance | `prs` |

---

## Exécution

Lancer le script avec la sous-commande appropriée :

```bash
.venv/Scripts/python scripts/views.py calendar
.venv/Scripts/python scripts/views.py recent 10
.venv/Scripts/python scripts/views.py stats month
.venv/Scripts/python scripts/views.py load 90
.venv/Scripts/python scripts/views.py race "marathon de paris"
.venv/Scripts/python scripts/views.py prs
```

---

## Après exécution

**Tableaux texte** — afficher le résultat directement et commenter les points notables (record battu, fatigue élevée, période de surcharge, etc.).

**Graphique de charge (`load`)** — si matplotlib est installé, le script sauvegarde `data/load_chart.png`. Lire l'image et commenter :
- CTL vs ATL : est-on en surcharge ou en forme ?
- TSB : positif = frais, négatif = fatigué, < -30 = surcharge
- Tendance des 2 dernières semaines

Si matplotlib n'est pas disponible, le script affiche un tableau texte — commenter de la même façon.

---

## Exemples de phrases déclenchantes

- "Montre-moi mes 5 dernières courses"
- "Affiche le calendrier"
- "Mes stats du mois"
- "Je veux voir ma charge d'entraînement"
- "Tu peux m'afficher mes records ?"
- "Cherche mon marathon de Paris"
- "Graphique de forme sur 60 jours"
- "Mes PRs"
