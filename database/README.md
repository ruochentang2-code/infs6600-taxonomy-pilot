# CS-44 database integration

This module adds MySQL storage and reproducible scoring to the existing project. It preserves the original code in the repository root. The release uses eight taxonomy categories, 36 Active rules and seven stored Proposed rules. Its operational schema has 22 tables and four query views.

The saved capture covers 27 INFS courses (12 UG, 15 PG). In the 11 September 2026 capture, 26 courses have an eligible outline; INFS3080 is unavailable. The policy is **S2 preferred**, then S1, then another session in the same year. This is not a strict S2-only sample.

## 1. Set up

Run all commands below from this `database/` directory. Use Python 3.10+ (tested with 3.12.14) and MySQL 8.4. The reference database server is MySQL 8.4.11.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export CS44_PASSWORD='choose-your-own-local-password'
export CS44_HOST=127.0.0.1
export CS44_PORT=3307
export CS44_USER=root
export CS44_DB=cs44
```

With Docker Desktop or Docker Engine + Compose installed and running:

```bash
bash scripts/start_mysql.sh
```

Compose publishes MySQL only on local port 3307 and keeps data in a named volume. Changing the password environment variable does not change the password of an already initialized volume. Use the password originally chosen for that volume. `bash scripts/stop_mysql.sh` stops the service without deleting its data.

For an existing MySQL server, skip Compose and set the host, port, username and password to that server. Alternatively, set `CS44_SOCKET` to an existing local socket; it takes precedence over host/port. Unset `CS44_SOCKET` when switching back to Docker. The importer needs permission to create the target database and its tables. Integration tests create and drop randomly named `cs44_test_*` databases.

`.env.example` documents the variables. The commands above export them explicitly because Python does not automatically load a `.env` file. No MySQL installation or virtual environment is shipped in Git. Direct dependencies are pinned in `requirements.txt`; the complete tested Python 3.12 environment is recorded in `reports/tested-python312-requirements.txt`.

## 2A. Restore the saved results and query them

Choose this route to inspect the exact saved release. The target database must be empty; the wrapper refuses to overwrite an existing database.

With Compose:

```bash
python scripts/restore_backup.py --docker
```

With an installed MySQL client:

```bash
python scripts/restore_backup.py
```

Use `--mysql /path/to/mysql` if the client is not on PATH. The SQL dump uses invoker-security views and does not bind them to the original machine's root account. No MySQL user accounts or passwords are included.

Open the Compose MySQL prompt:

```bash
docker compose exec db mysql -u root -p cs44
```

Enter the local password you chose. For another target database, replace `cs44` above with its name. For an existing server, use its usual MySQL client connection.

```sql
SHOW FULL TABLES;
SELECT COUNT(*) AS courses FROM course;
SELECT batch_id, kind, target_year, policy, status FROM crawl_batch;
SELECT * FROM v_ug_pg_analysis WHERE batch_id = 3;
SELECT * FROM v_failures WHERE batch_id = 3;
SELECT * FROM v_selected_course_category
WHERE batch_id = 3 AND course_code = 'INFS6600';
```

Expected: 22 tables, four views, 27 courses, 36 Active rules, and batches 1–3. Batch 3 contains 11 evaluated UG and 15 evaluated PG courses. `partial` reflects missing or failed coverage; it does not mean the program failed to finish. A missing course remains NULL in the category view; evaluated no-match evidence scores zero.

## 2B. Rebuild from saved inputs without fetching the website

Use a **different empty database** to compare this route with the restored release:

```bash
export CS44_DB=cs44_rebuild
bash scripts/reproduce_demo.sh
```

The script runs:

```bash
python src/pipeline.py demo
python src/pipeline.py replay
```

`demo` imports scope/rules, scores the original INFS6600 baseline and the historical corpus, and asserts all eight baseline outcomes. `replay` supplies the crawler with 62 recorded HTTP responses (27 discovery pages and 35 outlines) from `data/live_fetches.json` and `data/blobs/`. It verifies each response's content hash, reruns the HTML parser and scores the extracted evidence. It does not access the website.

A fresh database produces baseline, archive and replay batches in that order. Repeated runs create new batches, so use the batch IDs printed by the program; the scripts never assume Batch 3. Unchanged snapshots and scoring runs are reused. Export any chosen batch with:

```bash
python src/pipeline.py export --batch YOUR_BATCH_ID
```

The rebuilt scores and coverage should match the saved reports. New processing times and IDs are operational metadata and are not expected to match an old run. Replay batches use the existing `live` kind because they run the HTML collection path; their exported report directory additionally contains `replay_provenance.json` identifying the frozen capture date and source batch. The original saved capture remains dated 11 September 2026.

## 3. Verify, or collect new data

```bash
bash scripts/run_checks.sh
```

This checks the input/dump manifest and runs 20 automated tests against temporary databases. Test source files are written into temporary directories, not the released dataset. Tests include rule deduplication, baseline scoring, missing data, parser/fetch failures, multi-year offerings and preservation of batch scope history.

To fetch today's public outlines instead of replaying the saved capture:

```bash
python src/pipeline.py crawl --year 2026 --policy prefer_s2
```

Use `--policy s2_only` for strict S2 selection, or change `--year`. The fixed seed still lists the same 27 INFS courses. New website content can change results; source unavailability is recorded. This command requires internet access. The release validation does not claim a new live crawl.

## Schema and files

| Group | Tables |
|---|---|
| Course and batch scope | `course`, `course_offering`, `crawl_batch`, `scope_course`, `analysis_selection` |
| Collection and extraction | `fetch_attempt`, `source_snapshot`, `extraction_run` |
| Evidence | `evidence_item`, `assessment_detail`, `schedule_detail` |
| Taxonomy and rules | `taxonomy_version`, `category`, `ruleset_version`, `scoring_rule`, `rule_phrase` |
| Scores and explanations | `scoring_run`, `item_category_result`, `rule_match`, `match_phrase` |
| Review and maintenance | `review_decision`, `schema_version` |

`course` is unique by institution/course code. `course_offering` stores year, session, semester group, delivery and campus directly, with uniqueness on `(course_id, source_key)`. Course + year + semester alone cannot distinguish all delivery versions. `crawl_batch` preserves scope metadata; `scope_course` preserves each batch's membership and UG/PG classification. The 81 saved membership rows represent three copies of the 27-course scope, not 81 different courses.

Schema v2 removes `study_scope` and `academic_term`; their information is preserved in batches and offerings. Existing v1 users can run `python scripts/migrate_v2.py` with their connection variables set and `mysqldump` on PATH. The migrator backs up first and compares unchanged records and all views. Migration uses MySQL DDL, which is not transactionally reversible; if it fails, restore its backup before retrying. Fresh installations do not need the migration.

- `sql/`: schema, four analysis views and v1-to-v2 migration.
- `src/`: import, parser, scoring and collection/replay code.
- `database.sql`: complete saved database for route 2A.
- `data/seed.json`: extracted course list, final rules, thresholds and source hashes.
- `data/scope.docx`, `data/scoring_matrix.xlsx`: source documents for that seed.
- `data/infs6600_baseline.json`, `data/corpus_archive.json`: frozen input snapshots.
- `data/taxonomy_baseline.json`: original rule configuration retained for provenance.
- `data/blobs/`: 89 source files referenced by the saved database. SQL stores relative paths and hashes; keep these files alongside the module.
- `reports/batch-1`, `batch-2`, `batch-3`: saved baseline/archive/live query outputs.
- `reports/audit.json`, `reports/verification.md`: current counts and verification scope.
- `manifest.json`: SHA-256 checksums for immutable release inputs and SQL dump. Generated reports are excluded so reruns do not invalidate the input manifest.

The root README links to this module. The original root pipeline remains a separate entry point; its files and historical outputs are not replaced by database exports.

## Interpretation and remaining work

A rule contributes its weight once per evidence item/category even if several of its phrases match. Categories are independent. Proposed rules do not score. Review-only matches never independently produce a positive decision. Scores are evidence signals from public text, not validated teaching-quality measurements.

The baseline has 32 evidence items. The archive and saved HTML extraction for INFS6600 have 40, including eight additional assessment descriptions. With the saved final rules, WIL positive/review scores are 49/2 for the baseline and 60.5/6 for the expanded input. That difference reflects input coverage and does not establish a change in teaching.

Human review records are empty. Automated views do not apply review overrides. The seed and views currently select one fixed eight-category ruleset; importing additional rule versions requires further work. These limitations are unchanged by the database integration.
