# -*- coding: utf-8 -*-
"""Kodi music add-on for MusicIP mixes."""

from __future__ import annotations

import glob
import hashlib
import json
import os
import sys
import time
import unicodedata
from urllib.parse import parse_qsl, quote_from_bytes, urlencode, unquote
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


def mix_meta_path_from_cache_path(cache_path: str) -> str:
    return f"{cache_path}.json"


def save_json_file(path: str, payload: dict) -> None:
    handle = xbmcvfs.File(path, "w")
    try:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2))
    finally:
        handle.close()


def load_json_file(path: str) -> dict:
    if not xbmcvfs.exists(path):
        return {}
    handle = xbmcvfs.File(path, "r")
    try:
        payload = handle.read()
    finally:
        handle.close()
    try:
        return json.loads(payload) if payload else {}
    except Exception:
        return {}


def save_mix(seed: str, size: int, tracks: list[str]) -> None:
    path = mix_cache_path(seed, size)
    payload = "\n".join(tracks)
    handle = xbmcvfs.File(path, "w")
    try:
        handle.write(payload)
    finally:
        handle.close()

    meta = {
        "seed": seed,
        "size": size,
        "track_count": len(tracks),
        "label": path_to_label(seed),
        "updated_ts": int(time.time()),
    }
    save_json_file(mix_meta_path_from_cache_path(path), meta)


def load_mix(seed: str, size: int) -> list[str]:
    return load_mix_by_cache_path(mix_cache_path(seed, size))


def load_mix_by_cache_path(cache_path: str) -> list[str]:
    if not xbmcvfs.exists(cache_path):
        raise MusicIPError("No stored mix found for this song.")

    handle = xbmcvfs.File(cache_path, "r")
    try:
        payload = handle.read()
    finally:
        handle.close()

    return [line.strip() for line in payload.splitlines() if line.strip()]


def list_saved_mix_cache_paths() -> list[str]:
    pattern = os.path.join(get_profile_dir(), "mix_*.m3u")
    paths = [path for path in glob.glob(pattern) if os.path.isfile(path)]
    paths.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return paths


def infer_saved_mix_metadata(cache_path: str, tracks: list[str]) -> dict:
    seed = tracks[0] if tracks else ""
    try:
        modified_ts = int(os.path.getmtime(cache_path))
    except Exception:
        modified_ts = 0
    return {
        "seed": seed,
        "size": len(tracks),
        "track_count": len(tracks),
        "label": path_to_label(seed) if seed else os.path.basename(cache_path),
        "updated_ts": modified_ts,
        "cache_path": cache_path,
    }


def get_saved_mix_metadata(cache_path: str, tracks: list[str] | None = None) -> dict:
    meta = load_json_file(mix_meta_path_from_cache_path(cache_path))
    if tracks is None:
        tracks = load_mix_by_cache_path(cache_path)
    inferred = infer_saved_mix_metadata(cache_path, tracks)
    merged = dict(inferred)
    merged.update({k: v for k, v in meta.items() if v not in ("", None)})
    merged["cache_path"] = cache_path
    if not merged.get("track_count"):
        merged["track_count"] = len(tracks)
    if not merged.get("label"):
        merged["label"] = path_to_label(merged.get("seed", "")) or os.path.basename(cache_path)
    return merged


def format_saved_mix_label(meta: dict) -> str:
    label = meta.get("label") or path_to_label(meta.get("seed", ""))
    track_count = int(meta.get("track_count") or 0)
    if track_count > 0:
        return f"{label} ({track_count} tracks)"
    return label or "Stored mix"

def format_calendar_date(ts: int) -> str:
    if ts <= 0:
        return "Unknown date"
    return time.strftime("%Y-%m-%d", time.localtime(ts))


def build_saved_date_browse_url(date_key: str) -> str:
    return addon_url(action="saved_mixes_by_date", date=date_key, nonce=new_nonce())


def group_saved_mixes_by_date(cache_paths: list[str]) -> list[tuple[str, list[str]]]:
    grouped: dict[str, list[str]] = {}
    for cache_path in cache_paths:
        try:
            tracks = load_mix_by_cache_path(cache_path)
            meta = get_saved_mix_metadata(cache_path, tracks)
            updated_ts = int(meta.get("updated_ts") or 0)
        except Exception:
            updated_ts = 0
        date_key = format_calendar_date(updated_ts)
        grouped.setdefault(date_key, []).append(cache_path)

    def sort_key(item: tuple[str, list[str]]) -> tuple[int, str]:
        key = item[0]
        if key == "Unknown date":
            return (1, key)
        return (0, key)

    items = sorted(grouped.items(), key=sort_key, reverse=True)
    return items


