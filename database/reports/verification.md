# Database integration verification

Verified on 13 September 2026 using a newly created Python 3.12.14 environment and MySQL 8.4.11 on macOS ARM64. Direct dependencies were installed from `requirements.txt`; resolved versions are recorded in `tested-python312-requirements.txt`.

## Checks completed

- Restored the portable `database.sql` into a separate empty database using `scripts/restore_backup.py`. All 22 table counts matched `audit.json`, and every row in the saved batch 1–3 query reports matched the restored views.
- Confirmed the restore wrapper refuses a nonempty database before importing SQL.
- Rebuilt another empty database using `demo` and `replay`, with the saved inputs and recorded HTTP responses. All eight original INFS6600 baseline outcomes matched exactly.
- Replayed all 35 saved outline HTML pages through the parser. The rebuilt database contained 62 source snapshots, 2,117 evidence items and 16,936 item/category results. All course/category decisions and scores, and all UG/PG summaries, matched the saved baseline/archive/live reports. Comparisons exclude new IDs and processing timestamps.
- The replay retained the one missing course in its failure view. Expected live/replay coverage is 11 of 12 UG and 15 of 15 PG.
- Repeated the replay. It created a new batch/report directory while reusing unchanged snapshots, evidence and scoring runs.
- All 20 automated tests passed. Source-file hashes before and after the test suite matched, confirming test artifacts no longer enter the release dataset.
- The 89 shipped blob files were selected from actual `source_snapshot` and `fetch_attempt` references; each filename hash matched its contents. Tests, logs, local backups and unused captures were excluded.
- The dump contains no fixed root DEFINER and uses SQL SECURITY INVOKER views. The shipped schema uses invoker-security views as well.

## What was not tested here

Docker is not installed on the validation machine. Compose startup and the Docker-client restore option are documented but were not executed here. Database restoration, rebuilding, replay and integration tests were run against the local MySQL 8.4.11 server. No new internet crawl was performed for this release.

These checks establish software repeatability for the frozen capture. They do not establish classification accuracy, teaching quality or the validity of scoring thresholds. Human review remains pending.

## Schema v2 provenance

On 13 September, `study_scope` was replaced by scope metadata in `crawl_batch` and per-batch membership in `scope_course`; `academic_term` was merged into `course_offering`. The existing database migration was tested on an independent copy before use. Unchanged table contents, all four view results, scope memberships, and offering/batch metadata were compared before and after migration. The former 24-table schema is now 22 tables plus four views.
