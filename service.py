# -*- coding: utf-8 -*-
"""Background consistency checker for saved MusicIP mixes."""

from __future__ import annotations

import glob
import hashlib
import json
import datetime
import os
import random
import re
import time
import urllib.parse

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs


ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo("id")

DISCOVERY_INTERNAL_PLAYER_CHANGE_UNTIL = 0.0


def mark_discovery_internal_player_change(seconds: float = 4.0) -> None:
    global DISCOVERY_INTERNAL_PLAYER_CHANGE_UNTIL
    DISCOVERY_INTERNAL_PLAYER_CHANGE_UNTIL = time.time() + float(seconds)


def discovery_internal_player_change_active() -> bool:
    return time.time() < DISCOVERY_INTERNAL_PLAYER_CHANGE_UNTIL



def log(message: str, level: int = xbmc.LOGINFO) -> None:
    xbmc.log(f"[{ADDON_ID}] {message}", level)


def log_info(message: str) -> None:
    if get_setting_bool("service_extended_logging", False):
        log(message, xbmc.LOGINFO)



def log_discovery(message: str, level: int = xbmc.LOGINFO) -> None:
    log(f"Discovery mode: {message}", level)

def execute_jsonrpc(method: str, params: dict | None = None) -> dict:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
    }
    if params:
        payload["params"] = params

    raw = xbmc.executeJSONRPC(json.dumps(payload))
    response = json.loads(raw)
    if "error" in response:
        raise RuntimeError(f"Kodi JSON-RPC error for {method}: {response['error']}")
    return response.get("result", {})


def parse_kodi_datetime(value: object) -> int:
    text = str(value or "").strip()
    if not text:
        return 0

    match = re.search(
        r"([0-9]{4})-([0-9]{2})-([0-9]{2})(?:[ T]([0-9]{2}):([0-9]{2})(?::([0-9]{2}))?)?",
        text,
    )
    if not match:
        log_info(f"Repair readiness: could not parse Kodi datetime value {text!r}")
        return 0

    try:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        hour = int(match.group(4) or 0)
        minute = int(match.group(5) or 0)
        second = int(match.group(6) or 0)
        parsed = datetime.datetime(
            year,
            month,
            day,
            hour,
            minute,
            second,
            tzinfo=datetime.timezone.utc,
        )
        timestamp = int(parsed.timestamp())
        log_info(f"Repair readiness: parsed Kodi datetime {text!r} as timestamp {timestamp}")
        return timestamp
    except Exception as exc:
        log_info(f"Repair readiness: failed to convert Kodi datetime {text!r}: {exc}")
        return 0


def get_audio_library_freshness() -> dict:
    properties = [
        "librarylastupdated",
        "librarylastcleaned",
        "songslastadded",
        "songsmodified",
    ]

    try:
        result = execute_jsonrpc(
            "AudioLibrary.GetProperties",
            {"properties": properties},
        )
    except Exception as exc:
        log(f"Repair readiness: could not read Kodi audio library properties: {exc}", xbmc.LOGERROR)
        return {
            "properties": {},
            "timestamps": {},
            "freshest_ts": 0,
            "freshest_property": "",
        }

    timestamps = {}
    for key in properties:
        timestamps[key] = parse_kodi_datetime(result.get(key))
        log_info(
            f"Repair readiness: Kodi library property {key}="
            f"{str(result.get(key) or '')!r}, parsed_ts={timestamps[key]}"
        )

    freshest_property = ""
    freshest_ts = 0
    for key, value in timestamps.items():
        if value > freshest_ts:
            freshest_ts = value
            freshest_property = key

    return {
        "properties": {key: result.get(key, "") for key in properties},
        "timestamps": timestamps,
        "freshest_ts": freshest_ts,
        "freshest_property": freshest_property,
    }


def get_repair_readiness_required_ts(consistency: dict) -> int:
    values = [
        int(consistency.get("first_inconsistent_ts") or 0),
        int(consistency.get("last_inconsistency_change_ts") or 0),
    ]

    for item in consistency.get("missing") or []:
        if isinstance(item, dict):
            values.append(int(item.get("first_missing_ts") or 0))

    return max(values) if values else 0


def get_repair_readiness_for_consistency(consistency: dict) -> dict:
    first_inconsistent_ts = int(consistency.get("first_inconsistent_ts") or 0)
    last_inconsistency_change_ts = int(consistency.get("last_inconsistency_change_ts") or 0)
    required_library_ts = get_repair_readiness_required_ts(consistency)
    status = str(consistency.get("status") or "").lower()

    if status != "inconsistent":
        return {
            "status": "not_needed",
            "reason": "Mix is not inconsistent.",
            "checked_ts": int(time.time()),
        }

    freshness = get_audio_library_freshness()
    freshest_ts = int(freshness.get("freshest_ts") or 0)
    freshest_property = str(freshness.get("freshest_property") or "")

    if required_library_ts <= 0:
        readiness_status = "update_library_before_repair"
        reason = "Required library freshness time is not known yet. Run consistency check again."
    elif freshest_ts > required_library_ts:
        readiness_status = "ready"
        reason = "Kodi audio library is newer than the latest detected inconsistency."
    elif freshest_ts <= 0:
        readiness_status = "update_library_before_repair"
        reason = "Kodi audio library freshness could not be determined."
    else:
        readiness_status = "update_library_before_repair"
        reason = "Kodi audio library has not been updated since the latest detected inconsistency."

    return {
        "status": readiness_status,
        "reason": reason,
        "checked_ts": int(time.time()),
        "first_inconsistent_ts": first_inconsistent_ts,
        "last_inconsistency_change_ts": last_inconsistency_change_ts,
        "required_library_ts": required_library_ts,
        "library_freshest_ts": freshest_ts,
        "library_freshest_property": freshest_property,
        "library_properties": freshness.get("properties") or {},
        "library_timestamps": freshness.get("timestamps") or {},
    }


def get_setting(name: str, default: str = "") -> str:
    try:
        value = ADDON.getSetting(name)
        return value if value != "" else default
    except Exception:
        return default


