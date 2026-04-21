# MusicIP Kodi Add-on – Review and Function Documentation

## What changed in version 1.0.10

Version 1.0.10 keeps the original entry point based on the currently playing song and adds a second entry point through the Kodi music-library context menu.

New in 1.0.10:
- the existing **Mix from current song** flow stays in place
- a new **Create MusicIP mix** context-menu item is available for song entries in the music library
- the context-menu script reads the seed with `getMusicInfoTag().getURL()`
- the context-menu script opens the same `browse_mix(seed, size)` flow already used by the plugin

This means the add-on now has two ways to reach the same mix-generation logic.

---

## 1) Review

### What the program does well
- Clear separation between routing, MusicIP communication, cache handling, metadata lookup, UI, and the new context-menu entry point.
- A dedicated `MusicIPError` exception is used for user-facing failures in the plugin, and the context-menu script has its own `MusicIPContextError`.
- Mixes are cached so the add-on does not regenerate them unintentionally when the view gains focus again.
- The final mix always starts with the seed song, and duplicate occurrences of that seed are removed from the remaining MusicIP result.
- Context-menu actions are isolated and easy to follow.
- The mix presentation can preserve generator order instead of forcing a title sort.
- Metadata is resolved in a sensible order:
  1. currently playing item
  2. Kodi audio library

### Points that stand out in the code
1. **The library title does not currently replace the filename fallback**  
   In `get_track_metadata()`, `title` is initialized immediately with `path_to_label(path)`. Later, library values are only copied if the target field is empty. That means the filename-based fallback remains in many cases.

2. **`get_setting()` catches exceptions very broadly**  
   This is robust in Kodi runtime, but it also hides unexpected errors.

3. **`execute_jsonrpc()` always uses the same request id**  
   This is not really a problem here because the calls are synchronous, but a variable id would be cleaner.

4. **Path normalization is robust, but spread across several functions**  
   `split_full_path()`, `build_path_candidates()`, and `find_song_by_file()` work well together, but the overall lookup logic is a little harder to read at first glance.

---

## 2) Function documentation

### Main plugin functions

#### `MusicIPError(Exception)`
Custom exception for errors that should be shown to the user in a friendly way.

#### `log(message: str, level: int = xbmc.LOGINFO) -> None`
Writes a message to Kodi's log, prefixed with the add-on id.

#### `addon_url(**query: str) -> str`
Builds internal plugin URLs for actions and navigation.

#### `notify(message: str, level=xbmcgui.NOTIFICATION_INFO) -> None`
Shows a Kodi notification popup.

#### `get_setting(name: str, default: str = "") -> str`
Reads an add-on setting as a string.

#### `get_setting_int(name: str, default: int) -> int`
Reads an add-on setting and converts it to `int`.

#### `get_server_host() -> str`
Returns the MusicIP server host. Default: `localhost`.

#### `get_server_port() -> int`
Returns the MusicIP server port. Default: `10002`.

#### `get_playlist_size() -> int`
Returns the configured mix length. Minimum value: `1`.

#### `get_timeout() -> int`
Returns the HTTP timeout for MusicIP requests. Minimum value: `1`.

#### `parse_args() -> dict[str, str]`
Reads plugin parameters from `sys.argv`.

#### `get_profile_dir() -> str`
Resolves the add-on profile directory with `xbmcvfs.translatePath(...)` and creates it if needed.

#### `mix_cache_key(seed: str, size: int) -> str`
Builds a stable SHA-1 cache key from the seed and the mix size.

#### `mix_cache_path(seed: str, size: int) -> str`
Builds the file path for the cached mix.

#### `save_mix(seed: str, size: int, tracks: list[str]) -> None`
Saves the track list of a mix into the add-on profile directory.

#### `load_mix(seed: str, size: int) -> list[str]`
Loads a previously stored mix from cache.

#### `get_current_seed_song() -> str`
Retrieves the seed song from the currently playing audio item through `getMusicInfoTag().getURL()`.

#### `build_musicip_url(seed_song: str, size: int) -> str`
Builds the request URL for the MusicIP server.

#### `decode_response(data: bytes) -> str`
Decodes the MusicIP response body.

#### `fetch_mix(seed_song: str, size: int) -> list[str]`
Fetches a mix from the MusicIP server and returns a list of track paths.

#### `path_to_label(path: str) -> str`
Creates a readable label from a path.

#### `new_nonce() -> str`
Creates a timestamp used for cache-busting in plugin URLs.

#### `build_browse_url(seed: str, size: int, refresh: bool = False) -> str`
Builds the internal URL for the mix view.

#### `build_refresh_action(seed: str, size: int) -> str`
Builds a Kodi action that refreshes the mix using `Container.Update(...)`.

#### `build_remove_action(seed: str, size: int, index: int, path: str) -> str`
Builds a Kodi action that removes one track using `RunPlugin(...)`.

