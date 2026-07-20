# CHANGELOG

## Version 1.0.102

- Added a MusicIP server reload before every mix generation request.
- The add-on now calls:
  - `/server/reload`
- The reload is performed centrally inside `fetch_mix()`, before the `/api/mix` request is built and sent.
- This applies to all mix generation routes:
  - Generate mix from playing audio
  - Refresh mix
  - More like this
  - Less like this
  - Discovery-generated mixes
  - keyboard/context-menu actions that trigger mix generation
- If `/server/reload` fails, mix generation is aborted with a MusicIP error.
- Existing 1.0.101 metadata selection-refresh behavior is preserved.

## Version 1.0.101

- Changed phase 2 metadata presentation to refresh on selection movement.
- Background metadata refresh now updates SQLite and mix sidecars, then marks the visible MusicIP mix view as pending presentation.
- The service polls the current selection token.
- When the selection changes, the service rebuilds the visible container once:
  - `Container.Update(<current-folder>,replace)`
  - fallback: `Container.Refresh`
- This shows updated metadata without manually navigating out and back into the mix.
- Avoids immediate surprise refreshes while the user is only reading the current row.
- Existing phase 2 background metadata queue, cache, keymap, icon, and Discovery behavior are preserved.

## Version 1.0.100

- Added phase 2 background metadata refresh.
- Mix views no longer perform live per-track JSON-RPC metadata lookup while rendering.
- Missing or stale track metadata is written to `metadata_refresh_queue.json`.
- The background service processes queued metadata refreshes in small batches.
- Refreshed metadata is written to the global SQLite cache:
  - `track_metadata_cache.db`
- Relevant mix sidecar snapshots are updated after background lookup.
- If a MusicIP mix view is visible, it is refreshed once after a successful background batch.
- Generated mixes and Discovery-generated mixes now enqueue missing/stale metadata instead of blocking on live metadata lookup.
- Existing phase 1 cache, keymap install, icon, and Discovery behavior are preserved.

## Version 1.0.99

- Fixed metadata lookup regression introduced with phase 1 caching.
- Removed `songid` from Kodi `AudioLibrary.GetSongs` property requests.
- Added a safe retry path for metadata JSON-RPC lookups with a reduced property set.
- Empty fallback metadata snapshots are no longer considered valid only because `cached_ts` is present.
- Existing empty sidecar snapshots are ignored so live Kodi metadata lookup can run again.
- Added fallback to use a single strict or filename-only JSON-RPC candidate when Kodi did not return a `file` property.
- No background metadata refresh yet.

## Version 1.0.98

- Verified hotfix build based on 1.0.97.
- Carries forward and tightens the fix for:
  - `name 'KODI_MUSIC_TRACK_TEMPLATE_CACHE' is not defined`
- No new feature change.
- Explicitly initializes the full Kodi track-template global group:
  - `KODI_MUSIC_TRACK_TEMPLATE_CACHE`
  - `KODI_MUSIC_TRACK_TEMPLATE_FALLBACK`
  - `KODI_MUSIC_TRACK_TEMPLATE_SETTING_CANDIDATES`
- Added stricter pre-package checks for:
  - module-level template-cache initialization
  - hardened `get_kodi_music_track_template()`
  - phase 1 metadata cache path
  - mix opening path
  - keymap installation
  - packaged icon
  - Discovery mode preservation

## Version 1.0.97

- Fixed a 1.0.96 regression when opening mixes:
  - `name 'KODI_MUSIC_TRACK_TEMPLATE_CACHE' is not defined`
- Added an explicit module-level initialization for `KODI_MUSIC_TRACK_TEMPLATE_CACHE`.
- Hardened `get_kodi_music_track_template()` so it tolerates a missing cache global and recreates it safely.
- No intended functional change to phase 1 metadata caching beyond this hotfix.

## Version 1.0.96

- Added phase 1 of generated mix metadata caching.
- New cache layers:
  - per-mix sidecar track metadata snapshots
  - global SQLite metadata cache in the add-on profile
- Generated mix rendering now uses this order:
  - sidecar metadata snapshot
  - global metadata cache
  - live Kodi JSON-RPC lookup as last fallback
- Generated mix playback now reuses preloaded metadata instead of repeating per-track lookups.
- Generated and refreshed mixes now store track metadata snapshots in the sidecar.
- Added `track_metadata_cache.db` in the add-on profile.
- Discovery mode remains unchanged.
- This is only phase 1. No background metadata refresh is included yet.

