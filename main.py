# -*- coding: utf-8 -*-
"""Kodi music add-on for MusicIP mixes."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from urllib.parse import parse_qsl, quote_from_bytes, urlencode
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs


ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo("id")
ADDON_NAME = ADDON.getAddonInfo("name")
HANDLE = int(sys.argv[1])
BASE_URL = sys.argv[0]


class MusicIPError(Exception):
    """Raised for user-facing MusicIP failures."""


def log(message: str, level: int = xbmc.LOGINFO) -> None:
    xbmc.log(f"[{ADDON_ID}] {message}", level)


def addon_url(**query: str) -> str:
    return f"{BASE_URL}?{urlencode(query)}"


def notify(message: str, level=xbmcgui.NOTIFICATION_INFO) -> None:
    xbmcgui.Dialog().notification(ADDON_NAME, message, level)


def get_setting(name: str, default: str = "") -> str:
    try:
        value = ADDON.getSetting(name)
        return value if value != "" else default
    except Exception:
        return default


def get_setting_int(name: str, default: int) -> int:
    raw = get_setting(name, str(default))
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def get_server_host() -> str:
    return get_setting("host", "localhost").strip() or "localhost"


def get_server_port() -> int:
    return get_setting_int("port", 10002)


def get_playlist_size() -> int:
    size = get_setting_int("playlist_size", 20)
    return max(1, size)


def get_timeout() -> int:
    timeout = get_setting_int("timeout", 10)
    return max(1, timeout)


def parse_args() -> dict[str, str]:
    if len(sys.argv) < 3:
        return {}
    return dict(parse_qsl(sys.argv[2].lstrip("?")))


def get_profile_dir() -> str:
    profile = xbmcvfs.translatePath(ADDON.getAddonInfo("profile"))
    if not xbmcvfs.exists(profile):
        xbmcvfs.mkdirs(profile)
    return profile


def mix_cache_key(seed: str, size: int) -> str:
    payload = f"{seed}\n{size}".encode("utf-8", errors="replace")
    return hashlib.sha1(payload).hexdigest()


def mix_cache_path(seed: str, size: int) -> str:
    return os.path.join(get_profile_dir(), f"mix_{mix_cache_key(seed, size)}.m3u")


def save_mix(seed: str, size: int, tracks: list[str]) -> None:
    path = mix_cache_path(seed, size)
    payload = "\n".join(tracks)
    handle = xbmcvfs.File(path, "w")
    try:
        handle.write(payload)
    finally:
        handle.close()


def load_mix(seed: str, size: int) -> list[str]:
    path = mix_cache_path(seed, size)
    if not xbmcvfs.exists(path):
        raise MusicIPError("No stored mix found for this song.")

    handle = xbmcvfs.File(path, "r")
    try:
        payload = handle.read()
    finally:
        handle.close()

    return [line.strip() for line in payload.splitlines() if line.strip()]


def get_current_seed_song() -> str:
    player = xbmc.Player()

    if not player.isPlayingAudio():
        raise MusicIPError("No audio is currently playing.")

    try:
        playing_file = player.getMusicInfoTag().getURL()
    except Exception as exc:
        raise MusicIPError("Kodi did not provide a playable filename.") from exc

    seed_song = (playing_file or "").strip()
    if not seed_song:
        raise MusicIPError("Could not determine the current song path.")

    return seed_song



def build_musicip_url(seed_song: str, size: int) -> str:
    encoded_seed = quote_from_bytes(seed_song.encode("iso-8859-1", errors="replace"))
    host = get_server_host()
    port = get_server_port()
    return (
        f"http://{host}:{port}/api/mix"
        f"?song={encoded_seed}&size={size}&sizeType=tracks&content=text"
    )



def decode_response(data: bytes) -> str:
    for enc in ("utf-8", "iso-8859-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def normalize_track_identity(path: str) -> str:
    return (path or "").replace("\\", "/").strip()


def prepend_seed_track(seed_song: str, tracks: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for track in [seed_song] + list(tracks):
        cleaned = (track or "").strip()
        normalized = normalize_track_identity(cleaned)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(cleaned)

    return result



def fetch_mix(seed_song: str, size: int) -> list[str]:
    url = build_musicip_url(seed_song, size)
    timeout = get_timeout()
    log(f"Requesting MusicIP mix: {url}")

    try:
        with urlopen(url, timeout=timeout) as response:
            body = response.read()
    except HTTPError as exc:
        raise MusicIPError(f"MusicIP server returned HTTP {exc.code}.") from exc
    except URLError as exc:
        raise MusicIPError(f"Could not reach MusicIP server at {get_server_host()}:{get_server_port()}.") from exc
    except Exception as exc:
        raise MusicIPError(f"MusicIP request failed: {exc}") from exc

    text = decode_response(body)
    tracks = [line.strip() for line in text.splitlines() if line.strip()]
    if not tracks:
        raise MusicIPError("MusicIP returned an empty mix.")

    return prepend_seed_track(seed_song, tracks)



def path_to_label(path: str) -> str:
    base = os.path.basename(path.rstrip("/\\"))
    title, _ext = os.path.splitext(base)
    return title if title else base if base else path



def new_nonce() -> str:
    return str(int(time.time() * 1000))



def build_browse_url(seed: str, size: int, refresh: bool = False) -> str:
    query = {
        "action": "browse_mix",
        "seed": seed,
        "size": str(size),
        "nonce": new_nonce(),
    }
    if refresh:
        query["refresh"] = "1"
    return addon_url(**query)


def build_refresh_action(seed: str, size: int) -> str:
    return f"Container.Update({build_browse_url(seed, size, refresh=True)},replace)"


def build_remove_action(seed: str, size: int, index: int, path: str) -> str:
    remove_url = addon_url(
        action="remove_track",
        seed=seed,
        size=str(size),
        index=str(index),
        path=path,
        nonce=new_nonce(),
    )
    return f"RunPlugin({remove_url})"


def remove_track_from_mix(seed: str, size: int, index: int, path: str) -> str:
    tracks = load_mix(seed, size)
    if not tracks:
        raise MusicIPError("Stored mix is already empty.")

    removed_path = ""

    if 0 <= index < len(tracks):
        if not path or tracks[index] == path:
            removed_path = tracks.pop(index)

    if not removed_path and path:
        for pos, track in enumerate(tracks):
            if track == path:
                removed_path = tracks.pop(pos)
                break

    if not removed_path:
        raise MusicIPError("Could not remove the selected item from the stored mix.")

    save_mix(seed, size, tracks)
    return removed_path


def get_current_music_tag() -> object | None:
    try:
        player = xbmc.Player()
        if not player.isPlayingAudio():
            return None
        return player.getMusicInfoTag()
    except Exception:
        return None


def get_current_player_metadata(path: str | None = None) -> dict[str, str]:
    music_tag = get_current_music_tag()
    if music_tag is None:
        return {}

    try:
        current_path = (music_tag.getURL() or '').strip()
    except Exception:
        current_path = ''

    if path and current_path and current_path != path:
        return {}

    data: dict[str, str] = {}

    try:
        title = (music_tag.getTitle() or '').strip()
        if title:
            data['title'] = title
    except Exception:
        pass

    try:
        artist = (music_tag.getArtist() or '').strip()
        if artist:
            data['artist'] = artist
    except Exception:
        pass

    try:
        album = (music_tag.getAlbum() or '').strip()
        if album:
            data['album'] = album
    except Exception:
        pass

    return data


def execute_jsonrpc(method: str, params: dict | None = None) -> dict:
    payload = {
        'jsonrpc': '2.0',
        'id': 1,
        'method': method,
    }
    if params:
        payload['params'] = params

    raw = xbmc.executeJSONRPC(json.dumps(payload))
    response = json.loads(raw)
    if 'error' in response:
        raise MusicIPError(f"Kodi JSON-RPC error for {method}: {response['error']}")
    return response.get('result', {})


def split_full_path(path: str) -> tuple[str, str]:
    value = (path or '').strip().rstrip('/\\')
    if not value:
        return '', ''

    slash_pos = max(value.rfind('/'), value.rfind('\\'))
    if slash_pos < 0:
        return value, ''

    return value[slash_pos + 1 :], value[:slash_pos]


def build_path_candidates(directory: str) -> list[str]:
    raw = (directory or '').strip().rstrip('/\\')
    if not raw:
        return []

    candidates: list[str] = []

    def add(candidate: str) -> None:
        candidate = candidate.strip()
        if candidate and candidate not in candidates:
            candidates.append(candidate)

    add(raw)
    normalized = raw.replace('\\', '/')
    add(normalized)

    if '://' in normalized:
        add(normalized + '/')
    else:
        add(raw + os.sep)
        add(normalized + '/')
        if '\\' in raw:
            add(raw + '\\')

    return candidates


def find_song_by_file(songs: list[dict], path: str) -> dict | None:
    normalized_path = path.replace('\\', '/').strip()
    for song in songs:
        song_file = str(song.get('file') or '').replace('\\', '/').strip()
        if song_file == normalized_path:
            return song
    return None


def get_library_track_metadata(path: str) -> dict[str, str]:
    filename, directory = split_full_path(path)
    if not filename:
        return {}

    filters: list[dict] = [
        {'field': 'filename', 'operator': 'is', 'value': filename},
    ]

    path_candidates = build_path_candidates(directory)
    log(f'Library lookup filename={filename!r} path_candidates={path_candidates!r}', xbmc.LOGDEBUG)
    if path_candidates:
        filters.append({
            'or': [
                {'field': 'path', 'operator': 'is', 'value': candidate}
                for candidate in path_candidates
            ]
        })

    try:
        result = execute_jsonrpc(
            'AudioLibrary.GetSongs',
            {
                'properties': ['title', 'artist', 'album', 'file'],
                'filter': {'and': filters},
            },
        )
    except Exception as exc:
        log(f'Library metadata lookup failed for {path}: {exc}', xbmc.LOGDEBUG)
        return {}

    songs = result.get('songs') or []
    log(f'Library lookup returned {len(songs)} candidate song(s) for {path}', xbmc.LOGDEBUG)
    if not songs:
        return {}

    matched_song = find_song_by_file(songs, path)
    if matched_song is None:
        return {}

    artist_value = matched_song.get('artist') or ''
    if isinstance(artist_value, list):
        artist_value = ' / '.join(str(item).strip() for item in artist_value if str(item).strip())
    else:
        artist_value = str(artist_value).strip()

    return {
        'title': str(matched_song.get('title') or '').strip(),
        'artist': artist_value,
        'album': str(matched_song.get('album') or '').strip(),
    }


def get_track_metadata(path: str) -> dict[str, str]:
    metadata = {
        'title': path_to_label(path),
        'artist': '',
        'album': '',
    }

    current_data = get_current_player_metadata(path)
    for key, value in current_data.items():
        if value:
            metadata[key] = value

    if not metadata['artist'] or not metadata['album']:
        library_data = get_library_track_metadata(path)
        for key, value in library_data.items():
            if value and not metadata.get(key):
                metadata[key] = value

    return metadata


def apply_music_metadata(
    list_item: xbmcgui.ListItem,
    title: str,
    artist: str = '',
    album: str = '',
) -> None:
    try:
        music_tag = list_item.getMusicInfoTag()
        music_tag.setTitle(title)
        if artist:
            music_tag.setArtist(artist)
        if album:
            music_tag.setAlbum(album)
    except Exception:
        pass


def apply_music_path(list_item: xbmcgui.ListItem, path: str) -> None:
    list_item.setPath(path)
    try:
        music_tag = list_item.getMusicInfoTag()
        music_tag.setURL(path)
    except Exception:
        pass

def add_track_item(seed: str, size: int, index: int, path: str) -> None:
    metadata = get_track_metadata(path)
    label = metadata['title'] or path_to_label(path)
    list_item = xbmcgui.ListItem(label=label, offscreen=True)
    list_item.setProperty("IsPlayable", "true")
    apply_music_metadata(
        list_item,
        label,
        artist=metadata.get('artist', ''),
        album=metadata.get('album', ''),
    )
    apply_music_path(list_item, path)

    refresh_action = build_refresh_action(seed, size)
    remove_action = build_remove_action(seed, size, index, path)
    list_item.addContextMenuItems([
        ("Refresh mix", refresh_action),
        ("Remove from mix", remove_action),
    ])

    url = addon_url(
        action="play_track",
        path=path,
    )
    xbmcplugin.addDirectoryItem(HANDLE, url, list_item, isFolder=False)



def show_root() -> None:
    xbmcplugin.setPluginCategory(HANDLE, "MusicIP")
    xbmcplugin.setContent(HANDLE, "files")

    settings_item = xbmcgui.ListItem(label="Settings", offscreen=True)
    apply_music_metadata(settings_item, "Settings")
    xbmcplugin.addDirectoryItem(
        HANDLE,
        addon_url(action="open_settings"),
        settings_item,
        isFolder=True,
    )

    try:
        seed = get_current_seed_song()
    except MusicIPError as exc:
        info_item = xbmcgui.ListItem(label=str(exc), offscreen=True)
        xbmcplugin.addDirectoryItem(HANDLE, "", info_item, isFolder=False)
        xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=False)
        return

    size = get_playlist_size()
    label = f"Mix from current song: {path_to_label(seed)}"
    folder_item = xbmcgui.ListItem(label=label, offscreen=True)
    apply_music_metadata(folder_item, label)
    folder_item.addContextMenuItems([
        ("Refresh mix", build_refresh_action(seed, size)),
    ])

    xbmcplugin.addDirectoryItem(
        HANDLE,
        addon_url(action="browse_mix", seed=seed, size=str(size)),
        folder_item,
        isFolder=True,
    )

    xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=False)



def browse_mix(seed: str, size: int, force_refresh: bool = False, update_listing: bool = False) -> None:
    xbmcplugin.setPluginCategory(HANDLE, f"MusicIP mix: {path_to_label(seed)}")
    xbmcplugin.setContent(HANDLE, "songs")
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_UNSORTED)

    try:
        if force_refresh:
            tracks = fetch_mix(seed, size)
            save_mix(seed, size, tracks)
        else:
            try:
                tracks = load_mix(seed, size)
                log("Loaded stored mix from cache.")
            except MusicIPError:
                tracks = fetch_mix(seed, size)
                save_mix(seed, size, tracks)
    except MusicIPError as exc:
        notify(str(exc), xbmcgui.NOTIFICATION_ERROR)
        log(str(exc), xbmc.LOGERROR)
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False, updateListing=update_listing, cacheToDisc=False)
        return

    if not tracks:
        info_label = "Mix is empty. Use Refresh mix to generate a new one."
        info_item = xbmcgui.ListItem(label=info_label, offscreen=True)
        apply_music_metadata(info_item, info_label)
        xbmcplugin.addDirectoryItem(HANDLE, "", info_item, isFolder=False)
    else:
        for index, path in enumerate(tracks):
            add_track_item(seed, size, index, path)

    xbmcplugin.endOfDirectory(HANDLE, updateListing=update_listing, cacheToDisc=False)



def play_track(path: str) -> None:
    metadata = get_track_metadata(path)
    label = metadata['title'] or path_to_label(path)
    list_item = xbmcgui.ListItem(label=label, offscreen=True)
    apply_music_metadata(
        list_item,
        label,
        artist=metadata.get('artist', ''),
        album=metadata.get('album', ''),
    )
    apply_music_path(list_item, path)
    xbmcplugin.setResolvedUrl(HANDLE, True, list_item)



def open_settings() -> None:
    ADDON.openSettings()
    show_root()



def router() -> None:
    params = parse_args()
    action = params.get("action", "")

    if not action:
        show_root()
        return

    if action == "browse_mix":
        seed = params.get("seed", "").strip()
        if not seed:
            notify("No seed song was supplied.", xbmcgui.NOTIFICATION_ERROR)
            xbmcplugin.endOfDirectory(HANDLE, succeeded=False, cacheToDisc=False)
            return
        size = int(params.get("size") or get_playlist_size())
        refresh = params.get("refresh") == "1"
        browse_mix(seed, size, force_refresh=refresh, update_listing=refresh)
        return

    if action == "play_track":
        path = params.get("path", "")
        if not path:
            xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
            return
        play_track(path)
        return

    if action == "remove_track":
        seed = params.get("seed", "").strip()
        if not seed:
            notify("No seed song was supplied.", xbmcgui.NOTIFICATION_ERROR)
            return

        size = int(params.get("size") or get_playlist_size())
        try:
            index = int(params.get("index", "-1"))
        except (TypeError, ValueError):
            index = -1
        path = params.get("path", "")

        try:
            removed_path = remove_track_from_mix(seed, size, index, path)
        except MusicIPError as exc:
            notify(str(exc), xbmcgui.NOTIFICATION_ERROR)
            log(str(exc), xbmc.LOGERROR)
            return

        notify(f"Removed: {path_to_label(removed_path)}")
        xbmc.executebuiltin(f"Container.Update({build_browse_url(seed, size)},replace)")
        return

    if action == "open_settings":
        open_settings()
        return

    notify(f"Unknown action: {action}", xbmcgui.NOTIFICATION_ERROR)
    xbmcplugin.endOfDirectory(HANDLE, succeeded=False, cacheToDisc=False)


if __name__ == "__main__":
    try:
        router()
    except Exception as exc:  # pragma: no cover - defensive logging in Kodi runtime
        log(f"Unhandled error: {exc}", xbmc.LOGERROR)
        notify(str(exc), xbmcgui.NOTIFICATION_ERROR)
        try:
            xbmcplugin.endOfDirectory(HANDLE, succeeded=False, cacheToDisc=False)
        except Exception:
            pass
