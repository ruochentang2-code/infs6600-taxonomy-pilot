"""Upgrade v1 in place after a logical backup, then verify preserved data."""
import os
import sys
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from pipeline import Database, ROOT


def snapshot(db, names):
    return {name: sorted(json.dumps(row,sort_keys=True,default=str) for row in db.q(f'SELECT * FROM `{name}`')) for name in names}


def main():
    db=Database()
    version=db.one('SELECT MAX(version) AS v FROM schema_version')['v']
    if version==2:
        print('Schema v2 already installed; no changes.'); return
    if version!=1: raise ValueError('Only schema v1 is supported')
    if db.one('SELECT COUNT(*) n FROM study_scope s WHERE NOT EXISTS (SELECT 1 FROM crawl_batch b WHERE b.scope_id=s.scope_id)')['n']:
        raise ValueError('Unreferenced study scopes exist; preserve these before migrating')
    # Refuse customized constraint layouts rather than partially applying DDL.
    for table, name, target in [('course_offering','course_offering_ibfk_2','academic_term'),('crawl_batch','crawl_batch_ibfk_1','study_scope')]:
        if not db.one('SELECT 1 FROM information_schema.key_column_usage WHERE constraint_schema=DATABASE() AND table_name=%s AND constraint_name=%s AND referenced_table_name=%s',(table,name,target)):
            raise ValueError(f'Unexpected foreign key layout on {table}')
    objects=db.q('SHOW FULL TABLES')
    names=[list(r.values())[0] for r in objects]
    stable=[n for n in names if n not in ['schema_version','course_offering','crawl_batch','scope_course','study_scope','academic_term']]
    before=snapshot(db,stable)
    scopes=db.q('SELECT b.batch_id,sc.course_id,sc.level,sc.title FROM crawl_batch b JOIN scope_course sc ON sc.scope_id=b.scope_id ORDER BY b.batch_id,sc.course_id')
    offerings=db.q('SELECT o.offering_id,o.course_id,o.source_key,o.delivery_code,o.campus_code,t.academic_year,t.session_code,t.semester_group FROM course_offering o JOIN academic_term t USING(term_id) ORDER BY o.offering_id')
    batches=db.q('SELECT b.batch_id,b.kind,b.target_year,b.policy,b.started_at,b.finished_at,b.status,b.crawler_version,s.name AS scope_name,s.source_sha256 AS scope_source_sha256,s.target_year AS scope_target_year FROM crawl_batch b JOIN study_scope s USING(scope_id) ORDER BY b.batch_id')
    exe=shutil.which('mysqldump')
    if not exe: raise RuntimeError('mysqldump is required; in Bash, source scripts/env.sh first')
    name=db.one('SELECT DATABASE() n')['n']
    backup=ROOT/'backups'/f'{name}-before-v2-{datetime.now():%Y%m%d-%H%M%S-%f}.sql'
    backup.parent.mkdir(exist_ok=True)
    cmd=[exe,'--no-defaults','--single-transaction','--skip-lock-tables','--set-gtid-purged=OFF','--no-tablespaces','-u',os.environ.get('CS44_USER','root')]
    if os.environ.get('CS44_SOCKET'): cmd += ['--socket='+os.environ['CS44_SOCKET']]
    else: cmd += ['--host='+os.environ.get('CS44_HOST','127.0.0.1'),'--port='+os.environ.get('CS44_PORT','3306')]
    env=dict(os.environ,MYSQL_PWD=os.environ.get('CS44_PASSWORD',''))
    with backup.open('wb') as f: subprocess.run(cmd+[name],stdout=f,env=env,check=True)
    print(f'Backup: {backup}',flush=True)
    db.conn.commit()
    try:
        for path in [ROOT/'sql/migrations/002_simplify.sql',ROOT/'sql/views.sql']:
            for statement in path.read_text().split(';'):
                if statement.strip(): db.q(statement)
        if snapshot(db,stable)!=before: raise AssertionError('Preserved table or view changed')
        if db.q('SELECT batch_id,course_id,level,title FROM scope_course ORDER BY batch_id,course_id')!=scopes: raise AssertionError('Scope membership changed')
        if db.q('SELECT offering_id,course_id,source_key,delivery_code,campus_code,academic_year,session_code,semester_group FROM course_offering ORDER BY offering_id')!=offerings: raise AssertionError('Offering metadata changed')
        if db.q('SELECT batch_id,kind,target_year,policy,started_at,finished_at,status,crawler_version,scope_name,scope_source_sha256,scope_target_year FROM crawl_batch ORDER BY batch_id')!=batches: raise AssertionError('Batch metadata changed')
        db.q('INSERT INTO schema_version VALUES (2)');db.conn.commit()
        print('PASS: unchanged tables and all four views match; all scope, batch and offering metadata preserved.')
    except Exception:
        print(f'Migration failed. MySQL DDL is not transactional. Restore backup before retrying: {backup}',file=sys.stderr)
        raise
    finally: db.conn.close()

if __name__=='__main__': main()
