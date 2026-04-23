# MusicIP Kodi Add-on

Kodi music add-on that can build a MusicIP mix from the currently playing song or from a song selected in the Kodi music library, and can reopen stored mixes later from inside the plugin, grouped by calendar date.

## Features

- Listed under **Music add-ons**
- Can use the **currently playing audio** as the seed song
- Can open **Create MusicIP mix** from the **context menu of library songs**
- The library context-menu entry reads the seed with `getMusicInfoTag().getURL()`
- Calls MusicIP at `http://localhost:10002/api/mix`
- Playlist size is configurable in add-on settings
- Shows a folder view with one entry per returned track so the user can play a single song
- Keeps the mix **unsorted** so the displayed order matches the generated mix
- Includes **Refresh mix** in the context menu to request a new mix for the same seed
- Exposes previously generated mixes in a **Recent mixes** folder inside the add-on
- Displays saved mixes grouped by **calendar date**
- Each saved-mix date group now has cleanup options in its context menu
- Each individual saved mix now also has its own cleanup option in the context menu
- Uses a custom add-on icon via `icon.png` referenced from `addon.xml` metadata
- Includes **Remove from mix** in the context menu to remove a track from the stored current mix
- Always includes the **seed song as the first track** and removes duplicate occurrences of that seed from the rest of the mix

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
5. Open **Music** -> **Music add-ons** -> **MusicIP**.

## Usage

### Mix from the currently playing song
1. Start playing a song in Kodi.
2. Open **Music** -> **Music add-ons** -> **MusicIP**.
3. Open the folder **Mix from current song: ...**.

### Mix from a song in the music library
1. Open a song in the Kodi music library.
2. Open the context menu on that song.
3. Select **Create MusicIP mix**.
4. The add-on opens the mix view for that selected song.

### Open a previously generated mix later
1. Open **Music** -> **Music add-ons** -> **MusicIP**.
2. Open **Recent mixes**.
3. Open one of the calendar-date groups.
4. Select one of the stored mixes.

## Notes

- Individual saved mixes can be removed one by one from their own context menu.
- Date-group context menus can remove stored mixes for that date only, or for that date and all older dates.
- Stored mixes are saved as cache files plus metadata sidecar files in the add-on profile directory.
- `Remove from mix` is only available from within the MusicIP add-on view.

- The add-on uses the song title from Kodi metadata when available.
- If no title tag is available, it falls back to the current filename without extension.
- The refresh action forces the add-on to request a new mix for the same seed.
- If the MusicIP server returns deterministic results for the same seed, the refreshed mix may still be identical.
- When a list item path is set in Kodi, the add-on also writes the same value into the corresponding `MusicInfoTag` URL field.
- The add-on also writes artist and album into the corresponding `MusicInfoTag` when Kodi can resolve that metadata from the current player or the music library.

## Version 1.0.19

- Renamed **Saved mixes** to **Recent mixes** in the add-on UI.
- Renamed **Cleanup this saved mix** to **Cleanup this mix**.

## Version 1.0.18

- Added an individual cleanup action to each saved mix entry.
- You can now remove a single saved mix directly from its own context menu.
- Date-group cleanup options remain unchanged.

## Version 1.0.17

- Added two cleanup actions to each saved-mix **date group**.
- You can now remove stored mixes for **that date only**.
- You can also remove stored mixes for **that date and older**.
- These cleanup actions are exposed only on the date-group entries, not on individual mixes.

## Version 1.0.16

- Fixed the **Recent mixes** view so it is actually grouped by **calendar date**.
- Opening **Recent mixes** now shows date folders first.
- Opening a date folder shows the mixes saved on that day.

## Version 1.0.15

- Recent mixes are now displayed grouped by **calendar date**.
- Opening **Recent mixes** now shows date groups first, then the mixes stored on that date.
- The stored mix entries inside each date group still keep their previous ordering by most recent update time.

## Version 1.0.14

- Added a **Recent mixes** folder in the add-on root so previously generated mixes can be opened later.
- Stored mixes now keep sidecar metadata files to preserve seed, size, label, and last update time.
- Recent mixes can be reopened directly inside the add-on and refreshed again from there.

## Version 1.0.13

- Added a bundled `icon.png` for the add-on package.
- `Remove from mix` is now enforced to work only from within the MusicIP add-on container.
- If the action is triggered from outside the add-on, it is rejected with a user-facing message.

## Version 1.0.12

- The mix view now uses **unsorted** presentation so Kodi keeps the generated mix order instead of sorting by title.

## Version 1.0.11

- Kept the existing mix entry based on the currently playing song.
- Added a **Kodi context menu** entry for **library songs**.
- The new context-menu entry uses `getMusicInfoTag().getURL()` from the selected song as the seed.
- Opening a mix from the library reuses the normal mix view and cache handling.
- The generated mix now always starts with the seed song.
- If MusicIP returns the seed again later in the list, that duplicate is removed.

## Version 1.0.9

- Added **Remove from mix** to the context menu of each track in the mix view.
- Removing a track updates the stored current mix instead of requesting a new one.
- Reloading the view after removing a track uses the updated cached mix, so the mix is not regenerated unintentionally.

## Version 1.0.8

- Library metadata lookup now combines `filename` and `path` in the `AudioLibrary.GetSongs` filter.
- The returned `file` property is still used as the final full-path match check.
- Added debug logging for the effective `filename` and `path` candidates used in the Kodi library lookup.

## Version 1.0.7

- Fixed Kodi JSON-RPC song metadata lookup: uses `filename` as the `AudioLibrary.GetSongs` filter field and matches the returned `file` property against the full path.

