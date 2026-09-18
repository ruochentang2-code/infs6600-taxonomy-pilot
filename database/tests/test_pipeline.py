import copy
import json
import sys
import unittest
import uuid
import tempfile
import shutil
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from pipeline import Database, ROOT, evaluate, select_url, crawl
import pymysql

def rule(weight='4',phrases=('a','b'),treatment='Positive',implementation='Active'):
    return dict(weight=weight,phrases=[dict(phrase=p) for p in phrases],treatment=treatment,implementation=implementation)

class ScoringTests(unittest.TestCase):
    def test_alternatives_count_once(self):
        self.assertEqual(evaluate('a b a b',[rule()])[0],Decimal('4'))
    def test_review_only_cannot_be_positive(self):
        self.assertEqual(evaluate('a b',[rule('6',treatment='Review only')])[1],'review')
    def test_mixed_rules_preserve_baseline(self):
        result=evaluate('a b',[rule('2',('a',)),rule('2',('b',),'Review only')])
        self.assertEqual(result[1:4],('positive','moderate',True))
    def test_proposed_excluded(self):
        self.assertEqual(evaluate('a',[rule(implementation='Proposed')])[1],'no_match')
    def test_exact_thresholds(self):
        self.assertEqual(evaluate('a',[rule('3')])[2],'moderate')
        self.assertEqual(evaluate('a',[rule('5')])[2],'high')
    def test_selection(self):
        urls=['https://www.sydney.edu.au/units/INFS6600/2026-S1C-ND-CC','https://www.sydney.edu.au/units/INFS6600/2026-S2C-NE-CC']
        self.assertEqual(select_url(urls,'prefer_s2'),urls[1])
        self.assertIsNone(select_url(urls[:1],'s2_only'))

class MySQLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global ROOT
        cls.original_root=ROOT
        cls.temp=tempfile.TemporaryDirectory(prefix='cs44-tests-')
        ROOT=Path(cls.temp.name)
        for folder in ['data','sql']:
            shutil.copytree(cls.original_root/folder,ROOT/folder)
        cls.root_patch=patch('pipeline.ROOT',ROOT)
        cls.root_patch.start()
        cls.name='cs44_test_'+uuid.uuid4().hex[:12]
        cls.db=Database(cls.name);cls.db.init();cls.db.seed()
        cls.baseline=cls.db.archive(True);cls.archive=cls.db.archive(False)
    @classmethod
    def tearDownClass(cls):
        cls.db.conn.rollback()
        cls.db.q(f'DROP DATABASE `{cls.name}`')
        cls.db.conn.close()
        cls.root_patch.stop()
        global ROOT
        ROOT=cls.original_root
        cls.temp.cleanup()
    def setUp(self): self.db=self.__class__.db
    def tearDown(self): self.db.conn.rollback()
    def test_batch_scope_preserves_history(self):
        seed,ruleset=self.db.seed()
        old=self.db.q('SELECT course_id,level,title FROM scope_course WHERE batch_id=%s ORDER BY course_id',(self.archive,))
        changed=copy.deepcopy(seed)
        changed['courses'][0]['level']='PG' if changed['courses'][0]['level']=='UG' else 'UG'
        with patch.object(self.db,'seed',return_value=(changed,ruleset)):
            later=self.db.batch('live',2027)
        self.assertEqual(self.db.q('SELECT course_id,level,title FROM scope_course WHERE batch_id=%s ORDER BY course_id',(self.archive,)),old)
        self.assertEqual(self.db.one('SELECT COUNT(*) n FROM scope_course WHERE batch_id=%s',(later,))['n'],27)
        self.assertEqual(self.db.one('SELECT target_year,scope_target_year FROM crawl_batch WHERE batch_id=%s',(later,)),{'target_year':2027,'scope_target_year':2026})
        code=changed['courses'][0]['code']
        row=self.db.one('SELECT s.level FROM scope_course s JOIN course c USING(course_id) WHERE batch_id=%s AND course_code=%s',(later,code))
        self.assertEqual(row['level'],changed['courses'][0]['level'])

    def test_offering_year_session_and_delivery_are_distinct(self):
        urls=['2025-S2C-NE-CC','2026-S1C-NE-CC','2026-S2C-NE-CC','2026-S2C-ND-CC']
        ids=[self.db.offering('INFS6600','https://www.sydney.edu.au/units/INFS6600/'+u)[1] for u in urls]
        self.assertEqual(len(set(ids)),4)
        for oid,key in zip(ids,urls):
            row=self.db.one('SELECT academic_year,session_code,semester_group,source_key FROM course_offering WHERE offering_id=%s',(oid,))
            self.assertEqual(row,dict(academic_year=int(key[:4]),session_code=key.split('-')[1],semester_group=key.split('-')[1][:2],source_key=key))
        self.assertEqual(self.db.offering('INFS6600','https://www.sydney.edu.au/units/INFS6600/'+urls[0])[1],ids[0])

    def test_seed_counts(self):
        self.assertEqual(self.db.one('SELECT COUNT(*) n FROM course')['n'],27)
        self.assertEqual(self.db.one("SELECT COUNT(*) n FROM scoring_rule WHERE implementation='Active'")['n'],36)
        self.assertEqual(self.db.one("SELECT COUNT(*) n FROM scoring_rule WHERE implementation='Proposed'")['n'],7)
    def test_baseline(self):
        self.assertIn('PASS',self.db.validate_baseline(self.baseline))
        rows=self.db.q("SELECT * FROM v_selected_course_category WHERE batch_id=%s AND course_code='INFS6600'",(self.baseline,))
        expected={'work_integrated_applied':(11,1,'49.00','2.00'),'case_based':(1,2,'4.00','5.00'),
                  'project_problem_based':(4,2,'14.50','4.00'),'entrepreneurial_learning':(0,2,'0.00','6.00')}
        for r in rows:
            self.assertEqual((int(r['positive_items']),int(r['review_items']),str(r['positive_score']),str(r['review_score'])),expected.get(r['category_code'],(0,0,'0.00','0.00')))
        self.assertEqual(len(rows),8)
    def test_baseline_has_32_items_and_256_results(self):
        run=self.db.one('SELECT run_id FROM analysis_selection WHERE batch_id=%s',(self.baseline,))['run_id']
        self.assertEqual(self.db.one('SELECT COUNT(*) n FROM item_category_result WHERE run_id=%s',(run,))['n'],256)
    def test_reimport_idempotent(self):
        tables=['course','source_snapshot','evidence_item','scoring_run','rule_match']
        before={t:self.db.one(f'SELECT COUNT(*) n FROM {t}')['n'] for t in tables}
        self.db.ingest(json.loads((ROOT/'data/infs6600_baseline.json').read_text()))
        after={t:self.db.one(f'SELECT COUNT(*) n FROM {t}')['n'] for t in tables}
        self.assertEqual(before,after)
    def test_changed_content_preserves_history(self):
        snapshot=json.loads((ROOT/'data/infs6600_baseline.json').read_text())
        snapshot['items'][0]['text']+=' Updated evidence.'
        old=self.db.one('SELECT COUNT(*) n FROM source_snapshot')['n']
        self.db.ingest(snapshot)
        self.assertEqual(self.db.one('SELECT COUNT(*) n FROM source_snapshot')['n'],old+1)
    def test_composite_fk_rejects_cross_extraction(self):
        r=self.db.one('SELECT * FROM item_category_result LIMIT 1')
        wrong=self.db.one('SELECT item_id FROM evidence_item WHERE extraction_id<>%s LIMIT 1',(r['extraction_id'],))
        with self.assertRaises(pymysql.err.IntegrityError):
            self.db.q('UPDATE item_category_result SET item_id=%s WHERE result_id=%s',(wrong['item_id'],r['result_id']))
    def test_rule_dedup_constraint(self):
        r=self.db.one('SELECT * FROM rule_match LIMIT 1');r.pop('match_id')
        with self.assertRaises(pymysql.err.IntegrityError): self.db.insert('rule_match',**r)
    def test_archive_counts_and_missing_not_negative(self):
        rows=self.db.q('SELECT * FROM v_ug_pg_analysis WHERE batch_id=%s',(self.archive,))
        for r in rows:
            self.assertEqual((r['scope_courses'],r['evaluated_courses'],r['missing_courses']),(12,11,1) if r['level']=='UG' else (15,15,0))
        missing=self.db.q("SELECT * FROM v_selected_course_category WHERE batch_id=%s AND course_code='INFS3080'",(self.archive,))
        self.assertTrue(all(r['is_positive'] is None for r in missing))
        self.assertEqual(len(self.db.q('SELECT * FROM v_failures WHERE batch_id=%s',(self.archive,))),1)
    def test_archive_category_counts(self):
        rows=self.db.q('SELECT category_code,SUM(positive_courses) n FROM v_ug_pg_analysis WHERE batch_id=%s GROUP BY category_code',(self.archive,))
        for r in rows:
            self.assertEqual(int(r['n']),{'work_integrated_applied':13,'case_based':5,'project_problem_based':9,'entrepreneurial_learning':1}.get(r['category_code'],0))
    def test_duplicate_item_rejected(self):
        s=json.loads((ROOT/'data/infs6600_baseline.json').read_text());s['items'].append(s['items'][0])
        with self.assertRaises(ValueError): self.db.ingest(s)
    def test_live_success_preserves_html(self):
        snapshot=json.loads((ROOT/'data/infs6600_baseline.json').read_text())
        original=b'<html>original-source-for-test</html>'
        def fake(url):
            if url.endswith('INFS6600'):
                return b'<a href="/units/INFS6600/2026-S2C-NE-CC">S2</a>',200,url
            if '2026-S2C-NE-CC' in url: return original,200,url
            return b'<html>No outline</html>',200,url
        with patch('pipeline.request',side_effect=fake),patch('pipeline.time.sleep'),patch('outline_parser.parse_html',return_value=snapshot):
            batch=crawl(self.db,2026,'prefer_s2',0)
        row=self.db.one("SELECT s.* FROM fetch_attempt f JOIN source_snapshot s USING(snapshot_id) WHERE f.batch_id=%s AND f.stage='outline'",(batch,))
        self.assertEqual(row['payload_kind'],'html')
        self.assertEqual((ROOT/row['storage_uri']).read_bytes(),original)
    def test_live_failures_are_durable(self):
        def fake(url):
            code=url.split('/')[4]
            if code=='INFS1000': raise HTTPError(url,503,'service unavailable',{},None)
            if code=='INFS1020': raise URLError('temporary DNS failure')
            if code=='INFS2010':
                if url.endswith(code): return f'<a href="/units/{code}/2026-S2C-ND-CC">S2</a>'.encode(),200,url
                return b'<html><h1>invalid outline</h1></html>',200,url
            return b'<html>No current outline</html>',200,url
        with patch('pipeline.request',side_effect=fake),patch('pipeline.time.sleep'):
            batch=crawl(self.db,2026,'prefer_s2',0)
        statuses={r['status'] for r in self.db.q('SELECT * FROM v_failures WHERE batch_id=%s',(batch,))}
        self.assertTrue({'http_error','network_error','parse_error','unavailable'}.issubset(statuses))
        self.assertEqual(self.db.one('SELECT COUNT(*) n FROM analysis_selection WHERE batch_id=%s',(batch,))['n'],27)
        self.assertEqual(self.db.one('SELECT status FROM crawl_batch WHERE batch_id=%s',(batch,))['status'],'failed')

if __name__=='__main__': unittest.main(verbosity=2)
