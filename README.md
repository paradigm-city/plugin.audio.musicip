# MusicIP Kodi Add-on

Kodi music add-on that takes the currently playing audio track as the seed, calls a local MusicIP server, and shows the resulting mix as a folder-like listing.

## Features

- Listed under **Music add-ons**
- Uses the **currently playing audio** as the seed song
- Calls MusicIP at `http://localhost:10002/api/mix`
- Playlist size is configurable in add-on settings
- Shows a folder view with one entry per returned track so the user can play a single song
- Includes **Refresh mix** in the context menu to request a new mix for the same seed

## Settings

- Playlist size (tracks)
- HTTP timeout
- MusicIP host
- MusicIP port

## Install

1. Zip the `plugin.audio.musicip` directory or use the provided zip.
2. In Kodi, go to **Add-ons** -> **Install from ZIP file**.
3. Install the zip.
4. Open **Music** -> **Music add-ons** -> **MusicIP**.

## Notes

- The add-on uses the song title from Kodi metadata when available.
- If no title tag is available, it falls back to the current filename without extension.
- The refresh action forces Kodi to re-run the request and bypass plugin disk caching.
- If the MusicIP server returns deterministic results for the same seed, the refreshed mix may still be identical.

- When a list item path is set in Kodi, the add-on also writes the same value into the corresponding `MusicInfoTag` URL field.
- The add-on now also writes artist and album into the corresponding `MusicInfoTag` when Kodi can resolve that metadata from the current player or the music library.


## Version 1.0.8

- Library metadata lookup now combines `filename` and `path` in the `AudioLibrary.GetSongs` filter.
- The returned `file` property is still used as the final full-path match check.
- Added debug logging for the effective `filename` and `path` candidates used in the Kodi library lookup.

## Version 1.0.7

- Fixed Kodi JSON-RPC song metadata lookup: uses `filename` as the `AudioLibrary.GetSongs` filter field and matches the returned `file` property against the full path.
