# 🎵 Music folder

Drop your `.mp3` files (also `.ogg`, `.wav`, `.flac`, `.m4a`, `.opus`) into
this folder and push. The Discord bot in [`music-bot/`](../music-bot) discovers
everything here automatically — run `!refresh` in Discord after pushing new
songs.

Tips:

- **File names become track names.** `Daft_Punk-Around_the_World.mp3` shows up
  as "Daft Punk Around the World". Underscores and dashes become spaces.
- **Keep files under 100 MB** (GitHub's per-file limit). A normal MP3 is
  3–10 MB, so this is rarely an issue.
- **Only upload music you have the rights to share.**
- If GitHub's listing endpoint is ever unreachable, the bot falls back to a
  `tracks.json` manifest in this folder — a plain JSON array of filenames,
  e.g. `["song-one.mp3", "song-two.mp3"]`. You don't need one normally.