#### `remove_track_from_mix(seed: str, size: int, index: int, path: str) -> str`
Removes a track from the stored mix.

#### `get_current_music_tag() -> object | None`
Returns the current `MusicInfoTag` from the player, or `None`.

#### `get_current_player_metadata(path: str | None = None) -> dict[str, str]`
Reads title, artist, and album from the currently playing item.

#### `execute_jsonrpc(method: str, params: dict | None = None) -> dict`
Executes a Kodi JSON-RPC call and returns the `result`.

#### `split_full_path(path: str) -> tuple[str, str]`
Splits a full path into filename and directory.

#### `build_path_candidates(directory: str) -> list[str]`
Builds several path variants for Kodi library lookup.

#### `find_song_by_file(songs: list[dict], path: str) -> dict | None`
Finds the exact library match by comparing the `file` field to the full path.

#### `get_library_track_metadata(path: str) -> dict[str, str]`
Fetches metadata from the Kodi audio library.

#### `get_track_metadata(path: str) -> dict[str, str]`
Builds the metadata for a track shown or played by the add-on.

#### `apply_music_metadata(list_item, title, artist='', album='') -> None`
Writes title, artist, and album into the `MusicInfoTag` of a Kodi list item.

#### `apply_music_path(list_item, path: str) -> None`
Sets the list item's path and also writes `setURL(path)` into the `MusicInfoTag`.

#### `add_track_item(seed: str, size: int, index: int, path: str) -> None`
Builds a playable entry for one track in the mix view.

#### `show_root() -> None`
Builds the root view of the add-on, including the current-song entry point.

#### `browse_mix(seed: str, size: int, force_refresh: bool = False, update_listing: bool = False) -> None`
Builds the actual mix view.

#### `play_track(path: str) -> None`
Resolves a selected track into an actually playable Kodi item.

#### `open_settings() -> None`
Opens the add-on settings dialog and then rebuilds the root view.

#### `router() -> None`
Central dispatcher for the plugin entry point.

### Context-menu script functions (`context_mix.py`)

#### `MusicIPContextError(Exception)`
Custom exception for context-menu failures that should be shown to the user.

#### `get_context_seed_song() -> str`
Reads the selected library song from `sys.listitem` and pulls the seed from `getMusicInfoTag().getURL()`.

#### `build_browse_url(seed: str, size: int) -> str`
Builds the plugin URL that opens the mix view for the selected library song.

#### `open_mix(seed: str, size: int) -> None`
Opens the Music window on the plugin mix view.

#### `main() -> None`
Entry point for the context-menu script.

---

## 3) Flow: creating a mix from a seed song

The add-on now supports two entry paths that merge into the same mix flow.

### Path A: from the currently playing song
1. The user opens the add-on.
2. `router()` sees no `action` parameter and calls `show_root()`.
3. `show_root()` calls `get_current_seed_song()`.
4. The currently playing audio item provides the seed through `getMusicInfoTag().getURL()`.
5. The add-on shows a folder such as **Mix from current song: ...**.
6. The user opens that folder.
7. `router()` calls `browse_mix(seed, size)`.

### Path B: from a song in the music library
1. The user highlights a song in the music library.
2. The user opens the context menu and selects **Create MusicIP mix**.
3. Kodi starts `context_mix.py` through the `kodi.context.item` extension.
4. `context_mix.py` reads `sys.listitem`.
5. It gets the seed from `sys.listitem.getMusicInfoTag().getURL()`.
6. It opens the normal plugin mix view with that seed.
7. The plugin receives `action=browse_mix` and calls `browse_mix(seed, size)`.

### Shared mix-generation flow
1. `browse_mix()` first tries to load a stored mix using `load_mix()`.
2. If no cache exists, or if the user explicitly refreshes, `browse_mix()` calls `fetch_mix(seed, size)`.
3. `fetch_mix()` builds the MusicIP URL using `build_musicip_url(...)`.
4. The add-on sends an HTTP request to the local MusicIP server.
5. MusicIP returns plain text with one track path per line.
6. `decode_response()` decodes the response body.
7. `fetch_mix()` converts the text into a list of track paths.
8. `browse_mix()` stores the result with `save_mix()`.
9. For each track, `add_track_item()` creates a playable Kodi item.

### Important behavior
- Returning to the mix view does not regenerate the mix as long as a cache entry exists.
- A new mix is created only in a controlled way:
  - when no cache exists yet
  - or when the user triggers **Refresh mix**

---

## 4) Concrete improvement suggestions

1. Allow the library title to replace the filename fallback when Kodi provides a better title.
2. Narrow some broad exception handlers where practical.
3. Use a variable request id in the JSON-RPC helper.
4. Consider a small helper object for `title / artist / album / path`.
