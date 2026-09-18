"""Restore the release into an empty database using a local or Docker mysql client."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from pipeline import Database, ROOT


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--docker',action='store_true',help='Use the Compose container mysql client')
    parser.add_argument('--mysql',default='mysql',help='Path to an installed mysql client')
    args=parser.parse_args()
    db=Database()
    try:
        if db.q('SHOW FULL TABLES'):
            raise SystemExit('Restore refused: target database is not empty. Choose a new CS44_DB.')
        name=db.one('SELECT DATABASE() n')['n']
    finally:
        db.conn.close()
    env=dict(os.environ)
    if args.docker:
        if os.environ.get('CS44_SOCKET') or os.environ.get('CS44_HOST','127.0.0.1') not in ['127.0.0.1','localhost'] or os.environ.get('CS44_PORT','3306')!='3307' or os.environ.get('CS44_USER','root')!='root':
            raise SystemExit('--docker requires the documented Compose connection: root at 127.0.0.1:3307 without CS44_SOCKET.')
        cmd=['docker','compose','exec','-T','db','sh','-c',
             'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql --default-character-set=utf8mb4 -u root "$1"','sh',name]
    else:
        cmd=[args.mysql,'--no-defaults','--default-character-set=utf8mb4','-u',os.environ.get('CS44_USER','root')]
        if os.environ.get('CS44_SOCKET'):cmd+=['--socket='+os.environ['CS44_SOCKET']]
        else:cmd+=['--host='+os.environ.get('CS44_HOST','127.0.0.1'),'--port='+os.environ.get('CS44_PORT','3306')]
        env['MYSQL_PWD']=os.environ.get('CS44_PASSWORD','')
        cmd+=[name]
    with (ROOT/'database.sql').open('rb') as f:subprocess.run(cmd,stdin=f,cwd=ROOT,env=env,check=True)
    print(f'Restored release into {name}. Original saved batches are 1, 2 and 3.')

if __name__=='__main__':main()