def get_setting_bool(name: str, default: bool = False) -> bool:
    raw = get_setting(name, "true" if default else "false").strip().lower()
    return raw in ("true", "1", "yes", "on")


def get_setting_int(name: str, default: int) -> int:
    try:
        return int(get_setting(name, str(default)))
    except (TypeError, ValueError):
        return default


def is_consistency_service_enabled() -> bool:
    return get_setting_bool("consistency_enabled", True)


def is_service_auto_repair_enabled() -> bool:
    return get_setting_bool("service_auto_repair_enabled", False)


def get_check_interval_seconds() -> int:
    minutes = max(1, get_setting_int("consistency_interval_minutes", 60))
    return minutes * 60


def get_profile_dir() -> str:
    profile = xbmcvfs.translatePath(ADDON.getAddonInfo("profile"))
    if not xbmcvfs.exists(profile):
        xbmcvfs.mkdirs(profile)
    return profile


DISCOVERY_BUFFER_SIZE = 10
DISCOVERY_REFILL_THRESHOLD = 5
DISCOVERY_BACKLOG_SIZE = 10



def load_json_file(path: str) -> dict:
    try:
        if not xbmcvfs.exists(path):
            return {}
        with xbmcvfs.File(path, "r") as handle:
            raw = handle.read()
        if not raw:
            return {}
        return json.loads(raw)
    except Exception as exc:
        log(f"Could not load JSON file {path!r}: {exc}", xbmc.LOGWARNING)
        return {}


def save_json_file(path: str, payload: dict) -> None:
    try:
        parent = os.path.dirname(path)
        if parent and not xbmcvfs.exists(parent):
            xbmcvfs.mkdirs(parent)
        with xbmcvfs.File(path, "w") as handle:
            handle.write(json.dumps(payload or {}, indent=2, ensure_ascii=False))
    except Exception as exc:
        log(f"Could not save JSON file {path!r}: {exc}", xbmc.LOGERROR)

def get_music_playlist() -> xbmc.PlayList:
    return xbmc.PlayList(xbmc.PLAYLIST_MUSIC)


class DiscoveryPlaybackMonitor(xbmc.Player):
    def _stop_discovery_from_player_event(self, event_name: str) -> None:
        if discovery_internal_player_change_active():
            log_info(f"Discovery mode: ignored {event_name} during internal player change.")
            return

        state = load_discovery_state()
        if not state.get("enabled"):
            return

        state["enabled"] = False
        state["stopped_ts"] = int(time.time())
        state["stop_reason"] = event_name
        state["resume_allowed"] = False
        state["ui_refresh_requested"] = True
        state["ui_refresh_ts"] = int(time.time())
        save_discovery_state(state)
        log_info(f"Discovery mode stopped because Kodi player event occurred: {event_name}.")

    def onPlayBackStopped(self) -> None:
        if discovery_internal_player_change_active():
            log_info("Discovery mode: ignored player_stop during internal player change.")
            return

        state = load_discovery_state()
        if not state.get("enabled"):
            return

        state["pending_player_stop"] = True
        state["pending_player_stop_ts"] = int(time.time())
        state["pending_player_stop_reason"] = "player_stop_event"
        save_discovery_state(state)
        log_info("Discovery mode: player_stop event received; deferring classification.")

    def onPlayBackEnded(self) -> None:
        if discovery_internal_player_change_active():
            log_info("Discovery mode: ignored player_end during internal player change.")
            return

        state = load_discovery_state()
        if not state.get("enabled"):
            return

        state["playlist_change_pending"] = True
        state["playlist_change_pending_ts"] = int(time.time())
        save_discovery_state(state)
        log_info("Discovery mode: player ended; playlist change pending.")

    def onPlayBackError(self) -> None:
        self._stop_discovery_from_player_event("player_error")


def discovery_state_path() -> str:
    return os.path.join(get_profile_dir(), "discovery_mode_state.json")


def discovery_command_path() -> str:
    return os.path.join(get_profile_dir(), "discovery_mode_command.json")


def get_discovery_excerpt_seconds() -> int:
    try:
        value = int(ADDON.getSetting("discovery_excerpt_seconds") or 20)
    except Exception:
        value = 20
    return max(5, min(60, value))


def get_discovery_offset_percent() -> int:
    try:
        value = int(ADDON.getSetting("discovery_offset_percent") or 33)
    except Exception:
        value = 33
    return max(0, min(90, value))


def load_discovery_state() -> dict:
    return load_json_file(discovery_state_path())


def save_discovery_state(state: dict) -> None:
    save_json_file(discovery_state_path(), state or {})


def command_is_stale_for_state(command: dict, state: dict) -> bool:
    try:
        command_ts = int(command.get("ts") or 0)
    except Exception:
        command_ts = 0
    try:
        stopped_ts = int(state.get("stopped_ts") or 0)
    except Exception:
        stopped_ts = 0

    if command_ts <= 0 or stopped_ts <= 0:
        return False

    return command_ts <= stopped_ts


def read_discovery_command() -> dict:
    path = discovery_command_path()
    try:
        exists = bool(xbmcvfs.exists(path))
    except Exception:
        exists = False

    if exists:
        log_discovery(f"command file found: {path}")

    payload = load_json_file(path)
    if payload:
        log_discovery(f"command loaded: {payload!r}")
        try:
            deleted = xbmcvfs.delete(path)
            log_discovery(f"command file delete requested. deleted={deleted!r}")
        except Exception as exc:
            log_discovery(f"command file delete failed: {exc}", xbmc.LOGWARNING)
    return payload


def discovery_song_label(song: dict) -> str:
    title = str(song.get("title") or "").strip()
    artist = song.get("artist") or song.get("displayartist") or ""
    if isinstance(artist, list):
        artist = ", ".join(str(item) for item in artist if item)

    artist = str(artist or "").strip()
    if artist and title:
        return f"{artist} - {title}"
    return title or path_to_label(str(song.get("file") or ""))


