# 📻 GitHub Radio — self-contained Discord music bot

A Discord bot that streams MP3s **hosted in this GitHub repo** straight into a
voice channel. Think Winamp-meets-radio-station:

- **Radio mode** (`!radio`) — true shuffle through your whole library: every
  track plays once before anything repeats, forever, until you stop it.
- **Winamp-style playlists** — create named playlists, add/remove tracks,
  play them in order or shuffled. Saved to disk between restarts.
- **Zero cost, no uploads to Discord** — songs live in the repo's
  [`music/`](../music) folder and stream from `raw.githubusercontent.com`.
  No GitHub API application, token, or key is needed: public raw URLs and
  the public tree-listing endpoint work unauthenticated. Everyone in the
  voice channel hears it for free.

## How it works

```
GitHub repo (music/*.mp3)
        │  raw.githubusercontent.com (no API key)
        ▼
   bot.py + FFmpeg  ──►  Discord voice channel  ──►  everyone listens
```

On startup (and on `!refresh`) the bot lists the repo's file tree through
GitHub's public unauthenticated endpoint, finds every audio file under
`music/`, and builds its library. When a track plays, FFmpeg streams the raw
URL directly — nothing is downloaded to Discord or stored on their servers.

## Setup (one time, ~10 minutes)

### 1. Create the bot account (free)

This is the only registration needed — Discord requires it for any bot; GitHub
requires nothing.

1. Go to <https://discord.com/developers/applications> → **New Application**.
2. In **Bot**: click **Reset Token** and copy the token (keep it secret!).
   Under *Privileged Gateway Intents*, enable **Message Content Intent**.
3. In **OAuth2 → URL Generator**: check `bot`, then the permissions
   **Connect**, **Speak**, **Send Messages**, **Read Message History**.
   Open the generated URL and invite the bot to your server.

### 2. Install and run

Needs Python 3.10+ and [FFmpeg](https://ffmpeg.org/download.html) on PATH
(`sudo apt install ffmpeg` / `brew install ffmpeg` / `winget install ffmpeg`).

```bash
cd music-bot
pip install -r requirements.txt

export DISCORD_TOKEN="your-token-here"
export MUSIC_REPO="ALIGN-Tony/College-Checklist"   # owner/repo holding the MP3s
python bot.py
```

All settings (repo, branch, folder, prefix) are environment variables — see
[`.env.example`](.env.example).

### 3. Add music

Drop MP3s into the repo's [`music/`](../music) folder, commit, push, then run
`!refresh` in Discord. That's it — no re-deploys, no uploads to Discord.

## Commands

| Command | What it does |
|---|---|
| `!radio` | Endless shuffle of the whole library (radio-station mode) |
| `!play <# or name>` | Queue a specific track (`!play 7`, `!play daft punk`) |
| `!skip` / `!pause` / `!resume` | Playback control |
| `!volume <0–100>` | Set volume |
| `!np` | What's playing now |
| `!queue` | Show what's up next |
| `!shuffle` | Shuffle the current queue |
| `!tracks` | List the whole library, numbered |
| `!refresh` | Re-scan GitHub for new songs |
| `!join` / `!leave` | Join / leave your voice channel |
| `!help` | Show help |

### Playlists (Winamp style)

| Command | What it does |
|---|---|
| `!playlist create chill` | Make a playlist named "chill" |
| `!playlist add chill 12` | Add library track #12 (or search: `!playlist add chill lofi`) |
| `!playlist remove chill 3` | Remove the 3rd track from it |
| `!playlist show chill` | See its tracks |
| `!playlist play chill` | Queue it in order |
| `!playlist shuffle chill` | Queue it shuffled |
| `!playlist list` | All playlists |
| `!playlist delete chill` | Delete it |

`!pl` works as a short alias. Playlists persist in `music-bot/playlists.json`.

## Running it 24/7 for free

The bot process has to run *somewhere* while people listen. Free options:

- **A spare PC / old laptop / Raspberry Pi** — simplest; just leave
  `python bot.py` running (use `tmux` or a systemd service).
- **Oracle Cloud Always Free tier** — a free forever VM that can run it 24/7.
- **Your own machine, on demand** — start the bot only when friends want
  music; it connects in seconds.

Avoid ephemeral free hosts that sleep on inactivity (the bot drops out of
voice when the host sleeps).

## Notes & limits

- The repo (or at least its raw files) must be **public** for keyless
  streaming. Keep files under GitHub's 100 MB per-file limit — normal MP3s
  are 3–10 MB.
- GitHub's unauthenticated tree listing allows 60 requests/hour per IP; the
  bot only calls it at startup and on `!refresh`, so you'll never hit that.
  If it's ever unavailable, the bot falls back to a `music/tracks.json`
  manifest (plain JSON array of filenames).
- Only share music you have the rights to distribute.