## Version 1.0.95

- Fixed MusicIP mix editing keymap deployment.
- The keymap is now actively installed into Kodi's user keymap folder:
  - `special://profile/keymaps/musicip_mix_editing.xml`
- The add-on reloads Kodi keymaps when the installed file changes.
- Added direct key bindings for numeric Kodi window `10502` in addition to named music windows.
- Preserved shortcuts:
  - `DEL` → Remove from mix
  - `m` → More like this
  - `l` → Less like this
- Replaced the packaged `icon.png` with the agreed abstract orb icon.
- Discovery mode remains unchanged.
- Router and focused-item shortcut handlers are unchanged.

## Version 1.0.94

- Adjusted mix editing keyboard shortcuts.
- `DEL` remains mapped to Remove from mix.
- Replaced:
  - `+` / Numpad `+` → removed
  - `-` / Numpad `-` → removed
- New mappings:
  - `m` → More like this
  - `l` → Less like this
- Expanded the keymap to multiple Kodi music window contexts:
  - `MyMusicNav`
  - `MusicPlaylist`
  - `MusicFiles`
- Added both `<delete>` and `<del>` entries for the remove action to improve reliability of the DEL shortcut.
- Router and focused-item shortcut handlers are unchanged.
- Discovery mode remains unchanged.

## Version 1.0.93

- Added keyboard shortcuts for easier mix editing in the Kodi music window:
  - `DEL` → Remove from mix
  - `+` / Numpad `+` → More like this
  - `-` / Numpad `-` → Less like this
- Added `resources/keymaps/musicip_mix_editing.xml`.
- Mix rows now expose focused-item actions via:
  - `MusicIP.MixAction.Remove`
  - `MusicIP.MixAction.MoreLikeThis`
  - `MusicIP.MixAction.LessLikeThis`
- Added keyboard shortcut router actions:
  - `keyboard_remove_from_mix`
  - `keyboard_more_like_this`
  - `keyboard_less_like_this`
- Shortcut handlers no-op with a warning if the focused item is not a MusicIP mix row.
- Discovery mode remains unchanged.

## Version 1.0.92

- Fixed generated mix view still showing only the plain track title.
- Kodi music views may display `MusicInfoTag.title` instead of the raw `ListItem` label.
- Generated mix rows now set the formatted mix label as `MusicInfoTag.title`.
- Generated mix playback playlist items do the same.
- The original track title is preserved as `MusicIP.OriginalTitle` on the list item.
- `%N` still reflects the generated mix position.
- Discovery mode labels and playlist behavior remain unchanged.

## Version 1.0.91

- Generated mix track rows now use Kodi's configured music track naming template where available.
- Generated mix playback playlist items use the same formatting.
- For templates such as `[%N. ]%A - %T`, `%N` now reflects the position inside the generated mix.
- MusicInfoTag track number is also set to the mix position for generated mix items.
- Discovery mode labels and Discovery playlist behavior are intentionally unchanged.
- Generate mix autoplay from 1.0.90 is preserved.
- API parameter casing fix from 1.0.89 is preserved.

## Version 1.0.90

- `Generate mix from playing audio` now starts playback after successful mix generation.
- The route now uses the same proven primitives as the working Discovery mix path:
  - `fetch_mix_confirmed(seed, size)`
  - `save_mix(seed, size, tracks)`
  - `play_tracks_as_music_playlist(tracks)`
  - `Container.Update(build_browse_url(seed, size), replace)`
- Handled MusicIP/API errors are still shown as visible plugin items instead of causing a failed Kodi directory listing.
- The working `Generate mix from current discovery song` route is intentionally unchanged.
- API parameter casing fix from 1.0.89 is preserved.

## Version 1.0.89

- Fixed outgoing MusicIP API parameter casing.
- Mix requests now send:
  - `sizeType=tracks`
  - `rejectType=tracks`
- Internal config/sidecar keys remain lowercase, but the HTTP request maps them to the canonical API names.
- This addresses repeated MusicIP HTTP 500 responses where the request URL used `sizetype=tracks` and `rejecttype=tracks`.
- MusicIP HTTP errors are now represented by a visible error item in the plugin directory instead of returning `xbmcplugin.endOfDirectory(..., succeeded=False)`.
- This should prevent Kodi `GetDirectory(...generate_current_mix) failed` messages for handled MusicIP server errors.
- Documentation baseline from 1.0.88 is preserved.

