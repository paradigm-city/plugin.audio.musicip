# MusicIP Kodi Add-on – Review and Function Documentation

## Corrected note about checking whether the seed file exists

The idea of checking whether the seed file exists on disk before creating a mix does **not** make sense for this add-on.

Why:
- `get_current_seed_song()` gets the seed directly from the currently playing audio context through `xbmc.Player()` and `player.getMusicInfoTag().getURL()`.
- If Kodi is already playing the track as audio, that is the authoritative source for this add-on.
- An additional file-system check would be too strict for local files, network paths, special Kodi paths, or stream-like sources.
- What matters here is that Kodi provides a valid seed path or URL, not that Python can independently verify it as a local file.

Conclusion:
- **No extra existence check for the seed song**
- The current validation in `get_current_seed_song()` is enough:
  - audio is playing
  - a path or URL is available

---

## 1) Review

### What the program does well
- Clear separation between routing, MusicIP communication, cache handling, metadata lookup, and UI.
- A dedicated `MusicIPError` exception is used for user-facing failures.
- Mixes are cached so the add-on does not regenerate them unintentionally when the view gains focus again.
- Context-menu actions are isolated and easy to follow.
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

### `MusicIPError(Exception)`
**Purpose:** Custom exception for errors that should be shown to the user in a friendly way.

### `log(message: str, level: int = xbmc.LOGINFO) -> None`
**Purpose:** Writes a message to Kodi's log, prefixed with the add-on id.

### `addon_url(**query: str) -> str`
**Purpose:** Builds internal plugin URLs for actions and navigation.

### `notify(message: str, level=xbmcgui.NOTIFICATION_INFO) -> None`
**Purpose:** Shows a Kodi notification popup.

### `get_setting(name: str, default: str = "") -> str`
**Purpose:** Reads an add-on setting as a string.

### `get_setting_int(name: str, default: int) -> int`
**Purpose:** Reads an add-on setting and converts it to `int`.

### `get_server_host() -> str`
**Purpose:** Returns the MusicIP server host. Default: `localhost`.

### `get_server_port() -> int`
**Purpose:** Returns the MusicIP server port. Default: `10002`.

### `get_playlist_size() -> int`
**Purpose:** Returns the configured mix length. Minimum value: `1`.

### `get_timeout() -> int`
**Purpose:** Returns the HTTP timeout for MusicIP requests. Minimum value: `1`.

### `parse_args() -> dict[str, str]`
**Purpose:** Reads plugin parameters from `sys.argv`.

### `get_profile_dir() -> str`
**Purpose:** Resolves the add-on profile directory with `xbmcvfs.translatePath(...)` and creates it if needed.

### `mix_cache_key(seed: str, size: int) -> str`
**Purpose:** Builds a stable SHA-1 cache key from the seed and the mix size.

### `mix_cache_path(seed: str, size: int) -> str`
**Purpose:** Builds the file path for the cached mix.

### `save_mix(seed: str, size: int, tracks: list[str]) -> None`
**Purpose:** Saves the track list of a mix into the add-on profile directory.

### `load_mix(seed: str, size: int) -> list[str]`
**Purpose:** Loads a previously stored mix from cache.  
**Errors:** Raises `MusicIPError` if no cache file exists.

### `get_current_seed_song() -> str`
**Purpose:** Retrieves the seed song from the currently playing audio item.  
**Flow:**
- checks `player.isPlayingAudio()`
- reads `player.getMusicInfoTag().getURL()`
- returns the full path or URL

### `build_musicip_url(seed_song: str, size: int) -> str`
**Purpose:** Builds the request URL for the MusicIP server.  
**Details:**
- encodes the seed using ISO-8859-1
- uses `sizeType=tracks`
- uses `content=text`

### `decode_response(data: bytes) -> str`
**Purpose:** Decodes the MusicIP response body.  
**Order:** UTF-8, then ISO-8859-1, then UTF-8 with replacement.

### `fetch_mix(seed_song: str, size: int) -> list[str]`
**Purpose:** Fetches a mix from the MusicIP server.  
**Flow:**
- build request URL
- send HTTP request
- decode response
- split lines into track paths  
**Errors:** Converts HTTP, network, and empty-result failures into `MusicIPError`.

### `path_to_label(path: str) -> str`
**Purpose:** Creates a readable label from a path, preferring the filename without extension.

### `new_nonce() -> str`
**Purpose:** Creates a timestamp used for cache-busting in plugin URLs.

### `build_browse_url(seed: str, size: int, refresh: bool = False) -> str`
**Purpose:** Builds the internal URL for the mix view.

### `build_refresh_action(seed: str, size: int) -> str`
**Purpose:** Builds a Kodi action that refreshes the mix using `Container.Update(...)`.

### `build_remove_action(seed: str, size: int, index: int, path: str) -> str`
**Purpose:** Builds a Kodi action that removes one track using `RunPlugin(...)`.

### `remove_track_from_mix(seed: str, size: int, index: int, path: str) -> str`
**Purpose:** Removes a track from the stored mix.  
**Flow:**
- load mix
- try by index first
- otherwise search by path
- save the updated mix

