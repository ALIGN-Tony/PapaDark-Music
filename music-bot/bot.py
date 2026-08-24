"""
PapaDark Music — a self-contained Discord music bot.

Streams MP3s hosted in a public GitHub repository straight into a voice
channel. No GitHub API app, token, or key is required: the track list is
discovered from the repo's git tree (a public, unauthenticated endpoint)
and audio is pulled from raw.githubusercontent.com URLs, so the music
never has to be uploaded to Discord itself.

Modes:
  * Radio  — Winamp-style true shuffle: every track plays once before any
             repeats, forever, until told to stop.
  * Playlists — create named playlists, add/remove tracks, play them
             (optionally shuffled). Saved to playlists.json on disk.

Configuration is via environment variables (see .env.example / README).
"""

import asyncio
import hashlib
import json
import logging
import os
import random
from pathlib import Path

import aiohttp
import discord
from discord.ext import commands

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

TOKEN = os.environ.get("DISCORD_TOKEN", "")
# "owner/repo" of the public GitHub repo that holds the MP3s
MUSIC_REPO = os.environ.get("MUSIC_REPO", "ALIGN-Tony/PapaDark-Music")
MUSIC_BRANCH = os.environ.get("MUSIC_BRANCH", "main")
# Folder inside the repo that holds audio files ("" scans the whole repo)
MUSIC_PATH = os.environ.get("MUSIC_PATH", "music")
COMMAND_PREFIX = os.environ.get("COMMAND_PREFIX", "!")
# Web player URL for individual listening (GitHub Pages). Derived from
# MUSIC_REPO if unset; override with PLAYER_URL if hosted elsewhere.
_owner, _, _repo = MUSIC_REPO.partition("/")
PLAYER_URL = os.environ.get(
    "PLAYER_URL", f"https://{_owner.lower()}.github.io/{_repo}/player/"
)

AUDIO_EXTENSIONS = (".mp3", ".ogg", ".wav", ".flac", ".m4a", ".opus")

# Auto-setup: when the bot joins a server it creates its home channels and
# posts a pinned welcome message. Disable with AUTO_SETUP=0; names overridable.
AUTO_SETUP = os.environ.get("AUTO_SETUP", "1") != "0"
SETUP_TEXT_CHANNEL = os.environ.get("SETUP_TEXT_CHANNEL", "papadark-radio")
SETUP_VOICE_CHANNEL = os.environ.get("SETUP_VOICE_CHANNEL", "PapaDark Radio")

# Permissions baked into the !invite link: voice (connect/speak), chat
# (view/send/history), and channel setup (manage channels, pin messages).
INVITE_PERMISSIONS = discord.Permissions(
    view_channel=True, send_messages=True, read_message_history=True,
    connect=True, speak=True, manage_channels=True, manage_messages=True,
)

# Web server: keep-alive pings for hosts like Replit, and the streaming
# proxy the web player uses when the music repo is private. Auto-enabled on
# Replit or when a GitHub token is set; force with KEEP_ALIVE=1.
KEEP_ALIVE = (
    os.environ.get("KEEP_ALIVE") == "1"
    or "REPL_ID" in os.environ
    or bool(os.environ.get("GITHUB_TOKEN"))
)
KEEP_ALIVE_PORT = int(os.environ.get("PORT", "8080"))

# Where personal playlists are saved. On hosts with ephemeral filesystems
# (e.g. Railway), point this at a mounted volume: PLAYLISTS_FILE=/data/playlists.json
PLAYLISTS_FILE = Path(
    os.environ.get("PLAYLISTS_FILE", str(Path(__file__).with_name("playlists.json")))
)
# Likes / plays / skips tally. Same volume advice: STATS_FILE=/data/stats.json
STATS_FILE = Path(
    os.environ.get("STATS_FILE", str(Path(__file__).with_name("stats.json")))
)
# Private music repo support: a fine-grained GitHub token with read-only
# Contents access lets MUSIC_REPO be private. Unset = public repo, no token.
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

def gh_headers() -> dict:
    return {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

# Artist branding shown on now-playing embeds and the pinned welcome.
ARTIST_CREDIT = os.environ.get("ARTIST_CREDIT", "Written & Performed by PapaDark (BMI)")
SPOTIFY_URL = os.environ.get("SPOTIFY_URL", "https://open.spotify.com/artist/6cpAeJIXfIfiVg9R8hLhQC")
APPLE_MUSIC_URL = os.environ.get("APPLE_MUSIC_URL", "https://music.apple.com/us/artist/papadark/1865304620")

# Song cache: each track downloads once to local disk and plays from there
# afterwards. LRU-evicted at CACHE_MAX_MB (0 disables caching entirely).
# On Railway, point CACHE_DIR at the mounted volume: CACHE_DIR=/data/cache
CACHE_DIR = Path(os.environ.get("CACHE_DIR", str(Path(__file__).with_name("cache"))))
CACHE_MAX_MB = int(os.environ.get("CACHE_MAX_MB", "500"))

# Where the !support command and docs point people who want to chip in.
# PAYPAL_URL takes card / PayPal / Venmo with no account required.
SUPPORT_URL = os.environ.get("SUPPORT_URL", "https://www.venmo.com/u/papadarkmusic")
PAYPAL_URL = os.environ.get("PAYPAL_URL", "https://www.paypal.com/ncp/payment/KRT2Q5MKV59DL")

# Reconnect flags keep long streams from dying on a network hiccup.
FFMPEG_BEFORE = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
FFMPEG_OPTIONS = "-vn"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("papadark-music")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents, help_command=None)


# --------------------------------------------------------------------------
# Track library — discovered from GitHub, no API app required
# --------------------------------------------------------------------------

