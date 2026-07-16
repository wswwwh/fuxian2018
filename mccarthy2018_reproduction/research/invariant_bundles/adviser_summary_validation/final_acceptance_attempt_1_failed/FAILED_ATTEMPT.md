# Final acceptance attempt 1 — orchestration failure

- Status: **FAILED BEFORE ISOLATED BENCHMARK START**.
- Completed successfully before failure: full unit suite, authoritative benchmark check, reproduction smoke check, reproduction-target check, and `git diff --check`.
- Failure point: `isolated_worktree_add`.
- Exact exception: `NotADirectoryError: [WinError 267] The directory name is invalid`.
- Root cause: Git emits its top-level path as UTF-8, while the collector decoded it with the Windows `cp936` locale. The resulting mojibake path did not exist and was supplied as the subprocess working directory.
- Scientific interpretation: none. No isolated benchmark process started, no authoritative result file changed, and no scientific gate was evaluated from this failed attempt.
- Corrective action: decode the Git top-level path explicitly as UTF-8 and rerun from a fresh evidence directory.

The five command logs from this failed attempt are retained beside this note.