def get_song_duration_seconds(song: dict) -> int:
    try:
        duration = int(song.get("duration") or 0)
    except Exception:
        duration = 0

    if duration > 0:
        return duration

    song_id = song.get("songid")
    if song_id is None:
        return 0

    try:
        result = execute_jsonrpc(
            "AudioLibrary.GetSongDetails",
            {
                "songid": int(song_id),
                "properties": ["duration"],
            },
        )
        details = result.get("songdetails") or {}
        return max(0, int(details.get("duration") or 0))
    except Exception as exc:
        log_info(f"Discovery mode: could not read song duration for songid={song_id!r}: {exc}")
        return 0


def calculate_discovery_offset(duration: int, excerpt_seconds: int, offset_percent: int) -> int:
    try:
        duration = int(duration or 0)
        excerpt_seconds = int(excerpt_seconds or 0)
        offset_percent = int(offset_percent or 0)
    except Exception:
        return 0

    if duration <= 0:
        return 0

    offset_seconds = int(duration * (offset_percent / 100.0))
    if duration > excerpt_seconds + 2:
        return min(offset_seconds, max(0, duration - excerpt_seconds - 2))
    return 0


def discovery_queue_entry(song: dict, excerpt_seconds: int, offset_percent: int) -> dict:
    file_path = str(song.get("file") or "").strip()
    duration = get_song_duration_seconds(song)
    offset = calculate_discovery_offset(duration, excerpt_seconds, offset_percent)
    return {
        "file": file_path,
        "label": discovery_song_label(song),
        "duration": duration,
        "offset": offset,
        "songid": song.get("songid"),
    }


def discovery_playlist_item(entry: dict) -> xbmcgui.ListItem:
    label = str(entry.get("label") or path_to_label(str(entry.get("file") or "")))
    item = xbmcgui.ListItem(label=label, offscreen=True)
    try:
        item.setProperty("StartOffset", str(int(entry.get("offset") or 0)))
    except Exception:
        pass
    try:
        item.setProperty("MusicIP.Discovery", "true")
        item.setProperty("MusicIP.DiscoveryFile", str(entry.get("file") or ""))
        item.setProperty("MusicIP.DiscoveryOffset", str(int(entry.get("offset") or 0)))
    except Exception:
        pass
    return item


def append_discovery_entry_to_playlist(entry: dict) -> bool:
    file_path = str(entry.get("file") or "").strip()
    if not file_path:
        log_discovery("not appending empty playlist entry.", xbmc.LOGWARNING)
        return False
    try:
        get_music_playlist().add(file_path, discovery_playlist_item(entry))
        log_discovery(
            f"appended playlist item: label={entry.get('label')!r}, "
            f"offset={entry.get('offset')}s, file={file_path!r}"
        )
        return True
    except Exception as exc:
        log_discovery(f"could not append playlist item {file_path!r}: {exc}", xbmc.LOGERROR)
        return False


def state_playlist_position(state: dict, default: int = -1) -> int:
    try:
        value = state.get("current_playlist_position")
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def player_position() -> int:
    try:
        props = execute_jsonrpc("Player.GetProperties", {"playerid": 0, "properties": ["position"]})
        return int(props.get("position"))
    except Exception:
        return -1


def goto_music_playlist_position(position: int) -> None:
    execute_jsonrpc("Player.GoTo", {"playerid": 0, "to": int(position)})


def ensure_discovery_queue(state: dict, song_cache: list[dict]) -> tuple[dict, list[dict]]:
    queue = state.get("queue")
    if not isinstance(queue, list):
        queue = []

    excerpt_seconds = int(state.get("excerpt_seconds") or get_discovery_excerpt_seconds())
    offset_percent = int(state.get("offset_percent") or get_discovery_offset_percent())

    if not song_cache:
        song_cache = get_music_library_songs()

    log_discovery(
        f"ensuring playlist buffer: current_queue={len(queue)}, "
        f"target={DISCOVERY_BUFFER_SIZE}, song_cache={len(song_cache)}"
    )

    added = 0
    attempts = 0
    max_attempts = max(50, DISCOVERY_BUFFER_SIZE * 10)

    while len(queue) < DISCOVERY_BUFFER_SIZE and song_cache and attempts < max_attempts:
        attempts += 1
        song = choose_discovery_song(song_cache)
        entry = discovery_queue_entry(song, excerpt_seconds, offset_percent)
        if not entry.get("file"):
            continue
        if append_discovery_entry_to_playlist(entry):
            queue.append(entry)
            added += 1

    state["queue"] = queue
    state["buffer_size"] = DISCOVERY_BUFFER_SIZE
    state["refill_threshold"] = DISCOVERY_REFILL_THRESHOLD

    if added:
        log_discovery(f"playlist buffer appended {added} item(s); queue now {len(queue)}.")
    else:
        log_discovery(
            f"playlist buffer appended no items. attempts={attempts}, "
            f"song_cache={len(song_cache)}, queue={len(queue)}",
            xbmc.LOGWARNING,
        )

    return state, song_cache


def refill_discovery_playlist_if_needed(state: dict, song_cache: list[dict]) -> tuple[dict, list[dict]]:
    if not state.get("enabled") or state.get("startup_in_progress"):
        return state, song_cache

    position = player_position()
    queue = state.get("queue")
    if not isinstance(queue, list):
        queue = []

    remaining = len(queue) - position - 1 if position >= 0 else len(queue)
    if remaining >= DISCOVERY_REFILL_THRESHOLD:
        return state, song_cache

    target_len = max(DISCOVERY_BUFFER_SIZE, (position if position >= 0 else 0) + 1 + DISCOVERY_BUFFER_SIZE)
    excerpt_seconds = int(state.get("excerpt_seconds") or get_discovery_excerpt_seconds())
    offset_percent = int(state.get("offset_percent") or get_discovery_offset_percent())

    if not song_cache:
        song_cache = get_music_library_songs()

    added = 0
    while len(queue) < target_len and song_cache:
        song = choose_discovery_song(song_cache)
        entry = discovery_queue_entry(song, excerpt_seconds, offset_percent)
        if not entry.get("file"):
            continue
        if append_discovery_entry_to_playlist(entry):
            queue.append(entry)
            added += 1

    state["queue"] = queue
    if added:
        save_discovery_state(state)
        log_info(
            f"Discovery mode: appended {added} item(s) at playlist end; "
            f"remaining_future={len(queue) - position - 1 if position >= 0 else len(queue)}."
        )

    return state, song_cache