class Track:
    def __init__(self, path: str):
        self.path = path  # path inside the repo, e.g. "music/song.mp3"
        self.sha = None   # git blob sha when known — the cache key
        self.name = Path(path).stem.replace("_", " ").replace("-", " ").strip()
        # Station = first subfolder under MUSIC_PATH ("music/synthwave/x.mp3"
        # belongs to station "synthwave"); files directly in MUSIC_PATH have none.
        prefix = MUSIC_PATH.strip("/")
        rel = path[len(prefix) + 1:] if prefix and path.startswith(prefix + "/") else path
        parts = rel.split("/")
        self.station = (
            parts[0].replace("_", " ").replace("-", " ").strip().lower()
            if len(parts) > 1 else None
        )

    @property
    def url(self) -> str:
        # raw.githubusercontent.com serves file contents of public repos
        # with nothing more than a URL — no token, no registered app.
        from urllib.parse import quote
        return (
            f"https://raw.githubusercontent.com/{MUSIC_REPO}/"
            f"{MUSIC_BRANCH}/{quote(self.path)}"
        )

    def __str__(self):
        return self.name


class Library:
    """The full set of tracks found in the GitHub repo."""

    def __init__(self):
        self.tracks: list[Track] = []

    async def refresh(self) -> int:
        """Re-scan the repo for audio files. Returns the track count.

        Uses the unauthenticated git-trees endpoint (60 requests/hour per
        IP — plenty, since we only call it on startup and on !refresh).
        Falls back to a tracks.json manifest in the repo if the listing
        endpoint is unavailable.
        """
        tree_url = (
            f"https://api.github.com/repos/{MUSIC_REPO}"
            f"/git/trees/{MUSIC_BRANCH}?recursive=1"
        )
        prefix = MUSIC_PATH.strip("/")
        found: list[Track] = []
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(tree_url, headers=gh_headers(),
                                       timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for entry in data.get("tree", []):
                            path = entry.get("path", "")
                            if entry.get("type") != "blob":
                                continue
                            if prefix and not path.startswith(prefix + "/"):
                                continue
                            if path.lower().endswith(AUDIO_EXTENSIONS):
                                track = Track(path)
                                track.sha = entry.get("sha")
                                found.append(track)
                    else:
                        log.warning("Tree listing returned HTTP %s, trying manifest", resp.status)
            except aiohttp.ClientError as exc:
                log.warning("Tree listing failed (%s), trying manifest", exc)

            if not found:
                # Fallback: a hand-maintained manifest committed to the repo.
                manifest_url = (
                    f"https://raw.githubusercontent.com/{MUSIC_REPO}/"
                    f"{MUSIC_BRANCH}/{prefix + '/' if prefix else ''}tracks.json"
                )
                try:
                    async with session.get(manifest_url, headers=gh_headers(),
                                           timeout=aiohttp.ClientTimeout(total=30)) as resp:
                        if resp.status == 200:
                            for entry in json.loads(await resp.text()):
                                # entries may be bare filenames (relative to
                                # the music folder) or full repo paths
                                if "/" not in entry and prefix:
                                    entry = f"{prefix}/{entry}"
                                found.append(Track(entry))
                except (aiohttp.ClientError, json.JSONDecodeError):
                    pass

        found.sort(key=lambda t: t.name.lower())
        self.tracks = found
        log.info("Library refreshed: %d tracks", len(found))
        return len(found)

    def stations(self) -> dict[str, int]:
        """Station name -> track count, discovered from subfolders."""
        counts: dict[str, int] = {}
        for t in self.tracks:
            if t.station:
                counts[t.station] = counts.get(t.station, 0) + 1
        return counts

    def station_tracks(self, station: str | None) -> list[Track]:
        """Tracks for one station; None means the whole library."""
        if station is None:
            return list(self.tracks)
        return [t for t in self.tracks if t.station == station]

    def match_station(self, query: str) -> str | None:
        q = query.strip().lower()
        names = self.stations()
        if q in names:
            return q
        partial = [n for n in sorted(names) if q in n]
        return partial[0] if partial else None

    def find(self, query: str) -> Track | None:
        """Look a track up by list number or by (partial) name."""
        query = query.strip()
        if query.isdigit():
            idx = int(query) - 1
            if 0 <= idx < len(self.tracks):
                return self.tracks[idx]
            return None
        q = query.lower()
        exact = [t for t in self.tracks if t.name.lower() == q]
        if exact:
            return exact[0]
        partial = [t for t in self.tracks if q in t.name.lower()]
        return partial[0] if partial else None


library = Library()


# --------------------------------------------------------------------------
# Song cache — download each track once, play from local disk after that
# --------------------------------------------------------------------------

class SongCache:
    def __init__(self, directory: Path, max_mb: int):
        self.dir = directory
        self.max_bytes = max_mb * 1024 * 1024
        self.enabled = max_mb > 0
        self._locks: dict[str, asyncio.Lock] = {}

    def _key(self, track: Track) -> str:
        # Prefer the git blob sha: content-addressed, so replacing a file in
        # the repo automatically invalidates its old cache entry.
        sha = track.sha or next(
            (t.sha for t in library.tracks if t.path == track.path and t.sha), None
        )
        return sha or hashlib.sha1(track.path.encode()).hexdigest()

    def path_for(self, track: Track) -> Path:
        return self.dir / f"{self._key(track)}{Path(track.path).suffix.lower()}"

    def _entries(self):
        try:
            return [f for f in self.dir.iterdir() if f.is_file() and f.suffix != ".part"]
        except OSError:
            return []

    def size_bytes(self) -> int:
        return sum(f.stat().st_size for f in self._entries())

    def evict(self):
        """Drop least-recently-played files until under the size cap."""
        files = sorted(self._entries(), key=lambda f: f.stat().st_mtime)
        total = sum(f.stat().st_size for f in files)
        while files and total > self.max_bytes:
            oldest = files.pop(0)
            try:
                size = oldest.stat().st_size
                oldest.unlink()
                total -= size
                log.info("Cache evicted %s", oldest.name)
            except OSError:
                break

    async def get(self, track: Track) -> Path | None:
        """Local file for the track, downloading it on first play.

        Returns None when caching is off or the download fails — the caller
        then streams from GitHub directly, exactly as before.
        """
        if not self.enabled:
            return None
        path = self.path_for(track)
        if path.exists() and path.stat().st_size > 0:
            os.utime(path)  # refresh LRU recency
            return path
        lock = self._locks.setdefault(path.name, asyncio.Lock())
        async with lock:
            if path.exists() and path.stat().st_size > 0:
                return path  # another player cached it while we waited
            tmp = path.with_suffix(path.suffix + ".part")
            try:
                self.dir.mkdir(parents=True, exist_ok=True)
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        track.url, headers=gh_headers(),
                        timeout=aiohttp.ClientTimeout(total=180)
                    ) as resp:
                        if resp.status != 200:
                            log.warning("Cache download HTTP %s for %s", resp.status, track.name)
                            return None
                        with open(tmp, "wb") as f:
                            async for chunk in resp.content.iter_chunked(1 << 16):
                                f.write(chunk)
                tmp.rename(path)
                self.evict()
                log.info("Cached %s (%.1f MB)", track.name, path.stat().st_size / 1e6)
                return path
            except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as exc:
                log.warning("Cache download failed for %s: %s", track.name, exc)
                tmp.unlink(missing_ok=True)
                return None


