# Running Coach AI

Un coach running personnel alimenté par Claude AI et tes données Strava.

Pose-lui n'importe quelle question : objectifs de course, analyse de charge, récupération, nutrition le jour J, bilan post-course. Toutes tes données restent en local.

---

## Pour les coureurs — Utiliser le coach

### Ce que le coach peut faire

| Tu veux... | Dis... |
|---|---|
| Mettre à jour tes activités Strava | "sync" / "mets à jour" |
| Ajouter une prochaine course | "ajoute une course" / "je veux m'inscrire à..." |
| Faire un bilan après une course | "feedback" / "bilan de ma course de dimanche" |
| Vérifier ta forme / fatigue | "suis-je en surcharge ?" / "ai-je besoin de repos ?" |
| Connaître tes temps cibles | "que puis-je viser sur un semi ?" |
| Préparer une course à venir | "prépare-moi pour mon marathon" / "plan nutrition" |
| Voir le guide complet | "aide" / "help" |

### Démarrage rapide

1. Installe [Claude Code](https://claude.ai/code) (CLI ou extension VS Code)
2. Clone ce dépôt et ouvre le dossier dans Claude Code
3. Au premier lancement, dis "setup" — le coach te guide pas à pas
4. Connecte ton compte Strava (une seule fois)
5. C'est prêt. Dis bonjour !

### Fonctionnalités principales

**Sync Strava automatique** — au début de chaque session (après ton premier message), toutes tes dernières activités sont importées. Tu peux aussi dire "sync" à tout moment pour forcer une mise à jour.

**Calendrier de courses** — inscris tes prochaines courses avec tes objectifs. Quand tu cours la course, elle est automatiquement reconnue et retirée du calendrier.

**Feedback post-course** — raconte ta course au coach : ressenti, temps, fréquence cardiaque, nutrition. Il lie ton bilan à l'activité Strava correspondante et l'analyse.

**Charge d'entraînement** — le coach calcule ton CTL (forme), ATL (fatigue) et TSB (fraîcheur) pour t'aider à doser l'effort et éviter le surentraînement.

**Objectifs de performance** — à partir de tes activités récentes et de ta forme actuelle, le coach estime tes temps cibles réalistes sur toutes les distances.

**Préparation course** — stratégie de départ, allures au km, plan de ravitaillement personnalisé selon la distance et le dénivelé.

**Récupération** — après une course, le coach recommande un plan de récupération adapté à la distance et à ton état de forme.

### Confidentialité

Toutes tes données sont stockées **en local uniquement** — aucune base de données cloud, aucun service tiers en dehors de l'API Strava. Le seul appel externe est vers `api.strava.com` avec tes propres identifiants.

---

## Pour les développeurs — Contribuer au projet

### Prérequis

- [Claude Code](https://claude.ai/code)
- Python 3.10+
- Un compte [Strava](https://www.strava.com) avec tes sorties synchronisées
- Git + [GitHub CLI](https://cli.github.com) (optionnel, pour les PR)

### Installation

**1. Cloner le dépôt**

```bash
git clone https://github.com/your-username/RunningProject.git
cd RunningProject
```

**2. Créer le fichier d'environnement**

```bash
cp .env.example .env
```

**3. Créer l'environnement virtuel Python**

```bash
# Windows
py -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# macOS / Linux
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

**4. Créer une application Strava** (une seule fois)

1. Va sur [strava.com/settings/api](https://www.strava.com/settings/api)
2. Crée une application :
   - **Application Name** : RunningProject (ou ce que tu veux)
   - **Website** : `http://localhost`
   - **Authorization Callback Domain** : `localhost`
3. Copie le **Client ID** et le **Client Secret** dans `.env`

**5. Autoriser l'accès Strava** (une seule fois)

```bash
# Windows
.venv\Scripts\python scripts/strava_auth.py

# macOS / Linux
.venv/bin/python scripts/strava_auth.py
```

Un navigateur s'ouvre sur Strava. Après autorisation, copie l'URL de redirection et colle-la dans le terminal. Les tokens sont sauvegardés automatiquement dans `.env`.

**6. Première sync**

```bash
# Windows
.venv\Scripts\python scripts/strava_sync.py

# macOS / Linux
.venv/bin/python scripts/strava_sync.py
```

Importe toutes tes activités dans la base SQLite locale et génère `data/profile.md`.

**7. Lancer Claude Code**

```bash
claude
```

### Structure du projet

```
RunningProject/
├── .env.example              # Template des credentials
├── .gitignore
├── .gitattributes
├── requirements.txt
├── CLAUDE.md                 # Orchestrateur principal des agents
├── agents/
│   ├── mode-agent.md         # Sélection mode utilisateur / développeur
│   ├── setup-agent.md        # Onboarding et réinitialisation
│   ├── help-agent.md         # Guide interactif des fonctionnalités
│   ├── profile-agent.md      # Sync Strava et profil
│   ├── recovery-agent.md     # Charge d'entraînement et récupération
│   ├── race-planner-agent.md # Objectifs et stratégie de course
│   ├── nutrition-agent.md    # Nutrition le jour de course
│   └── feedback-agent.md     # Analyse des feedbacks post-course
├── rules/
│   ├── safety.md             # Protocole avant opérations destructives
│   ├── training-load.md      # Formules CTL/ATL/TSB et TSS
│   ├── recovery.md           # Tables de récupération par distance
│   ├── race-targets.md       # Formule de Riegel, estimations de temps
│   └── nutrition.md          # Protocoles nutrition par distance
├── scripts/
│   ├── strava_auth.py        # OAuth Strava (usage unique)
│   ├── strava_sync.py        # Sync Strava → SQLite + profil
│   ├── add_feedback.py       # Enregistrement feedback post-course
│   └── reset.py              # Réinitialisation des données (avec confirmation)
├── hooks/
│   ├── pre-push.py           # Bloque si données perso ou branche en retard
│   ├── post-write.py         # Hook post-écriture
│   └── on-stop.py            # Hook fin de session
├── dev/
│   └── git-agent.md          # Workflow git en mode développeur
└── data/
    ├── .gitkeep
    ├── calendar.example.md   # Exemple de format calendrier
    └── feedbacks.example.md  # Exemple de format feedback
```

**Fichiers locaux uniquement (hors GitHub) :**

| Fichier | Pourquoi |
|---|---|
| `.env` | Credentials Strava |
| `data/running.db` | Toutes tes activités (données de santé personnelles) |
| `data/profile.md` | Profil athlète généré |
| `data/calendar.md` | Tes prochaines courses |
| `data/feedbacks.md` | Tes bilans post-course |

### Workflow git

La branche `main` est protégée sur GitHub (ruleset, aucun bypass). Tout passe par une Pull Request.

En mode développeur dans Claude Code, un protocole de branches est géré automatiquement :
- **Gros changement** → branche `feature/YYYY-MM-DD-sujet`, multi-sessions
- **Reprendre un travail** → checkout d'une branche existante + rebase
- **Fix rapide** → branche `fix/YYYY-MM-DD-sujet`, merge dans la session

Le hook `hooks/pre-push.py` bloque automatiquement si des données personnelles sont détectées ou si la branche est en retard sur `origin/main`.

Conventions de nommage :

| Type | Format |
|---|---|
| Nouvelle fonctionnalité | `feature/YYYY-MM-DD-sujet` |
| Correction de bug | `fix/YYYY-MM-DD-sujet` |
| Mise à jour de règles | `rules/YYYY-MM-DD-sujet` |
| Mise à jour d'agent | `agent/YYYY-MM-DD-sujet` |

### Architecture des agents

Les agents sont des fichiers `.md` lus par Claude Code. `CLAUDE.md` est l'orchestrateur : il lit le contexte au démarrage et route chaque demande vers l'agent spécialisé approprié.

Les règles dans `rules/` encapsulent la logique métier (formules, protocoles) séparément des agents qui les appliquent. Les hooks dans `hooks/` s'exécutent automatiquement avant/après certaines opérations (écriture, push, fin de session).

---

## Licence

MIT
