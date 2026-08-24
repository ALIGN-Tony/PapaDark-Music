# 📻 PapaDark Music — self-contained Discord music bot

A Discord bot that streams MP3s **hosted in this GitHub repo** straight into a
voice channel. Think Winamp-meets-radio-station:

- **Radio mode** (`!radio`) — true shuffle through your whole library: every
  track plays once before anything repeats, forever, until you stop it.
- **Stations** — every subfolder of `music/` is a station (`music/rock/`,
  `music/chill/`, …). Retune the one radio stream any time with
  `!station rock`; add or change stations after deployment just by moving
  files on GitHub and running `!refresh`.
- **Personal Winamp-style playlists** — every server member gets their own
  private playlist collection built from the shared music library: create
  named playlists, add/remove tracks, play them in order or shuffled.
  Saved to disk between restarts, keyed to each user's Discord account.
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
   **Connect**, **Speak**, **Send Messages**, **Read Message History**,
   **Manage Channels**, and **Manage Messages** (permissions integer:
   `3222544`). Open the generated URL and invite the bot to your server.

   **Auto-setup:** the moment it joins, the bot builds its own home — a
   `#papadark-radio` text channel and a `PapaDark Radio` voice channel —
   and posts a pinned welcome message with the commands. Nothing to
   configure. If the channels already exist it reuses them; `!setup`
   re-runs it any time (admins only), and `!invite` prints a ready-made
   add-to-server link with the right permissions for spreading the bot to
   other servers. Set `AUTO_SETUP=0` to disable, or override the channel
   names with `SETUP_TEXT_CHANNEL` / `SETUP_VOICE_CHANNEL`.

### 2. Install and run