cache = SongCache(CACHE_DIR, CACHE_MAX_MB)


# --------------------------------------------------------------------------
# Playlists — Winamp-style, persisted to playlists.json
# --------------------------------------------------------------------------

class Playlists:
    def __init__(self, file: Path):
        self.file = file
        # Every Discord user gets their own private collection:
        # {user_id: {playlist name: [repo paths]}}
        self.data: dict[str, dict[str, list[str]]] = {}
        self.load()

    def load(self):
        if self.file.exists():
            try:
                data = json.loads(self.file.read_text())
                # discard any pre-per-user (name -> list) format
                if all(isinstance(v, dict) for v in data.values()):
                    self.data = data
                else:
                    log.warning("playlists.json uses the old shared format; starting empty")
            except json.JSONDecodeError:
                log.warning("playlists.json is corrupt; starting empty")

    def save(self):
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.file.write_text(json.dumps(self.data, indent=2))

    def of(self, user_id: int) -> dict[str, list[str]]:
        """The calling user's own playlists (name -> repo paths)."""
        return self.data.setdefault(str(user_id), {})

    def tracks_of(self, user_id: int, name: str) -> list[Track]:
        return [Track(p) for p in self.of(user_id).get(name, [])]


playlists = Playlists(PLAYLISTS_FILE)


# --------------------------------------------------------------------------
# Stats — likes, plays, skips; the data behind !top and !shelf
# --------------------------------------------------------------------------

class Stats:
    def __init__(self, file: Path):
        self.file = file
        self.likes: dict[str, list[str]] = {}   # track path -> user ids
        self.plays: dict[str, int] = {}         # track path -> times started
        self.skips: dict[str, int] = {}         # track path -> times skipped
        self.load()

    def load(self):
        if self.file.exists():
            try:
                data = json.loads(self.file.read_text())
                self.likes = data.get("likes", {})
                self.plays = data.get("plays", {})
                self.skips = data.get("skips", {})
            except json.JSONDecodeError:
                log.warning("stats.json is corrupt; starting fresh")

    def save(self):
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.file.write_text(json.dumps(
            {"likes": self.likes, "plays": self.plays, "skips": self.skips}, indent=2
        ))

    def add_like(self, path: str, user_id: int) -> bool:
        """Returns False if this user already liked the track."""
        users = self.likes.setdefault(path, [])
        if str(user_id) in users:
            return False
        users.append(str(user_id))
        self.save()
        return True

    def remove_like(self, path: str, user_id: int) -> bool:
        users = self.likes.get(path, [])
        if str(user_id) not in users:
            return False
        users.remove(str(user_id))
        self.save()
        return True

    def like_count(self, path: str) -> int:
        return len(self.likes.get(path, []))

    def record_play(self, path: str):
        self.plays[path] = self.plays.get(path, 0) + 1
        self.save()

    def record_skip(self, path: str):
        self.skips[path] = self.skips.get(path, 0) + 1
        self.save()

    def top_tracks(self, limit: int = 10) -> list[tuple[str, int, int]]:
        """(path, likes, plays) for every liked track, most loved first."""
        rows = [(p, len(u), self.plays.get(p, 0)) for p, u in self.likes.items() if u]
        rows.sort(key=lambda r: (-r[1], -r[2]))
        return rows[:limit]

    def shelf_candidates(self, limit: int = 10, min_plays: int = 3):
        """(path, likes, skips, plays) for played-but-unloved tracks.

        Ranked worst first: fewest likes, then highest skip rate.
        Only tracks with at least min_plays plays qualify — a song nobody
        has heard yet isn't a shelve candidate.
        """
        rows = []
        for path, plays in self.plays.items():
            if plays < min_plays:
                continue
            likes = self.like_count(path)
            skips = self.skips.get(path, 0)
            rows.append((path, likes, skips, plays))
        rows.sort(key=lambda r: (r[1], -(r[2] / r[3]), -r[3]))
        return rows[:limit]


stats = Stats(STATS_FILE)


# --------------------------------------------------------------------------
# Per-guild player: queue + radio shuffle cycle
# --------------------------------------------------------------------------

