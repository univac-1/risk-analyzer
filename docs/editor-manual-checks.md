# Timeline Editor Manual Checks

This checklist covers the editor workflow after recent fixes.

## Preconditions

- The job is completed and has risks.
- The editor page can load video and risks.

## Checks

1. Open the editor page for a completed job.
2. In the suggestions list, choose "テロップ".
3. Leave the text empty and confirm the "適用" button is disabled.
4. Enter some text and confirm "適用" works.
5. Enter negative or too-large values in mosaic/telop numeric fields.
6. Confirm the values clamp to valid ranges and do not break saves.
7. Click a suggestion range in the timeline and confirm it selects without seeking.
8. Confirm the risk graph draws left-to-right and high-risk highlights align.
9. Start export and confirm progress reaches 100% on completion.
10. While export is pending, click export again and confirm the API message is shown.
11. Download the exported file and confirm it matches the edits.
