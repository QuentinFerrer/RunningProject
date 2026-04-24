# Agent Git (développeur)

## Rôle
Assister dans les opérations git. Conventions complètes dans `rules/git-workflow.md`.
Protection de `main` assurée par GitHub (branch ruleset).

---

## Avant toute modification de code ou d'agent

Le choix de la branche est géré par `agents/mode-agent.md` (3 chemins : gros changement, branche en cours, fix rapide).

Une fois la branche choisie et active, vérifier avant toute modification :
```bash
git branch --show-current
git status
```

---

## Commit

Afficher le diff avant de stager :
```bash
git diff --stat
git status
```

Stager uniquement les fichiers autorisés (jamais `git add -A`) :
```bash
git add scripts/ agents/ rules/ dev/ hooks/ CLAUDE.md README.md \
        requirements.txt .gitignore .env.example .gitattributes \
        .claude/settings.json data/.gitkeep data/*.example.md
git commit -m "type: description courte"
```

---

## Push — rebase obligatoire avant chaque push

```bash
git fetch origin
git rebase origin/main
```

Si conflits pendant le rebase :
```bash
# Résoudre les fichiers en conflit, puis :
git add <fichier-résolu>
git rebase --continue
# Pour annuler : git rebase --abort
```

**Pousser après le rebase :**
```bash
# Premier push de la branche :
git push -u origin nom-de-la-branche

# Après un rebase (historique modifié) :
git push --force-with-lease origin nom-de-la-branche
```

> `--force-with-lease` refuse d'écraser si quelqu'un d'autre a pushé entre-temps.

---

## Après merge d'une PR

Toujours nettoyer :
```bash
git checkout main
git pull origin main
git branch -d nom-de-la-branche
```

---

## Pull Request

Sur demande explicite uniquement :
```bash
gh pr create --title "titre" --body "description"
```

- Toujours cibler `main`
- Vérifier qu'aucune autre PR ouverte ne touche aux mêmes fichiers
- Ne jamais merger sans validation explicite de l'utilisateur

---

## Commandes utiles

```bash
git log --oneline --graph -10    # Historique visuel
git branch -a                    # Toutes les branches
git diff --stat                  # Résumé des changements
git stash                        # Mettre de côté les changements
git rebase --abort               # Annuler un rebase en cours
```
