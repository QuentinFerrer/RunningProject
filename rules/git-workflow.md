# Règles — Workflow Git

## Protection de main

La branche `main` est protégée par GitHub (branch ruleset).
Aucun push direct — tout passe par une Pull Request.

---

## Règle fondamentale — une branche à la fois sur les fichiers partagés

Ces fichiers génèrent des conflits si modifiés sur plusieurs branches en parallèle :
`CLAUDE.md` · `agents/*.md` · `rules/*.md` · `dev/*.md`

**Avant de créer une nouvelle branche** : vérifier qu'aucune PR ouverte ne touche aux mêmes fichiers. Si oui → merger d'abord.

---

## Convention de nommage

| Type | Format |
|------|--------|
| Nouvelle fonctionnalité | `feature/YYYY-MM-DD-sujet` |
| Correction de bug | `fix/YYYY-MM-DD-sujet` |
| Mise à jour de règles | `rules/YYYY-MM-DD-sujet` |
| Mise à jour d'agent | `agent/YYYY-MM-DD-sujet` |

---

## Cycle de travail complet

### 1. Créer une branche depuis main à jour
```bash
git fetch origin
git checkout main
git pull origin main
git checkout -b feature/YYYY-MM-DD-sujet
```

### 2. Commiter
```bash
git add <fichiers spécifiques>
git commit -m "type: description"
```

### 3. Rebase avant chaque push (obligatoire)
```bash
git fetch origin
git rebase origin/main
```

En cas de conflits :
```bash
# Résoudre → puis :
git add <fichier>
git rebase --continue
```

### 4. Pousser
```bash
git push -u origin nom-de-la-branche          # premier push
git push --force-with-lease origin nom         # après un rebase
```

### 5. Après merge de la PR
```bash
git checkout main
git pull origin main
git branch -d nom-de-la-branche
```

---

## Fichiers autorisés dans un commit

| Autorisé ✅ | Interdit ❌ |
|------------|------------|
| `scripts/*.py` | `.env` |
| `agents/*.md` | `data/running.db` |
| `rules/*.md` | `data/profile.md` |
| `dev/*.md` | `data/calendar.md` |
| `hooks/*.py` | `data/feedbacks.md` |
| `CLAUDE.md` | `.venv/` · `personal/` |
| `README.md` · `.env.example` | |
