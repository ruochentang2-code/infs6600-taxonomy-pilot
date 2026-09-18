ALTER TABLE course_offering ADD academic_year INT, ADD session_code VARCHAR(30), ADD semester_group VARCHAR(10);
UPDATE course_offering o JOIN academic_term t ON t.term_id=o.term_id SET o.academic_year=t.academic_year,o.session_code=t.session_code,o.semester_group=t.semester_group;
ALTER TABLE course_offering MODIFY academic_year INT NOT NULL, MODIFY session_code VARCHAR(30) NOT NULL, MODIFY semester_group VARCHAR(10) NOT NULL;
ALTER TABLE crawl_batch ADD scope_name VARCHAR(100), ADD scope_source_sha256 CHAR(64), ADD scope_target_year INT;
UPDATE crawl_batch b JOIN study_scope s ON s.scope_id=b.scope_id SET b.scope_name=s.name,b.scope_source_sha256=s.source_sha256,b.scope_target_year=s.target_year;
ALTER TABLE crawl_batch MODIFY scope_name VARCHAR(100) NOT NULL, MODIFY scope_source_sha256 CHAR(64) NOT NULL, MODIFY scope_target_year INT NOT NULL;
CREATE TABLE scope_course_v2 (
 batch_id BIGINT NOT NULL, course_id BIGINT NOT NULL, level ENUM('UG','PG') NOT NULL,
 title VARCHAR(255) NOT NULL, PRIMARY KEY(batch_id,course_id),
 FOREIGN KEY(batch_id) REFERENCES crawl_batch(batch_id), FOREIGN KEY(course_id) REFERENCES course(course_id)
);
INSERT INTO scope_course_v2 SELECT b.batch_id,sc.course_id,sc.level,sc.title FROM crawl_batch b JOIN scope_course sc ON sc.scope_id=b.scope_id;
DROP VIEW v_ug_pg_analysis;
DROP VIEW v_selected_course_category;
DROP TABLE scope_course;
RENAME TABLE scope_course_v2 TO scope_course;
ALTER TABLE course_offering DROP FOREIGN KEY course_offering_ibfk_2;
ALTER TABLE course_offering DROP COLUMN term_id;
ALTER TABLE crawl_batch DROP FOREIGN KEY crawl_batch_ibfk_1;
ALTER TABLE crawl_batch DROP COLUMN scope_id;
DROP TABLE academic_term;
DROP TABLE study_scope;