## Version 1.0.88

- Documentation-only build based on 1.0.87.
- Updated README documentation section.
- Added `docs/` folder with current concept documentation:
  - concept overview
  - Discovery mode concept
  - repair strategy concept
  - sidecar metadata concept
  - testing and quality notes
- Added Mermaid flow diagrams and PNG exports:
  - Discovery mode flow
  - Discovery service state flow
  - playlist buffer flow
  - repair readiness flow
  - mix generation flow
- Clarified that the discarded 1.0.86 crossfade experiment is not part of the current baseline.
- No functional code change beyond the package version/documentation update.

## Version 1.0.87

- Added external playback takeover detection for Discovery mode.
- While Discovery mode is active, the service now checks whether the currently playing file still belongs to the Discovery queue.
- If Kodi starts playing something outside the Discovery queue, Discovery mode is stopped with `stop_reason="external_playback"`.
- External playback is left untouched:
  - no `Player.stop()`
  - no playlist clear
  - no forced navigation
- Discovery state is cleared and the Discovery screen is refreshed if visible.
- Base is 1.0.85; the discarded 1.0.86 crossfade feature is not included.

## Version 1.0.85

- Adjusted Discovery mix-dialog cancel timing.
- If the mix dialog was open shorter than the configured excerpt length, Discovery now continues the existing excerpt timer instead of resetting it to now.
- If the mix dialog was open at least as long as the excerpt length, Discovery still skips directly to the next song.
- This makes the timer behave as if the dialog had not been opened.
- Mix dialog hold from 1.0.84 is preserved.

## Version 1.0.84

- Added a Discovery **mix dialog hold** while creating a mix from the current Discovery song.
- The seed song is captured immediately when the action is selected.
- While the mix parameter dialog is open:
  - Discovery playback continues.
  - Excerpt-based auto-skip is paused.
  - The captured seed remains stable.
- On cancel/error:
  - if the dialog was open at least as long as the excerpt length, Discovery skips directly to the next song.
  - otherwise Discovery resumes from the current song with the excerpt timer reset to now.
- On confirmation, the mix is generated from the captured seed and Discovery mode stops as before.
- Double-next fix from 1.0.83 and mix-generation fix from 1.0.82 are preserved.

## Version 1.0.83

- Fixed double-skip after **Skip to next discovery song**.
- In buffered playlist mode, `player_stop` callbacks while playback continues are now treated as normal playlist transitions.
- The service no longer converts such pending stop events into a second `next_requested`.
- Real Stop still disables Discovery mode when playback is no longer active.
- Seek correction remains in place when Kodi restarts a playlist item near the beginning instead of respecting the Discovery offset.
- Mix generation fix from 1.0.82 is preserved.
- Manual next timer fix from 1.0.80 is preserved.

## Version 1.0.82

- Fixed **Generate mix from current discovery song** failing with `name get_mix_size not defined`.
- Reworked `discovery_mix_from_current()` to use existing add-on functions:
  - `get_playlist_size()`
  - `fetch_mix_confirmed(seed, size)`
  - `save_mix(seed, size, tracks)`
  - `play_tracks_as_music_playlist(tracks)`
  - `build_browse_url(seed, size)`
- Removed calls to non-existing helpers:
  - `get_mix_size()`
  - `get_mix_generation_params_from_dialog()`
  - `create_mix()`
  - `play_saved_mix()`
- The generated mix is saved, played immediately, and the container is replaced with the generated mix view.
- Discovery screen restore and playlist maintenance from previous builds are preserved.

## Version 1.0.81

- Fixed empty screen after **Generate mix from current discovery song**.
- `discovery_mix_from_current()` now avoids returning an empty plugin directory.
- On success it replaces the current container with the generated mix view.
- On cancellation, missing seed or errors it returns to the Discovery mode screen.
- Manual next timer fix from 1.0.80 is preserved.
- Discovery side-effect screen restore from 1.0.79 is preserved.
- Smooth playlist maintenance from 1.0.78 is preserved.

## Version 1.0.80

