# MusicIP Kodi Add-on

Kodi music add-on that can create a mix from the currently playing audio track or from a song selected in the Kodi music library, using a local MusicIP server.

## Features

- Listed under **Music add-ons**
- Can use the **currently playing audio** as the seed song
- Can open **Create MusicIP mix** from the **context menu of library songs**
- Playlist size is configurable in add-on settings
- Shows a folder view with one entry per returned track so the user can play a single song
- Includes **Refresh mix** in the context menu to request a new mix for the same seed
- Includes **Remove from mix** in the context menu to remove a track from the stored current mix

## Settings

- Playlist size (tracks)
- HTTP timeout
- MusicIP host
- MusicIP port

## Install

1. Put the add-on files into a folder named `plugin.audio.musicip`.
2. Zip that folder itself, not only its contents.
3. In Kodi, go to **Add-ons** -> **Install from ZIP file**.
4. Install the zip.
5. Install and configure MusicIPMixer software
6. Open **Music** -> **Music add-ons** -> **MusicIP**.

## Notes

- The add-on uses the song title from Kodi metadata when available.
- If no title tag is available, it falls back to the current filename without extension.
- The refresh action forces Kodi to re-run the request and bypass plugin disk caching.
- If the MusicIP server returns deterministic results for the same seed, the refreshed mix may still be identical.

- When a list item path is set in Kodi, the add-on also writes the same value into the corresponding `MusicInfoTag` URL field.
- The add-on now also writes artist and album into the corresponding `MusicInfoTag` when Kodi can resolve that metadata from the current player or the music library.