class Player:
    def __init__(self, guild: discord.Guild):
        self.guild = guild
        self.queue: list[Track] = []
        self.radio = False
        self.station: str | None = None    # None = whole library
        self.radio_pool: list[Track] = []  # shuffle cycle: refills when empty
        self.now_playing: Track | None = None
        self.text_channel: discord.abc.Messageable | None = None
        self.volume = 0.5

    # ---- radio shuffle: play every track once before any repeat ----
    def next_radio_track(self) -> Track | None:
        pool_source = library.station_tracks(self.station)
        if not pool_source:
            return None
        if not self.radio_pool:
            self.radio_pool = pool_source
            random.shuffle(self.radio_pool)
            # avoid the same song twice in a row across cycle boundaries
            if self.now_playing and len(self.radio_pool) > 1 \
                    and self.radio_pool[0].path == self.now_playing.path:
                self.radio_pool.append(self.radio_pool.pop(0))
        return self.radio_pool.pop(0)

    def next_track(self) -> Track | None:
        if self.queue:
            return self.queue.pop(0)
        if self.radio:
            return self.next_radio_track()
        return None

    @property
    def voice(self) -> discord.VoiceClient | None:
        return self.guild.voice_client

    def play_next(self, error: Exception | None = None):
        """Callback chained after each track finishes."""
        if error:
            log.error("Playback error: %s", error)
        vc = self.voice
        if vc is None or not vc.is_connected():
            self.now_playing = None
            return
        track = self.next_track()
        self.now_playing = track
        if track is None:
            return
        stats.record_play(track.path)
        # Runs on the voice thread; hop to the event loop so the cache can
        # download asynchronously before playback starts.
        asyncio.run_coroutine_threadsafe(self._start(track), bot.loop)

    async def _start(self, track: Track):
        vc = self.voice
        if vc is None or not vc.is_connected() or self.now_playing is not track:
            return  # skipped/stopped while we were getting ready
        local = await cache.get(track)
        if vc is None or not vc.is_connected() or self.now_playing is not track:
            return
        if local is not None:
            audio = discord.FFmpegPCMAudio(str(local), options=FFMPEG_OPTIONS)
        else:
            # cache miss/failure: stream straight from GitHub as before
            before = FFMPEG_BEFORE
            if GITHUB_TOKEN:
                before += f' -headers "Authorization: token {GITHUB_TOKEN}\r\n"'
            audio = discord.FFmpegPCMAudio(
                track.url, before_options=before, options=FFMPEG_OPTIONS
            )
        source = discord.PCMVolumeTransformer(audio, volume=self.volume)
        if vc.is_playing() or vc.is_paused():
            return  # something else started in the meantime
        vc.play(source, after=self.play_next)
        if self.text_channel is not None:
            try:
                await self.text_channel.send(
                    embed=now_playing_embed(track, self.station, self.radio),
                    view=branding_view(),
                )
            except discord.HTTPException:
                pass

    def start_if_idle(self):
        vc = self.voice
        if vc and vc.is_connected() and not vc.is_playing() and not vc.is_paused():
            self.play_next()


def branding_view() -> discord.ui.View | None:
    """Link buttons under now-playing embeds — Spotify / Apple Music CTAs."""
    links = [("Spotify", SPOTIFY_URL), ("Apple Music", APPLE_MUSIC_URL)]
    links = [(label, url) for label, url in links if url]
    if not links:
        return None
    view = discord.ui.View()
    for label, url in links:
        view.add_item(discord.ui.Button(label=label, url=url,
                                        style=discord.ButtonStyle.link))
    return view


def now_playing_embed(track: Track, station: str | None, radio: bool) -> discord.Embed:
    embed = discord.Embed(title=f"🎵 {track}", color=0x9D5CFF)
    if radio:
        embed.description = f"📻 {_station_label(station)}"
    embed.set_footer(text=ARTIST_CREDIT)
    return embed


players: dict[int, Player] = {}


def get_player(ctx: commands.Context) -> Player:
    player = players.get(ctx.guild.id)
    if player is None:
        player = Player(ctx.guild)
        players[ctx.guild.id] = player
    player.text_channel = ctx.channel
    return player


async def ensure_voice(ctx: commands.Context) -> discord.VoiceClient | None:
    """Join the caller's voice channel (or reuse the existing connection)."""
    if ctx.voice_client is not None and ctx.voice_client.is_connected():
        return ctx.voice_client
    if ctx.author.voice is None or ctx.author.voice.channel is None:
        await ctx.send("Join a voice channel first, then run the command again.")
        return None
    return await ctx.author.voice.channel.connect()


def chunk_lines(lines: list[str], limit: int = 1900) -> list[str]:
    """Split a list of lines into Discord-message-sized chunks."""
    chunks, current = [], ""
    for line in lines:
        if len(current) + len(line) + 1 > limit:
            chunks.append(current)
            current = ""
        current += line + "\n"
    if current:
        chunks.append(current)
    return chunks


# --------------------------------------------------------------------------
# Events
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Auto-setup: build the bot's home channels in a server
# --------------------------------------------------------------------------

def welcome_text() -> str:
    p = COMMAND_PREFIX
    return (
        "📻 **PapaDark Music is on the air!**\n"
        f"Join the **🔊 {SETUP_VOICE_CHANNEL}** voice channel and type `{p}radio` "
        "to start the station — an endless shuffle where every song plays once "
        "before anything repeats.\n\n"
        "**The dial:**\n"
        f"`{p}station <name>` — change stations · `{p}stations` — see what exists\n"
        f"`{p}play <song>` — request a track · `{p}skip` — next song · `{p}np` — what's playing\n"
        f"`{p}like` — ❤️ the current song (the charts decide what stays!)\n"
        f"`{p}playlist` — build your own personal playlists\n"
        f"`{p}listen` — web player link: everyone can play their own music at once\n"
        f"`{p}help` — everything else"
    )