- Fixed manual **Skip to next discovery song** causing the next song to play only briefly.
- After direct `Player.GoTo(next_position)`, the UI now immediately updates Discovery state:
  - current playlist position
  - current song
  - current label
  - current offset/duration
  - `current_started_ts`
- Added `update_discovery_state_for_playlist_position()` in `main.py`.
- Added a short service-side guard after UI-triggered next jumps so the old excerpt timer cannot immediately advance again.
- Discovery screen restore behavior from 1.0.79 is preserved.
- Smooth playlist maintenance from 1.0.78 is preserved.

## Version 1.0.79

- Fixed empty screen after Discovery side-effect actions.
- `Start discovery mode`, `Skip to next discovery song` and `Stop discovery mode` now explicitly replace the current container with the Discovery mode screen.
- Added `replace_with_discovery_mode_menu()` using `Container.Update(...action=discovery_mode..., replace)`.
- Removed `finish_plugin_action()` from those three routes to avoid returning an empty directory view.
- Discovery playlist buffering and smooth playback behavior from 1.0.78 are preserved.

## Version 1.0.78

- Fixed Discovery playlist being replaced after direct UI start.
- The UI no longer writes delayed Discovery `start`, `stop` or `next` command files for actions it already performs directly.
- Added `startup_in_progress` guard so the service does not write into the playlist while the UI is still loading the library and building the initial queue.
- Fixed playlist position handling where position `0` could be treated like an unset value.
- Fixed immediate/irregular excerpt switching when `current_started_ts` is not initialized.
- Refill now appends new songs only at the end of the Kodi music playlist.
- Added backlog pruning: old items are removed from the top only after more than 10 previous items exist.
- Discovery playlist now aims to keep 10 future items and 10 previous items where possible.
- Stop still clears the playlist and disables Discovery mode.
- Startup reset and JSON-RPC fixes from 1.0.77 are preserved.

## Version 1.0.77

- Discovery mode is now explicitly reset to off at addon/service startup.
- `discovery_mode_state.json` is normalized on service startup:
  - `enabled=false`
  - current song/label cleared
  - current playlist position reset
  - queue cleared
  - pending next/stop flags cleared
  - `stop_reason=startup_reset`
- Stale `discovery_mode_command.json` is removed on service startup.
- Kodi music playlist is cleared during the Discovery startup reset.
- Re-applied the 1.0.76 JSON-RPC fix: removed invalid `songid` from `AudioLibrary.GetSongs` properties.
- Re-applied the service JSON helper fix for `load_json_file()` / `save_json_file()`.
- Added a safe fallback `run_consistency_check()` if this Discovery branch does not contain the full consistency-service implementation.

## Version 1.0.75

- Discovery mode no longer depends on the background service merely to start playback.
- `start_discovery_mode()` now builds and starts the buffered Kodi music playlist directly from `main.py`.
- The service still receives the start command and can maintain/refill the buffer when it is running.
- The service now adopts an already direct-started Discovery queue instead of immediately rebuilding it.
- `stop_discovery_mode()` now directly stops the player, clears the music playlist and finishes the plugin route.
- `discovery_next_track()` now sends a direct `Player.GoTo` request as a fallback while still writing the service command.
- Added `finish_plugin_action()` so side-effect routes call `xbmcplugin.endOfDirectory(...)`.
- This should remove `GetDirectory(...discovery_start/stop...) failed` errors for those routes.
- Kept unconditional Discovery logging from 1.0.74.

## Version 1.0.74

- Added unconditional INFO logging for the Discovery playlist-buffer start path.
- Service startup now logs version, profile path, Discovery state path and Discovery command path.
- Discovery command loading now logs command-file presence, payload and delete result.
- Discovery start now logs command processing, library lookup, queue filling, playlist append operations and Player.play.
- `AudioLibrary.GetSongs` now requests `songid` and has a fallback without random sort.
- Playlist buffer filling now has an attempt limit and logs if no items can be appended.
- Discovery start now clears stale `stopped_ts` values before command processing.
- UI start command now also clears stale queue/current-song fields and logs the state/command paths.
- Intended to diagnose and fix the case where Discovery mode is enabled but the playlist remains empty.

## Version 1.0.73

