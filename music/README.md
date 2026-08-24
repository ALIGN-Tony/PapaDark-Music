# 🎵 Music folder

Drop your `.mp3` files (also `.ogg`, `.wav`, `.flac`, `.m4a`, `.opus`) into
this folder and push. The Discord bot in [`music-bot/`](../music-bot) discovers
everything here automatically — run `!refresh` in Discord after pushing new
songs.

## 📻 Stations

**Subfolders here become radio stations.** Create `music/synthwave/`,
`music/rock/`, `music/chill/` — whatever you like — and drop MP3s inside.
After a `!refresh`, listeners can retune the radio with
`!station synthwave` in Discord or the station dropdown in the web player.
Files sitting directly in `music/` (not in a subfolder) play only on the
**All Music** station. Stations can be added, renamed, or removed at any
time without touching the bot.

Tips:

- **File names become track names.** `Daft_Punk-Around_the_World.mp3` shows up
  as "Daft Punk Around the World". Underscores and dashes become spaces.
- **Keep files under 100 MB** (GitHub's per-file limit). A normal MP3 is
  3–10 MB, so this is rarely an issue.
- **Only upload music you have the rights to share.**
- If GitHub's listing endpoint is ever unreachable, the bot falls back to a
  `tracks.json` manifest in this folder — a plain JSON array of filenames,
  e.g. `["song-one.mp3", "song-two.mp3"]`. You don't need one normally.