def prune_discovery_playlist_backlog(state: dict) -> dict:
    if not state.get("enabled") or state.get("startup_in_progress"):
        return state

    position = player_position()
    if position <= DISCOVERY_BACKLOG_SIZE:
        return state

    queue = state.get("queue")
    if not isinstance(queue, list):
        return state

    remove_count = position - DISCOVERY_BACKLOG_SIZE
    if remove_count <= 0:
        return state

    removed = 0
    for _i in range(remove_count):
        try:
            execute_jsonrpc("Playlist.Remove", {"playlistid": 0, "position": 0})
            removed += 1
        except Exception as exc:
            log_info(f"Discovery mode: Playlist.Remove backlog prune failed: {exc}")
            break

    if removed <= 0:
        return state

    state["queue"] = queue[removed:]
    state["current_playlist_position"] = max(0, position - removed)
    state["playlist_pruned_count"] = int(state.get("playlist_pruned_count") or 0) + removed
    save_discovery_state(state)

    log_info(
        f"Discovery mode: pruned {removed} old playlist item(s); "
        f"backlog kept={DISCOVERY_BACKLOG_SIZE}, new_position={state.get('current_playlist_position')}."
    )
    return state


def update_discovery_current_from_playlist(state: dict) -> dict:
    if not state.get("enabled"):
        return state

    position = player_position()
    queue = state.get("queue")
    if not isinstance(queue, list) or position < 0 or position >= len(queue):
        return state

    entry = queue[position]
    current_file = str(entry.get("file") or "")
    if not current_file:
        return state

    previous_file = str(state.get("current_song") or "")
    previous_position = state_playlist_position(state, -1)

    if current_file != previous_file or position != previous_position:
        state["current_song"] = current_file
        state["current_label"] = str(entry.get("label") or path_to_label(current_file))
        state["current_playlist_position"] = position
        state["current_started_ts"] = int(time.time())
        state["current_offset_seconds"] = int(entry.get("offset") or 0)
        state["current_duration_seconds"] = int(entry.get("duration") or 0)
        state["current_seek_confirmed"] = False
        state["current_startoffset_requested"] = bool(int(entry.get("offset") or 0) > 0)
        state["playlist_change_pending"] = False
        save_discovery_state(state)
        log_info(
            f"Discovery mode: current playlist item is now position={position}, "
            f"label={state.get('current_label')!r}, offset={state.get('current_offset_seconds')}s."
        )

    return state


def correct_current_playlist_offset_if_needed(state: dict) -> dict:
    if not state.get("enabled"):
        return state

    try:
        offset_seconds = int(state.get("current_offset_seconds") or 0)
    except Exception:
        offset_seconds = 0

    if offset_seconds <= 3:
        return state

    try:
        started_ts = int(state.get("current_started_ts") or 0)
    except Exception:
        started_ts = 0

    if started_ts <= 0 or int(time.time()) - started_ts < 2:
        return state

    if discovery_internal_player_change_active():
        return state

    try:
        player = xbmc.Player()
        if not player.isPlayingAudio():
            return state
        current_time = int(player.getTime() or 0)
    except Exception:
        return state

    if current_time < max(1, offset_seconds - 5):
        try:
            mark_discovery_internal_player_change(2.0)
            player.seekTime(float(offset_seconds))
            state["last_seek_correction_ts"] = int(time.time())
            state["last_seek_correction_from"] = current_time
            state["last_seek_correction_to"] = offset_seconds
            save_discovery_state(state)
            log_info(
                f"Discovery mode: corrected playlist playback position from {current_time}s "
                f"back to offset {offset_seconds}s."
            )
        except Exception as exc:
            log_info(f"Discovery mode: playlist offset correction failed: {exc}")

    return state


def start_discovery_playlist(state: dict, song_cache: list[dict]) -> tuple[dict, list[dict]]:
    log_discovery(
        f"starting playlist buffer. state_path={discovery_state_path()}, "
        f"command_path={discovery_command_path()}"
    )

    mark_discovery_internal_player_change(4.0)
    playlist = get_music_playlist()
    try:
        playlist.clear()
        log_discovery("cleared Kodi music playlist for Discovery mode.")
    except Exception as exc:
        log_discovery(f"could not clear Kodi music playlist: {exc}", xbmc.LOGWARNING)

    state["queue"] = []
    state["current_playlist_position"] = -1
    state["stopped_ts"] = 0
    state["last_error"] = ""
    state, song_cache = ensure_discovery_queue(state, song_cache)

    queue_len = len(state.get("queue") or [])
    try:
        playlist_size = playlist.size()
    except Exception:
        playlist_size = -1

    log_discovery(f"playlist buffer prepared. queue_len={queue_len}, kodi_playlist_size={playlist_size}")

    if not state.get("queue"):
        state["enabled"] = False
        state["last_error"] = "No songs found in Kodi music library or playlist buffer could not be filled."
        save_discovery_state(state)
        log_discovery(state["last_error"], xbmc.LOGERROR)
        return state, song_cache

    try:
        xbmc.Player().play(playlist)
        log_discovery("called xbmc.Player().play(playlist).")
    except Exception as exc:
        state["enabled"] = False
        state["last_error"] = f"Could not start Discovery playlist: {exc}"
        save_discovery_state(state)
        log_discovery(state["last_error"], xbmc.LOGERROR)
        return state, song_cache

    for _i in range(20):
        if xbmc.Player().isPlayingAudio():
            log_discovery("Kodi reports audio playback active after starting Discovery playlist.")
            break
        xbmc.sleep(100)
    else:
        log_discovery("Kodi did not report active audio playback within 2 seconds.", xbmc.LOGWARNING)

    state = update_discovery_current_from_playlist(state)
    state = correct_current_playlist_offset_if_needed(state)
    save_discovery_state(state)
    log_discovery(
        f"start complete. current_song={state.get('current_song')!r}, "
        f"current_label={state.get('current_label')!r}, position={state.get('current_playlist_position')}"
    )
    return state, song_cache


