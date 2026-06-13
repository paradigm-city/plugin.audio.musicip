# Mix Consistency and Repair Concept

## Problem

Saved mixes reference file paths. Those files may later be moved, renamed, deleted, or changed outside Kodi.

This causes storage-level inconsistency: the saved mix contains missing file paths.

## Consistency sidecar

Each saved mix has sidecar metadata. The consistency section records:

- current consistency status
- check timestamp
- missing files
- first missing timestamp per track
- first inconsistent timestamp
- last inconsistency change timestamp
- missing signature

## Library freshness

Automatic repair depends on Kodi's library being recent enough.

The repair readiness check compares the first inconsistency timestamp with the freshest known Kodi music library timestamp.

If the library is not recent enough, the add-on does not offer auto-repair and tells the user to update the library first.

## Auto-repair

Auto-repair is allowed only when:

- the mix is inconsistent
- the Kodi library freshness is known
- the library is newer than the first detected inconsistency
- a unique, high-confidence repair candidate is found

If the result is ambiguous, automatic repair must not guess.