def build_cleanup_date_action(date_key: str, include_older: bool = False) -> str:
    cleanup_url = addon_url(
        action="cleanup_saved_mixes",
        date=date_key,
        older="1" if include_older else "0",
        nonce=new_nonce(),
    )
    return f"RunPlugin({cleanup_url})"


def build_cleanup_saved_mix_action(cache_path: str) -> str:
    cleanup_url = addon_url(
        action="cleanup_saved_mix",
        cache_path=cache_path,
        nonce=new_nonce(),
    )
    return f"RunPlugin({cleanup_url})"


def delete_saved_mix_files(cache_path: str) -> None:
    try:
        xbmcvfs.delete(cache_path)
    except Exception:
        pass
    meta_path = mix_meta_path_from_cache_path(cache_path)
    try:
        xbmcvfs.delete(meta_path)
    except Exception:
        pass


def cleanup_saved_mixes_for_date(date_key: str, include_older: bool = False) -> int:
    grouped = group_saved_mixes_by_date(list_saved_mix_cache_paths())
    removed = 0
    for group_date, cache_paths in grouped:
        match = False
        if include_older:
            if group_date == "Unknown date":
                match = False
            else:
                match = group_date <= date_key
        else:
            match = group_date == date_key

        if not match:
            continue

        for cache_path in cache_paths:
            delete_saved_mix_files(cache_path)
            removed += 1

    return removed

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


def build_saved_browse_url(cache_path: str, refresh: bool = False) -> str:
    query = {
        "action": "browse_saved_mix",
        "cache_path": cache_path,
        "nonce": new_nonce(),
    }
    if refresh:
        query["refresh"] = "1"
    return addon_url(**query)


def build_saved_mixes_url() -> str:
    return addon_url(action="saved_mixes", nonce=new_nonce())


def build_refresh_action(seed: str, size: int, cache_path: str = "") -> str:
    if cache_path:
        return f"Container.Update({build_saved_browse_url(cache_path, refresh=True)},replace)"
    return f"Container.Update({build_browse_url(seed, size, refresh=True)},replace)"


def build_remove_action(seed: str, size: int, index: int, path: str, cache_path: str = "") -> str:
    remove_url = addon_url(
        action="remove_track",
        seed=seed,
        size=str(size),
        index=str(index),
        path=path,
        cache_path=cache_path,
        nonce=new_nonce(),
    )
    return f"RunPlugin({remove_url})"


def remove_track_from_mix(seed: str, size: int, index: int, path: str, cache_path: str = "") -> str:
    target_cache_path = cache_path or mix_cache_path(seed, size)
    tracks = load_mix_by_cache_path(target_cache_path)
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

    payload = "\n".join(tracks)
    handle = xbmcvfs.File(target_cache_path, "w")
    try:
        handle.write(payload)
    finally:
        handle.close()

    meta = get_saved_mix_metadata(target_cache_path, tracks)
    meta["track_count"] = len(tracks)
    meta["updated_ts"] = int(time.time())
    save_json_file(mix_meta_path_from_cache_path(target_cache_path), meta)
    return removed_path


def is_addon_mix_container_active() -> bool:
    try:
        plugin_name = (xbmc.getInfoLabel("Container.PluginName") or "").strip()
        folder_path = (xbmc.getInfoLabel("Container.FolderPath") or "").strip()
    except Exception:
        return False

    if plugin_name == ADDON_ID:
        return True

    return folder_path.startswith(f"plugin://{ADDON_ID}/")


def ensure_remove_allowed_from_addon_container() -> None:
    if not is_addon_mix_container_active():
        raise MusicIPError("Remove from mix is only available inside the MusicIP add-on.")


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


def canonical_audio_path(path: str) -> str:
    value = (path or "").strip()
    value = unquote(value)
    value = unicodedata.normalize("NFC", value)
    value = value.replace("\\", "/")

    if "://" in value:
        scheme, rest = value.split("://", 1)
        while "//" in rest:
            rest = rest.replace("//", "/")
        value = f"{scheme.lower()}://{rest}"
    else:
        while "//" in value:
            value = value.replace("//", "/")

    return value.rstrip("/").casefold()


def basename_key(path: str) -> str:
    value = canonical_audio_path(path)
    slash_pos = value.rfind("/")
    return value[slash_pos + 1:] if slash_pos >= 0 else value


