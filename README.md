# Running Coach AI

A personal running coach powered by Claude AI and your Strava data.

Ask it anything: race targets, training load analysis, recovery advice, race-day nutrition, or post-race feedback. All your data stays local.

---

## Features

- **Auto-sync with Strava** — imports your full activity history on every session
- **Training load tracking** — CTL / ATL / TSB calculated from your activities
- **Race calendar** — add upcoming races with target times; matched automatically once completed
- **Post-race feedback** — linked to the actual Strava activity in the database
- **Specialized AI agents** — recovery, race planning, nutrition, feedback analysis

---

## Prerequisites

- [Claude Code](https://claude.ai/code) (CLI or VS Code extension)
- Python 3.10+
- A [Strava](https://www.strava.com) account with your runs synced

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/RunningProject.git
cd RunningProject
```

### 2. Create your environment file

```bash
cp .env.example .env
```

Open `.env` and fill in your Strava credentials (see step 3).

### 3. Create a Strava API application

1. Go to [strava.com/settings/api](https://www.strava.com/settings/api)
2. Create an application with these settings:
   - **Application Name**: RunningProject (or anything)
   - **Website**: `http://localhost`
   - **Authorization Callback Domain**: `localhost`
3. Copy your **Client ID** and **Client Secret** into `.env`

### 4. Create a Python virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\pip install -r requirements.txt

# macOS / Linux
.venv/bin/pip install -r requirements.txt
```

### 5. Authorize with Strava (one-time)

```bash
# Windows
.venv\Scripts\python scripts/strava_auth.py

# macOS / Linux
.venv/bin/python scripts/strava_auth.py
```

This opens Strava in your browser. Authorize the app, copy the `code` from the redirect URL, and paste it in the terminal. Your tokens are saved automatically to `.env`.

### 6. Sync your Strava data

```bash
# Windows
.venv\Scripts\python scripts/strava_sync.py

# macOS / Linux
.venv/bin/python scripts/strava_sync.py
```

This imports all your activities into a local SQLite database and generates `data/profile.md`.

### 7. Open Claude Code in this folder

```bash
claude
```

The AI coach will greet you, sync your latest activities, and offer a menu of options.

---

## Usage

Once set up, just open Claude Code in the project folder. On every session it automatically syncs Strava and loads your profile.

**Available actions:**

| What you say | What happens |
|---|---|
| "sync" | Force a Strava sync |
| "ajoute une course" | Add an upcoming race to the calendar |
| "feedback sur ma dernière course" | Log a post-race debrief linked to the Strava activity |
| "suis-je en surcharge ?" | Recovery & rest analysis based on CTL/ATL/TSB |
| "que puis-je viser sur un semi ?" | Race target estimation |
| "prépare-moi pour dimanche" | Race-day nutrition and strategy plan |

---

## Project structure

```
RunningProject/
├── .env.example              # Credentials template
├── .gitignore
├── requirements.txt
├── CLAUDE.md                 # Main AI agent instructions
├── agents/
│   ├── profile-agent.md      # Strava sync & profile management
│   ├── recovery-agent.md     # Training load & rest analysis
│   ├── race-planner-agent.md # Race targets & strategy
│   ├── nutrition-agent.md    # Race-day nutrition protocol
│   └── feedback-agent.md     # Post-race feedback analysis
├── scripts/
│   ├── strava_auth.py        # One-time OAuth setup
│   ├── strava_sync.py        # Sync Strava → SQLite + generate profile.md
│   └── add_feedback.py       # Log race feedback linked to Strava activity
└── data/
    ├── .gitkeep
    ├── calendar.example.md   # Race calendar format example
    └── feedbacks.example.md  # Feedback format example
```

**Files kept local (not on GitHub):**

| File | Why |
|---|---|
| `.env` | Strava credentials |
| `data/running.db` | All your Strava activities (personal health data) |
| `data/profile.md` | Generated athlete profile |
| `data/calendar.md` | Your upcoming races |
| `data/feedbacks.md` | Your post-race notes |

---

## Privacy

All your data is stored **locally only** — no cloud database, no third-party service beyond the Strava API. The only external call is to `api.strava.com` using your own credentials.

---

## License

MIT