- Reworked Discovery mode to use a buffered Kodi music playlist.
- Discovery mode now owns the Kodi music playlist while active.
- Start Discovery mode now clears the music playlist and fills it with a buffer of 10 random tracks.
- The service keeps the playlist buffer topped up in the background.
- Native Kodi Next can now move immediately to the next buffered Discovery item.
- Manual **Next discovery song** uses `Player.GoTo` instead of replacing the whole song manually.
- Automatic excerpt switching also advances the buffered playlist.
- The current Discovery song is tracked from the Kodi playlist position.
- Offset/StartOffset metadata is stored per buffered playlist item.
- This reduces reliance on delayed callback interpretation for Next behavior.

## Version 1.0.72

- Fixed Discovery mode treating Kodi's player-stop callback too aggressively.
- `onPlayBackStopped()` now sets a pending stop instead of immediately disabling Discovery mode.
- The service classifies the pending stop after a short delay:
  - playback really stopped => stop Discovery mode
  - playback continues near the beginning => treat as Previous/cursor-down and seek back to the Discovery offset
  - playback continues elsewhere => treat as Next/cursor-up and start the next Discovery song
- This addresses Next/cursor-up on a one-item playlist, where Kodi can emit a stop-like event without actually stopping playback.
- Stop still stops Discovery mode.
- Settings accessibility and Discovery StartOffset behavior from previous builds are preserved.

## Version 1.0.71

- Added Discovery-mode handling for player Next / cursor-up behavior.
- `onPlayBackEnded()` now requests the next discovery song while Discovery mode is active.
- Added `next_requested` state handling in the service loop.
- Added seek-position correction while Discovery mode is active.
- If Previous / cursor-down restarts the current song near the beginning, the service seeks back to the configured Discovery offset.
- Stop still stops Discovery mode through the existing player-stop handling.
- Settings accessibility fix from 1.0.70 is preserved.

## Version 1.0.70

- Fixed Settings becoming inaccessible.
- Removed `RunPlugin(...)` as a ListItem URL for Settings entries.
- Root **Settings** now uses a normal plugin URL again.
- **Discovery mode settings** now uses a normal plugin URL again.
- `open_settings()` opens the settings dialog and then replaces the current container with the canonical root menu.
- This avoids Kodi treating `RunPlugin(plugin://...)` as a playable media file while still reducing the chance that Settings remains in the Back navigation path.
- Discovery playback, StartOffset handling and UI refresh behavior from 1.0.68/1.0.69 are preserved.

## Version 1.0.69

- Settings are now opened through `RunPlugin(...)` actions instead of normal plugin-folder navigation.
- The root **Settings** item is now a non-folder action item.
- **Discovery mode settings** is now a non-folder action item.
- `open_settings()` now opens the settings dialog and returns without rendering the root directory.
- This keeps settings out of the normal Back navigation stack as far as Kodi plugin directories allow.
- Discovery playback, StartOffset handling and UI refresh behavior from 1.0.68 are preserved.

## Version 1.0.68

- Reduced audible Discovery-mode start/seek jump.
- Discovery mode now tries to resolve duration before playback using Kodi library song details.
- Discovery playback now uses a playlist item with `StartOffset` before playback starts.
- Seek confirmation remains as fallback after playback starts.
- Added visible Discovery-menu refresh after player stop.
- When Player Stop disables Discovery mode while the Discovery screen is open, the menu is refreshed so stopped state is reflected.
- Discovery state now records whether `StartOffset` was requested.

## Version 1.0.67

- Fixed Discovery mode stop handling by adding a `xbmc.Player` callback monitor.
- Player Stop now disables Discovery mode through `onPlayBackStopped()`.
- Player Error also disables Discovery mode.
- Kept the existing polling stop detection as a fallback.
- Added an internal playback-change guard so Discovery mode does not stop itself while switching songs.
- Fixed Discovery offset seeking by confirming the seek result.
- Discovery mode now retries `Player.seekTime()` several times and verifies `Player.getTime()`.
- Added JSON-RPC `Player.Seek` fallback if `seekTime()` is not confirmed.
- Discovery state now records `current_seek_confirmed`.

## Version 1.0.66

- Fixed Discovery mode starting excerpts at offset 0 when Kodi library duration is missing or zero.
- Discovery mode now falls back to `Player.getTotalTime()` after playback starts.
- The seek is applied after the player reports a usable duration.
- Offset diagnostics now record `current_duration_seconds` and `current_offset_seconds` in the Discovery state file.
- Navigation fixes from 1.0.64/1.0.65 are preserved.