async def run_setup(guild: discord.Guild) -> tuple[discord.TextChannel | None, list[str]]:
    """Create the radio channels if missing and post the welcome message.

    Returns (text channel, notes about what happened). Never raises for
    missing permissions — the notes explain what couldn't be done.
    """
    notes: list[str] = []
    me = guild.me
    can_manage = me.guild_permissions.manage_channels

    text_ch = discord.utils.get(guild.text_channels, name=SETUP_TEXT_CHANNEL)
    if text_ch is None:
        if can_manage:
            try:
                text_ch = await guild.create_text_channel(
                    SETUP_TEXT_CHANNEL,
                    topic="📻 PapaDark Music — commands and now-playing. "
                          f"{COMMAND_PREFIX}radio to start, {COMMAND_PREFIX}help for the dial.",
                    reason="PapaDark Music auto-setup",
                )
                notes.append(f"created #{SETUP_TEXT_CHANNEL}")
            except discord.HTTPException as exc:
                notes.append(f"couldn't create #{SETUP_TEXT_CHANNEL} ({exc.__class__.__name__})")
        else:
            notes.append(f"missing Manage Channels — couldn't create #{SETUP_TEXT_CHANNEL}")
    else:
        notes.append(f"#{SETUP_TEXT_CHANNEL} already exists")

    voice_ch = discord.utils.get(guild.voice_channels, name=SETUP_VOICE_CHANNEL)
    if voice_ch is None:
        if can_manage:
            try:
                await guild.create_voice_channel(
                    SETUP_VOICE_CHANNEL, reason="PapaDark Music auto-setup"
                )
                notes.append(f"created 🔊 {SETUP_VOICE_CHANNEL}")
            except discord.HTTPException as exc:
                notes.append(f"couldn't create 🔊 {SETUP_VOICE_CHANNEL} ({exc.__class__.__name__})")
        else:
            notes.append(f"missing Manage Channels — couldn't create 🔊 {SETUP_VOICE_CHANNEL}")
    else:
        notes.append(f"🔊 {SETUP_VOICE_CHANNEL} already exists")

    if text_ch is not None:
        try:
            msg = await text_ch.send(welcome_text())
            try:
                await msg.pin()
            except discord.HTTPException:
                notes.append("couldn't pin the welcome message (needs Manage Messages)")
        except discord.HTTPException:
            notes.append(f"couldn't post in #{SETUP_TEXT_CHANNEL}")
    return text_ch, notes


@bot.event
async def on_guild_join(guild: discord.Guild):
    log.info("Joined guild %s (%s)", guild.name, guild.id)
    if not AUTO_SETUP:
        return
    _, notes = await run_setup(guild)
    log.info("Auto-setup in %s: %s", guild.name, "; ".join(notes))


_keepalive_started = False


def build_web_app():
    """Web endpoints: keep-alive ping, plus a streaming proxy so the web
    player can list and play tracks through the bot (and its cache) when
    the music repo is private."""
    from aiohttp import web

    async def ping(_request):
        return web.Response(text="PapaDark Music is on the air 📻")

    async def library_json(_request):
        return web.json_response([
            {"path": t.path, "name": t.name, "station": t.station, "sha": t.sha}
            for t in library.tracks
        ])

    async def track_stream(request):
        path = request.query.get("p", "")
        track = next((t for t in library.tracks if t.path == path), None)
        if track is None:
            raise web.HTTPNotFound(text="unknown track")
        local = await cache.get(track)
        if local is None:
            raise web.HTTPBadGateway(text="track fetch failed")
        return web.FileResponse(local)  # supports Range → seeking works

    @web.middleware
    async def cors(request, handler):
        try:
            resp = await handler(request)
        except web.HTTPException as exc:
            exc.headers["Access-Control-Allow-Origin"] = "*"
            raise
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Expose-Headers"] = "Content-Length, Content-Range"
        return resp

    app = web.Application(middlewares=[cors])
    app.router.add_get("/", ping)
    app.router.add_get("/library.json", library_json)
    app.router.add_get("/track", track_stream)
    return app


async def start_keepalive():
    from aiohttp import web
    runner = web.AppRunner(build_web_app())
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", KEEP_ALIVE_PORT).start()
    log.info("Web server (keep-alive + stream proxy) on port %d", KEEP_ALIVE_PORT)


@bot.event
async def on_ready():
    global _keepalive_started
    if KEEP_ALIVE and not _keepalive_started:
        _keepalive_started = True
        try:
            await start_keepalive()
        except OSError as exc:
            log.warning("Keep-alive server failed to start: %s", exc)
    count = await library.refresh()
    log.info("Logged in as %s — %d tracks in library", bot.user, count)


# --------------------------------------------------------------------------
# Playback commands
# --------------------------------------------------------------------------

@bot.command(help="Join your voice channel")
async def join(ctx):
    vc = await ensure_voice(ctx)
    if vc:
        await ctx.send(f"Connected to **{vc.channel.name}**.")


@bot.command(aliases=["disconnect", "stop"], help="Stop playing and leave")
async def leave(ctx):
    player = get_player(ctx)
    player.radio = False
    player.queue.clear()
    player.now_playing = None
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Radio off. See you next time! 📻")
    else:
        await ctx.send("I'm not in a voice channel.")


def _station_label(station: str | None) -> str:
    return station.title() if station else "All Music"


@bot.command(help="Start radio mode: shuffle a station (or everything), forever")
async def radio(ctx, *, station: str = ""):
    if not library.tracks:
        await ctx.send("The library is empty — add MP3s to the repo and run `!refresh`.")
        return
    if station:
        await tune(ctx, name=station)
        return
    vc = await ensure_voice(ctx)
    if vc is None:
        return
    player = get_player(ctx)
    player.radio = True
    pool = library.station_tracks(player.station)
    if not pool:  # tuned station vanished after a refresh
        player.station = None
        pool = library.tracks
    await ctx.send(
        f"📻 Radio on — **{_station_label(player.station)}**, shuffling "
        f"**{len(pool)}** tracks. `{COMMAND_PREFIX}station` to change stations, "
        f"`{COMMAND_PREFIX}skip` for next song, `{COMMAND_PREFIX}leave` to stop."
    )
    player.start_if_idle()


@bot.command(name="station", aliases=["tune"],
             help="Tune the radio to a station (a subfolder of music/)")
