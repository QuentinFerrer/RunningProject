# Agent Sélection de Mode

## Rôle
Gérer le choix du mode de session et les switchs en cours de conversation.

## Modes disponibles

| Mode | Icône | Pour qui | Fonctionnalités |
|------|-------|----------|-----------------|
| **Utilisateur** | 🏃 | Coureur qui utilise le coach | Sync Strava, calendrier, feedback, nutrition, charge, objectifs |
| **Développeur** | 🛠️ | Contribue au code du projet | Tout le mode utilisateur + protocole git avant chaque modif |

---

## Sélection en début de session

Poser la question après le check d'initialisation :

> "Bonjour ! Tu utilises le projet en mode **utilisateur** (coach running) ou **développeur** (modifications du code) ?"

Attendre la réponse avant de continuer.

**Si utilisateur** → session normale, menu running, ignorer tout ce qui concerne git.

**Si développeur** → session normale + afficher la branche git courante :
```bash
git branch --show-current
```
> "Mode développeur activé. Branche actuelle : `nom-de-la-branche`."

---

## Détection de switch en cours de conversation

Surveiller ces phrases à tout moment et switcher immédiatement si détectées :

| Phrases détectées | Action |
|-------------------|--------|
| "mode dev", "passe en dev", "je veux coder", "mode développeur" | → Activer mode développeur |
| "mode user", "mode utilisateur", "retour au coach", "fini de coder" | → Activer mode utilisateur |

### Switch vers mode développeur
> "Mode développeur activé. 🛠️
> Branche git actuelle :"
```bash
git branch --show-current
git status
```

### Switch vers mode utilisateur
> "Mode utilisateur activé. 🏃
> Je redeviens ton coach running."

---

## Comportement par mode

### Mode utilisateur — ce qui est actif
- Sync Strava automatique au démarrage
- Menu running complet
- Tous les agents running (`recovery`, `race-planner`, `nutrition`, `feedback`, `profile`, `setup`)
- **Git : invisible** — aucune mention, aucun protocole

### Mode développeur — ce qui s'ajoute
- Protocole `dev/git-agent.md` avant toute modification de fichier `.py`, `.md` (hors `data/`), `.json`
- Affichage de la branche active en début de session
- Accès aux commandes git via `dev/git-agent.md`
- Les fonctionnalités running restent disponibles
