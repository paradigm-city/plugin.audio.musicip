# Testing and Quality Notes

## Discovery mode tests

Recommended tests:

1. Start Discovery mode
2. Confirm playback starts from a non-zero offset
3. Confirm the playlist is initially filled
4. Confirm no second playlist rebuild happens shortly after start
5. Confirm automatic next happens after the excerpt length
6. Confirm manual next does not double-skip
7. Confirm Stop disables Discovery mode
8. Confirm Discovery screen remains visible after start/stop/next
9. Confirm Generate mix opens parameter dialog
10. Confirm cancelling dialog resumes or skips according to dialog duration
11. Confirm confirming dialog stops Discovery and plays the generated mix
12. Confirm starting playback outside MusicIP stops Discovery mode but keeps external playback running

## Repair tests

Recommended tests:

1. Missing file with no candidate: no automatic repair
2. Moved/renamed track with unique candidate: automatic repair
3. Multiple candidates: no false automatic repair
4. Library too old: show update-library-before-repair
5. Library fresh enough: show repair option
6. Repaired mix keeps its date-group order