def advance_discovery_playlist(state: dict, song_cache: list[dict], reason: str) -> tuple[dict, list[dict]]:
    if not state.get("enabled"):
        return state, song_cache

    state, song_cache = refill_discovery_playlist_if_needed(state, song_cache)

    position = player_position()
    queue = state.get("queue") if isinstance(state.get("queue"), list) else []
    next_position = position + 1 if position >= 0 else 0

    if next_position >= len(queue):
        state, song_cache = ensure_discovery_queue(state, song_cache)
        queue = state.get("queue") if isinstance(state.get("queue"), list) else []

    if next_position < len(queue):
        mark_discovery_internal_player_change(3.0)
        try:
            goto_music_playlist_position(next_position)
            state["last_next_reason"] = reason
            state["last_next_ts"] = int(time.time())
            save_discovery_state(state)
            log_info(f"Discovery mode: advanced playlist to position {next_position} ({reason}).")
        except Exception as exc:
            log_info(f"Discovery mode: Player.GoTo next failed: {exc}")

    return update_discovery_current_from_playlist(state), song_cache


def get_music_library_songs() -> list[dict]:
    log_discovery("loading Kodi music library songs for playlist buffer.")
    params = {
        "properties": ["title", "artist", "displayartist", "album", "duration", "file"],
        "sort": {"method": "random"},
    }

    try:
        result = execute_jsonrpc("AudioLibrary.GetSongs", params)
    except Exception as exc:
        log_discovery(f"AudioLibrary.GetSongs with random sort failed: {exc}", xbmc.LOGWARNING)
        try:
            result = execute_jsonrpc(
                "AudioLibrary.GetSongs",
                {"properties": ["title", "artist", "displayartist", "album", "duration", "file"]},
            )
        except Exception as exc2:
            log_discovery(f"AudioLibrary.GetSongs fallback failed: {exc2}", xbmc.LOGERROR)
            return []

    songs = result.get("songs") or []
    usable = []
    for song in songs:
        file_path = str(song.get("file") or "").strip()
        if file_path:
            usable.append(song)

    log_discovery(f"loaded {len(usable)} usable song(s) from Kodi music library.")
    return usable


def choose_discovery_song(song_cache: list[dict]) -> dict:
    if not song_cache:
        return {}
    return random.choice(song_cache)


def jsonrpc_time_from_seconds(seconds: int) -> dict:
    seconds = max(0, int(seconds))
    hours = seconds // 3600
    seconds = seconds % 3600
    minutes = seconds // 60
    seconds = seconds % 60
    return {
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds,
        "milliseconds": 0,
    }


def seek_discovery_player_to_offset(player: xbmc.Player, offset_seconds: int, file_path: str) -> bool:
    offset_seconds = int(offset_seconds or 0)
    if offset_seconds <= 0:
        return False

    target_floor = max(1, offset_seconds - 2)

    for attempt in range(1, 13):
        try:
            if not player.isPlayingAudio():
                xbmc.sleep(200)
                continue

            player.seekTime(float(offset_seconds))
            xbmc.sleep(250)

            try:
                current_time = int(player.getTime() or 0)
            except Exception:
                current_time = 0

            if current_time >= target_floor:
                log_info(
                    f"Discovery mode: seekTime confirmed for {file_path!r}: "
                    f"target={offset_seconds}s, current={current_time}s, attempt={attempt}."
                )
                return True

            log_info(
                f"Discovery mode: seekTime not confirmed yet for {file_path!r}: "
                f"target={offset_seconds}s, current={current_time}s, attempt={attempt}."
            )
        except Exception as exc:
            log_info(f"Discovery mode: seekTime attempt {attempt} failed for {file_path!r}: {exc}")

    # Fallback: JSON-RPC seek against the music player.
    try:
        execute_jsonrpc(
            "Player.Seek",
            {
                "playerid": 0,
                "value": {"time": jsonrpc_time_from_seconds(offset_seconds)},
            },
        )
        xbmc.sleep(250)

        try:
            current_time = int(player.getTime() or 0)
        except Exception:
            current_time = 0

        if current_time >= target_floor:
            log_info(
                f"Discovery mode: JSON-RPC seek confirmed for {file_path!r}: "
                f"target={offset_seconds}s, current={current_time}s."
            )
            return True

        log_info(
            f"Discovery mode: JSON-RPC seek not confirmed for {file_path!r}: "
            f"target={offset_seconds}s, current={current_time}s."
        )
    except Exception as exc:
        log_info(f"Discovery mode: JSON-RPC seek failed for {file_path!r}: {exc}")

    return False


def get_song_duration_seconds(song: dict) -> int:
    try:
        duration = int(song.get("duration") or 0)
    except Exception:
        duration = 0

    if duration > 0:
        return duration

    song_id = song.get("songid")
    if song_id is None:
        return 0

    try:
        result = execute_jsonrpc(
            "AudioLibrary.GetSongDetails",
            {
                "songid": int(song_id),
                "properties": ["duration"],
            },
        )
        details = result.get("songdetails") or {}
        return max(0, int(details.get("duration") or 0))
    except Exception as exc:
        log_info(f"Discovery mode: could not read song duration for songid={song_id!r}: {exc}")
        return 0


def request_discovery_menu_refresh() -> None:
    state = load_discovery_state()
    state["ui_refresh_requested"] = True
    state["ui_refresh_ts"] = int(time.time())
    save_discovery_state(state)


def refresh_discovery_menu_if_visible() -> None:
    state = load_discovery_state()
    if not state.get("ui_refresh_requested"):
        return

    try:
        container_folder = xbmc.getInfoLabel("Container.FolderPath")
    except Exception:
        container_folder = ""

    if "plugin.audio.musicip" not in container_folder or "action=discovery_mode" not in container_folder:
        return

    state["ui_refresh_requested"] = False
    save_discovery_state(state)

    try:
        xbmc.executebuiltin(f"Container.Update({container_folder},replace)")
        log_info("Discovery mode: refreshed visible Discovery mode menu.")
    except Exception as exc:
        log_info(f"Discovery mode: could not refresh Discovery mode menu: {exc}")