### `get_current_music_tag() -> object | None`
**Purpose:** Returns the current `MusicInfoTag` from the player, or `None`.

### `get_current_player_metadata(path: str | None = None) -> dict[str, str]`
**Purpose:** Reads title, artist, and album from the currently playing item.  
**Special behavior:** If a path is passed in, the metadata is only used when the player's current path matches that path.

### `execute_jsonrpc(method: str, params: dict | None = None) -> dict`
**Purpose:** Executes a Kodi JSON-RPC call and returns the `result`.  
**Errors:** Raises `MusicIPError` when Kodi returns a JSON-RPC error.

### `split_full_path(path: str) -> tuple[str, str]`
**Purpose:** Splits a full path into filename and directory.

### `build_path_candidates(directory: str) -> list[str]`
**Purpose:** Builds several path variants for Kodi library lookup so different slash styles and trailing separators are handled.

### `find_song_by_file(songs: list[dict], path: str) -> dict | None`
**Purpose:** Finds the exact library match by comparing the `file` field to the full path.

### `get_library_track_metadata(path: str) -> dict[str, str]`
**Purpose:** Fetches metadata from the Kodi audio library.  
**Flow:**
- split the path into filename and directory
- build a filter for `filename` and `path`
- call `AudioLibrary.GetSongs`
- match the result exactly through `file`
- normalize the artist value

### `get_track_metadata(path: str) -> dict[str, str]`
**Purpose:** Builds the metadata for a track shown or played by the add-on.  
**Order:**
1. title from filename
2. metadata from the current player
3. missing fields from the Kodi library

### `apply_music_metadata(list_item, title, artist='', album='') -> None`
**Purpose:** Writes title, artist, and album into the `MusicInfoTag` of a Kodi list item.

### `apply_music_path(list_item, path: str) -> None`
**Purpose:** Sets the list item's path and also writes `setURL(path)` into the `MusicInfoTag`.

### `add_track_item(seed: str, size: int, index: int, path: str) -> None`
**Purpose:** Builds a playable entry for one track in the mix view.  
**Includes:**
- label
- `MusicInfoTag`
- path
- context menu:
  - Refresh mix
  - Remove from mix

### `show_root() -> None`
**Purpose:** Builds the root view of the add-on.  
**Contains:**
- Settings
- Mix folder for the currently playing song

### `browse_mix(seed: str, size: int, force_refresh: bool = False, update_listing: bool = False) -> None`
**Purpose:** Builds the actual mix view.  
**Flow:**
- if `force_refresh=True`: always request a new mix from MusicIP
- otherwise: try to load the mix from cache first
- if no cache exists: fetch from MusicIP and save it
- then display either tracks or an empty message

### `play_track(path: str) -> None`
**Purpose:** Resolves a selected track into an actually playable Kodi item.

### `open_settings() -> None`
**Purpose:** Opens the add-on settings dialog and then rebuilds the root view.

### `router() -> None`
**Purpose:** Central dispatcher for the add-on.  
**Handled actions:**
- root
- `browse_mix`
- `play_track`
- `remove_track`
- `open_settings`

### `if __name__ == "__main__":`
**Purpose:** Entry point of the add-on.  
**Flow:**
- call `router()`
- log unexpected errors
- show an error notification
- try to close the directory cleanly

---

## 3) Flow: creating a mix from a seed song

1. The user opens the add-on.
2. `router()` sees no `action` parameter and calls `show_root()`.
3. `show_root()` calls `get_current_seed_song()`.
4. The currently playing audio item provides the seed through `getMusicInfoTag().getURL()`.
5. The add-on shows a folder such as **Mix from current song: ...**.
6. The user opens that folder.
7. `router()` calls `browse_mix(seed, size)`.
8. `browse_mix()` first tries to load a stored mix using `load_mix()`.
9. If no cache exists, or if the user explicitly refreshes, `browse_mix()` calls `fetch_mix(seed, size)`.
10. `fetch_mix()` builds the MusicIP URL using `build_musicip_url(...)`.
11. The add-on sends an HTTP request to the local MusicIP server.
12. MusicIP returns plain text with one track path per line.
13. `decode_response()` decodes the response body.
14. `fetch_mix()` converts the text into a list of track paths.
15. `browse_mix()` stores the result with `save_mix()`.
16. For each track, `add_track_item()` creates a playable Kodi item.
17. The user can now:
    - play a track
    - refresh the mix
    - remove individual tracks from the stored mix

### Important behavior
- When the user simply returns to the view, the add-on does **not** regenerate the mix as long as a cache entry exists.
- A new mix is created only in a controlled way:
  - when no cache exists yet
  - or when the user triggers **Refresh mix**

---

## 4) Concrete improvement suggestions

1. **Allow the library title to replace the filename fallback**  
   If a Kodi library title is available, it should be allowed to replace the filename-derived title.

2. **Use narrower exception handlers in a few places**  
   Not everywhere, but in some parts this would make failures easier to understand.

3. **Refine the JSON-RPC helper a bit**  
   A variable request id would be a little cleaner.

4. **Make metadata handling more compact**  
   A small helper object or dataclass for `title / artist / album / path` would make the code easier to scan.