Needs Python 3.10+ and [FFmpeg](https://ffmpeg.org/download.html) on PATH
(`sudo apt install ffmpeg` / `brew install ffmpeg` / `winget install ffmpeg`).

```bash
cd music-bot
pip install -r requirements.txt

export DISCORD_TOKEN="your-token-here"
export MUSIC_REPO="ALIGN-Tony/PapaDark-Music"   # owner/repo holding the MP3s
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
| `!radio` | Endless shuffle radio — plays the tuned station (default: everything) |
| `!station <name>` | Retune the radio to a station, e.g. `!station chill` (`!station all` for everything) |
| `!stations` | List all stations and which one is tuned in |
| `!play <# or name>` | Queue a specific track (`!play 7`, `!play daft punk`) |
| `!skip` / `!pause` / `!resume` | Playback control |
| `!volume <0–100>` | Set volume |
| `!np` | What's playing now |
| `!like` / `!unlike` | ❤️ the current song (one like per person per song) |
| `!top` | The most-loved tracks, ranked |
| `!shelf` | Played-but-unloved tracks — candidates for removal (fewest likes, most skips) |
| `!support` | 💜 Post the donation link |
| `!queue` | Show what's up next |
| `!shuffle` | Shuffle the current queue |
| `!tracks` | List the whole library, numbered (`!tracks chill` for one station) |
| `!refresh` | Re-scan GitHub for new songs |
| `!join` / `!leave` | Join / leave your voice channel |
| `!setup` | Rebuild the radio channels + pinned welcome (admins only) |
| `!invite` | Link to add the bot to another server, permissions included |
| `!help` | Show help |

### Personal playlists (Winamp style)

Every member has their **own** playlist collection — your playlists are tied
to your Discord account, so two people can each have a "chill" playlist
without clashing. All playlists draw from the same shared music library.

| Command | What it does |
|---|---|
| `!playlist create chill` | Make *your* playlist named "chill" |
| `!playlist add chill 12` | Add library track #12 (or search: `!playlist add chill lofi`) |
| `!playlist remove chill 3` | Remove the 3rd track from it |
| `!playlist show chill` | See its tracks |
| `!playlist play chill` | Queue your playlist in order |
| `!playlist shuffle chill` | Queue your playlist shuffled |
| `!playlist list` | List your playlists |
| `!playlist delete chill` | Delete your playlist |

`!pl` works as a short alias. Playlists persist in `music-bot/playlists.json`.

Note: a Discord voice channel carries one audio stream, so everyone in the
channel hears whatever is currently queued — personal playlists give each
member their own saved collections to queue up, not simultaneous separate
audio feeds.

## 🎧 Individual listening — the web player

Discord can only play audio in voice channels, and a voice channel has one
shared stream — so for **everyone listening to their own playlist at the same
time**, this repo also ships a web player at [`player/`](../player) that runs
on **GitHub Pages, free**:

- Each person opens the page in their browser (the bot posts the link with
  `!listen`), sees the same shared library, and plays whatever they want.
- Winamp-style playlists are built right on the page and saved in each
  person's own browser (localStorage) — your lists are yours.
- Same 📻 radio shuffle mode, search, seek, volume — no accounts, no cost,
  no installs. Music streams from the same raw GitHub URLs.

**Enable it once:** repo **Settings → Pages → Deploy from a branch**, pick
`main` and `/ (root)`, save. A minute later the player is live at
`https://<owner>.github.io/<repo>/player/` (the `!listen` command derives
this automatically; override with the `PLAYER_URL` env var if needed).

So you get both modes: the **bot** for listening together in a voice channel,
and the **web player** for everyone listening to their own lists at once.

## Hosting on Railway (recommended)

Railway runs the bot 24/7 with no sleeping — the Hobby plan ($5/month,
usage included) is more than enough for this bot. The repo ships with a
`Dockerfile` and `railway.json`, so there is nothing to configure:

1. On [railway.com](https://railway.com): **New Project → Deploy from
   GitHub repo** → pick `ALIGN-Tony/PapaDark-Music` (connect your GitHub
   account if asked). Railway builds from the included Dockerfile
   automatically — FFmpeg and everything else is baked in.
2. Open the new service → **Variables** → add `DISCORD_TOKEN` with your
   bot token. The service redeploys and the bot comes online; the deploy
   logs will show `Logged in as PapaDark Music`.
3. Pushing to `main` on GitHub auto-redeploys the bot with the update.

**Optional — keep playlists, likes, and the song cache across redeploys:**
container storage is wiped on each deploy, which resets members' saved
`!playlist` lists, the `!like` tallies, and the cached songs. To persist
them: service → **Volumes** → mount a volume at `/data`, then add three
variables: `PLAYLISTS_FILE=/data/playlists.json`,
`STATS_FILE=/data/stats.json`, and `CACHE_DIR=/data/cache`.

## Private music library

The bot code can stay public while the music lives in a **private repo**:

1. Create a private GitHub repo (e.g. `ALIGN-Tony/PapaDark-Library`) with a
   `music/` folder — subfolders are stations, exactly as before.
2. Make a **fine-grained personal access token**: GitHub → Settings →
   Developer settings → Fine-grained tokens → restrict it to that one
   repo, with Repository permissions → **Contents: Read-only**. Nothing else.
3. On Railway, set `MUSIC_REPO` to the private repo and `GITHUB_TOKEN` to
   the token. The bot's listing, downloads, and cache all authenticate
   automatically.
4. **Web player:** browsers can't hold the token, so in private mode the
   player streams *through the bot*. On Railway: service → Settings →
   Networking → **Generate Domain**, then put that URL into
   `player/index.html` as `STREAM_BASE`. The bot serves `/library.json`
   and `/track` from its song cache (with seeking support). Note that web
   listening then counts toward Railway egress instead of GitHub's.

## Artist branding

- `ARTIST_CREDIT` — credit line shown on now-playing embeds and the web
  player footer, e.g. `Written & Performed by PapaDark (BMI)`.
- `SPOTIFY_URL` / `APPLE_MUSIC_URL` — when set, link buttons appear under
  the bot's now-playing embeds and in the web player (also editable as
  constants at the top of `player/index.html`).

## Song cache

Every track downloads to the host **once** on its first play and plays
from local disk after that — no repeated pulls from GitHub for the same
song, instant starts, and immunity to network hiccups mid-song. The
cache is LRU-bounded by `CACHE_MAX_MB` (default 500; set 0 to disable)
and keyed by each file's git content hash, so replacing a song in the
repo automatically invalidates its old cached copy. If a download ever
fails, the bot streams straight from GitHub as before. `!cache` shows
what's on disk.

## Hosting on Replit

The repo ships ready for Replit — `.replit` and `replit.nix` at the root
install Python, FFmpeg, and the dependencies automatically:

1. On [replit.com](https://replit.com): **Create Repl → Import from GitHub**
   → paste `https://github.com/ALIGN-Tony/PapaDark-Music`.
2. Open the **Secrets** tool (padlock icon) and add a secret named
   `DISCORD_TOKEN` with your bot token as the value. Never paste the token
   into code on Replit — repls can be public.
3. Click **Run**. The bot comes online and also starts a tiny web page
   ("PapaDark Music is on the air 📻") on the repl's URL.

**The honest catch:** free Replit workspaces go to sleep shortly after you
close the tab, which takes the bot offline. Mitigations, best first:

- **Paid, bulletproof:** deploy it as a Replit **Reserved VM deployment**
  (the only Replit mode designed to run 24/7).
- **Free, best-effort:** point a free uptime monitor (e.g. UptimeRobot) at
  the repl's web URL every 5 minutes. The built-in keep-alive page exists
  for exactly this. It reduces sleeping but Replit doesn't guarantee it —
  expect occasional dropouts.
- **Free, on-demand:** open the repl and hit Run when people want music;
  it's on the air in seconds.

## Other ways to run it 24/7 for free

- **A spare PC / old laptop / Raspberry Pi** — simplest and most reliable;
  just leave `python bot.py` running (use `tmux` or a systemd service).
- **Oracle Cloud Always Free tier** — a free forever VM that can run it 24/7.
- **Your own machine, on demand** — start the bot only when friends want
  music; it connects in seconds.

## Notes & limits

- The repo (or at least its raw files) must be **public** for keyless
  streaming. Keep files under GitHub's 100 MB per-file limit — normal MP3s
  are 3–10 MB.
- GitHub's unauthenticated tree listing allows 60 requests/hour per IP; the
  bot only calls it at startup and on `!refresh`, so you'll never hit that.
  If it's ever unavailable, the bot falls back to a `music/tracks.json`
  manifest (plain JSON array of filenames).
- Only share music you have the rights to distribute.
