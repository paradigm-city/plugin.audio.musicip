# CHANGELOG

## Version 1.0.42

- Fixed plugin-side extended logging crash caused by missing `get_setting_bool(...)` in `main.py`.
- Moved **Extended plugin logging** to the general settings section.
- **Extended service logging** remains in the consistency-check settings section.
- Auto-repair diagnostics remain controlled by **Extended plugin logging**.
- Consistency service info logs remain controlled by **Extended service logging**.

## Version 1.0.41

- Dropped the previous 1.0.41 build with a shared logging option.
- Rebuilt from 1.0.40.
- Added separate settings:
  - **Extended plugin logging**
  - **Extended service logging**
- **Extended plugin logging** controls auto-repair diagnostics in the plugin.
- **Extended service logging** controls normal info logging from the consistency service.
- Auto-repair now logs missing paths, filename lookup, raw/unique candidate counts, candidates, automatic selections, manual selections, skipped tracks, replacements, and final repair count.
- Error logging remains always enabled.

## Version 1.0.40

- Replaced the red dot marker with a plain red bold exclamation mark: `[B][COLOR red]![/COLOR][/B]`.
- Missing songs in mix views now use the exclamation marker and populate `label2` with a missing-file warning.
- Inconsistent date groups now populate `label2` with the warning count.
- Added optional info-level logging for the consistency service.
- New setting: **Enable consistency service info logging**.
- Info logging shows service start/stop, check start/completion, number of mixes/tracks checked, inconsistent mixes found, and metadata updates.
- Error logging remains always enabled.

## Version 1.0.39

- Added a Kodi service component for saved-mix consistency checks.
- The service checks saved mixes in the background and writes `consistency` status to sidecar metadata.
- Mix files are not modified by the background check.
- Inconsistent mixes are marked with a red dot in the Recent Mixes views.
- Date groups with inconsistent mixes are marked with a red dot and warning count.
- Missing songs are marked with a red dot inside mix views.
- Added **Check consistency** for saved mixes.
- Added **Auto-repair this mix** for inconsistent saved mixes.
- Auto-repair runs in the foreground and uses Kodi JSON-RPC lookup based on the old filename/path.
- Ambiguous repair candidates are shown to the user for manual selection.

## Version 1.0.38

- Fixed repeated focus movement when the add-on view gains focus again.
- Focus movement is now one-shot and requires a `focus_token`.
- The token is generated only for refreshes triggered by **More like this** or **Less like this**.
- The token is stored after it is applied, so the same refreshed URL cannot move focus repeatedly.
- Existing `focus_index` values without a valid token no longer trigger cursor movement.
- Relative `Action(Down)` navigation from 1.0.36 is preserved.

## Version 1.0.37

- Dropped the previous 1.0.37 seed-protection build.
- Rebuilt from 1.0.36.
- **Less like this** is no longer shown in the track context menu when the original mix seed at position 0 is selected.
- **Less like this** remains available for all later tracks in the mix.
- **More like this** remains available for the seed and all other tracks.

## Version 1.0.36

- Changed focus restoration after **More like this** and **Less like this** again.
- Removed the absolute `SetFocus(50,<index>,absolute)` approach.
- The refreshed mix view now waits briefly and then moves down with repeated `Action(Down)` calls until the intended row is reached.
- After **More like this**, the target row remains the previously selected item.
- After **Less like this**, the target row remains the item above the removed selection.
- This assumes Kodi resets the refreshed list to the first item, which matches observed behavior.

## Version 1.0.35

- Fixed focus restoration after **More like this** and **Less like this** again.
- The focus index was already passed correctly through the refreshed mix URL.
- The focus operation now uses `SetFocus(50,<index>,absolute)` so Kodi interprets the index as an absolute item index instead of a visible-window-relative position.
- This should keep the selection on the intended row after the mix view refreshes.

## Version 1.0.34

- Fixed focus restoration after **More like this** and **Less like this**.
- Focus is no longer applied immediately after `Container.Update(...)`.
- The intended focus index is now passed into the refreshed mix URL.
- The refreshed mix view applies the pending focus after `endOfDirectory(...)`.
- After **More like this**, focus should stay on the previously selected song.
- After **Less like this**, focus should move to the song above the removed selection.
- This release replaces the earlier experimental 1.0.34 consistency-check build, which is deferred for later.

## Version 1.0.33

- Removed local shuffling from **More like this** so insertion follows the intentional MusicIP submix order.
- **Less like this** remains unshuffled.
- After **More like this**, the view refreshes and tries to keep the selection on the previously selected song.
- After **Less like this**, the view refreshes and tries to move the selection to the song above the one that was removed.
- This keeps the presentation focused on the altered part of the mix.

## Version 1.0.32

- Removed local shuffling from **Less like this** so removal follows the intentional MusicIP submix order.
- **More like this** still shuffles its generated submix before inserting tracks.
- Altered mixes now keep their original saved-mix date group when changed by **More like this** or **Less like this**.
- A separate `modified_ts` metadata value is written when a saved mix is changed in place.
- Track count is still updated after in-place changes.

## Version 1.0.31

- Adjusted **Less like this** so the selected seed track identity is added to the removal match set before submix matches are added.
- The selected seed track is still removed explicitly by its source-mix position.
- This makes the intention clearer and keeps seed removal independent from whether the generated submix contains the seed.

## Version 1.0.30

- Changed **Less like this** to request a larger submix.
- The submix request now uses double the configured mix size to increase the chance of finding matches in the source mix.
- The selected track, which is the seed for the submix, is now removed from the source mix as well.
- Duplicate/path matching still uses normalized track identity.
- The source mix is saved immediately after removal.

## Version 1.0.29

- Added **Less like this** below **More like this** in track context menus inside MusicIP mix views.
- The action generates a submix based on the selected track, shuffles the result locally, and removes matching tracks from the source mix.
- Removing stops when 20% of the configured mix size has been reached.
- The selected seed track itself is kept in the source mix.
- The source mix is saved immediately after removal.
- The action is guarded so it only works from within MusicIP add-on mix views.

## Version 1.0.28

- Added **More like this** to track context menus inside MusicIP mix views.
- The action generates a submix based on the selected track and inserts new tracks directly below it in the source mix.
- The source mix is modified and saved immediately.
- The submix request uses the configured full mix size, then shuffles the result locally.
- New tracks are added until 20% of the configured mix size is reached.
- Existing tracks in the source mix are skipped to avoid duplicates.
- The action is guarded so it only works from within MusicIP add-on mix views.

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
