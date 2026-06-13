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

## Documentation snapshot 1.0.88

The add-on package now contains an updated `docs/` folder with concept notes and flow diagrams.

Current feature baseline: **1.0.87**.

The discarded crossfade experiment from 1.0.86 is not included.

Included documentation:

- `docs/concept_overview.md`
- `docs/concept_discovery_mode.md`
- `docs/concept_repair_strategy.md`
- `docs/concept_sidecar_metadata.md`
- `docs/testing_quality_notes.md`
- `docs/diagrams/*.mmd`
- `docs/diagrams/*.png`

Key documented flows:

- Discovery mode playback and state transitions
- Rolling playlist buffer with backlog and future items
- Mix dialog hold behavior
- External playback takeover handling
- Repair readiness and auto-repair decision flow

## MusicIP API request compatibility note 1.0.89

Outgoing MusicIP mix requests now use the canonical API key casing for track-based size and artist-repeat rejection:

- `sizeType=tracks`
- `rejectType=tracks`

The add-on still keeps internal configuration and sidecar keys lowercase, but maps them to the expected API parameter names when building the HTTP request.

HTTP errors from the MusicIP server are now shown as a visible item in the plugin view instead of causing Kodi to report a failed directory listing.

## Generate mix autoplay note 1.0.90

`Generate mix from playing audio` now behaves like the Discovery mix path after successful mix creation:

- generate the MusicIP mix
- save the mix
- start playback immediately
- show the generated mix view

The working Discovery mix route is intentionally left unchanged.

## Mix track label formatting note 1.0.91

Generated mix track rows and generated mix playback playlist items now use Kodi's configured music track naming template where available.

For the common Kodi template:

```text
[%N. ]%A - %T
```

`%N` is set to the position inside the generated mix, not the original album track number.

Discovery mode labels are intentionally unchanged in this build.

## Mix label display fix 1.0.92

Kodi's music views may display `MusicInfoTag.title` instead of the raw `ListItem` label. Generated mix items now set the formatted mix label as the MusicInfoTag title as well.

This means a Kodi-style template such as:

```text
[%N. ]%A - %T
```

is visible in the mix view, with `%N` reflecting the generated mix position.

Discovery mode remains unchanged.