## Version 1.0.65

- Restored Discovery mode offset/seek behavior from 1.0.60.
- Replaced `start_discovery_song()` with the 1.0.60 implementation.
- Removed the additional post-seek state guard that was introduced later and could interfere with the working offset behavior.
- Kept the 1.0.64 navigation fix that prevents Backspace from reactivating Discovery mode.

## Version 1.0.64

- Fixed Backspace/navigation reactivating Discovery mode.
- Discovery control actions now replace the current container with the canonical Discovery mode menu URL.
- After creating a mix from Discovery mode, the current container is replaced with the canonical mix browse URL.
- Added service-side stale-start-command protection.
- Offset calculation/playback logic is intentionally left unchanged from the working Discovery implementation.

## Version 1.0.63

- Fixed Discovery mode immediately stopping/restarting after start.
- Starting Discovery mode now clears stale stop markers such as `manual_stop`, `player_stop` or `mix_from_discovery_song`.
- Skipping to the next discovery song also clears stale stop markers.
- The service race guard now aborts a starting discovery song only when the latest state is actually disabled.
- This prevents an old `stop_reason` from cancelling a fresh Discovery mode start.

## Version 1.0.62

- Discovery mode now stops when Kodi player playback is stopped by the user.
- Added service-side detection for player stop while Discovery mode is active.
- **Create mix from current discovery song** now asks for mix generation first.
- If the user cancels mix generation, Discovery mode continues.
- Discovery mode is stopped only after the user actually confirms mix generation.
- After creating a mix from Discovery mode, Discovery mode remains off even after playback stop and navigation back.
- Added stronger stop markers (`stop_reason`, `resume_allowed=false`) to prevent Discovery mode from being re-enabled by a stale service tick.

## Version 1.0.61

- Fixed Discovery mode menu entries that behaved like selectable no-op/status rows.
- Discovery mode menu now contains only real actions.
- Removed selectable status and excerpt/offset rows from the Discovery mode menu.
- Added **Discovery mode settings** action.
- Creating a mix from the current discovery song now stops Discovery mode more robustly.
- The generated mix is now started as a Kodi music playlist immediately after creation.
- Added a race-condition guard in the service so a started discovery excerpt cannot re-enable Discovery mode after the UI has stopped it.
- The current discovery song is shown in the plugin category title when the Discovery mode menu is opened.

## Version 1.0.60

- Added first version of **Discovery mode**.
- Discovery mode is service-driven and controlled through state/command files.
- Added root menu entry **Discovery mode**.
- Added Discovery mode actions:
  - Start discovery mode
  - Stop discovery mode
  - Skip to next discovery song
  - Create mix from current discovery song
- Discovery mode plays random songs from the Kodi music library.
- Each song is played as a short excerpt.
- Added separate **Discovery mode** settings section.
- Added configurable excerpt length, default 20 seconds.
- Added configurable start offset into the song, default 33%.
- Creating a mix from the current discovery song stops Discovery mode first.
- Crossfade is not changed yet; this first version focuses on stable playback control.

## Version 1.0.59

- More like this and Less like this no longer show the pre-generation parameter dialog.
- More/Less now use the configured default mix parameters directly.
- Mix generation parameters are now recorded in the sidecar metadata under `mix_generation_parameters`.
- Added a mix information dialog showing seed, track count, saved/modified timestamps, generation parameters, consistency and repair-readiness state.
- Added **Information** / **Show mix information** context actions for saved mixes.
- Saved mix list items now expose `MusicIP.CachePath`, `InfoAction` and sidecar text properties for Kodi information/keymap integration.
- Added `mix_info_selected` action, which can be used by a Kodi keymap to show information for the currently selected saved mix.
- Numeric mix parameter edits now use Kodi slider dialogs where available, with numeric input as fallback.
- Style remains mapped from UI range `0..10` to MusicIP API range `0..200`.

## Version 1.0.58

- Fixed empty page when selecting **Generate MusicIP mix**.
- Replaced the fragile custom `WindowDialog` pre-generation form with Kodi standard dialogs.
- The explicit Cancel list entry remains removed; cancellation uses the normal window/back action.
- Parameters remain editable before generation:
  - mix size
  - style
  - variety
  - seed-genre restriction
  - MusicIP filter
  - artist-repeat restriction