def tail_key(path: str, segments: int = 3) -> str:
    value = canonical_audio_path(path)
    parts = [part for part in value.split("/") if part]
    if not parts:
        return ""
    return "/".join(parts[-segments:])


def find_song_by_file(songs: list[dict], path: str) -> dict | None:
    target = canonical_audio_path(path)

    for song in songs:
        song_file = canonical_audio_path(str(song.get("file") or ""))
        if song_file == target:
            return song

    return None


def find_song_by_file_relaxed(songs: list[dict], path: str) -> dict | None:
    matched_song = find_song_by_file(songs, path)
    if matched_song is not None:
        return matched_song

    target_base = basename_key(path)
    basename_matches = [
        song for song in songs
        if basename_key(str(song.get("file") or "")) == target_base
    ]
    if len(basename_matches) == 1:
        return basename_matches[0]

    target_tail = tail_key(path, segments=3)
    suffix_matches: list[dict] = []
    for song in songs:
        song_file = canonical_audio_path(str(song.get("file") or ""))
        if target_tail and song_file.endswith(target_tail):
            suffix_matches.append(song)

    if len(suffix_matches) == 1:
        return suffix_matches[0]

    return None


def log_library_candidates(path: str, songs: list[dict]) -> None:
    log(f"MusicIP path: {path!r}", xbmc.LOGDEBUG)
    log(f"Canonical MusicIP path: {canonical_audio_path(path)!r}", xbmc.LOGDEBUG)
    for song in songs:
        file_value = str(song.get("file") or "")
        log(f"Kodi candidate file: {file_value!r}", xbmc.LOGDEBUG)
        log(f"Kodi candidate canonical: {canonical_audio_path(file_value)!r}", xbmc.LOGDEBUG)


def query_library_songs_by_filename(filename: str) -> list[dict]:
    if not filename:
        return []

    try:
        result = execute_jsonrpc(
            'AudioLibrary.GetSongs',
            {
                'properties': ['title', 'artist', 'displayartist', 'album', 'albumartist', 'file'],
                'filter': {'field': 'filename', 'operator': 'is', 'value': filename},
            },
        )
    except Exception as exc:
        log(f"Filename-only library lookup failed for {filename!r}: {exc}", xbmc.LOGDEBUG)
        return []

    return result.get('songs') or []


def query_library_songs_strict(filename: str, directory: str) -> list[dict]:
    if not filename:
        return []

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
                'properties': ['title', 'artist', 'displayartist', 'album', 'albumartist', 'file'],
                'filter': {'and': filters},
            },
        )
    except Exception as exc:
        log(f'Library metadata strict lookup failed for {filename!r}: {exc}', xbmc.LOGDEBUG)
        return []

    return result.get('songs') or []


def first_non_empty_text(value: object) -> str:
    if isinstance(value, list):
        parts = [str(item).strip() for item in value if str(item).strip()]
        return ' / '.join(parts)
    return str(value or '').strip()


def extract_song_metadata(song: dict) -> dict[str, str]:
    artist_value = ''
    for key in ('artist', 'displayartist', 'albumartist'):
        artist_value = first_non_empty_text(song.get(key))
        if artist_value:
            break

    return {
        'title': str(song.get('title') or '').strip(),
        'artist': artist_value,
        'album': str(song.get('album') or '').strip(),
    }


def get_library_track_metadata(path: str) -> dict[str, str]:
    filename, directory = split_full_path(path)
    if not filename:
        return {}

    strict_candidates = query_library_songs_strict(filename, directory)
    log(f'Strict library lookup returned {len(strict_candidates)} candidate song(s) for {path}', xbmc.LOGDEBUG)

    matched_song = find_song_by_file_relaxed(strict_candidates, path)
    if matched_song is not None:
        return extract_song_metadata(matched_song)

    filename_candidates = query_library_songs_by_filename(filename)
    log(f'Filename-only library lookup returned {len(filename_candidates)} candidate song(s) for {path}', xbmc.LOGDEBUG)

    matched_song = find_song_by_file_relaxed(filename_candidates, path)
    if matched_song is not None:
        return extract_song_metadata(matched_song)

    if strict_candidates:
        log("No unique relaxed match found in strict library candidates.", xbmc.LOGDEBUG)
        log_library_candidates(path, strict_candidates)
    if filename_candidates:
        log("No unique relaxed match found in filename-only library candidates.", xbmc.LOGDEBUG)
        log_library_candidates(path, filename_candidates)

    return {}


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

    library_data = get_library_track_metadata(path)
    for key, value in library_data.items():
        if value:
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