def play_discovery_file_at_offset(file_path: str, offset_seconds: int, label: str) -> None:
    mark_discovery_internal_player_change(4.0)

    list_item = xbmcgui.ListItem(label=label, offscreen=True)
    try:
        list_item.setProperty("StartOffset", str(int(offset_seconds or 0)))
    except Exception:
        pass

    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    playlist.clear()
    playlist.add(file_path, list_item)
    xbmc.Player().play(playlist)


def start_discovery_song(song: dict, state: dict) -> dict:
    # Compatibility wrapper. Discovery mode is now playlist-buffer based.
    state["queue"] = []
    state["current_playlist_position"] = -1
    try:
        get_music_playlist().clear()
    except Exception:
        pass

    excerpt_seconds = int(state.get("excerpt_seconds") or get_discovery_excerpt_seconds())
    offset_percent = int(state.get("offset_percent") or get_discovery_offset_percent())
    entry = discovery_queue_entry(song, excerpt_seconds, offset_percent)
    state["queue"] = []
    append_discovery_entry_to_playlist(entry)
    state["queue"].append(entry)

    # Fill the rest of the buffer.
    try:
        cache = get_music_library_songs()
        state, _cache = ensure_discovery_queue(state, cache)
    except Exception:
        pass

    try:
        xbmc.Player().play(get_music_playlist())
    except Exception as exc:
        log(f"Discovery mode: could not play buffered playlist: {exc}", xbmc.LOGWARNING)
        return state

    for _i in range(20):
        if xbmc.Player().isPlayingAudio():
            break
        xbmc.sleep(100)

    state = update_discovery_current_from_playlist(state)
    state = correct_current_playlist_offset_if_needed(state)
    save_discovery_state(state)
    return state


def stop_discovery_playback(state: dict | None = None) -> dict:
    state = dict(state or load_discovery_state())
    state["enabled"] = False
    state["stopped_ts"] = int(time.time())
    state["resume_allowed"] = False
    state["startup_in_progress"] = False
    state["next_requested"] = False
    state["next_reason"] = ""
    state["pending_player_stop"] = False
    state["pending_player_stop_reason"] = ""
    state["mix_dialog_active"] = False
    state["mix_dialog_seed"] = ""
    state["mix_dialog_started_ts"] = 0
    state["mix_dialog_excerpt_seconds"] = 0
    if not state.get("stop_reason"):
        state["stop_reason"] = "manual_stop"
    save_discovery_state(state)
    try:
        xbmc.Player().stop()
    except Exception:
        pass
    return state


def handle_pending_discovery_player_stop(state: dict) -> dict:
    if not state.get("enabled") or not state.get("pending_player_stop"):
        return state

    try:
        pending_ts = int(state.get("pending_player_stop_ts") or 0)
    except Exception:
        pending_ts = 0

    if pending_ts > 0 and int(time.time()) - pending_ts < 1:
        return state

    try:
        player = xbmc.Player()
        still_playing = bool(player.isPlayingAudio())
    except Exception:
        still_playing = False

    if not still_playing:
        state["enabled"] = False
        state["stopped_ts"] = int(time.time())
        state["stop_reason"] = "player_stop"
        state["resume_allowed"] = False
        state["startup_in_progress"] = False
        state["pending_player_stop"] = False
        state["pending_player_stop_reason"] = ""
        state["next_requested"] = False
        state["next_reason"] = ""
        state["ui_refresh_requested"] = True
        state["ui_refresh_ts"] = int(time.time())
        save_discovery_state(state)
        log_info("Discovery mode stopped after confirmed Kodi player stop.")
        return state

    # In buffered playlist mode, Kodi emits player_stop-like events for
    # perfectly valid playlist transitions: manual Next, automatic GoTo(next),
    # and sometimes player-internal item changes. Do not convert such an event
    # into a second next request. Just clear it and let the playlist position
    # tracker update the current Discovery item.
    try:
        current_time = int(player.getTime() or 0)
    except Exception:
        current_time = 0

    try:
        offset_seconds = int(state.get("current_offset_seconds") or 0)
    except Exception:
        offset_seconds = 0

    state["pending_player_stop"] = False
    state["pending_player_stop_reason"] = ""

    # If Kodi restarted the item near the beginning although Discovery mode
    # expects an offset, correct the position. This also helps Previous/backlog
    # navigation when StartOffset is not applied by Kodi.
    if offset_seconds > 3 and current_time < max(1, offset_seconds - 5):
        try:
            mark_discovery_internal_player_change(2.0)
            player.seekTime(float(offset_seconds))
            state["last_seek_correction_ts"] = int(time.time())
            state["last_seek_correction_from"] = current_time
            state["last_seek_correction_to"] = offset_seconds
            save_discovery_state(state)
            log_info(
                f"Discovery mode: treated pending player_stop as playlist transition; "
                f"corrected from {current_time}s to {offset_seconds}s."
            )
        except Exception as exc:
            save_discovery_state(state)
            log_info(f"Discovery mode: pending transition seek correction failed: {exc}")
        return state

    save_discovery_state(state)
    log_info("Discovery mode: ignored pending player_stop because playback continues.")
    return state



def discovery_next_requested(state: dict) -> bool:
    return bool(state.get("enabled") and state.get("next_requested"))


def clear_discovery_next_request(state: dict) -> dict:
    state["next_requested"] = False
    state["next_reason"] = ""
    return state


def correct_discovery_seek_position(state: dict) -> None:
    if not state.get("enabled"):
        return

    try:
        offset_seconds = int(state.get("current_offset_seconds") or 0)
    except Exception:
        offset_seconds = 0

    if offset_seconds <= 3:
        return

    try:
        started_ts = int(state.get("current_started_ts") or 0)
    except Exception:
        started_ts = 0

    if started_ts <= 0 or int(time.time()) - started_ts < 4:
        return

    if discovery_internal_player_change_active():
        return

    try:
        player = xbmc.Player()
        if not player.isPlayingAudio():
            return
        current_time = int(player.getTime() or 0)
    except Exception:
        return

    # If Previous/cursor-down restarts the current song near the beginning,
    # move it back to the Discovery offset instead of letting the mode break.
    if current_time < max(1, offset_seconds - 5):
        file_path = str(state.get("current_song") or "")
        mark_discovery_internal_player_change(2.0)
        try:
            player.seekTime(float(offset_seconds))
            state["last_seek_correction_ts"] = int(time.time())
            state["last_seek_correction_from"] = current_time
            state["last_seek_correction_to"] = offset_seconds
            save_discovery_state(state)
            log_info(
                f"Discovery mode: corrected playback position from {current_time}s "
                f"back to offset {offset_seconds}s for {file_path!r}."
            )
        except Exception as exc:
            log_info(f"Discovery mode: seek correction failed: {exc}")


