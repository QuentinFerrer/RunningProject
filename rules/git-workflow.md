# Règles — Workflow Git

## Principe général

- `main` est **protégée** : aucun push direct, uniquement via Pull Request
- Toute modification de code ou d'agent passe par une branche dédiée
- Les branches sont toujours créées depuis `main`, jamais depuis une autre branche
- Les données personnelles ne sont jamais committées (voir `rules/safety.md`)

## Convention de nommage des branches

| Type | Format | Exemple |
|------|--------|---------|
| Nouvelle fonctionnalité | `feature/YYYY-MM-DD-sujet` | `feature/2026-04-25-nutrition-agent` |
| Correction de bug | `fix/YYYY-MM-DD-sujet` | `fix/2026-04-25-strava-token` |
| Mise à jour de règles | `rules/YYYY-MM-DD-sujet` | `rules/2026-04-25-recovery-thresholds` |
| Mise à jour d'agent | `agent/YYYY-MM-DD-sujet` | `agent/2026-04-25-setup-flow` |

## Protocole avant toute modification de code ou d'agent

**Déclencheur** : l'utilisateur demande une modification de fichier `.py`, `.md` (hors `data/`), `.json`, `.txt`.

**Étapes obligatoires avant de toucher au moindre fichier :**

### 1. Afficher les branches existantes
```bash
git branch -a
git status
```

### 2. Demander à l'utilisateur
> "Sur quelle branche veux-tu travailler ?
> Branches existantes : [liste]
> → Travailler sur une branche existante
> → Créer une nouvelle branche"

### 3a. Si branche existante
```bash
git checkout nom-de-la-branche
```

### 3b. Si nouvelle branche
Toujours partir de `main` à jour :
```bash
git checkout main
git pull origin main
git checkout -b feature/YYYY-MM-DD-sujet
```
Demander le sujet à l'utilisateur pour nommer la branche.

### 4. Confirmer la branche active avant toute modification
```bash
git branch --show-current
```
Annoncer à l'utilisateur : "Je travaille maintenant sur `nom-de-la-branche`."

## Cycle de travail sur une branche

```
1. Modifications (code, agents, règles)
2. git add <fichiers spécifiques>     ← jamais git add -A
3. git commit -m "message clair"
4. git push origin nom-de-la-branche
```

## Création d'une Pull Request

Sur demande de l'utilisateur uniquement :
```bash
gh pr create --title "titre" --body "description"
```

- Demander titre et description si non fournis
- Ne jamais merger sans validation explicite de l'utilisateur
- Ne jamais cibler une autre branche que `main`

## Fichiers autorisés dans un commit

| Autorisé ✅ | Interdit ❌ |
|------------|------------|
| `scripts/*.py` | `.env` |
| `agents/*.md` | `data/running.db` |
| `rules/*.md` | `data/profile.md` |
| `hooks/*.py` | `data/calendar.md` |
| `CLAUDE.md` | `data/feedbacks.md` |
| `README.md` | `.venv/` |
| `.env.example` | `personal/` |
| `data/*.example.md` | |
| `data/.gitkeep` | |