async def tune(ctx, *, name: str = ""):
    player = get_player(ctx)
    stations = library.stations()
    if not name:
        lines = [f"📻 Tuned to: **{_station_label(player.station)}**"]
        if stations:
            lines.append("Available stations: " + ", ".join(
                f"**{s.title()}**" for s in sorted(stations)) + f", **All** — switch with `{COMMAND_PREFIX}station <name>`")
        else:
            lines.append("No stations yet — an admin can create one by making a "
                         f"subfolder inside `{MUSIC_PATH}/` on GitHub (e.g. "
                         f"`{MUSIC_PATH}/synthwave/`) and dropping MP3s in it.")
        await ctx.send("\n".join(lines))
        return

    if name.strip().lower() in ("all", "everything", "any", "main"):
        new_station = None
    else:
        new_station = library.match_station(name)
        if new_station is None:
            available = ", ".join(f"**{s.title()}**" for s in sorted(stations)) or "none yet"
            await ctx.send(f"No station matching `{name}`. Available: {available}, **All**.")
            return

    vc = await ensure_voice(ctx)
    if vc is None:
        return
    player.station = new_station
    player.radio_pool = []          # rebuild the shuffle cycle from the new station
    player.radio = True
    count = len(library.station_tracks(new_station))
    await ctx.send(f"📻 Tuned to **{_station_label(new_station)}** — {count} tracks.")
    if vc.is_playing() or vc.is_paused():
        vc.stop()                   # jump straight into the new station
    else:
        player.start_if_idle()


@bot.command(help="List the radio stations")
async def stations(ctx):
    player = get_player(ctx)
    st = library.stations()
    if not st:
        await ctx.send("No stations yet — an admin can create one by making a "
                       f"subfolder inside `{MUSIC_PATH}/` on GitHub and adding MP3s. "
                       f"Meanwhile `{COMMAND_PREFIX}radio` shuffles everything.")
        return
    loose = len(library.tracks) - sum(st.values())
    lines = ["**📻 Stations:**"]
    for s in sorted(st):
        now = "  ← tuned in" if player.station == s else ""
        lines.append(f"• **{s.title()}** — {st[s]} tracks{now}")
    all_now = "  ← tuned in" if player.station is None else ""
    lines.append(f"• **All Music** — {len(library.tracks)} tracks{all_now}")
    if loose:
        lines.append(f"_({loose} tracks sit outside any station and play only on All Music)_")
    lines.append(f"Switch with `{COMMAND_PREFIX}station <name>`.")
    await ctx.send("\n".join(lines))


@bot.command(help="Play a track by number or name, or queue it")
async def play(ctx, *, query: str = ""):
    vc = await ensure_voice(ctx)
    if vc is None:
        return
    player = get_player(ctx)
    if not query:
        # bare !play behaves like radio
        await radio(ctx)
        return
    track = library.find(query)
    if track is None:
        await ctx.send(f"No track matching `{query}`. Try `{COMMAND_PREFIX}tracks`.")
        return
    player.queue.append(track)
    await ctx.send(f"➕ Queued: **{track}** (position {len(player.queue)})")
    player.start_if_idle()


@bot.command(aliases=["next"], help="Skip the current track")
async def skip(ctx):
    vc = ctx.voice_client
    if vc and (vc.is_playing() or vc.is_paused()):
        player = get_player(ctx)
        if player.now_playing:
            stats.record_skip(player.now_playing.path)
        vc.stop()  # triggers play_next via the after-callback
        await ctx.send("⏭️ Skipped.")
    else:
        await ctx.send("Nothing is playing.")


@bot.command(help="Pause playback")
async def pause(ctx):
    vc = ctx.voice_client
    if vc and vc.is_playing():
        vc.pause()
        await ctx.send("⏸️ Paused.")
    else:
        await ctx.send("Nothing is playing.")


@bot.command(help="Resume playback")
async def resume(ctx):
    vc = ctx.voice_client
    if vc and vc.is_paused():
        vc.resume()
        await ctx.send("▶️ Resumed.")
    else:
        await ctx.send("Nothing is paused.")


@bot.command(aliases=["np"], help="Show the current track")
async def nowplaying(ctx):
    player = get_player(ctx)
    if player.now_playing:
        await ctx.send(
            embed=now_playing_embed(player.now_playing, player.station, player.radio),
            view=branding_view(),
        )
    else:
        await ctx.send("Nothing is playing.")


@bot.command(aliases=["q"], help="Show the queue")
async def queue(ctx):
    player = get_player(ctx)
    if not player.queue:
        extra = " Radio mode will keep picking shuffled tracks." if player.radio else ""
        await ctx.send(f"The queue is empty.{extra}")
        return
    lines = [f"{i}. {t}" for i, t in enumerate(player.queue[:20], start=1)]
    more = f"\n…and {len(player.queue) - 20} more" if len(player.queue) > 20 else ""
    await ctx.send("**Up next:**\n" + "\n".join(lines) + more)


@bot.command(help="Shuffle the current queue")
async def shuffle(ctx):
    player = get_player(ctx)
    if len(player.queue) < 2:
        await ctx.send("Not enough queued tracks to shuffle — try `!radio` for endless shuffle.")
        return
    random.shuffle(player.queue)
    await ctx.send("🔀 Queue shuffled.")


@bot.command(help="Set volume 0–100")
async def volume(ctx, level: int):
    level = max(0, min(100, level))
    player = get_player(ctx)
    player.volume = level / 100
    vc = ctx.voice_client
    if vc and vc.source and isinstance(vc.source, discord.PCMVolumeTransformer):
        vc.source.volume = player.volume
    await ctx.send(f"🔊 Volume set to {level}%.")


# --------------------------------------------------------------------------
# Library commands
# --------------------------------------------------------------------------

@bot.command(aliases=["songs", "library"], help="List the library (optionally one station)")
async def tracks(ctx, *, station: str = ""):
    if not library.tracks:
        await ctx.send("The library is empty — add MP3s to the repo's "
                       f"`{MUSIC_PATH}/` folder and run `{COMMAND_PREFIX}refresh`.")
        return
    matched = library.match_station(station) if station else None
    if station and matched is None:
        await ctx.send(f"No station matching `{station}` — try `{COMMAND_PREFIX}stations`.")
        return
    lines = [
        f"`{i:>3}` {t}" + (f"  ·  {t.station.title()}" if t.station and not matched else "")
        for i, t in enumerate(library.tracks, start=1)
        if matched is None or t.station == matched
    ]
    if matched:
        await ctx.send(f"**📻 {matched.title()}** station:")
    for chunk in chunk_lines(lines):
        await ctx.send(chunk)


