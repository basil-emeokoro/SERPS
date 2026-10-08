"""Disposable Docker integration; never uses native env/data or publishes images."""
from pathlib import Path
import json
import argparse
import os
import secrets
import socket
import subprocess
import tempfile
import urllib.request
import urllib.error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reuse-api-image', help='Previously built, verified API image from this exact source; local validation recovery only.')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    output = Path(tempfile.mkdtemp(prefix='serps-cloud-check-'))
    project = 'serps-security-' + secrets.token_hex(4)
    web_port, api_port = 34000, 34080
    for port in (web_port, api_port):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', port))
    password, jwt, admin_password = (secrets.token_hex(32) for _ in range(3))
    environment = {k:v for k,v in os.environ.items() if not k.startswith(('SERPS_', 'NEXT_PUBLIC_'))}
    env_file = output/'validation.env'
    env_file.write_text('\n'.join([
        'SERPS_ENV=staging', 'SERPS_POSTGRES_PASSWORD='+password,
        'SERPS_DATABASE_URL=postgresql+psycopg://serps:'+password+'@db:5432/serps_pop',
        'SERPS_JWT_SECRET='+jwt, 'SERPS_CORS_ORIGINS=http://localhost:34000',
        'NEXT_PUBLIC_API_BASE_URL=http://localhost:34080', 'SERPS_BIND_ADDRESS=127.0.0.1',
        'SERPS_WEB_PORT=34000', 'SERPS_API_PORT=34080', 'SERPS_IMAGE_TAG='+project,
    ])+'\n')
    base = ['docker','compose','--env-file',str(env_file),'-p',project]
    def command(name, args, *, input=None, env=None, success=0):
        result = subprocess.run(base+args,cwd=repo,env=env or environment,input=input,
                                text=True,encoding='utf-8',errors='replace',stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        safe = result.stdout
        for value in (password,jwt,admin_password):safe=safe.replace(value,'[redacted]')
        (output/(name+'.log')).write_text(safe,encoding='utf-8')
        if result.returncode != success:
            raise RuntimeError(name+' failed; inspect sanitized local log '+str(output/(name+'.log')))
        print(name+': PASS',flush=True)
        return result.stdout.strip()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def request(path, data=None, token=None, origin='http://localhost:34000'):
        headers={'Origin':origin}
        if data is not None:headers['Content-Type']='application/json'
        if token:headers['Authorization']='Bearer '+token
        req=urllib.request.Request('http://127.0.0.1:34080'+path,
              data=json.dumps(data).encode() if data is not None else None,headers=headers)
        return opener.open(req,timeout=30)
    print('Validation output: '+str(output),flush=True)
    print('Project: '+project,flush=True)
    results={'project':project,'ports':[web_port,api_port]}
    started=False
    try:
        command('config',['config','--quiet'])
        if args.reuse_api_image:
            subprocess.run(['docker','image','tag',args.reuse_api_image,'serps-api:'+project], check=True,env=environment)
            print('build-api: reused verified local image',flush=True)
        else:
            command('build-api',['--progress','plain','build','api'])
        command('build-web',['--progress','plain','build','web'])
        started=True
        command('startup',['up','-d','--no-build','--wait','--wait-timeout','240'])
        results['containers']=command('containers',['ps'])
        with request('/api/v1/ready') as response:
            assert response.status==200 and response.headers['Access-Control-Allow-Origin']=='http://localhost:34000'
        with request('/api/v1/health',origin='https://not-approved.example') as response:
            assert response.headers.get('Access-Control-Allow-Origin') is None
        for path in ('/','/login'):
            with opener.open('http://127.0.0.1:34000'+path,timeout=30) as response:
                assert response.status==200
                assert response.headers['X-Content-Type-Options']=='nosniff'
        schema=command('schema',['exec','-T','api','python','-'],input="""from apps.api.app.main import app
from sqlalchemy import inspect,text
from serps_pop.infrastructure.database import Base,engine
from alembic.config import Config
from alembic.script import ScriptDirectory
with engine.connect() as db:
    assert set(db.execute(text('SELECT version_num FROM alembic_version')).scalars())==set(ScriptDirectory.from_config(Config('alembic.ini')).get_heads())
inspector=inspect(engine)
assert not set(Base.metadata.tables)-set(inspector.get_table_names())
for name,table in Base.metadata.tables.items():
    assert not set(table.columns.keys())-{col['name'] for col in inspector.get_columns(name)}
print('All model tables/columns present; migration head matches')
""")
        results['schema']=schema
        command('web-to-api',['exec','-T','web','node','-e',"fetch('http://api:8000/api/v1/ready').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"])
        command('web-content',['exec','-T','web','node','-e',"const fs=require('fs');for(const dir of ['/app','/app/apps/web'])if(fs.readdirSync(dir).some(p=>p.startsWith('.env')))process.exit(1);if(fs.existsSync('/app/node_modules/vitest')||fs.existsSync('/app/node_modules/eslint'))process.exit(1);const dir='/app/apps/web/.next/static';if(!fs.readdirSync(dir,{recursive:true}).filter(p=>p.endsWith('.js')).some(p=>fs.readFileSync(dir+'/'+p,'utf8').includes('http://localhost:34080')))process.exit(1);console.log('Public URL correct; local env and dev tools absent')"])
        bootstrap_env={**environment,'SERPS_BOOTSTRAP_CONFIRM':'fresh-database',
            'SERPS_BOOTSTRAP_INSTITUTION_CODE':'STAGE','SERPS_BOOTSTRAP_INSTITUTION_NAME':'Disposable staging fixture',
            'SERPS_BOOTSTRAP_EMAIL':'operator@example.test','SERPS_BOOTSTRAP_FULL_NAME':'Staging Operator',
            'SERPS_BOOTSTRAP_PASSWORD':admin_password}
        options=[]
        for key in bootstrap_env:
            if key.startswith('SERPS_BOOTSTRAP_'):options.extend(['-e',key])
        command('bootstrap',['exec','-T',*options,'api','python','scripts/deploy/bootstrap.py'],env=bootstrap_env)
        command('bootstrap-repeat-refused',['exec','-T',*options,'api','python','scripts/dev/seed_demo_data.py'],env=bootstrap_env,success=1)
        with request('/api/v1/auth/login',{'email':'operator@example.test','password':admin_password,'institution_code':'STAGE'}) as response:
            login=json.load(response)
        assert login['authentication_stage']=='complete'
        with request('/api/v1/auth/me',token=login['access_token']) as response:
            assert json.load(response)['roles']==['System Administrator']
        try:
            request('/api/v1/auth/login',{'email':'operator@example.test','password':'incorrect-password','institution_code':'STAGE'})
            raise AssertionError('Invalid password accepted')
        except urllib.error.HTTPError as exc:assert exc.code==401
        command('bootstrap-boundaries',['exec','-T','api','python','-'],input="""from apps.api.app.main import app
from sqlalchemy import select,func
from serps_pop.infrastructure.database import SessionLocal
from serps_pop.identity.models import Candidate,ExaminationSession,AuditLog
from serps_pop.identity_assurance.models import IdentityAssuranceProfile
with SessionLocal() as db:
    assert db.scalar(select(func.count()).select_from(Candidate))==0
    assert db.scalar(select(func.count()).select_from(ExaminationSession))==0
    assert db.scalar(select(func.count()).select_from(IdentityAssuranceProfile).where(IdentityAssuranceProfile.demo_bypass.is_(True)))==0
    assert db.scalar(select(AuditLog).where(AuditLog.action=='deployment.bootstrap')) is not None
print('No candidates, sessions or bypass; bootstrap audit present')
""")
        results['status']='PASS; physical/provider acceptance remains pending'
        (output/'results.json').write_text(json.dumps(results,indent=2))
        print(results['status'],flush=True)
    finally:
        if started:command('cleanup',['down'])
        print('Disposable volume and private validation env retained at '+str(output),flush=True)


if __name__=='__main__':
    main()
