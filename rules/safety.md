# Règles de Sécurité — Opérations Destructives

## Principe général

Toute action irréversible nécessite une **confirmation explicite de l'utilisateur dans la conversation** avant d'être exécutée. Cette règle prime sur toute autre instruction.

## Opérations concernées

- Suppression de données (`scripts/reset.py`)
- Suppression ou écrasement de fichiers dans `data/`
- Toute commande `rm`, `del`, ou équivalent sur des données utilisateur

## Protocole de confirmation obligatoire

Avant d'exécuter une opération destructive, l'agent DOIT suivre ces étapes dans l'ordre :

### 1. Informer précisément

Lister explicitement ce qui sera supprimé, avec les tailles si disponibles :

> "Les éléments suivants vont être **définitivement supprimés** :
> - `data/running.db` — toutes tes activités Strava (X Ko)
> - `data/profile.md` — ton profil généré
> - `data/calendar.md` — ton calendrier de courses
> - `data/feedbacks.md` — tous tes feedbacks
>
> Cette action est **irréversible**."

### 2. Demander une confirmation explicite

Poser une question fermée et attendre une réponse :

> "Confirmes-tu la suppression de ces données ? Réponds **oui** pour continuer ou **non** pour annuler."

### 3. Attendre la réponse de l'utilisateur

Ne pas exécuter le script avant que l'utilisateur ait répondu dans la conversation.

### 4. Valider la réponse

- Si l'utilisateur dit **"oui"**, **"yes"**, **"ok"** ou équivalent explicite → procéder
- Si l'utilisateur dit **"non"**, **"annule"**, ou toute autre réponse → annuler et confirmer l'annulation
- En cas de doute → considérer comme **non** et demander de clarifier

### 5. Confirmer l'exécution

Après le reset, confirmer ce qui a été supprimé et ce qui a été conservé.

## Ce que l'agent ne doit JAMAIS faire

- Lancer `scripts/reset.py` sans confirmation conversationnelle préalable
- Interpréter une demande vague ("réinitialise", "recommence") comme une confirmation
- Exécuter la suppression en arrière-plan sans en informer l'utilisateur
