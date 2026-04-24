# Règles — Charge d'Entraînement (CTL / ATL / TSB)

## Définitions

| Indicateur | Nom complet | Fenêtre | Rôle |
|------------|-------------|---------|------|
| **CTL** | Chronic Training Load | 42 jours | Forme / Fitness long terme |
| **ATL** | Acute Training Load | 7 jours | Fatigue récente |
| **TSB** | Training Stress Balance | CTL − ATL | Fraîcheur du moment |

## Calcul (lissage exponentiel)

```
CTL[j] = CTL[j-1] × exp(-1/42) + TSS[j] × (1 - exp(-1/42))
ATL[j] = ATL[j-1] × exp(-1/7)  + TSS[j] × (1 - exp(-1/7))
TSB[j] = CTL[j] − ATL[j]
```

## TSS — Estimation depuis Strava

| Donnée disponible | Formule |
|-------------------|---------|
| `suffer_score` Strava | TSS = suffer_score |
| FC moyenne disponible | TSS = durée_h × (FC_moy / FC_max)² × 100 |
| Aucune | TSS = durée_h × 50 (effort modéré supposé) |

## Interprétation CTL (Fitness)

| CTL | Niveau |
|-----|--------|
| < 30 | Base faible / récupération |
| 30–50 | Base aérobie modérée |
| 50–70 | Bonne forme compétitive |
| 70–90 | Haute performance |
| > 90 | Élite |

## Interprétation TSB (Fraîcheur)

| TSB | État | Recommandation |
|-----|------|----------------|
| > 15 | Trop frais | Augmenter la charge progressivement |
| 5 à 15 | Optimal pré-compétition | Idéal pour une course dans 2–5 jours |
| −10 à 5 | Zone d'entraînement | Continuer, progression en cours |
| −20 à −10 | Fatigue modérée | Réduire volume −20 à −30%, soigner le sommeil |
| < −20 | Surcharge | Repos obligatoire — risque de blessure |
