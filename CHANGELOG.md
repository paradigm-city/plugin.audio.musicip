# CHANGELOG

## Version 1.0.27

- Fixed the root menu when no audio is playing.
- The root menu now always contains exactly three entries:
  1. Generate mix from playing audio
  2. Recent mixes
  3. Settings
- The message `No audio is currently playing` is no longer shown as a separate root-menu item.
- If the user opens **Generate mix from playing audio** while no audio is playing, the add-on now shows a notification instead.

## Version 1.0.26

- Added detailed MusicIP HTTP error logging.
- The add-on now logs the raw seed, encoded seed, request URL, playlist size, HTTP status, and HTTP error body when MusicIP returns an HTTP error.
- Added URL-error logging for connection failures.
- Rearranged the root menu so **Recent mixes** is item 2 of 3 and **Settings** is item 3 of 3.
- The first root-menu entry is now **Generate mix from playing audio**.

## Version 1.0.25

- Added genre metadata from the Kodi music library when available.
- Added decade metadata derived from the release year, e.g. `1990s` or `2010s`.
- Genre is written to `MusicInfoTag` through `setGenres(...)` when available.
- Decade is exposed as the add-on property `MusicIP.Decade` because Kodi has no native music-tag decade field.
- The secondary label now shows decade, genre, and duration when available.
- Genre and decade are metadata/display only and are not used for mix comparison or relation logic.

## Version 1.0.24

- Added release year display for mix entries.
- Kodi library metadata lookup now requests `year`.
- Year is written into the `MusicInfoTag` through `setYear(...)` when available.
- The list item's secondary label now shows year and duration together when both are available.

## Version 1.0.23

- Added track duration display for mix entries.
- Kodi library metadata lookup now requests `duration`.
- Duration is written into the `MusicInfoTag` through `setDuration(...)` when available.
- Duration is also shown as the list item's secondary label.

## Version 1.0.22

- Added album artwork support for mix track entries.
- Kodi library metadata lookup now requests `thumbnail` and `fanart` in addition to title, artist, album, and file data.
- Track list items now receive `thumb`, `icon`, and, when available, `fanart` artwork through `ListItem.setArt(...)`.
- Playback paths remain unchanged and still use the original MusicIP path.

## Version 1.0.21

- Split the documentation into two files:
  - `README.md` for general concepts and usage
  - `CHANGELOG.md` for version-by-version changes
- Updated the package structure to include both files.
- Consolidated the changelog so it includes all versions up to **1.0.21**.

## Version 1.0.20

- Added canonical and relaxed Kodi library metadata lookup for MusicIP results.
- Metadata lookup now tolerates path-representation differences such as case, URL escaping, Unicode normalization, SMB/root variations, and other differing path forms.
- Playback paths remain unchanged. The original MusicIP path is still used for playback.
- Expanded JSON-RPC metadata lookup to include `displayartist` and `albumartist`.
- Artist fallback order is now:
  - `artist`
  - `displayartist`
  - `albumartist`
- Kodi library titles can now override the filename-based fallback title when a unique library match is found.
- Added debug logging for failed metadata candidate matching to make path mismatches visible.

## Version 1.0.19

- Renamed **Saved mixes** to **Recent mixes** in the add-on UI.
- Renamed **Cleanup this saved mix** to **Cleanup this mix**.

## Version 1.0.18

- Added an individual cleanup action to each saved mix entry.
- You can now remove a single saved mix directly from its own context menu.
- Date-group cleanup options remain unchanged.

## Version 1.0.17

- Added two cleanup actions to each saved-mix date group.
- You can now remove stored mixes for **that date only**.
- You can also remove stored mixes for **that date and older**.
- These cleanup actions are exposed only on the date-group entries, not on individual mixes.

## Version 1.0.16

- Fixed the **Saved mixes** view so it is actually grouped by **calendar date**.
- Opening **Saved mixes** now shows date folders first.
- Opening a date folder shows the mixes saved on that day.

## Version 1.0.15

- Saved mixes are now displayed grouped by **calendar date**.
- Opening **Saved mixes** now shows date groups first, then the mixes stored on that date.
- The stored mix entries inside each date group still keep their previous ordering by most recent update time.

## Version 1.0.14

- Added a **Saved mixes** folder in the add-on root so previously generated mixes can be opened later.
- Stored mixes now keep sidecar metadata files to preserve seed, size, label, and last update time.
- Saved mixes can be reopened directly inside the add-on and refreshed again from there.

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

## Version 1.0.10

- Kept the existing mix entry based on the currently playing song.
- Added a **Kodi context menu** entry for **library songs**.
- The new context-menu entry uses `getMusicInfoTag().getURL()` from the selected song as the seed.
- Opening a mix from the library reuses the normal mix view and cache handling.

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