@bot.command(aliases=["webplayer", "solo"],
             help="Get the web player link — listen to your own playlists solo")
async def listen(ctx):
    await ctx.send(
        "🎧 **Listen on your own** — open the web player, build your own "
        "playlists, and listen independently while others hear theirs:\n"
        f"{PLAYER_URL}\n"
        "Playlists there are saved in your own browser."
    )


# --------------------------------------------------------------------------
# Likes — !like / !unlike / !top / !shelf, plus !support
# --------------------------------------------------------------------------

@bot.command(aliases=["love", "fav"], help="Like the song that's playing right now")
async def like(ctx):
    player = get_player(ctx)
    track = player.now_playing
    if track is None:
        await ctx.send("Nothing is playing — likes go to the current song.")
        return
    if stats.add_like(track.path, ctx.author.id):
        await ctx.send(f"❤️ {ctx.author.display_name} likes **{track}** — "
                       f"{stats.like_count(track.path)} like(s) total.")
    else:
        await ctx.send(f"You already liked **{track}** ❤️ "
                       f"(`{COMMAND_PREFIX}unlike` to take it back).")


@bot.command(help="Remove your like from the current song")
async def unlike(ctx):
    player = get_player(ctx)
    track = player.now_playing
    if track is None:
        await ctx.send("Nothing is playing.")
        return
    if stats.remove_like(track.path, ctx.author.id):
        await ctx.send(f"💔 Removed your like from **{track}** — "
                       f"{stats.like_count(track.path)} like(s) left.")
    else:
        await ctx.send(f"You hadn't liked **{track}**.")


@bot.command(aliases=["chart", "loved"], help="The most-loved tracks")
async def top(ctx, limit: int = 10):
    rows = stats.top_tracks(max(1, min(25, limit)))
    if not rows:
        await ctx.send(f"No likes yet — `{COMMAND_PREFIX}like` the current song to start the chart!")
        return
    medals = ["🥇", "🥈", "🥉"]
    lines = ["**❤️ Most loved:**"]
    for i, (path, likes, plays) in enumerate(rows):
        badge = medals[i] if i < len(medals) else f"`{i + 1:>2}`"
        lines.append(f"{badge} **{Track(path)}** — ❤️ {likes} · played {plays}×")
    await ctx.send("\n".join(lines))


@bot.command(aliases=["unloved", "cold"], help="Played-but-unloved tracks — shelve candidates")
async def shelf(ctx, limit: int = 10):
    rows = stats.shelf_candidates(max(1, min(25, limit)))
    if not rows:
        await ctx.send("Not enough listening data yet — the shelf list needs songs "
                       "with at least 3 plays.")
        return
    lines = ["**🥶 Shelve candidates** (fewest likes, most skipped):"]
    for i, (path, likes, skips, plays) in enumerate(rows, start=1):
        lines.append(f"`{i:>2}` **{Track(path)}** — ❤️ {likes} · ⏭️ {skips} of {plays} plays")
    lines.append("_Remove a song by deleting its file from the repo's music folder, "
                 f"then `{COMMAND_PREFIX}refresh`._")
    await ctx.send("\n".join(lines))


@bot.command(aliases=["donate", "tip"], help="Optional donation info — the music is always free")
async def support(ctx):
    await ctx.send(
        "💜 **PapaDark Music is free for everyone, always.**\n"
        "If you'd like to chip in toward the hosting bill, donations are "
        "welcome but never expected:\n"
        f"• Card / PayPal / Venmo (no account needed): {PAYPAL_URL}\n"
        f"• Venmo direct: {SUPPORT_URL}"
    )


@bot.command(help="Create the radio channels and pinned welcome (admins only)")
@commands.has_guild_permissions(manage_guild=True)
async def setup(ctx):
    text_ch, notes = await run_setup(ctx.guild)
    where = f" Head to {text_ch.mention}!" if text_ch else ""
    await ctx.send("🛠️ Setup: " + "; ".join(notes) + "." + where)


@bot.command(aliases=["addme"], help="Get the link to add this bot to another server")
async def invite(ctx):
    url = discord.utils.oauth_url(bot.user.id, permissions=INVITE_PERMISSIONS)
    await ctx.send(
        "➕ **Add PapaDark Music to a server** (you need Manage Server there):\n"
        f"{url}\n"
        "It sets up its own radio channels and posts the how-to automatically."
    )


@bot.command(name="cache", help="Show the song cache status")
async def cache_info(ctx):
    if not cache.enabled:
        await ctx.send("💾 Song caching is disabled (CACHE_MAX_MB=0) — every play streams from GitHub.")
        return
    files = cache._entries()
    await ctx.send(
        f"💾 Song cache: **{len(files)}** tracks on disk · "
        f"**{cache.size_bytes() / 1e6:.0f} MB** of {CACHE_MAX_MB} MB — "
        "each song downloads once, then plays locally."
    )


@bot.command(help="Re-scan the GitHub repo for new tracks")
async def refresh(ctx):
    count = await library.refresh()
    await ctx.send(f"🔄 Library refreshed — **{count}** tracks found in `{MUSIC_REPO}`.")


# --------------------------------------------------------------------------
# Playlist commands (Winamp style)
# --------------------------------------------------------------------------

@bot.group(aliases=["pl"], invoke_without_command=True,
           help="Personal playlist commands — try: playlist list")
async def playlist(ctx):
    await ctx.send(
        f"**Your personal playlists** (also `{COMMAND_PREFIX}pl …`) — every "
        "member has their own, built from the shared library:\n"
        f"`{COMMAND_PREFIX}playlist create <name>` — new empty playlist\n"
        f"`{COMMAND_PREFIX}playlist add <name> <track # or search>` — add a track\n"
        f"`{COMMAND_PREFIX}playlist remove <name> <position>` — remove a track\n"
        f"`{COMMAND_PREFIX}playlist show <name>` — show a playlist's tracks\n"
        f"`{COMMAND_PREFIX}playlist list` — your playlists\n"
        f"`{COMMAND_PREFIX}playlist play <name>` — queue yours up\n"
        f"`{COMMAND_PREFIX}playlist shuffle <name>` — queue yours shuffled\n"
        f"`{COMMAND_PREFIX}playlist delete <name>` — delete yours"
    )