- Style stays on the `0..10` UI scale and is mapped to the MusicIP API range `0..200`.

## Version 1.0.57

- Reworked the pre-generation mix-parameter dialog.
- Removed the explicit **Cancel** option from the parameter list; cancellation now uses the normal window/back action.
- The dialog now uses visible controls instead of a scrolling edit menu:
  - sliders for mix size, style, variety and artist-repeat size
  - radio button for seed-genre restriction
  - text field for MusicIP filter
  - button for **Generate mix**
- All mix options are visible at once.
- Style preference is explicitly mapped from UI range `0..10` to MusicIP API range `0..200`.
- The MusicIP API request normalizes parameters before building the query string.

## Version 1.0.56

- Mix parameters are now adjustable immediately before mix generation.
- The pre-generation dialog now shows:
  - Generate mix
  - Cancel
  - editable size
  - editable style
  - editable variety
  - toggle for seed-genre restriction
  - editable MusicIP filter
  - editable artist-repeat restriction
- The style setting now supports values from 0 to 10 in steps of 1.
- Style labels were expanded for all values from 0 to 10.
- The edited one-time parameters are used for the MusicIP API request without changing the saved configuration.

## Version 1.0.55

- Added **Mix parameters** configuration section.
- Added configurable MusicIP mix parameters:
  - mix size
  - style preference
  - variety
  - restrict to seed genre
  - MusicIP filter
  - artist-repeat rejection size
- Reject type is fixed to `tracks`.
- Artist-repeat setting is shown as “do not repeat artist within N tracks”.
- Style is configured on a 0..10 scale in steps of 2 and mapped to the MusicIP API range 0..200.
- Before mix generation, the add-on shows a parameter summary dialog with **Generate mix** and **Cancel**.
- Mix API requests now send explicit `sizetype=tracks`, `style`, `variety`, `mixgenre`, optional `filter`, optional `rejectsize`, fixed `rejecttype=tracks`, and `content=text`.

## Version 1.0.54

- Fixed Recent Mixes ordering after auto-repair.
- Recent mixes are no longer sorted by the `.m3u` filesystem modification time.
- Sorting now uses the stable sidecar `updated_ts` value.
- `updated_ts` remains the visible date/order timestamp.
- `modified_ts` continues to record repair/edit time without moving the mix inside its date group.
- This keeps the order of mixes inside a date group stable after automatic or manual repair.

## Version 1.0.53

- Renamed the consistency-check setting label from **Enable automatic service repair** to **Enable automatic mix repair**.
- The setting id remains unchanged to preserve existing user configuration.
- Fixed service auto-repair import failure caused by `main.py` expecting Kodi plugin arguments when imported from the service context.
- `HANDLE` and `BASE_URL` are now guarded so repair helper functions can be imported by the service.
- Service auto-repair still performs no dialogs and only runs when enabled and repair readiness is `ready`.

## Version 1.0.52

- Added optional automatic repair in the consistency service.
- New consistency-check setting: **Enable automatic service repair**.
- Default is disabled.
- Service auto-repair only runs when repair readiness is `ready`.
- Service auto-repair performs no dialogs and no user interaction.
- Primary one-candidate repairs can be performed automatically.
- Fallback repairs require exactly one safe high-confidence candidate.
- Fallback auto-repair requires score >= 120, score gap >= 35, strong title match and no track-number mismatch.
- If no safe automatic repair is available, the mix remains unchanged.

## Version 1.0.51

- Tightened auto-repair fallback scoring to avoid optimistic false repairs.
- Added parser support for filenames like `Artist - Album - 12 - Title`.
- Fallback auto-selection now requires a strong title match and no track-number mismatch.
- Fallback auto-selection threshold changed to score >= 120 and gap >= 35.
- Album, artist, year and folder hints are now ranking evidence only; they are no longer enough for automatic fallback repair.
- Removed broad fallback queries for top-level/category terms such as `music` and `modernrock`.
- Update-library dialog now shows raw Kodi library timestamps: last updated, last cleaned, songs last added and songs modified.
- Update-library dialog now offers Kodi library maintenance actions: scan, cleanup, or scan then cleanup.

## Version 1.0.50