def add_track_item(seed: str, size: int, index: int, path: str, cache_path: str = '') -> None:
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

    refresh_action = build_refresh_action(seed, size, cache_path=cache_path)
    remove_action = build_remove_action(seed, size, index, path, cache_path=cache_path)
    list_item.addContextMenuItems([
        ("Refresh mix", refresh_action),
        ("Remove from mix", remove_action),
    ])

    url = addon_url(
        action="play_track",
        path=path,
    )
    xbmcplugin.addDirectoryItem(HANDLE, url, list_item, isFolder=False)



def add_saved_mix_date_item(date_key: str, cache_paths: list[str]) -> None:
    count = len(cache_paths)
    label = f"{date_key} ({count} mix{'es' if count != 1 else ''})"
    list_item = xbmcgui.ListItem(label=label, offscreen=True)
    apply_music_metadata(list_item, label)
    list_item.setProperty("IsPlayable", "false")
    list_item.addContextMenuItems([
        ("Cleanup mixes from this date", build_cleanup_date_action(date_key, include_older=False)),
        ("Cleanup mixes from this date and older", build_cleanup_date_action(date_key, include_older=True)),
    ])
    xbmcplugin.addDirectoryItem(
        HANDLE,
        build_saved_date_browse_url(date_key),
        list_item,
        isFolder=True,
    )


def add_saved_mix_item(cache_path: str) -> None:
    tracks = load_mix_by_cache_path(cache_path)
    meta = get_saved_mix_metadata(cache_path, tracks)
    label = format_saved_mix_label(meta)
    list_item = xbmcgui.ListItem(label=label, offscreen=True)
    apply_music_metadata(list_item, label)
    list_item.setProperty("IsPlayable", "false")
    list_item.addContextMenuItems([
        ("Cleanup this mix", build_cleanup_saved_mix_action(cache_path)),
    ])

    updated_ts = int(meta.get("updated_ts") or 0)
    if updated_ts > 0:
        list_item.setLabel2(time.strftime("%Y-%m-%d %H:%M", time.localtime(updated_ts)))

    xbmcplugin.addDirectoryItem(
        HANDLE,
        build_saved_browse_url(cache_path),
        list_item,
        isFolder=True,
    )


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

    saved_item = xbmcgui.ListItem(label="Recent mixes", offscreen=True)
    apply_music_metadata(saved_item, "Recent mixes")
    xbmcplugin.addDirectoryItem(
        HANDLE,
        build_saved_mixes_url(),
        saved_item,
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


def show_saved_mixes() -> None:
    xbmcplugin.setPluginCategory(HANDLE, "MusicIP recent mixes")
    xbmcplugin.setContent(HANDLE, "files")

    cache_paths = list_saved_mix_cache_paths()
    if not cache_paths:
        info_label = "No recent mixes found yet."
        info_item = xbmcgui.ListItem(label=info_label, offscreen=True)
        apply_music_metadata(info_item, info_label)
        xbmcplugin.addDirectoryItem(HANDLE, "", info_item, isFolder=False)
        xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=False)
        return

    grouped = group_saved_mixes_by_date(cache_paths)
    for date_key, group_paths in grouped:
        add_saved_mix_date_item(date_key, group_paths)

    xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=False)


def show_saved_mixes_by_date(date_key: str) -> None:
    xbmcplugin.setPluginCategory(HANDLE, f"MusicIP recent mixes: {date_key}")
    xbmcplugin.setContent(HANDLE, "files")

    cache_paths = list_saved_mix_cache_paths()
    grouped = dict(group_saved_mixes_by_date(cache_paths))
    selected = grouped.get(date_key, [])

    if not selected:
        info_label = "No recent mixes found for this date."
        info_item = xbmcgui.ListItem(label=info_label, offscreen=True)
        apply_music_metadata(info_item, info_label)
        xbmcplugin.addDirectoryItem(HANDLE, "", info_item, isFolder=False)
        xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=False)
        return

    for cache_path in selected:
        try:
            add_saved_mix_item(cache_path)
        except Exception as exc:
            log(f"Skipping invalid stored mix {cache_path}: {exc}", xbmc.LOGDEBUG)

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
        cache_path = mix_cache_path(seed, size)
        for index, path in enumerate(tracks):
            add_track_item(seed, size, index, path, cache_path=cache_path)

    xbmcplugin.endOfDirectory(HANDLE, updateListing=update_listing, cacheToDisc=False)