@playlist.command(name="create")
async def playlist_create(ctx, name: str):
    mine = playlists.of(ctx.author.id)
    if name in mine:
        await ctx.send(f"You already have a playlist named **{name}**.")
        return
    mine[name] = []
    playlists.save()
    await ctx.send(f"📝 Created your playlist **{name}**. Add tracks with "
                   f"`{COMMAND_PREFIX}playlist add {name} <track # or search>`.")


@playlist.command(name="add")
async def playlist_add(ctx, name: str, *, query: str):
    mine = playlists.of(ctx.author.id)
    if name not in mine:
        await ctx.send(f"You don't have a playlist named **{name}** — create it with "
                       f"`{COMMAND_PREFIX}playlist create {name}`.")
        return
    track = library.find(query)
    if track is None:
        await ctx.send(f"No track matching `{query}`. Try `{COMMAND_PREFIX}tracks`.")
        return
    mine[name].append(track.path)
    playlists.save()
    await ctx.send(f"➕ Added **{track}** to your **{name}** "
                   f"({len(mine[name])} tracks).")


@playlist.command(name="remove")
async def playlist_remove(ctx, name: str, position: int):
    items = playlists.of(ctx.author.id).get(name)
    if items is None:
        await ctx.send(f"You don't have a playlist named **{name}**.")
        return
    if not 1 <= position <= len(items):
        await ctx.send(f"Your **{name}** has {len(items)} tracks — pick 1–{len(items)}.")
        return
    removed = Track(items.pop(position - 1))
    playlists.save()
    await ctx.send(f"➖ Removed **{removed}** from your **{name}**.")


@playlist.command(name="show")
async def playlist_show(ctx, name: str):
    mine = playlists.of(ctx.author.id)
    if name not in mine:
        await ctx.send(f"You don't have a playlist named **{name}**.")
        return
    items = playlists.tracks_of(ctx.author.id, name)
    if not items:
        await ctx.send(f"Your **{name}** is empty.")
        return
    lines = [f"`{i:>3}` {t}" for i, t in enumerate(items, start=1)]
    await ctx.send(f"**{name}** ({ctx.author.display_name}, {len(items)} tracks):")
    for chunk in chunk_lines(lines):
        await ctx.send(chunk)


@playlist.command(name="list")
async def playlist_list(ctx):
    mine = playlists.of(ctx.author.id)
    if not mine:
        await ctx.send(f"You have no playlists yet — "
                       f"`{COMMAND_PREFIX}playlist create <name>` to start one.")
        return
    lines = [f"• **{n}** — {len(items)} tracks" for n, items in mine.items()]
    await ctx.send(f"**{ctx.author.display_name}'s playlists:**\n" + "\n".join(lines))


@playlist.command(name="delete")
async def playlist_delete(ctx, name: str):
    if playlists.of(ctx.author.id).pop(name, None) is None:
        await ctx.send(f"You don't have a playlist named **{name}**.")
        return
    playlists.save()
    await ctx.send(f"🗑️ Deleted your playlist **{name}**.")


async def _queue_playlist(ctx, name: str, do_shuffle: bool):
    if name not in playlists.of(ctx.author.id):
        await ctx.send(f"You don't have a playlist named **{name}** — "
                       f"`{COMMAND_PREFIX}playlist list` shows yours.")
        return
    items = playlists.tracks_of(ctx.author.id, name)
    if not items:
        await ctx.send(f"Your **{name}** is empty — add tracks first.")
        return
    vc = await ensure_voice(ctx)
    if vc is None:
        return
    if do_shuffle:
        random.shuffle(items)
    player = get_player(ctx)
    player.queue.extend(items)
    label = "shuffled " if do_shuffle else ""
    await ctx.send(f"▶️ Queued {ctx.author.display_name}'s {label}playlist "
                   f"**{name}** ({len(items)} tracks).")
    player.start_if_idle()


@playlist.command(name="play")
async def playlist_play(ctx, name: str):
    await _queue_playlist(ctx, name, do_shuffle=False)


@playlist.command(name="shuffle")
async def playlist_shuffle(ctx, name: str):
    await _queue_playlist(ctx, name, do_shuffle=True)


# --------------------------------------------------------------------------
# Help
# --------------------------------------------------------------------------

@bot.command(name="help")
async def help_command(ctx):
    p = COMMAND_PREFIX
    await ctx.send(
        "**📻 PapaDark Music — commands**\n"
        f"`{p}radio` — endless shuffle radio · `{p}station <name>` — change stations\n"
        f"`{p}stations` — list stations (subfolders of the music library)\n"
        f"`{p}play <# or name>` — queue a specific track\n"
        f"`{p}skip` / `{p}pause` / `{p}resume` / `{p}volume <0-100>`\n"
        f"`{p}np` — now playing · `{p}queue` — up next · `{p}shuffle` — shuffle queue\n"
        f"`{p}like` — ❤️ the current song · `{p}top` — most loved · `{p}shelf` — least loved\n"
        f"`{p}tracks` — list the library · `{p}refresh` — re-scan GitHub\n"
        f"`{p}support` — 💜 optional donations (listening is always free)\n"
        f"`{p}playlist` — your own personal playlists (create/add/play/…)\n"
        f"`{p}listen` — web player link: everyone can play their own list at once\n"
        f"`{p}join` / `{p}leave` · `{p}setup` — rebuild radio channels (admin) · "
        f"`{p}invite` — add me elsewhere"
    )


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
        await ctx.send(f"Usage problem: {error}. Try `{COMMAND_PREFIX}help`.")
        return
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("That command needs the **Manage Server** permission.")
        return
    log.exception("Command error", exc_info=error)
    await ctx.send("Something went wrong running that command.")


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit(
            "Set the DISCORD_TOKEN environment variable (see README.md for setup)."
        )
    bot.run(TOKEN)
