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

PLAYLISTS_FILE = Path(__file__).with_name("playlists.json")

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
        self.name = Path(path).stem.replace("_", " ").replace("-", " ").strip()

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
                async with session.get(tree_url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for entry in data.get("tree", []):
                            path = entry.get("path", "")
                            if entry.get("type") != "blob":
                                continue
                            if prefix and not path.startswith(prefix + "/"):
                                continue
                            if path.lower().endswith(AUDIO_EXTENSIONS):
                                found.append(Track(path))
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
                    async with session.get(manifest_url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
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
        self.file.write_text(json.dumps(self.data, indent=2))

    def of(self, user_id: int) -> dict[str, list[str]]:
        """The calling user's own playlists (name -> repo paths)."""
        return self.data.setdefault(str(user_id), {})

    def tracks_of(self, user_id: int, name: str) -> list[Track]:
        return [Track(p) for p in self.of(user_id).get(name, [])]


playlists = Playlists(PLAYLISTS_FILE)


# --------------------------------------------------------------------------
# Per-guild player: queue + radio shuffle cycle
# --------------------------------------------------------------------------

class Player:
    def __init__(self, guild: discord.Guild):
        self.guild = guild
        self.queue: list[Track] = []
        self.radio = False
        self.radio_pool: list[Track] = []  # shuffle cycle: refills when empty
        self.now_playing: Track | None = None
        self.text_channel: discord.abc.Messageable | None = None
        self.volume = 0.5

    # ---- radio shuffle: play every track once before any repeat ----
    def next_radio_track(self) -> Track | None:
        if not library.tracks:
            return None
        if not self.radio_pool:
            self.radio_pool = list(library.tracks)
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
        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(
                track.url, before_options=FFMPEG_BEFORE, options=FFMPEG_OPTIONS
            ),
            volume=self.volume,
        )
        vc.play(source, after=self.play_next)
        if self.text_channel is not None:
            coro = self.text_channel.send(f"🎵 Now playing: **{track}**")
            asyncio.run_coroutine_threadsafe(coro, bot.loop)

    def start_if_idle(self):
        vc = self.voice
        if vc and vc.is_connected() and not vc.is_playing() and not vc.is_paused():
            self.play_next()


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

@bot.event
async def on_ready():
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


@bot.command(help="Start radio mode: shuffle through every track, forever")
async def radio(ctx):
    if not library.tracks:
        await ctx.send("The library is empty — add MP3s to the repo and run `!refresh`.")
        return
    vc = await ensure_voice(ctx)
    if vc is None:
        return
    player = get_player(ctx)
    player.radio = True
    await ctx.send(f"📻 Radio on — shuffling **{len(library.tracks)}** tracks. `{COMMAND_PREFIX}skip` to change songs, `{COMMAND_PREFIX}leave` to stop.")
    player.start_if_idle()


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
        mode = " (radio 📻)" if player.radio else ""
        await ctx.send(f"🎵 Now playing: **{player.now_playing}**{mode}")
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

@bot.command(aliases=["songs", "library"], help="List every track in the library")
async def tracks(ctx):
    if not library.tracks:
        await ctx.send("The library is empty — add MP3s to the repo's "
                       f"`{MUSIC_PATH}/` folder and run `{COMMAND_PREFIX}refresh`.")
        return
    lines = [f"`{i:>3}` {t}" for i, t in enumerate(library.tracks, start=1)]
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
        f"`{p}radio` — endless Winamp-style shuffle of the whole library\n"
        f"`{p}play <# or name>` — queue a specific track\n"
        f"`{p}skip` / `{p}pause` / `{p}resume` / `{p}volume <0-100>`\n"
        f"`{p}np` — now playing · `{p}queue` — up next · `{p}shuffle` — shuffle queue\n"
        f"`{p}tracks` — list the library · `{p}refresh` — re-scan GitHub\n"
        f"`{p}playlist` — your own personal playlists (create/add/play/…)\n"
        f"`{p}listen` — web player link: everyone can play their own list at once\n"
        f"`{p}join` / `{p}leave`"
    )


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
        await ctx.send(f"Usage problem: {error}. Try `{COMMAND_PREFIX}help`.")
        return
    log.exception("Command error", exc_info=error)
    await ctx.send("Something went wrong running that command.")


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit(
            "Set the DISCORD_TOKEN environment variable (see README.md for setup)."
        )
    bot.run(TOKEN)
