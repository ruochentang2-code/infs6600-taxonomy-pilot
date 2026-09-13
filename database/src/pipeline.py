"""MySQL-backed, reproducible CS-44 ingestion and scoring pipeline."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urljoin
from urllib.request import Request, urlopen

import pymysql
from pymysql.cursors import DictCursor

ROOT = Path(__file__).resolve().parents[1]
SCORER = 'baseline-compatible-decimal-v1'
NORMALIZER = 'baseline-v1'
PARSER = 'outline-v1'

def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

def dumps(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def normalise(text):
    return re.sub(r'\s+', ' ', text.lower().replace('–','-').replace('—','-').replace('’',"'").replace('‘',"'")).strip()

def evaluate(text, rules, positive=Decimal('3'), high=Decimal('5')):
    text = normalise(text)
    matched = []
    for rule in rules:
        if rule['implementation'] != 'Active':
            continue
        phrases = [p for p in rule['phrases'] if normalise(p['phrase']) in text]
        if phrases:
            matched.append((rule, phrases))
    score = sum((Decimal(str(r['weight'])) for r, _ in matched), Decimal(0))
    review = any(r['treatment']=='Review only' for r,_ in matched)
    decision = 'no_match'
    if matched:
        decision = 'positive' if score >= positive and any(r['treatment']=='Positive' for r,_ in matched) else 'review'
    confidence = ('high' if score >= high else 'moderate') if decision=='positive' else ('review' if matched else 'none')
    return score, decision, confidence, review, matched

class Database:
    def __init__(self, database=None):
        name = database or os.environ.get('CS44_DB','cs44')
        if not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_]*',name):
            raise ValueError('Invalid database name')
        opts = dict(user=os.environ.get('CS44_USER','root'), password=os.environ.get('CS44_PASSWORD',''),
                    charset='utf8mb4',cursorclass=DictCursor,autocommit=False)
        if os.environ.get('CS44_SOCKET'):
            opts['unix_socket']=os.environ['CS44_SOCKET']
        else:
            opts.update(host=os.environ.get('CS44_HOST','127.0.0.1'),port=int(os.environ.get('CS44_PORT','3306')))
        self.conn=pymysql.connect(**opts)
        self.q(f'CREATE DATABASE IF NOT EXISTS `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci')
        self.conn.select_db(name)

    def q(self, sql, args=()):
        with self.conn.cursor() as cur:
            cur.execute(sql,args)
            return cur.fetchall() if cur.description else cur.lastrowid

    def one(self,sql,args=()):
        rows=self.q(sql,args)
        return rows[0] if rows else None

    def insert(self,table,**fields):
        return self.q(f"INSERT INTO {table} ({','.join(fields)}) VALUES ({','.join(['%s']*len(fields))})",tuple(fields.values()))

    def get_or_insert(self,table,key,id_col,**fields):
        where=' AND '.join(f'{k}=%s' for k in key)
        found=self.one(f'SELECT {id_col} FROM {table} WHERE {where}',tuple(key.values()))
        return found[id_col] if found else self.insert(table,**key,**fields)

    def init(self):
        if self.one("SELECT 1 FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='schema_version'"):
            version=self.one('SELECT MAX(version) AS version FROM schema_version')['version']
            if version != 2:
                raise ValueError('Schema upgrade required: run python scripts/migrate_v2.py before initialization')
        for filename in ['schema.sql','views.sql']:
            for statement in (ROOT/'sql'/filename).read_text().split(';'):
                if statement.strip(): self.q(statement)
        self.conn.commit()

    def seed(self):
        raw=(ROOT/'data/seed.json').read_bytes(); seed=json.loads(raw)
        for course in seed['courses']:
            cid=self.get_or_insert('course',{'institution':'University of Sydney','course_code':course['code']},'course_id')
        tax=self.get_or_insert('taxonomy_version',{'version_code':'cs44-eight-v1'},'taxonomy_id')
        cats={}
        for c in seed['categories']:
            cats[c['code']]=self.get_or_insert('category',{'taxonomy_id':tax,'code':c['code']},'category_id',name=c['name'],definition=c['definition'])
        version='2026-09-08-final-active-v1'
        existing=self.one('SELECT * FROM ruleset_version WHERE version_code=%s',(version,))
        if existing and existing['config_sha256']!=sha(raw):
            raise ValueError('Seed changed under an immutable ruleset version: create a new version')
        ruleset=self.get_or_insert('ruleset_version',{'version_code':version},'ruleset_id',taxonomy_id=tax,
            source_sha256=seed['matrix_sha256'],config_sha256=sha(raw),positive_threshold=seed['thresholds']['positive'],
            high_threshold=seed['thresholds']['high_confidence'],policy=dumps(seed['policies']),validation_status=seed['thresholds']['status'])
        for r in seed['rules']:
            rid=self.get_or_insert('scoring_rule',{'ruleset_id':ruleset,'rule_code':r['code']},'rule_id',category_id=cats[r['category']],taxonomy_id=tax,
                label=r['label'],weight=r['weight'],treatment=r['treatment'],implementation=r['implementation'],weight_status=r['weight_status'],basis=r['basis'])
            for phrase in r['phrases']:
                self.get_or_insert('rule_phrase',{'rule_id':rid,'phrase':phrase},'phrase_id')
        self.conn.commit()
        return seed,ruleset

    def batch(self,kind,year=2026,policy='prefer_s2'):
        seed,_=self.seed()
        batch=self.insert('crawl_batch',scope_name='CS-44 INFS',scope_source_sha256=seed['scope_sha256'],scope_target_year=2026,kind=kind,target_year=year,policy=policy,started_at=now(),status='running',crawler_version='cs44-v1')
        for course in seed['courses']:
            cid=self.one('SELECT course_id FROM course WHERE institution=%s AND course_code=%s',('University of Sydney',course['code']))['course_id']
            self.insert('scope_course',batch_id=batch,course_id=cid,level=course['level'],title=course['title'])
        self.conn.commit(); return batch

    def offering(self,code,url):
        key=urlparse(url).path.rstrip('/').split('/')[-1]
        m=re.fullmatch(r'(\d{4})-([A-Za-z0-9]+)-([A-Za-z0-9]+)-([A-Za-z0-9]+)',key)
        if not m or urlparse(url).path.split('/')[-2]!=code:
            raise ValueError(f'Invalid offering URL for {code}: {url}')
        year,session,delivery,campus=m.groups()
        semester='S2' if session.startswith('S2') else ('S1' if session.startswith('S1') else 'OTHER')
        cid=self.one('SELECT course_id FROM course WHERE course_code=%s',(code,))['course_id']
        oid=self.get_or_insert('course_offering',{'course_id':cid,'source_key':key},'offering_id',academic_year=int(year),session_code=session,semester_group=semester,delivery_code=delivery,campus_code=campus)
        return cid,oid

    def store(self,raw,suffix):
        relative=Path('data/blobs')/(sha(raw)+suffix)
        path=ROOT/relative; path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists(): path.write_bytes(raw)
        return relative.as_posix()

    def ingest(self,snapshot,raw=None):
        """Caller owns transaction: snapshot, extraction and scoring commit together."""
        if not snapshot.get('items'): raise ValueError('No evidence items extracted')
        keys=[i['item_id'] for i in snapshot['items']]
        if len(keys)!=len(set(keys)): raise ValueError('Duplicate local evidence keys')
        cid,oid=self.offering(snapshot['unit_code'],snapshot['source_url'])
        # Archive payloads are extracted JSON, never misrepresented as original HTML.
        content=raw if raw is not None else dumps({k:v for k,v in snapshot.items() if k!='retrieved_at'}).encode()
        kind='html' if raw is not None else 'archive_json'
        sid=self.get_or_insert('source_snapshot',{'offering_id':oid,'payload_kind':kind,'content_sha256':sha(content)},'snapshot_id',
            source_url=snapshot['source_url'],storage_uri=self.store(content,'.html' if raw is not None else '.json'),source_retrieved_at=snapshot.get('retrieved_at'))
        parser=PARSER if raw is not None else 'archive-import-v1'
        eid=self.get_or_insert('extraction_run',{'snapshot_id':sid,'parser_version':parser,'normalizer_version':NORMALIZER},'extraction_id',
            extracted_at=now(),title=snapshot['unit_title'],metadata=dumps({k:v for k,v in snapshot.items() if k not in ['items','teaching_staff']}))
        if not self.one('SELECT item_id FROM evidence_item WHERE extraction_id=%s LIMIT 1',(eid,)):
            for ordinal,item in enumerate(snapshot['items'],1):
                if not item['text'].strip(): raise ValueError('Empty evidence item')
                iid=self.insert('evidence_item',extraction_id=eid,local_key=item['item_id'],section_type=item['section'],ordinal=ordinal,
                    label=item['label'],original_text=item['text'],normalized_text=normalise(item['text']),source_locator=f"{item['section']}:{item['item_id']}")
                meta=item.get('metadata',{})
                if item['section']=='assessment':
                    if not meta: meta=snapshot.get('assessments',[])[int(item['item_id'][2:])-1]
                    weight=meta.get('weight',''); percent=re.fullmatch(r'(\d+(?:\.\d+)?)%',weight)
                    self.insert('assessment_detail',item_id=iid,assessment_type=meta.get('type'),description=meta.get('description'),
                        weight_percent=percent[1] if percent else None,weight_text=weight,due_text=meta.get('due'),length_text=meta.get('length'))
                elif item['section']=='weekly_schedule':
                    if not meta: meta=snapshot.get('weekly_schedule',[])[int(item['item_id'][2:])-1]
                    self.insert('schedule_detail',item_id=iid,week_label=meta.get('week'),topic=meta.get('topic'),activity=meta.get('activity'),outcome_labels=meta.get('learning_outcomes'))
        run=self.score(eid)
        return cid,oid,sid,run

    def score(self,eid):
        rs=self.one('SELECT * FROM ruleset_version WHERE version_code=%s',('2026-09-08-final-active-v1',))
        old=self.one('SELECT run_id FROM scoring_run WHERE extraction_id=%s AND ruleset_id=%s AND scorer_version=%s',(eid,rs['ruleset_id'],SCORER))
        if old: return old['run_id']
        run=self.insert('scoring_run',extraction_id=eid,ruleset_id=rs['ruleset_id'],taxonomy_id=rs['taxonomy_id'],scorer_version=SCORER,created_at=now())
        cats=self.q('SELECT * FROM category WHERE taxonomy_id=%s',(rs['taxonomy_id'],))
        rules=self.q('SELECT * FROM scoring_rule WHERE ruleset_id=%s AND implementation=%s',(rs['ruleset_id'],'Active'))
        for rule in rules: rule['phrases']=self.q('SELECT * FROM rule_phrase WHERE rule_id=%s',(rule['rule_id'],))
        for item in self.q('SELECT * FROM evidence_item WHERE extraction_id=%s ORDER BY ordinal',(eid,)):
            for cat in cats:
                score,decision,confidence,review,matched=evaluate(item['original_text'],[r for r in rules if r['category_id']==cat['category_id']],rs['positive_threshold'],rs['high_threshold'])
                result=self.insert('item_category_result',run_id=run,extraction_id=eid,item_id=item['item_id'],ruleset_id=rs['ruleset_id'],taxonomy_id=rs['taxonomy_id'],category_id=cat['category_id'],
                    score=score,decision=decision,confidence_band=confidence,manual_review_required=review)
                for rule,phrases in matched:
                    mid=self.insert('rule_match',result_id=result,rule_id=rule['rule_id'],ruleset_id=rs['ruleset_id'],category_id=cat['category_id'])
                    for phrase in phrases: self.insert('match_phrase',match_id=mid,rule_id=rule['rule_id'],phrase_id=phrase['phrase_id'])
        return run

    def attempt(self,batch,cid,url,stage,status,**kwargs):
        self.insert('fetch_attempt',batch_id=batch,course_id=cid,requested_url=url,stage=stage,status=status,attempted_at=now(),**kwargs)
        self.conn.commit()

    def select(self,batch,cid,run,status,reason):
        if run:
            valid=self.one('SELECT o.course_id,o.academic_year FROM scoring_run r JOIN extraction_run e USING(extraction_id) JOIN source_snapshot s USING(snapshot_id) JOIN course_offering o USING(offering_id) WHERE r.run_id=%s',(run,))
            b=self.one('SELECT target_year,policy FROM crawl_batch WHERE batch_id=%s',(batch,))
            if valid['course_id']!=cid or valid['academic_year']!=b['target_year']: raise ValueError('Selection identity/year mismatch')
        self.insert('analysis_selection',batch_id=batch,course_id=cid,run_id=run,status=status,reason=reason)
        self.conn.commit()

    def finish(self,batch):
        counts=self.one("SELECT COUNT(*) AS total,SUM(status='selected') AS selected FROM analysis_selection WHERE batch_id=%s",(batch,))
        selected=int(counts['selected'] or 0)
        status='complete' if selected==counts['total'] and selected else ('partial' if selected else 'failed')
        failures=self.one("SELECT COUNT(*) AS n FROM fetch_attempt WHERE batch_id=%s AND status<>'success'",(batch,))['n']
        if failures and status=='complete': status='partial'
        self.q('UPDATE crawl_batch SET status=%s,finished_at=%s WHERE batch_id=%s',(status,now(),batch));self.conn.commit()
        return status

    def archive(self,baseline=False):
        batch=self.batch('baseline' if baseline else 'archive')
        payload=json.loads((ROOT/'data'/('infs6600_baseline.json' if baseline else 'corpus_archive.json')).read_text())
        for snapshot in ([payload] if baseline else payload['units']):
            cid,oid,sid,run=self.ingest(snapshot)
            self.attempt(batch,cid,snapshot['source_url'],'archive','success',offering_id=oid,snapshot_id=sid)
            self.select(batch,cid,run,'selected','Uploaded historical snapshot; not a new HTTP fetch')
        for failure in ([] if baseline else payload['failures']):
            cid=self.one('SELECT course_id FROM course WHERE course_code=%s',(failure['unit_code'],))['course_id']
            self.attempt(batch,cid,f"https://www.sydney.edu.au/units/{failure['unit_code']}",'archive','archive_failure',error=failure['error'])
            self.select(batch,cid,None,'missing',failure['error'])
        self.finish(batch);return batch

    def export(self,batch):
        dest=ROOT/'reports'/f'batch-{batch}';dest.mkdir(parents=True,exist_ok=True)
        for view in ['v_selected_course_category','v_ug_pg_analysis','v_failures']:
            rows=self.q(f'SELECT * FROM {view} WHERE batch_id=%s',(batch,))
            (dest/(view+'.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2,default=str))
            if rows:
                with (dest/(view+'.csv')).open('w',newline='',encoding='utf-8-sig') as f:
                    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        return dest

    def validate_baseline(self,batch):
        expected={'work_integrated_applied':(11,1,Decimal('49'),Decimal('2')),
                  'case_based':(1,2,Decimal('4'),Decimal('5')),
                  'project_problem_based':(4,2,Decimal('14.5'),Decimal('4')),
                  'entrepreneurial_learning':(0,2,Decimal('0'),Decimal('6'))}
        rows=self.q("SELECT * FROM v_selected_course_category WHERE batch_id=%s AND course_code='INFS6600'",(batch,))
        if len(rows)!=8: raise ValueError('Baseline must contain eight categories')
        for r in rows:
            actual=tuple(r[k] for k in ['positive_items','review_items','positive_score','review_score'])
            if actual!=expected.get(r['category_code'],(0,0,0,0)):
                raise ValueError(f"Baseline mismatch: {r['category_code']} {actual}")
        return 'PASS: all 8 INFS6600 baseline categories exactly reproduced'

def request(url):
    req=Request(url,headers={'User-Agent':'CS44-TaxonomyResearch/1.0 (public course outlines)'})
    with urlopen(req,timeout=25) as response:
        if urlparse(response.url).hostname!='www.sydney.edu.au': raise ValueError('Unexpected redirect host')
        return response.read(),response.status,response.url

def discover(raw,code,year):
    import lxml.html
    root=lxml.html.fromstring(raw)
    links={urljoin(f'https://www.sydney.edu.au/units/{code}',x) for x in root.xpath('//a/@href')}
    return sorted(u for u in links if urlparse(u).hostname=='www.sydney.edu.au' and re.fullmatch(rf'/units/{code}/{year}-[A-Za-z0-9]+-[A-Za-z0-9]+-[A-Za-z0-9]+',urlparse(u).path))

def select_url(urls,policy):
    s2=[u for u in urls if re.search(r'/\d{4}-S2',u)]
    s1=[u for u in urls if re.search(r'/\d{4}-S1',u)]
    pool=s2 if policy=='s2_only' else (s2 or s1 or urls)
    return sorted(pool)[0] if pool else None

def crawl(db,year,policy,delay,request_fn=None):
    request_fn = request if request_fn is None else request_fn
    from outline_parser import parse_html
    batch=db.batch('live',year,policy)
    courses=db.q('SELECT c.course_id,c.course_code FROM course c JOIN scope_course s USING(course_id) WHERE s.batch_id=%s ORDER BY c.course_code',(batch,))
    try:
        for c in courses:
            cid,code=c['course_id'],c['course_code'];base=f'https://www.sydney.edu.au/units/{code}'
            try:
                raw,http,final=request_fn(base)
                storage=db.store(raw,'.html');urls=discover(raw,code,year)
                db.attempt(batch,cid,base,'discovery','success',http_status=http,final_url=final,response_storage_uri=storage)
            except (HTTPError,URLError,TimeoutError,OSError,ValueError) as exc:
                status='http_error' if isinstance(exc,HTTPError) else 'network_error'
                db.attempt(batch,cid,base,'discovery',status,http_status=getattr(exc,'code',None),error=str(exc))
                db.select(batch,cid,None,'failed',f'Discovery failed: {exc}');continue
            chosen=select_url(urls,policy);chosen_run=None;errors=[]
            # Keep every discovered offering. Selection is a separate research decision.
            for url in urls:
                time.sleep(delay);raw=None;http=None;final=None;storage=None;stage='fetch'
                try:
                    raw,http,final=request_fn(url);storage=db.store(raw,'.html');stage='parse'
                    if urlparse(final).path!=urlparse(url).path: raise ValueError('Redirect changed offering identity')
                    snapshot=parse_html(url,raw.decode('utf-8',errors='replace'))
                    if snapshot['unit_code']!=code: raise ValueError('Outline course mismatch')
                    cid,oid,sid,run=db.ingest(snapshot,raw=raw)
                    db.attempt(batch,cid,url,'outline','success',offering_id=oid,snapshot_id=sid,http_status=http,final_url=final,response_storage_uri=storage)
                    if url==chosen: chosen_run=run
                except (HTTPError,URLError,TimeoutError,OSError,ValueError,IndexError,KeyError) as exc:
                    db.conn.rollback();status='parse_error' if stage=='parse' else ('http_error' if isinstance(exc,HTTPError) else 'network_error')
                    db.attempt(batch,cid,url,'outline',status,http_status=http or getattr(exc,'code',None),error=str(exc),final_url=final,response_storage_uri=storage)
                    errors.append(f'{url}: {exc}')
            if chosen_run:
                db.select(batch,cid,chosen_run,'selected',f'{policy}; lexical source-key tie-break; selected {chosen}; {len(urls)} offering(s) discovered')
            else:
                reason='; '.join(errors) if chosen else f'No {year} outline satisfying {policy}'
                if not chosen: db.attempt(batch,cid,base,'discovery','unavailable',error=reason)
                db.select(batch,cid,None,'failed' if chosen else 'missing',reason)
            print(f'{code}: {len(urls)} offerings, selected={bool(chosen_run)}',flush=True)
    except BaseException:
        db.conn.rollback()
        db.q("UPDATE crawl_batch SET status='failed',finished_at=%s WHERE batch_id=%s",(now(),batch));db.conn.commit()
        raise
    db.finish(batch);return batch

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['init','demo','crawl','replay','export']);p.add_argument('--year',type=int,default=2026)
    p.add_argument('--policy',choices=['prefer_s2','s2_only'],default='prefer_s2');p.add_argument('--delay',type=float,default=0.3);p.add_argument('--batch',type=int)
    args=p.parse_args();db=Database();db.init();db.seed()
    if args.command=='demo':
        for baseline in [True,False]:
            batch=db.archive(baseline)
            if baseline: print(db.validate_baseline(batch))
            print(f'Imported batch {batch}; reports: {db.export(batch)}')
    elif args.command=='replay':
        saved=json.loads((ROOT/'data/live_fetches.json').read_text())
        responses={r['requested_url']:r for r in saved['responses']}
        def cached_request(url):
            if url not in responses: raise ValueError(f'URL not in frozen capture: {url}')
            row=responses[url]
            path=ROOT/row['response_storage_uri']
            raw=path.read_bytes()
            if sha(raw)!=path.stem: raise ValueError(f'Source checksum mismatch: {path.name}')
            return raw,row['http_status'],row['final_url']
        batch=crawl(db,saved['year'],saved['policy'],0,request_fn=cached_request)
        destination=db.export(batch)
        (destination/'replay_provenance.json').write_text(json.dumps({'mode':'offline_replay','capture_date':saved['collected_at'],'source_batch':saved['source_batch'],'replay_batch':batch},indent=2))
        print(f'Offline replay of {saved["collected_at"]} capture; batch {batch}; reports: {destination}')
    elif args.command=='crawl':
        batch=crawl(db,args.year,args.policy,max(args.delay,0.1));print(f'Live batch {batch}; reports: {db.export(batch)}')
        if db.one('SELECT status FROM crawl_batch WHERE batch_id=%s',(batch,))['status']=='failed': raise SystemExit(2)
    elif args.command=='export':
        if args.batch is None: p.error('--batch is required')
        print(db.export(args.batch))
    db.conn.close()

if __name__=='__main__': main()
