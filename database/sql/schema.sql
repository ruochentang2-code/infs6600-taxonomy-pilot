CREATE TABLE IF NOT EXISTS schema_version (version INT PRIMARY KEY);
INSERT IGNORE INTO schema_version VALUES (2);
CREATE TABLE IF NOT EXISTS course (
 course_id BIGINT AUTO_INCREMENT PRIMARY KEY,
 institution VARCHAR(100) NOT NULL DEFAULT 'University of Sydney',
 course_code VARCHAR(20) NOT NULL,
 UNIQUE(institution,course_code)
);
CREATE TABLE IF NOT EXISTS course_offering (
 offering_id BIGINT AUTO_INCREMENT PRIMARY KEY, course_id BIGINT NOT NULL, academic_year INT NOT NULL,
 session_code VARCHAR(30) NOT NULL, semester_group VARCHAR(10) NOT NULL,
 source_key VARCHAR(100) NOT NULL, delivery_code VARCHAR(30) NOT NULL, campus_code VARCHAR(30) NOT NULL,
 UNIQUE(course_id,source_key), UNIQUE(offering_id,course_id),
 FOREIGN KEY(course_id) REFERENCES course(course_id)
);
CREATE TABLE IF NOT EXISTS crawl_batch (
 batch_id BIGINT AUTO_INCREMENT PRIMARY KEY, scope_name VARCHAR(100) NOT NULL,
 scope_source_sha256 CHAR(64) NOT NULL, scope_target_year INT NOT NULL,
 kind ENUM('baseline','archive','live') NOT NULL, target_year INT NOT NULL,
 policy ENUM('prefer_s2','s2_only') NOT NULL, started_at DATETIME(6) NOT NULL,
 finished_at DATETIME(6), status ENUM('running','complete','partial','failed') NOT NULL,
 crawler_version VARCHAR(80) NOT NULL
);
CREATE TABLE IF NOT EXISTS scope_course (
 batch_id BIGINT NOT NULL, course_id BIGINT NOT NULL, level ENUM('UG','PG') NOT NULL,
 title VARCHAR(255) NOT NULL, PRIMARY KEY(batch_id,course_id),
 FOREIGN KEY(batch_id) REFERENCES crawl_batch(batch_id), FOREIGN KEY(course_id) REFERENCES course(course_id)
);
CREATE TABLE IF NOT EXISTS source_snapshot (
 snapshot_id BIGINT AUTO_INCREMENT PRIMARY KEY, offering_id BIGINT NOT NULL,
 content_sha256 CHAR(64) NOT NULL, payload_kind ENUM('html','archive_json') NOT NULL,
 source_url TEXT NOT NULL, storage_uri TEXT NOT NULL, source_retrieved_at VARCHAR(60),
 UNIQUE(offering_id,payload_kind,content_sha256),
 FOREIGN KEY(offering_id) REFERENCES course_offering(offering_id)
);
CREATE TABLE IF NOT EXISTS fetch_attempt (
 attempt_id BIGINT AUTO_INCREMENT PRIMARY KEY, batch_id BIGINT NOT NULL,
 course_id BIGINT NOT NULL, offering_id BIGINT, snapshot_id BIGINT,
 requested_url TEXT NOT NULL, final_url TEXT, attempted_at DATETIME(6) NOT NULL,
 stage ENUM('discovery','outline','archive') NOT NULL,
 status ENUM('success','http_error','network_error','parse_error','unavailable','archive_failure') NOT NULL,
 http_status INT, error TEXT, response_storage_uri TEXT,
 FOREIGN KEY(batch_id) REFERENCES crawl_batch(batch_id),
 FOREIGN KEY(course_id) REFERENCES course(course_id),
 FOREIGN KEY(offering_id,course_id) REFERENCES course_offering(offering_id,course_id),
 FOREIGN KEY(snapshot_id) REFERENCES source_snapshot(snapshot_id)
);
CREATE TABLE IF NOT EXISTS extraction_run (
 extraction_id BIGINT AUTO_INCREMENT PRIMARY KEY, snapshot_id BIGINT NOT NULL,
 parser_version VARCHAR(80) NOT NULL, normalizer_version VARCHAR(50) NOT NULL,
 extracted_at DATETIME(6) NOT NULL, title VARCHAR(255) NOT NULL,
 metadata JSON NOT NULL, UNIQUE(snapshot_id,parser_version,normalizer_version),
 FOREIGN KEY(snapshot_id) REFERENCES source_snapshot(snapshot_id)
);
CREATE TABLE IF NOT EXISTS evidence_item (
 item_id BIGINT AUTO_INCREMENT PRIMARY KEY, extraction_id BIGINT NOT NULL,
 local_key VARCHAR(30) NOT NULL, section_type VARCHAR(40) NOT NULL,
 ordinal INT NOT NULL, label TEXT NOT NULL, original_text LONGTEXT NOT NULL,
 normalized_text LONGTEXT NOT NULL, source_locator VARCHAR(200) NOT NULL,
 UNIQUE(extraction_id,local_key), UNIQUE(item_id,extraction_id),
 FOREIGN KEY(extraction_id) REFERENCES extraction_run(extraction_id)
);
CREATE TABLE IF NOT EXISTS assessment_detail (
 item_id BIGINT PRIMARY KEY, assessment_type TEXT, description TEXT,
 weight_percent DECIMAL(6,2), weight_text VARCHAR(100), due_text TEXT, length_text TEXT,
 FOREIGN KEY(item_id) REFERENCES evidence_item(item_id)
);
CREATE TABLE IF NOT EXISTS schedule_detail (
 item_id BIGINT PRIMARY KEY, week_label VARCHAR(80), topic TEXT, activity TEXT, outcome_labels TEXT,
 FOREIGN KEY(item_id) REFERENCES evidence_item(item_id)
);
CREATE TABLE IF NOT EXISTS taxonomy_version (
 taxonomy_id BIGINT AUTO_INCREMENT PRIMARY KEY, version_code VARCHAR(100) NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS category (
 category_id BIGINT AUTO_INCREMENT PRIMARY KEY, taxonomy_id BIGINT NOT NULL,
 code VARCHAR(80) NOT NULL, name VARCHAR(150) NOT NULL, definition TEXT NOT NULL,
 UNIQUE(taxonomy_id,code), UNIQUE(category_id,taxonomy_id),
 FOREIGN KEY(taxonomy_id) REFERENCES taxonomy_version(taxonomy_id)
);
CREATE TABLE IF NOT EXISTS ruleset_version (
 ruleset_id BIGINT AUTO_INCREMENT PRIMARY KEY, taxonomy_id BIGINT NOT NULL,
 version_code VARCHAR(120) NOT NULL UNIQUE, source_sha256 CHAR(64) NOT NULL,
 config_sha256 CHAR(64) NOT NULL, positive_threshold DECIMAL(12,2) NOT NULL,
 high_threshold DECIMAL(12,2) NOT NULL, policy JSON NOT NULL,
 validation_status VARCHAR(80) NOT NULL,
 UNIQUE(ruleset_id,taxonomy_id), CHECK(high_threshold>=positive_threshold),
 FOREIGN KEY(taxonomy_id) REFERENCES taxonomy_version(taxonomy_id)
);
CREATE TABLE IF NOT EXISTS scoring_rule (
 rule_id BIGINT AUTO_INCREMENT PRIMARY KEY, ruleset_id BIGINT NOT NULL,
 category_id BIGINT NOT NULL, taxonomy_id BIGINT NOT NULL,
 rule_code VARCHAR(30) NOT NULL, label VARCHAR(200) NOT NULL,
 weight DECIMAL(12,2) NOT NULL, treatment ENUM('Positive','Review only') NOT NULL,
 implementation ENUM('Active','Proposed') NOT NULL, weight_status VARCHAR(100), basis VARCHAR(200),
 UNIQUE(ruleset_id,rule_code), UNIQUE(rule_id,ruleset_id,category_id), CHECK(weight>=0),
 FOREIGN KEY(ruleset_id,taxonomy_id) REFERENCES ruleset_version(ruleset_id,taxonomy_id),
 FOREIGN KEY(category_id,taxonomy_id) REFERENCES category(category_id,taxonomy_id)
);
CREATE TABLE IF NOT EXISTS rule_phrase (
 phrase_id BIGINT AUTO_INCREMENT PRIMARY KEY, rule_id BIGINT NOT NULL,
 phrase VARCHAR(255) COLLATE utf8mb4_bin NOT NULL, UNIQUE(rule_id,phrase), UNIQUE(phrase_id,rule_id),
 FOREIGN KEY(rule_id) REFERENCES scoring_rule(rule_id)
);
CREATE TABLE IF NOT EXISTS scoring_run (
 run_id BIGINT AUTO_INCREMENT PRIMARY KEY, extraction_id BIGINT NOT NULL,
 ruleset_id BIGINT NOT NULL, taxonomy_id BIGINT NOT NULL,
 scorer_version VARCHAR(80) NOT NULL, created_at DATETIME(6) NOT NULL,
 UNIQUE(extraction_id,ruleset_id,scorer_version),
 UNIQUE(run_id,extraction_id,ruleset_id,taxonomy_id),
 FOREIGN KEY(extraction_id) REFERENCES extraction_run(extraction_id),
 FOREIGN KEY(ruleset_id,taxonomy_id) REFERENCES ruleset_version(ruleset_id,taxonomy_id)
);
CREATE TABLE IF NOT EXISTS item_category_result (
 result_id BIGINT AUTO_INCREMENT PRIMARY KEY, run_id BIGINT NOT NULL,
 extraction_id BIGINT NOT NULL, item_id BIGINT NOT NULL, ruleset_id BIGINT NOT NULL,
 taxonomy_id BIGINT NOT NULL, category_id BIGINT NOT NULL,
 score DECIMAL(12,2) NOT NULL, decision ENUM('positive','review','no_match') NOT NULL,
 confidence_band ENUM('high','moderate','review','none') NOT NULL, manual_review_required BOOLEAN NOT NULL,
 UNIQUE(run_id,item_id,category_id), UNIQUE(result_id,ruleset_id,category_id),
 CHECK(score>=0),
 FOREIGN KEY(run_id,extraction_id,ruleset_id,taxonomy_id) REFERENCES scoring_run(run_id,extraction_id,ruleset_id,taxonomy_id),
 FOREIGN KEY(item_id,extraction_id) REFERENCES evidence_item(item_id,extraction_id),
 FOREIGN KEY(category_id,taxonomy_id) REFERENCES category(category_id,taxonomy_id)
);
CREATE TABLE IF NOT EXISTS rule_match (
 match_id BIGINT AUTO_INCREMENT PRIMARY KEY, result_id BIGINT NOT NULL,
 rule_id BIGINT NOT NULL, ruleset_id BIGINT NOT NULL, category_id BIGINT NOT NULL,
 UNIQUE(result_id,rule_id), UNIQUE(match_id,rule_id),
 FOREIGN KEY(result_id,ruleset_id,category_id) REFERENCES item_category_result(result_id,ruleset_id,category_id),
 FOREIGN KEY(rule_id,ruleset_id,category_id) REFERENCES scoring_rule(rule_id,ruleset_id,category_id)
);
CREATE TABLE IF NOT EXISTS match_phrase (
 match_id BIGINT NOT NULL, rule_id BIGINT NOT NULL, phrase_id BIGINT NOT NULL,
 PRIMARY KEY(match_id,phrase_id),
 FOREIGN KEY(match_id,rule_id) REFERENCES rule_match(match_id,rule_id),
 FOREIGN KEY(phrase_id,rule_id) REFERENCES rule_phrase(phrase_id,rule_id)
);
CREATE TABLE IF NOT EXISTS review_decision (
 review_id BIGINT AUTO_INCREMENT PRIMARY KEY, result_id BIGINT NOT NULL,
 reviewer VARCHAR(150) NOT NULL, decision VARCHAR(30) NOT NULL,
 reason TEXT NOT NULL, reviewed_at DATETIME(6) NOT NULL,
 FOREIGN KEY(result_id) REFERENCES item_category_result(result_id)
);
CREATE TABLE IF NOT EXISTS analysis_selection (
 batch_id BIGINT NOT NULL, course_id BIGINT NOT NULL, run_id BIGINT,
 status ENUM('selected','missing','failed') NOT NULL, reason TEXT NOT NULL,
 PRIMARY KEY(batch_id,course_id),
 CHECK((status='selected' AND run_id IS NOT NULL) OR (status<>'selected' AND run_id IS NULL)),
 FOREIGN KEY(batch_id) REFERENCES crawl_batch(batch_id), FOREIGN KEY(course_id) REFERENCES course(course_id),
 FOREIGN KEY(run_id) REFERENCES scoring_run(run_id)
);
