# Rust Squad Leaderboard

Self-updating Rust stats leaderboard for the group. Pulls straight from the
Steam Web API (same source RustStats.io uses), refreshes every 6 hours via
GitHub Actions, served free on GitHub Pages. No server, no cost.

## Setup (one time, ~10 minutes)

### 1. Get a Steam API key
Go to https://steamcommunity.com/dev/apikey — sign in, enter any domain
(e.g. `localhost`), copy the key. Free and instant.

### 2. Create the GitHub repo
- New repository (must be **public** for free GitHub Pages)
- Upload everything in this folder, keeping the structure intact —
  the `.github/workflows/update.yml` path matters
- Easiest way: `git init`, `git add .`, `git commit`, push. Or drag-and-drop
  via "Add file → Upload files" on github.com (create the workflow file
  separately via "Add file → Create new file" and type the path
  `.github/workflows/update.yml`, since drag-and-drop skips dotfolders)

### 3. Add the API key as a secret
Repo → Settings → Secrets and variables → Actions → **New repository secret**
- Name: `STEAM_API_KEY`
- Value: your key

The key stays hidden — it never appears in the site or the repo files.

### 4. Turn on GitHub Pages
Repo → Settings → Pages
- Source: **Deploy from a branch**
- Branch: `main`, folder: `/docs`
- Save. Your site will be at `https://<username>.github.io/<repo-name>/`

### 5. First run
Repo → Actions → **Update stats** → **Run workflow**

After ~30 seconds the real numbers land. From then on it refreshes itself
every 6 hours (edit the `cron` line in `update.yml` to change the schedule).

## Requirements for players to show up
Each player's Steam privacy settings need **Game details** set to Public
(Steam → Profile → Edit Profile → Privacy Settings). Anyone private shows
as "Private profile" on the board.

## Adding / removing / naming players
Edit `config.json`, commit. Next run picks it up. Each entry pairs a Steam ID
with a fixed `label` — the label is what shows big on the board (Steam
aliases change constantly; the label doesn't), with the player's current
Steam name shown small underneath.

```json
{ "steam_id": "7656119...", "label": "Dave" }
```

## If a column shows 0 for everyone
Steam's internal stat names occasionally differ from the ones in
`STAT_MAP` (top of `fetch_stats.py`). The full raw stat dump for every
player is saved in `docs/data.json` — find the right key name there and
add it to the candidate list in `STAT_MAP`.

## Files
- `config.json` — list of Steam IDs on the board
- `fetch_stats.py` — pulls stats from Steam, writes `docs/data.json`
- `.github/workflows/update.yml` — the 6-hour schedule
- `docs/index.html` — the leaderboard page
- `docs/data.json` — the data (auto-generated, don't edit by hand)