def discovery_player_was_stopped_by_user(state: dict) -> bool:
    if not state.get("enabled"):
        return False

    current_song = str(state.get("current_song") or "").strip()
    if not current_song:
        return False

    started_ts = int(state.get("current_started_ts") or 0)
    if started_ts <= 0:
        return False

    # Kodi needs a short grace period after Player.play() before
    # Player.isPlayingAudio() becomes reliable.
    if int(time.time()) - started_ts < 3:
        return False

    try:
        return not xbmc.Player().isPlayingAudio()
    except Exception:
        return False


def discovery_needs_next_song(state: dict) -> bool:
    if not state.get("enabled") or state.get("mix_dialog_active"):
        return False

    try:
        started_ts = int(state.get("current_started_ts") or 0)
    except Exception:
        started_ts = 0

    try:
        last_ui_next_ts = int(state.get("last_ui_next_ts") or 0)
    except Exception:
        last_ui_next_ts = 0

    if last_ui_next_ts > 0 and int(time.time()) - last_ui_next_ts < 2:
        return False

    if started_ts <= 0:
        return False

    try:
        excerpt_seconds = int(state.get("excerpt_seconds") or get_discovery_excerpt_seconds())
    except Exception:
        excerpt_seconds = get_discovery_excerpt_seconds()

    return int(time.time()) - started_ts >= excerpt_seconds


def normalize_discovery_playback_path(path: str) -> str:
    if not path:
        return ""

    try:
        value = urllib.parse.unquote(str(path))
    except Exception:
        value = str(path)

    value = value.replace("\\", "/").strip().lower()

    while "//" in value and not value.startswith("smb://"):
        value = value.replace("//", "/")

    return value


def get_current_playing_file_for_discovery() -> str:
    try:
        player = xbmc.Player()
        if not player.isPlayingAudio():
            return ""
        return str(player.getPlayingFile() or "")
    except Exception as exc:
        log_info(f"Discovery mode: could not read current playing file: {exc}")
        return ""


def current_playback_belongs_to_discovery(state: dict) -> bool:
    current_file = get_current_playing_file_for_discovery()
    if not current_file:
        return True

    current_norm = normalize_discovery_playback_path(current_file)
    if not current_norm:
        return True

    queue = state.get("queue")
    if not isinstance(queue, list) or not queue:
        return True

    discovery_files = set()
    for entry in queue:
        if not isinstance(entry, dict):
            continue
        file_path = normalize_discovery_playback_path(str(entry.get("file") or ""))
        if file_path:
            discovery_files.add(file_path)

    if current_norm in discovery_files:
        return True

    expected = normalize_discovery_playback_path(str(state.get("current_song") or ""))
    if expected and current_norm == expected:
        return True

    log_info(
        f"Discovery mode: current playback is outside Discovery queue. "
        f"current={current_file!r}, queue_size={len(discovery_files)}."
    )
    return False


def stop_discovery_due_to_external_playback(state: dict) -> dict:
    state["enabled"] = False
    state["stopped_ts"] = int(time.time())
    state["stop_reason"] = "external_playback"
    state["resume_allowed"] = False
    state["startup_in_progress"] = False
    state["mix_dialog_active"] = False
    state["mix_dialog_seed"] = ""
    state["mix_dialog_started_ts"] = 0
    state["mix_dialog_excerpt_seconds"] = 0
    state["next_requested"] = False
    state["next_reason"] = ""
    state["pending_player_stop"] = False
    state["pending_player_stop_reason"] = ""
    state["playlist_change_pending"] = False
    state["ui_refresh_requested"] = True
    state["ui_refresh_ts"] = int(time.time())
    save_discovery_state(state)
    log_info("Discovery mode stopped because playback changed outside MusicIP.")
    try:
        refresh_discovery_menu_if_visible()
    except Exception as exc:
        log_info(f"Discovery mode: could not refresh menu after external playback takeover: {exc}")
    return state