- Fixed repair-readiness gating when new missing tracks are added after a prior library scan.
- Repair readiness now compares the Kodi audio-library timestamp against the latest relevant inconsistency timestamp, not only `first_inconsistent_ts`.
- The required timestamp is now the maximum of:
  - `first_inconsistent_ts`
  - `last_inconsistency_change_ts`
  - all per-track `first_missing_ts` values
- If a new missing track is detected after the latest Kodi library update, **Auto-repair this mix** is hidden and **Update library before repair** is shown.
- The update-library dialog now shows first inconsistency, latest inconsistency change, required library timestamp, and latest library timestamp.

## Version 1.0.49

- Fixed stale repair-readiness state in the Recent Mixes UI.
- Inconsistent mixes now recalculate `repair_readiness` when they are rendered, so a recent Kodi library scan is reflected immediately.
- The service still writes `repair_readiness`, but the UI no longer trusts an old sidecar value when deciding whether to show **Auto-repair this mix**.
- Improved **Update library before repair** behavior: if the library is now current enough, the dialog says that repair is available and asks the user to reopen the context menu.
- This avoids needing a Kodi restart after updating the music library.

## Version 1.0.48

- The consistency service now also derives and writes `repair_readiness` into the sidecar metadata.
- Repair readiness is calculated from the current consistency state and Kodi audio-library freshness timestamps.
- The Recent Mixes UI now uses existing service-calculated `repair_readiness` when available.
- Plugin-side readiness calculation remains as fallback and for explicit actions.
- This makes repair readiness a service-maintained state instead of depending only on user navigation.

## Version 1.0.47

- Fixed the repair-readiness datetime parser again.
- The 1.0.46 regex was over-escaped and did not match valid Kodi values such as `2026-05-08 22:16:17`.
- The parser now uses `[0-9]` ranges instead of escaped digit tokens.
- Added extended plugin logging for successful Kodi datetime parsing.
- Repair readiness behavior is otherwise unchanged.

## Version 1.0.46

- Replaced the repair-readiness timestamp parser again.
- Kodi audio-library timestamps are now parsed by a direct regex + `datetime` parser.
- This avoids the `time.strptime(...)` path used in 1.0.45, which still produced zero timestamps on the tested Kodi setup.
- Raw Kodi values such as `2026-05-08 22:16:17` should now produce non-zero Unix timestamps in `library_timestamps`.
- Repair readiness behavior is otherwise unchanged.

## Version 1.0.45

- Fixed repair-readiness timestamp parsing.
- Kodi audio-library freshness values from `AudioLibrary.GetProperties` are now parsed correctly instead of producing `0`.
- Library freshness timestamps are treated as UTC-like values for comparison with `time.time()` sidecar timestamps.
- Added extended plugin logging for raw and parsed Kodi audio-library freshness properties.
- This fixes the case where `library_properties` contained valid dates but `library_timestamps` were all zero.

## Version 1.0.44

- Added first-inconsistency tracking for saved-mix consistency metadata.
- Sidecar metadata now keeps `first_inconsistent_ts`, `last_inconsistency_change_ts`, `missing_signature`, and per-track `first_missing_ts`.
- `first_inconsistent_ts` is preserved while the same inconsistent state remains active.
- `last_inconsistency_change_ts` changes when the missing-path signature changes.
- Added repair-readiness checks based on Kodi audio-library freshness timestamps.
- **Auto-repair this mix** is only shown when the Kodi audio library is newer than the first detected inconsistency.
- If repair is not ready, the context menu shows **Update library before repair** instead.
- The repair action itself now also checks readiness before running.
- Added a dialog explaining why the Kodi library should be updated before repair.

## Version 1.0.43

- Improved auto-repair candidate discovery while keeping the existing strategy as the primary path.
- Auto-repair still first tries the current exact-filename JSON-RPC lookup.
- Broader fallback heuristics now run only when the primary lookup returns no candidates.
- Added tolerant filename parsing for leading track numbers, trailing years, bracketed years, and ambiguous `artist - title` / `title - artist` forms.
- Added fallback candidate collection through broader Kodi JSON-RPC contains searches.
- Added fallback scoring based on title, artist, filename stem, year, track number, and weak folder/album hints.
- Fallback candidates are auto-selected only when the score is high and clearly above the second-best candidate.
- Ambiguous fallback candidates are shown ranked by score with reasons in the selection dialog.
- Extended plugin logging now records primary lookup, fallback hints, fallback queries, scores, reasons, and decisions.

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
