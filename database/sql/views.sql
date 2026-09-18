CREATE OR REPLACE SQL SECURITY INVOKER VIEW v_offering_category AS
SELECT r.run_id,r.category_id,
 SUM(r.decision='positive') AS positive_items,
 SUM(r.decision='review') AS review_items,
 SUM(CASE WHEN r.decision='positive' THEN r.score ELSE 0 END) AS positive_score,
 SUM(CASE WHEN r.decision='review' THEN r.score ELSE 0 END) AS review_score,
 MAX(r.decision='positive') AS is_positive
FROM item_category_result r GROUP BY r.run_id,r.category_id;

CREATE OR REPLACE SQL SECURITY INVOKER VIEW v_selected_course_category AS
SELECT b.batch_id,b.kind,b.target_year,b.policy,c.course_code,sc.level,
 a.status AS selection_status,a.reason,a.run_id,k.category_id,k.code AS category_code,k.name AS category,
 o.academic_year,o.semester_group,o.source_key,ss.source_retrieved_at,
 rs.version_code AS ruleset_version,
 v.positive_items,v.review_items,v.positive_score,v.review_score,v.is_positive
FROM crawl_batch b
JOIN scope_course sc ON sc.batch_id=b.batch_id
JOIN course c ON c.course_id=sc.course_id
JOIN category k ON k.taxonomy_id=(SELECT taxonomy_id FROM taxonomy_version WHERE version_code='cs44-eight-v1')
LEFT JOIN analysis_selection a ON a.batch_id=b.batch_id AND a.course_id=c.course_id
LEFT JOIN scoring_run sr ON sr.run_id=a.run_id
LEFT JOIN ruleset_version rs ON rs.ruleset_id=sr.ruleset_id
LEFT JOIN extraction_run e ON e.extraction_id=sr.extraction_id
LEFT JOIN source_snapshot ss ON ss.snapshot_id=e.snapshot_id
LEFT JOIN course_offering o ON o.offering_id=ss.offering_id
LEFT JOIN v_offering_category v ON v.run_id=a.run_id AND v.category_id=k.category_id
WHERE b.kind<>'baseline' OR a.course_id IS NOT NULL;

CREATE OR REPLACE SQL SECURITY INVOKER VIEW v_ug_pg_analysis AS
SELECT batch_id,kind,target_year,policy,level,category_code,category,
 COUNT(*) AS scope_courses,COUNT(run_id) AS evaluated_courses,
 COUNT(*)-COUNT(run_id) AS missing_courses,
 COALESCE(SUM(is_positive),0) AS positive_courses,
 COALESCE(SUM(positive_items),0) AS positive_items,
 COALESCE(SUM(review_items),0) AS review_items,
 ROUND(100.0*SUM(is_positive)/NULLIF(COUNT(run_id),0),2) AS positive_pct_evaluated
FROM v_selected_course_category
GROUP BY batch_id,kind,target_year,policy,level,category_code,category;

CREATE OR REPLACE SQL SECURITY INVOKER VIEW v_failures AS
SELECT f.attempt_id,f.batch_id,b.kind,c.course_code,f.stage,f.status,f.http_status,f.error,f.requested_url
FROM fetch_attempt f JOIN course c ON c.course_id=f.course_id JOIN crawl_batch b ON b.batch_id=f.batch_id
WHERE f.status<>'success';
