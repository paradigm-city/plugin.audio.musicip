# -*- coding: utf-8 -*-
"""Background consistency checker for saved MusicIP mixes."""

from __future__ import annotations

import glob
import json
import os
import time

import xbmc
import xbmcaddon
import xbmcvfs


ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo("id")


def log(message: str, level: int = xbmc.LOGINFO) -> None:
    xbmc.log(f"[{ADDON_ID}] {message}", level)


def log_info(message: str) -> None:
    if get_setting_bool("service_extended_logging", False):
        log(message, xbmc.LOGINFO)


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


def get_check_interval_seconds() -> int:
    minutes = max(1, get_setting_int("consistency_interval_minutes", 60))
    return minutes * 60


def get_profile_dir() -> str:
    profile = xbmcvfs.translatePath(ADDON.getAddonInfo("profile"))
    if not xbmcvfs.exists(profile):
        xbmcvfs.mkdirs(profile)
    return profile


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


def load_mix_by_cache_path(cache_path: str) -> list[str]:
    if not xbmcvfs.exists(cache_path):
        return []

    handle = xbmcvfs.File(cache_path, "r")
    try:
        payload = handle.read()
    finally:
        handle.close()

    return [line.strip() for line in payload.splitlines() if line.strip()]


def path_to_label(path: str) -> str:
    value = (path or "").strip().rstrip("/\\")
    if not value:
        return ""
    slash_pos = max(value.rfind("/"), value.rfind("\\"))
    return value[slash_pos + 1:] if slash_pos >= 0 else value


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


def list_saved_mix_cache_paths() -> list[str]:
    pattern = os.path.join(get_profile_dir(), "mix_*.m3u")
    paths = [path for path in glob.glob(pattern) if os.path.isfile(path)]
    paths.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return paths


def track_file_exists(path: str) -> bool:
    value = str(path or "").strip()
    if not value:
        return False

    try:
        return bool(xbmcvfs.exists(value))
    except Exception:
        return False


def set_mix_consistency_metadata(cache_path: str, tracks: list[str], consistency: dict) -> bool:
    old_meta = get_saved_mix_metadata(cache_path, tracks)
    old_consistency = old_meta.get("consistency")

    new_meta = dict(old_meta)
    new_meta["track_count"] = len(tracks)
    new_meta["consistency"] = consistency

    if old_consistency == consistency:
        return False

    save_json_file(mix_meta_path_from_cache_path(cache_path), new_meta)
    return True


def analyze_mix_consistency(cache_path: str) -> bool:
    tracks = load_mix_by_cache_path(cache_path)
    missing: list[dict] = []

    for index, track in enumerate(tracks):
        if track_file_exists(track):
            continue

        missing.append({
            "index": index,
            "path": track,
        })

    consistency = {
        "status": "ok" if not missing else "inconsistent",
        "checked_ts": int(time.time()),
        "checked_tracks": len(tracks),
        "missing_files": len(missing),
        "missing": missing,
    }
    return set_mix_consistency_metadata(cache_path, tracks, consistency)


def run_consistency_check() -> int:
    cache_paths = list_saved_mix_cache_paths()
    log_info(f"Consistency check started: {len(cache_paths)} saved mix(es).")

    changed = 0
    checked_tracks = 0
    inconsistent = 0

    for cache_path in cache_paths:
        try:
            tracks = load_mix_by_cache_path(cache_path)
            checked_tracks += len(tracks)

            consistency_changed = analyze_mix_consistency(cache_path)
            meta = get_saved_mix_metadata(cache_path, tracks)
            consistency = meta.get("consistency") if isinstance(meta.get("consistency"), dict) else {}
            missing_files = int(consistency.get("missing_files") or 0)

            if missing_files > 0:
                inconsistent += 1
                log_info(
                    f"Inconsistent mix: {meta.get('label') or os.path.basename(cache_path)}, "
                    f"missing files: {missing_files}."
                )

            if consistency_changed:
                changed += 1
        except Exception as exc:
            log(f"Consistency check failed for {cache_path!r}: {exc}", xbmc.LOGERROR)

    log_info(
        f"Consistency check completed: {len(cache_paths)} mix(es), "
        f"{checked_tracks} track(s), {inconsistent} inconsistent mix(es), "
        f"{changed} metadata update(s)."
    )

    if changed:
        log_info(f"Saved-mix consistency check updated {changed} mix(es).")

    return changed


def main() -> None:
    monitor = xbmc.Monitor()
    last_run_ts = 0

    log_info(
        f"Consistency service started. Enabled={is_consistency_service_enabled()}, "
        f"interval={get_check_interval_seconds()} seconds."
    )

    while not monitor.abortRequested():
        if is_consistency_service_enabled():
            now = int(time.time())
            interval = get_check_interval_seconds()

            if last_run_ts <= 0 or now - last_run_ts >= interval:
                run_consistency_check()
                last_run_ts = now
        else:
            log_info("Consistency service is disabled in settings.")

        if monitor.waitForAbort(60):
            break

    log_info("Consistency service stopped.")


if __name__ == "__main__":
    main()