def browse_saved_mix(cache_path: str, force_refresh: bool = False, update_listing: bool = False) -> None:
    try:
        tracks = load_mix_by_cache_path(cache_path)
        meta = get_saved_mix_metadata(cache_path, tracks)
        seed = (meta.get("seed") or (tracks[0] if tracks else "")).strip()
        size = int(meta.get("size") or len(tracks) or get_playlist_size())
    except MusicIPError as exc:
        notify(str(exc), xbmcgui.NOTIFICATION_ERROR)
        log(str(exc), xbmc.LOGERROR)
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False, updateListing=update_listing, cacheToDisc=False)
        return

    xbmcplugin.setPluginCategory(HANDLE, f"Saved MusicIP mix: {path_to_label(seed)}")
    xbmcplugin.setContent(HANDLE, "songs")
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_UNSORTED)

    if force_refresh:
        if not seed:
            notify("Stored mix does not contain a valid seed song.", xbmcgui.NOTIFICATION_ERROR)
            xbmcplugin.endOfDirectory(HANDLE, succeeded=False, updateListing=update_listing, cacheToDisc=False)
            return
        try:
            tracks = fetch_mix(seed, size)
            save_mix(seed, size, tracks)
            cache_path = mix_cache_path(seed, size)
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
            add_track_item(seed, size, index, path, cache_path=cache_path)

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

    if action == "saved_mixes":
        show_saved_mixes()
        return

    if action == "saved_mixes_by_date":
        date_key = params.get("date", "").strip()
        if not date_key:
            notify("No date was supplied.", xbmcgui.NOTIFICATION_ERROR)
            xbmcplugin.endOfDirectory(HANDLE, succeeded=False, cacheToDisc=False)
            return
        show_saved_mixes_by_date(date_key)
        return

    if action == "cleanup_saved_mixes":
        date_key = params.get("date", "").strip()
        include_older = params.get("older") == "1"
        if not date_key:
            notify("No date was supplied.", xbmcgui.NOTIFICATION_ERROR)
            return
        try:
            removed = cleanup_saved_mixes_for_date(date_key, include_older=include_older)
        except Exception as exc:
            notify(str(exc), xbmcgui.NOTIFICATION_ERROR)
            log(str(exc), xbmc.LOGERROR)
            return
        if include_older:
            notify(f"Removed {removed} stored mix(es) from {date_key} and older.")
        else:
            notify(f"Removed {removed} stored mix(es) from {date_key}.")
        xbmc.executebuiltin(f"Container.Update({build_saved_mixes_url()},replace)")
        return

    if action == "cleanup_saved_mix":
        cache_path = params.get("cache_path", "").strip()
        if not cache_path:
            notify("No stored mix path was supplied.", xbmcgui.NOTIFICATION_ERROR)
            return
        try:
            delete_saved_mix_files(cache_path)
        except Exception as exc:
            notify(str(exc), xbmcgui.NOTIFICATION_ERROR)
            log(str(exc), xbmc.LOGERROR)
            return
        notify("Removed mix.")
        xbmc.executebuiltin(f"Container.Update({build_saved_mixes_url()},replace)")
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

    if action == "browse_saved_mix":
        cache_path = params.get("cache_path", "").strip()
        if not cache_path:
            notify("No stored mix path was supplied.", xbmcgui.NOTIFICATION_ERROR)
            xbmcplugin.endOfDirectory(HANDLE, succeeded=False, cacheToDisc=False)
            return
        refresh = params.get("refresh") == "1"
        browse_saved_mix(cache_path, force_refresh=refresh, update_listing=refresh)
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
        size = int(params.get("size") or get_playlist_size())
        try:
            index = int(params.get("index", "-1"))
        except (TypeError, ValueError):
            index = -1
        path = params.get("path", "")
        cache_path = params.get("cache_path", "").strip()

        try:
            ensure_remove_allowed_from_addon_container()
            removed_path = remove_track_from_mix(seed, size, index, path, cache_path=cache_path)
        except MusicIPError as exc:
            notify(str(exc), xbmcgui.NOTIFICATION_ERROR)
            log(str(exc), xbmc.LOGERROR)
            return

        notify(f"Removed: {path_to_label(removed_path)}")
        if cache_path:
            xbmc.executebuiltin(f"Container.Update({build_saved_browse_url(cache_path)},replace)")
        else:
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
