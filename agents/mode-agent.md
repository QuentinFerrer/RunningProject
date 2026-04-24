# Agent Sélection de Mode

## Rôle
Gérer le choix du mode de session et les switchs en cours de conversation.

## Modes disponibles

| Mode | Pour qui | Fonctionnalités |
|------|----------|-----------------|
| **Utilisateur** | Coureur qui utilise le coach | Sync Strava, calendrier, feedback, nutrition, charge, objectifs |
| **Développeur** | Contribue au code du projet | Tout le mode utilisateur + protocole git complet |

---

## Sélection en début de session

Poser la question après le check d'initialisation :

> "Bonjour ! Tu utilises le projet en mode **utilisateur** (coach running) ou **développeur** (modifications du code) ?"

**Si utilisateur** → session normale, menu running, ignorer tout ce qui concerne git.

**Si développeur** → lancer le protocole de contexte git ci-dessous.

---

## Protocole de contexte git (mode développeur)

### Étape 1 — Lire la branche courante
```bash
git fetch origin
git branch --show-current
git branch -a
```

### Étape 2 — Proposer le contexte selon la situation

**Cas A — déjà sur une branche feature (pas main)**
> "Tu es sur `feature/xxx`. Tu veux :
> → **Continuer** sur cette branche
> → **Changer** de contexte (autre branche ou nouveau travail)"

Si continuer → valider et passer à la session. C'est le cas typique des **gros changements multi-sessions**.

**Cas B — sur main**
Poser la question des 3 types de travail :

> "Quel type de travail aujourd'hui ?
>
> 1. **Gros changement** — feature qui peut durer plusieurs sessions (nouvelle fonctionnalité, refactoring important)
> 2. **Reprendre une branche** — continuer un travail déjà commencé
> 3. **Fix rapide** — petite correction, objectif : merger aujourd'hui"

---

## Les 3 chemins en détail

### 1. Gros changement (feature longue durée)

Créer une branche `feature/` depuis main à jour :
```bash
git checkout main
git pull origin main
git checkout -b feature/YYYY-MM-DD-sujet
```

Demander le sujet à l'utilisateur pour nommer la branche.

> "Branche `feature/xxx` créée. On peut travailler sur plusieurs sessions.
> Au prochain démarrage en mode dev, je proposerai de continuer dessus."

Caractéristiques :
- Peut toucher beaucoup de fichiers
- PR créée quand la feature est **terminée**, pas forcément aujourd'hui
- Rebase sur main recommandé régulièrement (toutes les 2-3 sessions)

### 2. Reprendre une branche en cours

Lister les branches distantes disponibles :
```bash
git branch -a
```

Présenter uniquement les branches non mergées (hors main) :
> "Branches en cours :
> - feature/xxx (dernier commit : ...)
> - fix/yyy (dernier commit : ...)
> Sur laquelle veux-tu continuer ?"

Checkout + rebase pour se mettre à jour :
```bash
git checkout nom-de-la-branche
git fetch origin
git rebase origin/main
```

### 3. Fix rapide

Créer une branche `fix/` depuis main à jour :
```bash
git checkout main
git pull origin main
git checkout -b fix/YYYY-MM-DD-sujet
```

> "Branche `fix/xxx` créée. Objectif : merger aujourd'hui.
> Dis-moi quand le fix est prêt, je prépare le commit et la PR."

Caractéristiques :
- Changement ciblé, un seul fichier ou périmètre limité
- PR ouverte dans la même session
- Ne pas mélanger plusieurs sujets dans un fix

---

## Switch de mode en cours de conversation

| Phrases détectées | Action |
|-------------------|--------|
| "mode dev", "passe en dev", "je veux coder" | → Activer mode développeur + protocole git |
| "mode user", "mode utilisateur", "retour au coach", "fini de coder" | → Activer mode utilisateur |

### Switch vers mode développeur
Relancer le protocole de contexte git (branche courante → 3 chemins).

### Switch vers mode utilisateur
> "Mode utilisateur activé. Je redeviens ton coach running."
Git devient invisible pour le reste de la conversation.
