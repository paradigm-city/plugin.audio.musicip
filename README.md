# MusicIP Kodi Add-on

Kodi music add-on that takes the full path of the currently playing audio track as the seed, calls a local MusicIP server, and shows the resulting mix as a folder-like listing.

## Features

- Listed under **Music add-ons**
- Uses the **full path of the currently playing audio file** as the seed
- Checks that the seed file **exists** before requesting a new mix
- Calls MusicIP at `http://localhost:10002/api/mix`
- Playlist size is configurable in add-on settings
- Shows a folder view with one entry per returned track so the user can play a single song
- Includes **Refresh mix** in the context menu to request a new mix for the same seed
- Includes **Remove from mix** in the context menu for individual tracks
- Keeps the current mix in cache so Kodi focus changes do not regenerate it

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

- The add-on sends the full current file path to MusicIP as the `song` seed value.
- A new mix is only requested when no cached mix exists or when **Refresh mix** is used.
- If the current seed file no longer exists, the add-on shows an error instead of calling MusicIP.
- If the MusicIP server returns deterministic results for the same seed, a refreshed mix may still be identical.