def run_discovery_tick(song_cache: list[dict]) -> list[dict]:
    command = read_discovery_command()
    state = load_discovery_state()

    if command:
        name = str(command.get("command") or "").strip().lower()
        log_discovery(
            f"processing command={name!r}, command_ts={command.get('ts')}, "
            f"state_enabled={state.get('enabled')}, stopped_ts={state.get('stopped_ts')}"
        )
        if name == "start" and (command_is_stale_for_state(command, state) or state.get("enabled") or state.get("startup_in_progress")):
            log_info("Discovery mode: ignored stale or redundant start command.")
            return song_cache

        if name == "start":
            state["enabled"] = True
            state["excerpt_seconds"] = int(command.get("excerpt_seconds") or get_discovery_excerpt_seconds())
            state["offset_percent"] = int(command.get("offset_percent") or get_discovery_offset_percent())
            state["current_started_ts"] = 0
            state["stopped_ts"] = 0
            state["current_song"] = ""
            state["current_label"] = ""
            state["current_playlist_position"] = -1
            state["stop_reason"] = ""
            state["resume_allowed"] = True
            state["next_requested"] = False
            state["next_reason"] = ""
            state["pending_player_stop"] = False
            state["pending_player_stop_reason"] = ""
            state["queue"] = []
            save_discovery_state(state)
            log_discovery("start command accepted.")
            existing_queue = state.get("queue") if isinstance(state.get("queue"), list) else []
            try:
                already_playing = bool(xbmc.Player().isPlayingAudio())
            except Exception:
                already_playing = False

            if existing_queue and already_playing:
                log_discovery(
                    f"direct-started playlist already active; adopting existing queue_len={len(existing_queue)}."
                )
                return song_cache

            log_discovery("starting playlist buffer from service.")
            state, song_cache = start_discovery_playlist(state, song_cache)
            return song_cache

        if name == "stop":
            if not state.get("stop_reason"):
                state["stop_reason"] = "manual_stop"
            state["resume_allowed"] = False
            stop_discovery_playback(state)
            return song_cache

        if name == "next":
            if state.get("enabled"):
                state, song_cache = advance_discovery_playlist(state, song_cache, "manual_next")
            return song_cache

    if state.get("startup_in_progress"):
        log_info("Discovery mode: startup in progress; service maintenance skipped.")
        return song_cache

    if not state.get("enabled"):
        return song_cache

    state = handle_pending_discovery_player_stop(state)
    if not state.get("enabled"):
        return song_cache

    if not state.get("startup_in_progress") and not current_playback_belongs_to_discovery(state):
        stop_discovery_due_to_external_playback(state)
        return song_cache

    if discovery_next_requested(state):
        state = clear_discovery_next_request(state)
        state, song_cache = advance_discovery_playlist(state, song_cache, "next_requested")
        return song_cache

    if state.get("mix_dialog_active"):
        state = handle_pending_discovery_player_stop(state)
        if not state.get("enabled"):
            return song_cache
        state = update_discovery_current_from_playlist(state)
        state, song_cache = refill_discovery_playlist_if_needed(state, song_cache)
        state = prune_discovery_playlist_backlog(state)
        state = update_discovery_current_from_playlist(state)
        state = correct_current_playlist_offset_if_needed(state)
        log_info("Discovery mode: mix dialog active; auto-skip paused.")
        return song_cache

    state = update_discovery_current_from_playlist(state)
    state, song_cache = refill_discovery_playlist_if_needed(state, song_cache)
    state = prune_discovery_playlist_backlog(state)
    state = update_discovery_current_from_playlist(state)
    state = correct_current_playlist_offset_if_needed(state)

    if discovery_player_was_stopped_by_user(state):
        state["enabled"] = False
        state["stopped_ts"] = int(time.time())
        state["stop_reason"] = "player_stop"
        state["resume_allowed"] = False
        state["ui_refresh_requested"] = True
        state["ui_refresh_ts"] = int(time.time())
        state["next_requested"] = False
        state["next_reason"] = ""
        state["pending_player_stop"] = False
        state["pending_player_stop_reason"] = ""
        save_discovery_state(state)
        log_info("Discovery mode stopped because Kodi player playback was stopped.")
        return song_cache

    if state.get("enabled") and discovery_needs_next_song(state):
        state, song_cache = advance_discovery_playlist(state, song_cache, "excerpt_elapsed")
        return song_cache

    return song_cache


def run_consistency_check() -> int:
    log_info("Consistency service check skipped in this build branch.")
    return 0


def reset_discovery_mode_on_startup() -> None:
    state = load_discovery_state()
    now = int(time.time())

    state.update({
        "enabled": False,
        "startup_in_progress": False,
        "stopped_ts": now,
        "stop_reason": "startup_reset",
        "resume_allowed": False,
        "current_started_ts": 0,
        "current_song": "",
        "current_label": "",
        "current_playlist_position": -1,
        "current_offset_seconds": 0,
        "current_duration_seconds": 0,
        "current_seek_confirmed": False,
        "current_startoffset_requested": False,
        "ui_refresh_requested": False,
        "next_requested": False,
        "next_reason": "",
        "pending_player_stop": False,
        "pending_player_stop_reason": "",
        "playlist_change_pending": False,
        "mix_dialog_active": False,
        "mix_dialog_seed": "",
        "mix_dialog_started_ts": 0,
        "mix_dialog_excerpt_seconds": 0,
        "queue": [],
        "last_error": "",
    })

    save_discovery_state(state)

    command_path = discovery_command_path()
    try:
        if xbmcvfs.exists(command_path):
            deleted = xbmcvfs.delete(command_path)
            log_discovery(f"startup reset removed stale command file. deleted={deleted!r}")
    except Exception as exc:
        log_discovery(f"startup reset could not remove stale command file: {exc}", xbmc.LOGWARNING)

    try:
        get_music_playlist().clear()
        log_discovery("startup reset cleared Kodi music playlist.")
    except Exception as exc:
        log_discovery(f"startup reset could not clear Kodi music playlist: {exc}", xbmc.LOGWARNING)

    log_discovery(
        f"startup reset completed. state_path={discovery_state_path()}, command_path={command_path}"
    )


def main() -> None:
    monitor = xbmc.Monitor()
    playback_monitor = DiscoveryPlaybackMonitor()
    last_run_ts = 0
    song_cache: list[dict] = []

    log(
        f"[{ADDON_ID}] MusicIP service started. "
        f"version={ADDON.getAddonInfo('version')}, "
        f"profile={get_profile_dir()}, "
        f"discovery_state={discovery_state_path()}, "
        f"discovery_command={discovery_command_path()}, "
        f"consistency_enabled={is_consistency_service_enabled()}, "
        f"interval={get_check_interval_seconds()} seconds.",
        xbmc.LOGINFO,
    )

    reset_discovery_mode_on_startup()

    while not monitor.abortRequested():
        try:
            refresh_discovery_menu_if_visible()
            song_cache = run_discovery_tick(song_cache)
        except Exception as exc:
            log(f"Discovery mode tick failed: {exc}", xbmc.LOGERROR)

        if is_consistency_service_enabled():
            now = int(time.time())
            interval = get_check_interval_seconds()

            if last_run_ts <= 0 or now - last_run_ts >= interval:
                run_consistency_check()
                last_run_ts = now
        else:
            log_info("Consistency service is disabled in settings.")

        if monitor.waitForAbort(1):
            break

    try:
        state = load_discovery_state()
        if state.get("enabled"):
            stop_discovery_playback(state)
    except Exception:
        pass

    log_info("MusicIP service stopped.")


if __name__ == "__main__":
    main()
