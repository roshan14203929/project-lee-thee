#!/usr/bin/env python3
"""Python lifecycle controller for Layerlift project artifacts."""
from __future__ import annotations
import copy, hashlib, json, re, shutil, sys, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse, urlunparse, parse_qs

ROOT=Path(__file__).resolve().parent.parent; PROJECTS=ROOT/'projects'; ID=re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$'); TERMINAL={'COMPLETED','NEEDS_REVIEW','FAILED'}; QA=('content','ui','accessibility','technical'); PAYLOAD=['base.css','images','index.html','page.css']; TRANS={'CREATED':{'BUILDING','FAILED'},'BUILDING':{'VERIFYING','FAILED'},'VERIFYING':{'REFINING','COMPLETED','NEEDS_REVIEW','FAILED'},'REFINING':{'VERIFYING','NEEDS_REVIEW','FAILED'}}
COMPACT_OUT={'inventory','spec-compact'}
def bad(s): raise ValueError(s)
def replace_atomic(t,f,tries=8):
 # On Windows an antivirus scanner or the search indexer can briefly hold a
 # freshly written .tmp, so the atomic replace intermittently raises
 # PermissionError (WinError 5). The write itself already succeeded, so retry
 # briefly rather than fail a run for a transient lock.
 for i in range(tries):
  try:return t.replace(f)
  except PermissionError:
   if i==tries-1:raise
   time.sleep(0.05*(i+1))
def now(): return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')
def dump(v,compact=False): return json.dumps(v,ensure_ascii=False,indent=None if compact else 2,separators=(',',':') if compact else None)
def sha(v): return hashlib.sha256(dump(v,True).encode()).hexdigest()
def gcache(a,role,h):d=prj(a)/'.guideline-cache';d.mkdir(exist_ok=True);return d/f"{role or 'all'}-{h}.md"
def safe(v,label='identifier'):
 if not v or not ID.fullmatch(str(v)): bad(f"Invalid {label}: {v if v is not None else '<missing>'}")
 return str(v)
def sid(v):
 if not isinstance(v,str) or not re.fullmatch(r'source-\d{3,}',v): bad(f"Invalid source identifier: {v if v is not None else '<missing>'}")
 return v
def rid(v):
 if not isinstance(v,str) or not re.fullmatch(r'run-\d{3,}',v): bad(f"Invalid run identifier: {v if v is not None else '<missing>'}")
 return v
def extref(v):
 parts=str(v).split('/')
 if len(parts)!=4:bad(f"Invalid external reference (expected project/page/run/candidate): {v}")
 xa,xb,xr,xc=parts
 return safe(xa,'source project identifier'),safe(xb,'source page identifier'),rid(xr),safe(xc,'source candidate identifier')
def opts(v):
 p=[];o={};i=0
 while i<len(v):
  if not v[i].startswith('--'): p.append(v[i]);i+=1;continue
  k=v[i][2:]; x=v[i+1] if i+1<len(v) else None
  if x is None or x.startswith('--'): o[k]=True
  else: o[k]=[*o[k],x] if isinstance(o.get(k),list) else ([o[k],x] if k in o else x);i+=1
  i+=1
 return p,o
def vals(v): return [] if v is None else (v if isinstance(v,list) else [v])
def prj(a): return PROJECTS/safe(a,'project identifier')
def page(a,b): return prj(a)/'pages'/safe(b,'page identifier')
def src(a,b,c): return page(a,b)/'sources'/sid(c)
def run(a,b,c): return page(a,b)/'runs'/rid(c)
def read(f): return json.loads(Path(f).read_text(encoding='utf8'))
def write(f,v):
 f=Path(f);f.parent.mkdir(parents=True,exist_ok=True); t=f.with_name(f.name+'.tmp');t.write_text(dump(v)+'\n',encoding='utf8');replace_atomic(t,f)
def update(f,fn):
 v=fn(copy.deepcopy(read(f)));write(f,v);return v
def cp(a,b):
 a=Path(a);b=Path(b)
 if a.is_dir(): shutil.copytree(a,b,dirs_exist_ok=True)
 else: b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a,b)
def specbase(a,b,c):
 d=src(a,b,c)/'spec';m=d/'manifest.json'
 if (d/'spec.json').exists():return d
 if m.exists():return src(a,b,read(m)['baseSourceId'])/'spec'
 return d
def rm(a):
 a=Path(a)
 if a.is_dir(): shutil.rmtree(a,ignore_errors=True)
 else: a.unlink(missing_ok=True)
def numbered(d,p):
 n=[int(m.group(1)) for x in Path(d).glob(f'{p}-*') if x.is_dir() and (m:=re.fullmatch(re.escape(p)+r'-(\d+)',x.name))]; return f'{p}-{max(n,default=0)+1:03d}'
def jcr_paths(spec):
 ap=Path(spec['articlePath']);html_rel=Path('content')/spec['contentRoot']/f"{spec['articlePath']}.html";assets_rel=Path('content')/'dam'/spec['damRoot']/ap;css_dir=Path('etc')/'designs'/'code'/spec['cssRoot']/ap
 return html_rel,assets_rel,css_dir/'base.css',css_dir/'page.css',css_dir
def dam_prefix(spec):return f"/content/dam/{spec['damRoot']}/{spec['articlePath']}/"
def css_prefix(spec):return f"/etc/designs/code/{spec['cssRoot']}/{spec['articlePath']}/"
def payload(d,label,spec,ignore=('candidate.json','structural-check','_conversion-input')):
 d=Path(d)
 if spec['kind']=='flat':
  for x in PAYLOAD:
   if not(d/x).exists():bad(f'{label} is missing {x}.')
  found=sorted(x.name for x in d.iterdir() if x.name not in ignore)
  if found!=PAYLOAD:bad(f"{label} must contain exactly: {', '.join(PAYLOAD)}. Found: {', '.join(found)}.")
  return
 html_rel,assets_rel,base_rel,page_rel,css_dir=jcr_paths(spec)
 for rel,what in ((html_rel,'article HTML'),(base_rel,'base.css'),(page_rel,'page.css')):
  if not (d/rel).is_file():bad(f'{label} is missing {rel.as_posix()} ({what}).')
 if not (d/assets_rel).is_dir():bad(f'{label} is missing {assets_rel.as_posix()}/ (DAM asset directory).')
 allowed_files={html_rel,base_rel,page_rel};allowed_dirs={p for rel in (html_rel,assets_rel,base_rel,page_rel) for p in rel.parents if p!=Path('.')}|{assets_rel}
 stray=[]
 for x in sorted(d.rglob('*')):
  rel=x.relative_to(d)
  if rel.parts[0] in ignore:continue
  if rel==assets_rel or assets_rel in rel.parents:continue
  if x.is_dir():
   if rel not in allowed_dirs:stray.append(rel.as_posix()+'/')
  elif rel not in allowed_files:stray.append(rel.as_posix())
 if stray:bad(f"{label} contains unexpected entries not part of the JCR payload: {', '.join(stray)}.")
def figurl(v):
 q=urlparse(str(v));
 if q.scheme!='https' or not(q.hostname=='figma.com' or (q.hostname or '').endswith('.figma.com')): bad(f'Figma URL must use HTTPS on figma.com: {v}')
 return urlunparse(q)
def node(v):
 m=re.fullmatch(r'(\d+)[-:](\d+)',unquote(str(v or '')).strip())
 if not m: bad(f"Invalid Figma node identifier: {v if v is not None else '<missing>'}")
 return f'{m.group(1)}:{m.group(2)}'
def identity(v):
 q=urlparse(figurl(v));m=re.match(r'^/(?:design|file)/([^/]+)',q.path);n=parse_qs(q.query).get('node-id')
 if not m: bad(f'Figma URL must contain a design or file key: {v}')
 if not n: bad(f'Figma URL must contain node-id: {v}')
 return {'fileKey':m.group(1),'nodeId':node(n[0])}
def fp(variants): return sha(sorted(({'label':v['label'],**identity(v['url'])} for v in variants),key=lambda x:x['label']))
def require_page(a,b):
 if not (prj(a)/'project.json').exists(): bad(f'Project does not exist: {a}')
 if not (page(a,b)/'page.json').exists(): bad(f'Page does not exist: {a}/{b}')
 return page(a,b)
def sources(a,b):
 d=page(a,b)/'sources';return sorted([read(x/'source.json') for x in d.glob('source-*') if (x/'source.json').exists()],key=lambda x:x['id']) if d.exists() else []
def stored_fp(s):
 if s.get('fingerprint'):return s['fingerprint']
 vs=(s.get('figma') or {}).get('variants') or []
 return fp(vs) if all(x.get('label') and x.get('url') for x in vs) else None
def mutable(a,b,c):
 v=read(run(a,b,c)/'run.json')
 if v['status'] in TERMINAL: bad(f"Run {c} is immutable because it is {v['status']}. Start a new run.")
 return v
STATED=ROOT/'.claude'/'state';ACTIVE=STATED/'active-run.json'
def active(**kw):
 """Record the active run so the SubagentStop audit hook can attribute events."""
 try:
  if kw.get('status') in TERMINAL:ACTIVE.unlink(missing_ok=True);return
  cur=json.loads(ACTIVE.read_text(encoding='utf8')) if ACTIVE.exists() else {}
  if not isinstance(cur,dict):cur={}
  ACTIVE.parent.mkdir(parents=True,exist_ok=True);t=ACTIVE.with_suffix('.json.tmp')
  t.write_text(dump({**cur,**{k:v for k,v in kw.items() if v is not None},'updatedAt':now()})+'\n',encoding='utf8');replace_atomic(t,ACTIVE)
 except Exception:pass
def transition(a,b,c,status,extra={}):
 f=run(a,b,c)/'run.json'
 def fn(x):
  if x['status'] in TERMINAL: bad(f"Run {c} is immutable because it is {x['status']}.")
  if status not in TRANS.get(x['status'],set()): bad(f"Invalid run transition {x['status']} -> {status}.")
  at=now();x['status']=status;x['completedAt']=at if status in TERMINAL else None;x['events'].append({'at':at,'type':'status','status':status,**extra});return x
 v=update(f,fn);active(project=a,page=b,run=c,status=status);return v
def checkplatform(v):
 if v is None or v is True:return None
 v=str(v).strip().lower()
 if v not in PLATFORM_DIR:bad(f"Unknown platform: {v}. Use one of: {', '.join(sorted(PLATFORM_DIR))}.")
 return v
PATHFRAG=re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*(?:/[A-Za-z0-9][A-Za-z0-9._-]*)*$')
def pathfrag(v,label):
 v=str(v).strip()
 if not v or not PATHFRAG.fullmatch(v):bad(f"Invalid {label}: {v or '<empty>'}")
 return v
DELIVERY_FLAGS=(('content-root','contentRoot'),('dam-root','damRoot'),('css-root','cssRoot'))
DEFAULT_TEMPLATE='1column'
def template_id(v):
 v=pathfrag(v,'--template')
 root=ROOT/'delivery-templates'/'medichannel'
 if not (root/v/'shell.html').exists():
  avail=sorted(p.name for p in root.iterdir() if (p/'shell.html').exists()) if root.exists() else []
  bad(f"Unknown MediChannel delivery template: {v}. Available: {', '.join(avail) or '<none>'}.")
 return v
def delivery_overrides(o):
 out={}
 for flag,key in DELIVERY_FLAGS:
  if flag in o:
   if o[flag] is True:bad(f"--{flag} requires a value.")
   out[key]=pathfrag(o[flag],f'--{flag}')
 if 'template' in o:
  if o['template'] is True:bad('--template requires a value.')
  out['template']=template_id(o['template'])
 return out
def require_delivery(d):
 # Content/dam/css roots are per-engagement JCR paths. A default would
 # silently publish one client's build into another client's content tree.
 # The delivery template has a safe default -- it's a shared shell, not a
 # per-engagement path -- so it's the one field that's optional here.
 missing=[f'--{flag}' for flag,key in DELIVERY_FLAGS if not d.get(key)]
 if missing:bad(f"A medichannel project requires {', '.join(missing)} with no default.")
 return {**{key:d[key] for flag,key in DELIVERY_FLAGS},'template':d.get('template') or DEFAULT_TEMPLATE}
def init_project(a,name,o=None):
 d=prj(a)
 if d.exists(): bad(f'Project already exists: {a}')
 o=o or {};pf=checkplatform(o.get('platform'));overrides=delivery_overrides(o)
 if overrides and pf!='medichannel':bad('--content-root/--dam-root/--css-root require --platform medichannel.')
 delivery=require_delivery(overrides) if pf=='medichannel' else None
 t=now();(d/'guidelines').mkdir(parents=True);(d/'pages').mkdir();write(d/'project.json',{'id':a,'name':name or a,'description':'','platform':pf,'delivery':delivery,'createdAt':t,'updatedAt':t});return {'projectId':a,'root':str(d),'platform':pf,'delivery':delivery}
def setplatform(a,o):
 f=prj(a)/'project.json'
 if not f.exists():bad(f'Project does not exist: {a}')
 pf=checkplatform(o.get('platform'))
 if pf is None:bad(f"set-platform requires --platform <{'|'.join(sorted(PLATFORM_DIR))}>.")
 overrides=delivery_overrides(o)
 if overrides and pf!='medichannel':bad('--content-root/--dam-root/--css-root require --platform medichannel.')
 def fn(x):
  delivery=require_delivery({**(x.get('delivery') or {}),**overrides}) if pf=='medichannel' else None
  return {**x,'platform':pf,'delivery':delivery,'updatedAt':now()}
 v=update(f,fn);return {'projectId':a,'platform':pf,'delivery':v.get('delivery'),'guidelines':sorted({p.relative_to(ROOT).as_posix() for p in platform_files('builder',pf)+platform_files('ui',pf)+coding_files('builder')+coding_files('ui')})}
def init_page(a,b,name,o=None):
 require_page_base=prj(a)
 if not (require_page_base/'project.json').exists(): bad(f'Project does not exist: {a}')
 o=o or {};d=page(a,b)
 if d.exists():bad(f'Page already exists: {a}/{b}')
 plat=platform_of(a);ap=o.get('article-path')
 if plat=='medichannel':
  if not ap or ap is True:bad('init-page requires --article-path <path> for a medichannel project.')
  ap=pathfrag(ap,'--article-path')
 elif ap is not None:bad('--article-path only applies to medichannel projects.')
 for x in ('guidelines','sources','runs','releases'):(d/x).mkdir(parents=True,exist_ok=True)
 t=now();write(d/'page.json',{'id':b,'name':name or b,'status':'DRAFT','currentSourceId':None,'currentRunId':None,'currentReleaseId':None,'articlePath':ap,'createdAt':t,'updatedAt':t});return {'projectId':a,'pageId':b,'root':str(d),'articlePath':ap}
def setarticlepath(a,b,o):
 # Recovery path for a page created before its project became medichannel,
 # which leaves articlePath unset and blocks every candidate and release.
 d=require_page(a,b)
 if platform_of(a)!='medichannel':bad('--article-path only applies to medichannel projects.')
 ap=(o or {}).get('article-path')
 if not ap or ap is True:bad('set-article-path requires --article-path <path>.')
 v=update(d/'page.json',lambda x:{**x,'articlePath':pathfrag(ap,'--article-path'),'updatedAt':now()})
 return {'projectId':a,'pageId':b,'articlePath':v.get('articlePath')}
def new_source(a,b,o):
 d=require_page(a,b); base=o.get('from-source'); changes=[]
 for z in vals(o.get('changed-node')):
  k,eq,v=str(z).partition('=')
  if not eq or not k:bad(f'Invalid changed node {z}; expected <variant-label>=<node-id>.')
  changes.append({'variantLabel':safe(k,'variant label'),'nodeId':node(v)})
 force=o.get('force-new') in (True,'true')
 if base:
  if vals(o.get('figma-url')) or vals(o.get('variant')):bad('Incremental sources inherit variants; do not combine --from-source with --figma-url or --variant.')
  if not changes:bad('Incremental sources require one or more --changed-node <variant-label>=<node-id> values.')
  if not isinstance(o.get('reason'),str) or not o['reason'].strip():bad('Incremental sources require --reason <text>.')
  base=sid(base);bd=src(a,b,base); old=read(bd/'source.json')
  if old['status']!='READY':bad(f"Base source {base} is {old['status']}, not READY.")
  for z in changes:
   if z['variantLabel'] not in {x['label'] for x in old['figma']['variants']}:bad(f"Changed node variant does not exist in {base}: {z['variantLabel']}")
  f=sha({'baseSourceId':base,'changedNodes':sorted(changes,key=lambda x:x['variantLabel']+':'+x['nodeId']),'reason':o['reason'].strip()});du=next((x for x in sources(a,b) if (x.get('changeSet') or {}).get('fingerprint')==f),None)
  if du and not force:
   if du['status']=='READY':return {'projectId':a,'pageId':b,'sourceId':du['id'],'root':str(src(a,b,du['id'])),'reused':True,'created':False,'extractionMode':'INCREMENTAL'}
   bad(f"Matching incremental source {du['id']} is {du['status']}. Reuse it, or pass --force-new --reason <text> for a deliberate new extraction.")
  ident=numbered(d/'sources','source');r=src(a,b,ident);r.mkdir(parents=True)
  for x in ('raw','assets','reference'): cp(bd/x,r/x) if (bd/x).exists() else (r/x).mkdir()
  (r/'spec').mkdir();write(r/'spec/manifest.json',{'baseSourceId':base})
  if (bd/'asset-manifest.json').exists():cp(bd/'asset-manifest.json',r/'asset-manifest.json')
  stale={x['variantLabel'] for x in changes};t=now();write(r/'source.json',{'id':ident,'status':'EXTRACTING','fingerprint':old.get('fingerprint'),'extractionMode':'INCREMENTAL','baseSourceId':base,'changeSet':{'fingerprint':f,'changedNodes':changes,'reason':o['reason'].strip()},'figma':copy.deepcopy(old['figma']),'referenceState':{x['label']:'STALE' if x['label'] in stale else 'REUSED' for x in old['figma']['variants']},'provenance':{'reusedFrom':base,'refreshedSections':[],'refreshedAssets':[],'appliedPatches':[]},'callLedger':[],'forceNewReason':o['reason'].strip() if force else None,'createdAt':t,'completedAt':None,'warnings':[],'error':None});return {'projectId':a,'pageId':b,'sourceId':ident,'baseSourceId':base,'root':str(r),'reused':False,'created':True,'extractionMode':'INCREMENTAL','changedNodes':changes}
 raw=vals(o.get('variant')); urls=vals(o.get('figma-url'))
 if changes:bad('--changed-node requires --from-source.')
 if not raw and not urls:bad('new-source requires --figma-url <url> or one or more --variant <label>=<url> values.')
 vs=[]
 for z in raw:
  k,eq,v=str(z).partition('=');
  if not eq or not k:bad(f'Invalid variant {z}; expected <label>=<url>.')
  vs.append({'label':safe(k,'variant label'),'url':figurl(v),'nodeId':None,'width':None,'height':None,'reference':None})
 vs += [{'label':'primary' if i==0 else f'variant-{i+1}','url':figurl(v),'nodeId':None,'width':None,'height':None,'reference':None} for i,v in enumerate(urls)]
 if len({x['label'] for x in vs})!=len(vs):bad('Variant labels must be unique.')
 f=fp(vs);du=next((x for x in sources(a,b) if stored_fp(x)==f),None)
 if du and not force:
  if du['status']=='READY':return {'projectId':a,'pageId':b,'sourceId':du['id'],'root':str(src(a,b,du['id'])),'reused':True,'created':False,'extractionMode':du.get('extractionMode','FULL')}
  bad(f"Matching source {du['id']} is {du['status']}. Reuse or resolve it, or pass --force-new --reason <text> for a deliberate new extraction.")
 if force and(not isinstance(o.get('reason'),str) or not o['reason'].strip()):bad('--force-new requires --reason <text>.')
 ident=numbered(d/'sources','source');r=src(a,b,ident)
 for x in ('raw','spec','assets','reference'):(r/x).mkdir(parents=True,exist_ok=True)
 t=now();write(r/'source.json',{'id':ident,'status':'EXTRACTING','fingerprint':f,'extractionMode':'FULL','baseSourceId':None,'changeSet':None,'figma':{'url':vs[0]['url'],'variants':vs},'referenceState':{x['label']:'PENDING' for x in vs},'provenance':{'reusedFrom':None,'refreshedSections':[],'refreshedAssets':[],'appliedPatches':[]},'callLedger':[],'forceNewReason':o['reason'].strip() if force else None,'createdAt':t,'completedAt':None,'warnings':[],'error':None});return {'projectId':a,'pageId':b,'sourceId':ident,'root':str(r),'reused':False,'created':True,'extractionMode':'FULL'}
def convertsource(a,b,o):
 # Materializes another page's READY source (spec/inventory/pattern-map/
 # assets/references) into this page's own sources/, so every existing tool
 # that resolves paths under a page's own sources/ keeps working unmodified
 # for a channel-conversion run. Sources are page-scoped, so a page targeting
 # a different platform has no access to another page's sources otherwise.
 d=require_page(a,b)
 fa=safe(o.get('from-project'),'source project identifier');fb=safe(o.get('from-page'),'source page identifier');fc=sid(o.get('from-source'))
 osrc=read(src(fa,fb,fc)/'source.json')
 if osrc['status']!='READY':bad(f"Source {fc} is {osrc['status']}, not READY.")
 force=o.get('force-new') in (True,'true')
 du=next((x for x in sources(a,b) if (x.get('provenance') or {}).get('convertedFrom')=={'project':fa,'page':fb,'sourceId':fc}),None)
 if du and not force:
  if du['status']=='READY':return {'projectId':a,'pageId':b,'sourceId':du['id'],'root':str(src(a,b,du['id'])),'reused':True}
  bad(f"Matching converted source {du['id']} is {du['status']}. Reuse it, or pass --force-new for a fresh copy.")
 ident=numbered(d/'sources','source');r=src(a,b,ident);orig=src(fa,fb,fc)
 for x in ('spec','assets','reference'):
  cp(orig/x,r/x) if (orig/x).exists() else (r/x).mkdir(parents=True,exist_ok=True)
 if (orig/'asset-manifest.json').exists():cp(orig/'asset-manifest.json',r/'asset-manifest.json')
 t=now();write(r/'source.json',{'id':ident,'status':'READY','fingerprint':osrc.get('fingerprint'),'extractionMode':osrc.get('extractionMode','FULL'),'baseSourceId':None,'changeSet':None,'figma':copy.deepcopy(osrc['figma']),'referenceState':{k:'REUSED' for k in osrc.get('referenceState',{})},'provenance':{'reusedFrom':None,'refreshedSections':[],'refreshedAssets':[],'appliedPatches':[],'convertedFrom':{'project':fa,'page':fb,'sourceId':fc}},'callLedger':[],'forceNewReason':None,'createdAt':t,'completedAt':t,'warnings':[],'error':None})
 return {'projectId':a,'pageId':b,'sourceId':ident,'root':str(r),'reused':False,'convertedFrom':{'project':fa,'page':fb,'sourceId':fc}}
def call(a,b,c,o):
 f=src(a,b,c)/'source.json';s=read(f)
 if s['status']!='EXTRACTING':bad(f"Source {c} is immutable because it is {s['status']}.")
 st=str(o.get('status','')).upper()
 if not isinstance(o.get('operation'),str) or st not in {'SUCCESS','TRANSIENT_ERROR','AUTH_ERROR','RATE_LIMITED','FAILED'}:bad('Source calls require operation and a valid status.')
 retry=None
 if st=='RATE_LIMITED':
  try:retry=float(o.get('retry-after'))
  except:bad('RATE_LIMITED source calls require retryAfterSeconds.')
  if retry<0:bad('RATE_LIMITED source calls require retryAfterSeconds.')
  retry=int(retry) if retry.is_integer() else retry
 z={'at':now(),'operation':o['operation'],'nodeId':node(o['node']) if o.get('node') else None,'status':st,'retryAfterSeconds':retry,'message':o.get('message')}
 def fn(x):
  x.setdefault('callLedger',[]).append(z)
  if st=='RATE_LIMITED':
   end=(datetime.fromisoformat(z['at'].replace('Z','+00:00'))+timedelta(seconds=retry)).isoformat(timespec='milliseconds').replace('+00:00','Z');x['rateLimit']={'operation':z['operation'],'nodeId':z['nodeId'],'observedAt':z['at'],'retryAfterSeconds':retry,'blockedUntil':end};w=f"Figma rate limit recorded for {z['operation']}; no automatic retry is permitted before the recorded retry window.";x.setdefault('warnings',[]);x['warnings']+=[] if w in x['warnings'] else [w]
  return x
 update(f,fn);return {'projectId':a,'pageId':b,'sourceId':c,'call':z}
def budget(a,b,c):
 s=read(src(a,b,c)/'source.json');until=s.get('rateLimit',{}).get('blockedUntil');d=datetime.fromisoformat(until.replace('Z','+00:00')) if until else None;ok=not d or d<=datetime.now(timezone.utc);return {'projectId':a,'pageId':b,'sourceId':c,'allowed':ok,'blockedUntil':None if ok else until,'retryAfterSeconds':0 if ok else max(1,int((d-datetime.now(timezone.utc)).total_seconds()+.999))}
INVFIELDS=('id','kind','text','required','nodeId','sectionId','variant')
def wcompact(f,v):
 f=Path(f);t=f.with_name(f.name+'.tmp');t.write_text(dump(v,True)+'\n',encoding='utf8');replace_atomic(t,f)
def styletable(v):
 items=v.get('items')
 if not isinstance(items,list) or not items:return v
 tbl={};order=[];out=[]
 for it in items:
  s=it.get('style')
  if isinstance(s,dict):
   k=dump(s,True)
   if k not in tbl:tbl[k]=f's{len(tbl)}';order.append(k)
   it={**it,'style':tbl[k]}
  out.append(it)
 if not tbl or len(tbl)>=len(items):return v
 return {**v,'styles':{**v.get('styles',{}),**{tbl[k]:json.loads(k) for k in order}},'items':out}
def cssrgba(v):
 if not isinstance(v,dict) or not {'r','g','b'}<=set(v):return None
 r,g,b=(round(float(v.get(k,0))*255) for k in 'rgb');a=float(v.get('a',1))
 return '#%02x%02x%02x'%(r,g,b) if a>=.999 else f'rgba({r},{g},{b},{round(a,3)})'
TOKDROP=('uses','nodeIds')
def tokennorm(v):
 t=v.get('tokens')
 if not isinstance(t,dict):return v
 out={}
 for group,entries in t.items():
  if not isinstance(entries,list):out[group]=entries;continue
  rows=[]
  for e in entries:
   if not isinstance(e,dict):rows.append(e);continue
   e={k:x for k,x in e.items() if k not in TOKDROP}
   if group=='colors' and (h:=cssrgba(e.get('value'))):e['value']=h
   rows.append(e)
  out[group]=rows
 return {**v,'tokens':out}
def compact(a,b,c):
 r=src(a,b,c);res=[]
 for name,fn in (('spec/spec.json',tokennorm),('spec/content-inventory.json',styletable)):
  f=r/name
  if not f.exists():continue
  before=f.stat().st_size;v=read(f);wcompact(f,fn(v) if fn else v)
  res.append({'file':name,'bytesBefore':before,'bytesAfter':f.stat().st_size})
 return {'projectId':a,'pageId':b,'sourceId':c,'normalized':res}
def patternmap(a,b,c):
 d=specbase(a,b,c);f=d/'spec.json'
 if not f.exists():bad(f'spec.json not found for source {c}.')
 spec=read(f);comps=spec.get('tokens',{}).get('components',[]) or [];secs=spec.get('sections',[]) or []
 cg=[];csmap={}
 for e in comps:
  nm=e.get('name','');sids=e.get('sectionIds',[]) or []
  cg.append({'figmaId':e.get('id',''),'name':nm,'instanceCount':e.get('instanceCount',0),'sectionIds':sids});csmap[nm]=set(sids)
 sp=[]
 for s in secs:
  sid=s.get('id','');sc=sorted(nm for nm,sids in csmap.items() if sid in sids)
  lay={k:v for k,v in (s.get('layout') or {}).items() if k in ('direction','paddingX','paddingY')}
  bg=(s.get('visual') or {}).get('background');prof={'sectionId':sid,'role':s.get('role',''),'components':sc,'layout':lay}
  if bg is not None:prof['background']=bg
  sp.append(prof)
 grp={}
 for prof in sp:
  key=tuple(sorted(prof['components']))
  if key not in grp:grp[key]=[]
  grp[key].append(prof['sectionId'])
 lg=[{'label':('-'.join(k).lower().replace('/','') or 'no-components'),'sectionIds':ids,'sharedComponents':list(k)} for k,ids in grp.items() if len(ids)>1]
 out={'version':1,'sourceId':c,'generatedAt':now(),'componentGroups':cg,'sectionProfiles':sp,'layoutGroups':lg}
 target=src(a,b,c)/'spec'/'pattern-map.json';write(target,out)
 return {'sourceId':c,'path':str(target),'componentGroups':len(cg),'sectionProfiles':len(sp),'layoutGroups':len(lg)}
def sourcedelta(a,b,c):
 s=read(src(a,b,c)/'source.json')
 if s.get('extractionMode')!='INCREMENTAL':return {'sourceId':c,'extractionMode':'FULL'}
 changed_nids={x['nodeId'] for x in s.get('changeSet',{}).get('changedNodes',[])}
 spec=read(specbase(a,b,c)/'spec.json')
 stale=[sec['id'] for sec in spec.get('sections',[]) if any(n in changed_nids for n in sec.get('sourceNodeIds',[]))]
 reused=[sec['id'] for sec in spec.get('sections',[]) if sec['id'] not in stale]
 return {'sourceId':c,'baseSourceId':s.get('baseSourceId'),'extractionMode':'INCREMENTAL','staleSectionIds':stale,'reusedSectionIds':reused,'changedNodes':s.get('changeSet',{}).get('changedNodes',[])}
def speclite(a,b,c):
 f=specbase(a,b,c)/'spec.json'
 return read(f) if f.exists() else {}
def inventory(a,b,c,o):
 v=read(specbase(a,b,c)/'content-inventory.json');items=v.get('items',[]) or [];st=v.get('styles',{}) or {};total=len(items)
 # --component: restrict items to the sections that use the named Figma component(s).
 # Every failure here is explicit: silently returning the whole page or nothing at all
 # is worse than an error, because the caller cannot tell which happened.
 comp_filter=vals(o.get('component'));matched_comps=[]
 if comp_filter:
  if not (src(a,b,c)/'spec/spec.json').exists():bad('--component needs spec/spec.json, which is missing from this source.')
  cat=[e for e in (speclite(a,b,c).get('tokens',{}) or {}).get('components') or [] if isinstance(e,dict)]
  hits=[e for e in cat if any(str(w).lower() in str(e.get('name') or '').lower() for w in comp_filter)]
  if not hits:bad(f"No entry in tokens.components matches {', '.join(str(w) for w in comp_filter)}. Recorded components: {', '.join(sorted(str(e.get('name') or '?') for e in cat)) or '<none>'}")
  matched_comps=sorted({str(e.get('name') or '?') for e in hits})
  keep_secs={sid for e in hits for sid in (e.get('sectionIds') or [])}
  if not keep_secs:bad(f"Matched components ({', '.join(matched_comps)}) record no sectionIds, so the inventory cannot be filtered by component. Re-extract the source.")
  items=[it for it in items if it.get('sectionId') in keep_secs]
 if o.get('sections') is True:
  g={}
  for it in items:
   k=str(it.get('sectionId'));x=g.setdefault(k,{'sectionId':it.get('sectionId'),'items':0,'kinds':set(),'variants':set()})
   x['items']+=1;x['kinds'].add(it.get('kind'));x['variants'].add(it.get('variant'))
  res={'sourceId':c,'total':total,'matched':len(items),'sections':[{**x,'kinds':sorted(y for y in x['kinds'] if y),'variants':sorted(y for y in x['variants'] if y)} for x in g.values()]}
  if matched_comps:res['components']=matched_comps
  return res
 def keep(it):
  for k,f in (('variant','variant'),('kind','kind'),('section','sectionId'),('node','nodeId'),('id','id')):
   w=[str(x) for x in vals(o.get(k))]
   if w and str(it.get(f)) not in w:return False
  q=o.get('text')
  if isinstance(q,str) and q not in str(it.get('text') or ''):return False
  if o.get('required') is True and not it.get('required'):return False
  return True
 sel=[it for it in items if keep(it)]
 fl=o.get('fields')
 fl=None if fl=='all' else ([x for w in vals(fl) for x in str(w).split(',') if x] or list(INVFIELDS))
 def proj(it):return {k:it[k] for k in fl if k in it} if fl else it
 def styles(out):
  used={it['style'] for it in out if isinstance(it.get('style'),str)}
  return {k:st[k] for k in sorted(used) if k in st} if used else None
 if o.get('tree') is True:
  # Paging a tree would truncate mid-section and yield a misleading blueprint.
  if o.get('limit') is not None or o.get('offset') is not None:bad('--limit and --offset do not apply to --tree. Narrow the tree with --section, --variant, --kind, or --component instead.')
  sp_secs=[s for s in speclite(a,b,c).get('sections') or [] if isinstance(s,dict) and s.get('id')]
  sec_meta={s['id']:s for s in sp_secs};rank={s['id']:i for i,s in enumerate(sp_secs)}
  # Bucket by (sectionId, variant): desktop and mobile share a sectionId, and
  # merging them would list every node twice in one group.
  bkts={}
  for it in sel:bkts.setdefault((it.get('sectionId'),it.get('variant')),[]).append(it)
  out_secs=[];shown=[]
  for sid,var in sorted(bkts,key=lambda k:(rank.get(k[0],len(sp_secs)),str(k[0]),str(k[1]))):
   its=bkts[(sid,var)];sm=sec_meta.get(sid) or {}
   gs=[g for g in (sm.get('groups') or []) if isinstance(g,dict)]
   gid=lambda i,g:str(g.get('groupId') or f'{sid}__group-{i+1:02d}')
   nid_map={nid:gid(i,g) for i,g in enumerate(gs) for nid in (g.get('textNodeIds') or [])}
   if nid_map:
    label={gid(i,g):g.get('label') for i,g in enumerate(gs)};order={gid(i,g):i for i,g in enumerate(gs)}
    gbkt={}
    for it in its:gbkt.setdefault(nid_map.get(it.get('nodeId'),f'{sid}__other'),[]).append(it)
    groups=[]
    for k in sorted(gbkt,key=lambda g:(order.get(g,len(gs)),g)):
     rows=[proj(x) for x in gbkt[k]];shown+=rows
     groups.append({'groupId':k,**({'label':label[k]} if label.get(k) else {}),'items':rows})
    gsrc='spec'
   else:
    rows=[proj(it) for it in its];shown+=rows
    groups=[{'groupId':f'{sid}__content','items':rows}];gsrc='fallback'
   out_secs.append({'sectionId':sid,'variant':var,'role':sm.get('role'),'groupSource':gsrc,'groups':groups})
  res={'sourceId':c,'total':total,'matched':len(sel),'sections':out_secs}
  if matched_comps:res['components']=matched_comps
  if (s:=styles(shown)):res['styles']=s
  return res
 off=max(0,int(o.get('offset') or 0));lim=o.get('limit');sel2=sel[off:off+int(lim)] if lim and lim is not True else sel[off:]
 out=[proj(it) for it in sel2]
 res={'sourceId':c,'total':total,'matched':len(sel),'returned':len(out),'offset':off,'items':out}
 if matched_comps:res['components']=matched_comps
 if (s:=styles(out)):res['styles']=s
 return res
def ready(a,b,c):
 r=src(a,b,c);f=r/'source.json';s=read(f)
 if s['status']!='EXTRACTING':bad(f"Source {c} is immutable because it is {s['status']}.")
 stale=[k for k,v in s.get('referenceState',{}).items() if v in {'STALE','PENDING'}]
 if s.get('extractionMode')=='INCREMENTAL' and stale:bad(f"Incremental source has stale reference evidence for: {', '.join(stale)}. Apply refreshed references before marking it READY.")
 if (r/'spec/manifest.json').exists() and not (r/'spec/spec.json').exists():
  bd=specbase(a,b,c)
  for nm in ('spec.json','content-inventory.json'):
   if (bd/nm).exists():cp(bd/nm,r/'spec'/nm)
 for x in ('spec/spec.json','spec/content-inventory.json','asset-manifest.json'):
  if not(r/x).exists():bad(f'Source cannot become READY; missing {x}.')
 spec=read(r/'spec/spec.json')
 if not spec.get('sections'):bad('Source spec must contain at least one semantic section.')
 if spec.get('openQuestions'):bad('Source has unresolved open questions. Resolve them or record an explicit user decision before continuing.')
 png={x.name for x in (r/'reference').glob('*.png')}
 for v in s['figma']['variants']:
  q=next((x for x in spec.get('variants',[]) if x.get('label')==v['label'] or x.get('id')==v['label']),None); ref=(q or {}).get('reference',(q or {}).get('referenceFilename'))
  if not q:bad(f"Source spec is missing supplied variant: {v['label']}.")
  if not ref or Path(ref).name not in png:bad(f"Source variant {v['label']} has no matching PNG reference export.")
 norm=compact(a,b,c)
 t=now();update(f,lambda x:{**x,'status':'READY','completedAt':t,'error':None,'referenceState':x['referenceState'] if x.get('extractionMode')=='INCREMENTAL' else {z['label']:'REFRESHED' for z in x['figma']['variants']}});update(page(a,b)/'page.json',lambda x:{**x,'status':'SOURCE_READY','currentSourceId':c,'updatedAt':t});return {'projectId':a,'pageId':b,'sourceId':c,'status':'READY','normalized':norm['normalized']}
GUIDE=ROOT/'guidelines';GLOBAL=GUIDE/'global'
# Cross-role global layer. general-rules.md is always first; fidelity.md is the
# shared content/UI/quality bar, needed by the builder and the reviewers but not
# by the extractor. global/orchestrator.md is deliberately in neither map: run,
# gate, and release rules belong to the primary orchestrator, so no role read
# delivers them (the unscoped read still archives them for release evidence).
ROLE_GLOBAL={'builder':('fidelity.md',),'extractor':(),'ui':('fidelity.md',),'content':('fidelity.md',),'accessibility':('fidelity.md',),'technical':('fidelity.md',)}
ROLE_FILES={'builder':GUIDE/'builder.md','extractor':GUIDE/'extractor.md','ui':GUIDE/'global'/'qa'/'ui-qa.md','content':GUIDE/'global'/'qa'/'content-qa.md','accessibility':GUIDE/'global'/'qa'/'accessibility-qa.md','technical':GUIDE/'global'/'qa'/'technical-qa.md'}
# Platform coding standards are a second axis, orthogonal to role. MediChannel
# (XHTML 1.0 Strict) and HTML5 are mutually exclusive: building under the wrong
# ruleset means a rebuild, so a role-scoped read delivers the role file *and*
# the channel's coding/QA bundle under guidelines/<channel>/. Without this,
# guidelines/global/general-rules.md names these folders while no agent ever
# receives them.
PLATFORM_DIR={'medichannel':'medichannel','html5':'m3'}
QAROLES={'ui','content','accessibility','technical'}
def relkey(p):return p.relative_to(ROOT).as_posix()
def platform_of(a):
 f=prj(a)/'project.json'
 v=(read(f).get('platform') if f.exists() else None) or None
 if v is not None and v not in PLATFORM_DIR:bad(f"Project {a} records an unknown platform: {v}. Use one of: {', '.join(sorted(PLATFORM_DIR))}.")
 return v
def payload_spec(a,article_path,conversion=False):
 # Native MediChannel builds are flat (identical contract to html5/M3) for
 # the whole BUILDING/VERIFYING/REFINING lifecycle; the nested AEM/JCR tree
 # is materialized separately (see materialize-medichannel.py), only at
 # release or on demand. Only a channel-conversion run's own candidates
 # (m3-to-medichannel direction, produced by convert-platform.py's genuine
 # HTML5->XHTML structural transform) are nested from creation -- callers
 # pass conversion=True for those, derived from run.json.convertedFrom.
 plat=platform_of(a)
 if plat is None:bad(f"Project {a} has no platform set; cannot determine deployable output shape.")
 if plat!='medichannel' or not conversion:return {'kind':'flat'}
 delivery=read(prj(a)/'project.json').get('delivery') or {}
 missing=[k for k in ('contentRoot','damRoot','cssRoot') if not delivery.get(k)]
 if missing:bad(f"Project {a} is missing delivery path field(s): {', '.join(missing)}. Set them with: kit.py set-platform {a} --platform medichannel --content-root <path> --dam-root <path> --css-root <path>.")
 if not article_path:bad(f'Page has no articlePath recorded. Set it with: kit.py set-article-path {a} <page> --article-path <path>.')
 return {'kind':'jcr','articlePath':article_path,**delivery}
def is_conversion_run(s):
 return (s.get('convertedFrom') or {}).get('direction')=='m3-to-medichannel'
# Which guidelines/global/coding/*.md each role can act on. base-css-template.md
# is builder-only: it is non-normative sample CSS full of comment banners, while
# global/qa/technical-qa.md requires delivered CSS to carry zero comments, so
# shipping it to reviewers manufactures false findings.
CODING_FOR_ROLE={
 'builder':      {'assets-media.md','base-css-template.md','css.md','html.md'},
 'extractor':    {'assets-media.md'},
 'ui':           {'assets-media.md','css.md'},
 'content':      {'assets-media.md'},
 'accessibility':{'assets-media.md','html.md'},
 'technical':    {'assets-media.md','css.md','html.md'},
}
def coding_files(role):
 sel=CODING_FOR_ROLE.get(role) or set()
 return sorted((p for p in (GLOBAL/'coding').glob('*.md') if p.name in sel),key=relkey)
def platform_files(role,plat):
 if not plat or role is None:return []
 d=GUIDE/PLATFORM_DIR[plat]
 out=[]
 gr=d/'general-rules.md'
 if gr.exists():out.append(gr)
 out+=sorted((d/'coding').glob('*.md'),key=relkey)
 if role in QAROLES:out+=sorted((d/'qa').glob('*.md'),key=relkey)
 return out
def gfiles(a,b,role=None):
 gr=GLOBAL/'general-rules.md'
 out=[gr] if gr.exists() else []
 if role is None:
  out+=sorted((p for p in GUIDE.rglob('*.md') if p.is_file() and p!=gr),key=relkey)
 else:
  out+=[p for p in (GLOBAL/n for n in ROLE_GLOBAL[role]) if p.exists()]
  rf=ROLE_FILES[role]
  if rf.exists():out.append(rf)
  out+=coding_files(role)
  out+=platform_files(role,platform_of(a))
 for d in (prj(a)/'guidelines',page(a,b)/'guidelines'):
  if d.is_dir():out+=sorted(x for x in d.glob('*.md') if x.is_file())
 return out
def guidelines(a,b,o):
 role=o.get('role');prev=o.get('prev-hash')
 if role is True:bad(f"guidelines --role requires a value. Use one of: {', '.join(sorted(ROLE_FILES))}.")
 if isinstance(role,list):bad('guidelines accepts a single --role.')
 if role is not None and role not in ROLE_FILES:bad(f"Unknown role: {role}. Use one of: {', '.join(sorted(ROLE_FILES))}.")
 g,_,h=snapshot(a,b,role)
 if prev and prev==h:cp=gcache(a,role,h);return f"GUIDELINE_CACHE_HIT\nhash: {h}\npath: {str(cp)}"
 return g
def snapshot(a,b,role=None):
 plat=platform_of(a)
 body=['# Effective guideline snapshot','',f"Role scope: {role or 'all'}.",f"Platform: {plat or 'not set'}.",'Resolved in precedence order: global, channel, project, page. Later rules override','earlier rules only where they address the same requirement explicitly.','']
 if role is not None and not plat:body+=['> **Warning:** no platform is set for this project, so no channel coding','> standards are included below. The rules named in the Channels section of','> `guidelines/global/general-rules.md` are NOT part of this snapshot. Set the','> platform with `kit.py set-platform <project> --platform <name>` and re-read.','']
 srcs=[]
 for f in gfiles(a,b,role):
  x=f.read_text(encoding='utf8');rel=f.relative_to(ROOT).as_posix()
  srcs.append({'path':rel,'sha256':hashlib.sha256(x.encode()).hexdigest()})
  body+=[f'## {rel}','',x.strip(),'']
 if not srcs:bad('No guideline sources resolved; a run requires at least guidelines/global/general-rules.md.')
 g='\n'.join(body)+'\n';h=hashlib.sha256(g.encode()).hexdigest();cp=gcache(a,role,h)
 if not cp.exists():
  cp.write_text(g,encoding='utf8')
  # One live snapshot per role scope: a stale sibling can only ever be wrong
  # content, and nothing resolves it except a --prev-hash that no longer matches.
  for old in cp.parent.glob(f"{role or 'all'}-*.md"):
   if old!=cp:old.unlink()
 return g,srcs,h
def newrun(a,b,o):
 d=require_page(a,b);p=read(d/'page.json');c=o.get('source') or p.get('currentSourceId')
 # Platform is confirmed at ticket intake: MediChannel and HTML5 standards are
 # mutually exclusive, so a run started without one would build against no
 # coding standard at all.
 if not platform_of(a):bad(f"Project {a} has no platform. Confirm it at intake and set it with: kit.py set-platform {a} --platform <{'|'.join(sorted(PLATFORM_DIR))}>")
 if not c:bad('No ready source is selected. Extract and mark a source READY first.')
 s=read(src(a,b,c)/'source.json')
 if s['status']!='READY':bad(f"Source {c} is {s['status']}, not READY.")
 i=numbered(d/'runs','run');r=run(a,b,i)
 for x in ('candidates','generated','visual','qa'):(r/x).mkdir(parents=True,exist_ok=True)
 t=now();g,gs,h=snapshot(a,b);(r/'effective-guidelines.md').write_text(g,encoding='utf8');write(r/'run.json',{'id':i,'status':'CREATED','sourceId':c,'sourceExtractionMode':s.get('extractionMode','FULL'),'baseSourceId':s.get('baseSourceId'),'previousRunId':p.get('currentRunId'),'startedAt':t,'completedAt':None,'guidelineSnapshot':{'sources':gs,'sha256':h},'repair':{'round':0,'maxRounds':3},'candidates':[],'events':[{'at':t,'type':'created','sourceId':c}],'error':None});update(d/'page.json',lambda x:{**x,'status':'BUILDING','currentRunId':i,'updatedAt':t});active(project=a,page=b,run=i,round=0,status='CREATED',candidate=None,task=None);return {'projectId':a,'pageId':b,'runId':i,'sourceId':c,'root':str(r),'guidelineSnapshot':{'sources':[x['path'] for x in gs]}}
def newconversionrun(a,b,o):
 # A conversion run is an ordinary run (same run.json status machine) whose
 # BUILDING phase transforms an accepted candidate from another platform's
 # page instead of extracting fresh from Figma. Reuses newrun()'s scaffold
 # entirely; only a convertedFrom provenance field is added afterward.
 direction=str(o.get('direction') or '')
 if direction not in ('m3-to-medichannel','medichannel-to-m3'):bad('new-conversion-run requires --direction m3-to-medichannel|medichannel-to-m3.')
 to_plat='medichannel' if direction.endswith('medichannel') else 'html5'
 plat=platform_of(a)
 if plat!=to_plat:bad(f"Target project {a} has platform {plat or '<none>'}, but --direction {direction} targets {to_plat}.")
 fa=safe(o.get('from-project'),'source project identifier');fb=safe(o.get('from-page'),'source page identifier');fr=rid(o.get('from-run'))
 fc=o.get('from-candidate')
 if not fc or fc is True:bad('new-conversion-run requires --from-candidate <id>.')
 fc=safe(fc,'source candidate identifier')
 fs=read(run(fa,fb,fr)/'run.json')
 if fs.get('acceptedCandidateId')!=fc:bad(f"{fc} is not the accepted candidate of {fa}/{fb}/{fr}.")
 cs=convertsource(a,b,{'from-project':fa,'from-page':fb,'from-source':fs['sourceId']})
 rv=newrun(a,b,{'source':cs['sourceId']});i=rv['runId']
 meta={'project':fa,'page':fb,'run':fr,'candidate':fc,'direction':direction}
 update(run(a,b,i)/'run.json',lambda x:{**x,'convertedFrom':meta})
 return {**rv,'convertedFrom':meta}
def candidate(a,b,c,o):
 s=mutable(a,b,c);r=run(a,b,c);i=numbered(r/'candidates','candidate');d=r/'candidates'/i;d.mkdir(parents=True);n=int(o.get('round',s['repair']['round']))
 if n<0 or n>s['repair']['maxRounds']:bad('Candidate round is outside the configured repair range.')
 from_accepted=str(o.get('from-accepted','')).lower() in ('true','1') or o.get('from-accepted') is True
 convertedfrom=None
 if from_accepted:
  if o.get('from-external'):bad('--from-accepted cannot be combined with --from-external.')
  if not s.get('acceptedCandidateId'):bad('Cannot seed from accepted output because no candidate has been accepted.')
  cp(r/'generated',d)
 elif o.get('from-external'):
  # Seeds a candidate from another page's accepted output for a channel-
  # conversion run. The frozen source payload lives in a subfolder so it
  # never collides with this candidate's own (target-shaped) output tree.
  xa,xb,xr,xc=extref(o['from-external']);xrun=read(run(xa,xb,xr)/'run.json')
  if xrun.get('acceptedCandidateId')!=xc:bad(f"{xc} is not the accepted candidate of {xa}/{xb}/{xr}.")
  xd=run(xa,xb,xr)/'generated'
  if not xd.exists():bad(f'No accepted output found at {xa}/{xb}/{xr}/generated.')
  cp(xd,d/'_conversion-input');convertedfrom={'project':xa,'page':xb,'run':xr,'candidate':xc}
 spec=payload_spec(a,read(page(a,b)/'page.json').get('articlePath'),is_conversion_run(s))
 if spec['kind']=='flat':(d/'images').mkdir(exist_ok=True)
 else:(d/jcr_paths(spec)[1]).mkdir(parents=True,exist_ok=True)
 t=now();cand={'id':i,'projectId':a,'pageId':b,'runId':c,'sourceId':s['sourceId'],'baseSourceId':s.get('baseSourceId'),'round':n,'scope':o.get('scope','full-page'),'status':'PENDING','createdAt':t,'evaluatedAt':None,'metrics':None,'reasons':[]}
 if convertedfrom:cand['convertedFrom']=convertedfrom
 write(d/'candidate.json',cand)
 update(r/'run.json',lambda x:{**x,'candidates':[ *x['candidates'],{'id':i,'status':'PENDING','createdAt':t,'round':n,'scope':o.get('scope','full-page'),'sourceId':x['sourceId']}],'events':[ *x['events'],{'at':t,'type':'candidate-created','candidateId':i,'round':n,'scope':o.get('scope','full-page')} ]});active(project=a,page=b,run=c,candidate=i,round=n,task=o.get('scope','full-page'));return {'projectId':a,'pageId':b,'runId':c,'candidateId':i,'root':str(d)}
def result(a,b,c,i,o):
 s=mutable(a,b,c);r=run(a,b,c);d=r/'candidates'/i;f=d/'candidate.json';st=str(o.get('status','')).upper()
 if st not in {'ACCEPTED','REJECTED'}:bad('candidate-result requires --status accepted|rejected.')
 spec=payload_spec(a,read(page(a,b)/'page.json').get('articlePath'),is_conversion_run(s));payload(d,'Candidate deployable output',spec)
 m=read(Path(o['metrics'])) if o.get('metrics') else None; static=read(Path(o['static'])) if o.get('static') else None; browser=read(Path(o['browser'])) if o.get('browser') else None
 if st=='ACCEPTED' and m and m.get('status')=='ERROR':bad(f"Visual evidence is unavailable, so this candidate cannot be accepted: {m.get('reason') or 'comparison error'}. Fix the evidence and re-measure; do not treat it as a visual failure.")
 if st=='ACCEPTED' and any(not q or q.get('status')!='PASS' for q in (m,static,browser)):bad('Accepted candidates require passing static, browser, and visual reports.')
 t=now();x=read(f);x.update(status=st,evaluatedAt=t,metrics=m,evidence={'static':static,'browser':browser},reasons=[o['reason']] if o.get('reason') else []);write(f,x)
 if st=='ACCEPTED':rm(r/'generated');cp(d,r/'generated');(r/'generated'/'candidate.json').unlink(missing_ok=True);rm(r/'generated'/'structural-check');rm(r/'generated'/'_conversion-input');rm(r/'qa');(r/'qa').mkdir()
 def fn(z):
  q={'id':i,'status':st,'evaluatedAt':t,'round':z['repair']['round'],'metrics':m,'evidence':{'static':static.get('status') if static else None,'browser':browser.get('status') if browser else None},'reasons':x['reasons'],'sourceId':z['sourceId']};z['candidates']=[{**v,**q} if v['id']==i else v for v in z['candidates']];z['acceptedCandidateId']=i if st=='ACCEPTED' else z.get('acceptedCandidateId');z['events'].append({'at':t,'type':'candidate','candidateId':i,'status':st});return z
 update(r/'run.json',fn);return {'projectId':a,'pageId':b,'runId':c,'candidateId':i,'status':st,'acceptedCandidateId':i if st=='ACCEPTED' else s.get('acceptedCandidateId')}
def patch(a,b,c,o):
 f=src(a,b,c)/'source.json';s=read(f);q=read(Path(o['file']))
 if s['status']!='EXTRACTING':bad(f"Source {c} is immutable because it is {s['status']}.")
 r=src(a,b,c);sb=specbase(a,b,c);spec=read(sb/'spec.json');inv=read(sb/'content-inventory.json');man=read(r/'asset-manifest.json'); sections=[x for x in spec['sections'] if x['id'] not in q.get('removeSectionIds',[])]
 for e in q.get('sections',[]):
  x=e.get('section',e);at=next((i for i,v in enumerate(sections) if v['id']==x['id']),-1)
  if at>=0:sections[at]=x
  else:
   after=next((i for i,v in enumerate(sections) if v['id']==e.get('insertAfter')),-1)
   if after<0:bad(f"New section {x['id']} requires insertBefore or insertAfter referencing an existing section.")
   sections.insert(after+1,x)
 spec['sections']=sections;replace=set(q.get('replaceContentForSections',[]));inv['items']=[x for x in inv.get('items',[]) if x.get('sectionId') not in replace]; inv['items']+=q.get('contentItems',[])
 for e in q.get('files',{}).get('references',[]):cp(Path(o['file']).parent/e['from'],r/'reference'/e.get('to',Path(e['from']).name))
 write(r/'spec/spec.json',spec);write(r/'spec/content-inventory.json',inv);write(r/'asset-manifest.json',man)
 def fn(x):
  for k in q.get('refreshedVariants',[]):x['referenceState'][k]='REFRESHED'
  return x
 update(f,fn);return {'projectId':a,'pageId':b,'sourceId':c,'sections':len(sections),'contentItems':len(inv['items']),'assets':len(man.get('assets',[])),'staleReferences':[k for k,v in read(f).get('referenceState',{}).items() if v=='STALE']}
def qarecord(a,b,c,k,o):
 s=mutable(a,b,c)
 if not s.get('acceptedCandidateId'):bad('QA cannot be recorded before a candidate is accepted.')
 q=read(Path(o['file']));
 if q.get('kind')!=k or q.get('status') not in {'PASS','FAIL','UNAVAILABLE'} or not isinstance(q.get('findings'),list):bad(f'QA file kind {q.get("kind","<missing>")} does not match {k}.')
 if k in {'ui','accessibility'} and not q.get('webInterfaceGuidelines'):bad(f'QA file for {k} requires Web Interface Guidelines provenance.')
 q.update(runId=c,candidateId=s['acceptedCandidateId']);q.setdefault('checkedAt',now());write(run(a,b,c)/'qa'/f'{k}.json',q);return {'projectId':a,'pageId':b,'runId':c,'kind':k,'status':q['status'],'target':str(run(a,b,c)/'qa'/f'{k}.json')}
def summary(a,b,c):
 r=run(a,b,c);s=read(r/'run.json');q={k:read(r/'qa'/f'{k}.json') if (r/'qa'/f'{k}.json').exists() else None for k in QA};missing=[k for k in QA if not q[k]];failed=[k for k in QA if q[k] and q[k].get('status')!='PASS']; stale=[k for k in QA if q[k] and (q[k].get('runId')!=c or q[k].get('candidateId')!=s.get('acceptedCandidateId'))];v={'status':'PASS' if not(missing or failed or stale) else 'FAIL','checkedAt':now(),'required':list(QA),'missing':missing,'failed':failed,'stale':stale,'checks':{k:q[k].get('status') if q[k] else 'MISSING' for k in QA}};write(r/'qa/summary.json',v);return v
def releasecheck(a,b,c,o):
 s=mutable(a,b,c);q=read(Path(o['file']))
 if s['status']!='VERIFYING' or q.get('status')!='READY' or q.get('runId')!=c or q.get('candidateId')!=s.get('acceptedCandidateId'):bad('Release verifier verdict must be READY and match the run and accepted candidate.')
 q.setdefault('checkedAt',now());write(run(a,b,c)/'qa/release-verifier.json',q);return {'projectId':a,'pageId':b,'runId':c,'status':'READY','candidateId':s['acceptedCandidateId']}
def release(a,b,c):
 s=mutable(a,b,c);r=run(a,b,c)
 if s['status']!='VERIFYING':bad(f"Run must be VERIFYING before release; current status is {s['status']}.")
 if summary(a,b,c)['status']!='PASS' or not (r/'qa/release-verifier.json').exists():bad('Cannot release without passing QA and a recorded release-verifier verdict.')
 payload(r/'generated','Generated output',payload_spec(a,read(page(a,b)/'page.json').get('articlePath'),is_conversion_run(s)))
 d=page(a,b);i=numbered(d/'releases','v');target=d/'releases'/i;cp(r/'generated',target/'site');cp(r/'effective-guidelines.md',target/'effective-guidelines.md');cp(r/'qa',target/'qa');checks={x.relative_to(target/'site').as_posix():hashlib.sha256(x.read_bytes()).hexdigest() for x in (target/'site').rglob('*') if x.is_file()};write(target/'release.json',{'releaseId':i,'runId':c,'sourceId':s['sourceId'],'createdAt':now(),'checksums':checks});rm(d/'current');cp(target/'site',d/'current');done=transition(a,b,c,'COMPLETED',{'releaseId':i});cp(r/'run.json',target/'run.json');update(d/'page.json',lambda x:{**x,'status':'COMPLETED','currentRunId':c,'currentReleaseId':i,'updatedAt':done['completedAt']});return {'projectId':a,'pageId':b,'runId':c,'releaseId':i,'release':str(target)}
QA_PDF=('content','visual-cutoff')
def newpdfexport(a,b,c,o):
 # PDF export is a side artifact attached to a run, not a run-state
 # transition, so it must work whether the run is terminal or not: it never
 # touches run.json/transition(), only reads acceptedCandidateId from it.
 s=read(run(a,b,c)/'run.json');fc=o.get('from-candidate')
 if not fc or fc is True:bad('new-pdf-export requires --from-candidate <id>.')
 if s.get('acceptedCandidateId')!=fc:bad(f"{fc} is not the accepted candidate of run {c}.")
 pd=run(a,b,c)/'pdf';i=numbered(pd,'pdf');d=pd/i;d.mkdir(parents=True)
 t=now();write(d/'pdf.json',{'id':i,'projectId':a,'pageId':b,'runId':c,'sourceCandidateId':fc,'status':'PENDING','createdAt':t,'completedAt':None})
 return {'projectId':a,'pageId':b,'runId':c,'pdfId':i,'root':str(d)}
def pdfresult(a,b,c,i,o):
 d=run(a,b,c)/'pdf'/i;f=d/'pdf.json'
 if not f.exists():bad(f'PDF export does not exist: {i}')
 st=str(o.get('status','')).upper()
 if st not in ('READY','FAILED'):bad('pdf-result requires --status ready|failed.')
 meta=read(Path(o['file'])) if o.get('file') else {}
 t=now();update(f,lambda x:{**x,**meta,'status':st,'completedAt':t});return {'projectId':a,'pageId':b,'runId':c,'pdfId':i,'status':st}
def pdfqarecord(a,b,c,i,k,o):
 d=run(a,b,c)/'pdf'/i
 if k not in QA_PDF:bad(f"Unknown PDF QA kind: {k}. Use one of: {', '.join(QA_PDF)}.")
 if not (d/'pdf.json').exists():bad(f'PDF export does not exist: {i}')
 q=read(Path(o['file']))
 if q.get('kind')!=k or q.get('status') not in {'PASS','FAIL','UNAVAILABLE'} or not isinstance(q.get('findings'),list):bad(f'QA file kind {q.get("kind","<missing>")} does not match {k}.')
 q.update(runId=c,pdfId=i);q.setdefault('checkedAt',now());(d/'qa').mkdir(exist_ok=True);write(d/'qa'/f'{k}.json',q)
 return {'projectId':a,'pageId':b,'runId':c,'pdfId':i,'kind':k,'status':q['status']}
def pdfqasummary(a,b,c,i):
 d=run(a,b,c)/'pdf'/i;q={k:read(d/'qa'/f'{k}.json') if (d/'qa'/f'{k}.json').exists() else None for k in QA_PDF}
 missing=[k for k in QA_PDF if not q[k]];failed=[k for k in QA_PDF if q[k] and q[k].get('status')!='PASS']
 v={'status':'PASS' if not(missing or failed) else 'FAIL','checkedAt':now(),'required':list(QA_PDF),'missing':missing,'failed':failed,'checks':{k:q[k].get('status') if q[k] else 'MISSING' for k in QA_PDF}}
 write(d/'qa/summary.json',v);return v
def pdfrelease(a,b,c,i):
 d=run(a,b,c)/'pdf'/i;f=d/'pdf.json'
 if not f.exists():bad(f'PDF export does not exist: {i}')
 if pdfqasummary(a,b,c,i)['status']!='PASS':bad('Cannot release a PDF without passing its QA gate.')
 srcpdf=d/'index.pdf'
 if not srcpdf.exists():bad(f'PDF export {i} has no index.pdf.')
 pg=page(a,b);cp(srcpdf,pg/'current'/'index.pdf');relid=read(pg/'page.json').get('currentReleaseId')
 if relid:cp(srcpdf,pg/'releases'/relid/'pdf'/'index.pdf')
 update(f,lambda x:{**x,'releasedAt':now()});return {'projectId':a,'pageId':b,'runId':c,'pdfId':i,'released':True,'releaseId':relid}
def require_medichannel_native(a,s,verb):
 # Shared guard for both materialization entry points: the nested AEM/JCR
 # tree is only ever an additional artifact derived from a *native* flat
 # MediChannel build. A channel-conversion run's candidates/generated/site
 # are already nested (produced by convert-platform.py) -- materializing
 # them again makes no sense and must not be attempted.
 if is_conversion_run(s):bad(f"This run is a channel-conversion run; its output is already nested. {verb} only applies to native MediChannel builds.")
 plat=platform_of(a)
 if plat!='medichannel':bad(f"Project {a} has platform {plat or '<none>'}; {verb} only applies to medichannel projects.")
def newmaterialization(a,b,c,o):
 # Materialization is a side artifact attached to a run, not a run-state
 # transition -- mirrors new-pdf-export exactly, so it works whether the run
 # is terminal or not and never touches run.json/transition().
 s=read(run(a,b,c)/'run.json');require_medichannel_native(a,s,'new-materialization')
 fc=o.get('from-candidate')
 if fc is True:bad('--from-candidate requires a value.')
 if fc:
  srcdir=run(a,b,c)/'candidates'/str(fc)
  if not srcdir.exists():bad(f'Candidate does not exist: {fc}')
 else:
  srcdir=run(a,b,c)/'generated'
  if not srcdir.exists():bad(f'No accepted output found at {a}/{b}/{c}/generated.')
 article_path=read(page(a,b)/'page.json').get('articlePath')
 delivery=require_delivery(read(prj(a)/'project.json').get('delivery') or {})
 md=run(a,b,c)/'materialized';i=numbered(md,'materialized');d=md/i;out=d/'jcr';out.mkdir(parents=True)
 t=now();write(d/'materialize.json',{'id':i,'projectId':a,'pageId':b,'runId':c,'sourceCandidateId':fc or None,'status':'PENDING','createdAt':t,'completedAt':None})
 return {'projectId':a,'pageId':b,'runId':c,'materializationId':i,'root':str(out),'input':str(srcdir),'articlePath':article_path,'delivery':delivery}
def materializationresult(a,b,c,i,o):
 d=run(a,b,c)/'materialized'/i;f=d/'materialize.json'
 if not f.exists():bad(f'Materialization does not exist: {i}')
 st=str(o.get('status','')).upper()
 if st not in ('READY','FAILED'):bad('materialization-result requires --status ready|failed.')
 meta=read(Path(o['file'])) if o.get('file') else {}
 t=now();update(f,lambda x:{**x,**meta,'status':st,'completedAt':t});return {'projectId':a,'pageId':b,'runId':c,'materializationId':i,'status':st}
def releasematerialize(a,b,c):
 s=read(run(a,b,c)/'run.json');require_medichannel_native(a,s,'release-materialize')
 d=page(a,b)/'releases'
 target=next((x for x in sorted(d.iterdir()) if x.is_dir() and read(x/'release.json').get('runId')==c),None) if d.exists() else None
 if target is None:bad(f'No release found for run {c}. Run kit.py release first.')
 article_path=read(page(a,b)/'page.json').get('articlePath')
 delivery=require_delivery(read(prj(a)/'project.json').get('delivery') or {})
 out=target/'jcr';rm(out);out.mkdir(parents=True)
 return {'projectId':a,'pageId':b,'runId':c,'releaseId':target.name,'root':str(out),'input':str(target/'site'),'articlePath':article_path,'delivery':delivery}
def resolve(a,b,c,o):
 f=src(a,b,c)/'source.json';s=read(f)
 if s['status']!='EXTRACTING':bad(f"Source {c} is immutable because it is {s['status']}.")
 if not isinstance(o.get('question'),str) or not isinstance(o.get('decision'),str):bad('resolve-question requires --question <id> --decision <text>.')
 sf=src(a,b,c)/'spec/spec.json';spec=read(sf);q=spec.get('openQuestions') or []
 i=next((n for n,x in enumerate(q) if (x if isinstance(x,str) else x.get('id'))==o['question']),-1)
 if i<0:bad(f"Open question does not exist: {o['question']}")
 item=q.pop(i);spec['openQuestions']=q;spec['decisions']=[*(spec.get('decisions') or []),{'questionId':o['question'],'question':item,'decision':o['decision'],'decidedBy':o.get('by') or 'user','decidedAt':now()}]
 write(sf,spec);return {'projectId':a,'pageId':b,'sourceId':c,'questionId':o['question'],'remaining':len(q)}
def srcfail(a,b,c,message):
 f=src(a,b,c)/'source.json';s=read(f)
 if s['status']!='EXTRACTING':bad(f"Source {c} is immutable because it is {s['status']}.")
 write(f,{**s,'status':'FAILED','completedAt':now(),'error':message or 'Extraction failed.'});return {'projectId':a,'pageId':b,'sourceId':c,'status':'FAILED'}
def nextrepair(a,b,c):
 s=mutable(a,b,c)
 if s['repair']['round']>=s['repair']['maxRounds']:bad(f"Repair cap reached ({s['repair']['maxRounds']}). Mark the run NEEDS_REVIEW.")
 n=s['repair']['round']+1
 def fn(x):
  x['repair']['round']=n;x['events'].append({'at':now(),'type':'repair-round','round':n});active(project=a,page=b,run=c,round=n);return x
 update(run(a,b,c)/'run.json',fn);return {'projectId':a,'pageId':b,'runId':c,'round':n,'maxRounds':s['repair']['maxRounds']}
def terminal(a,b,c,status,message):
 if status not in {'NEEDS_REVIEW','FAILED'}:bad(f'Unsupported terminal status: {status}')
 s=mutable(a,b,c)
 if status=='NEEDS_REVIEW' and s['status'] not in {'VERIFYING','REFINING'}:bad('Run must be VERIFYING or REFINING before NEEDS_REVIEW.')
 r=transition(a,b,c,status,{'message':message or None});update(page(a,b)/'page.json',lambda x:{**x,'status':status,'updatedAt':r['completedAt']});return {'projectId':a,'pageId':b,'runId':c,'status':status,'message':message or None}
def report(a,b):
 pr=read(prj(a)/'project.json') if (prj(a)/'project.json').exists() else bad(f'Project does not exist: {a}')
 if not b:
  d=prj(a)/'pages';return {'project':pr,'pages':[read(x/'page.json') for x in sorted(d.iterdir()) if (x/'page.json').exists()] if d.exists() else []}
 require_page(a,b);d=page(a,b)/'runs'
 return {'project':pr,'page':read(page(a,b)/'page.json'),'runs':[read(x/'run.json') for x in sorted(d.iterdir()) if (x/'run.json').exists()] if d.exists() else []}
def help():return 'Layerlift agent-kit state controller\n'
def main():
 # Guideline documents are UTF-8. On a cp1252 console, printing one raises
 # UnicodeEncodeError and the agent gets no guidelines at all.
 for s in (sys.stdout,sys.stderr):
  try:s.reconfigure(encoding='utf-8')
  except Exception:pass
 cmd,*v=sys.argv[1:] or ['help'];p,o=opts(v)
 if cmd=='help':out=help()
 elif cmd=='init-project':out=init_project(safe(p[0],'project identifier'),p[1] if len(p)>1 else None,o)
 elif cmd=='set-platform':out=setplatform(safe(p[0],'project identifier'),o)
 elif cmd=='init-page':out=init_page(safe(p[0],'project identifier'),safe(p[1],'page identifier'),p[2] if len(p)>2 else None,o)
 elif cmd=='set-article-path':out=setarticlepath(safe(p[0],'project identifier'),safe(p[1],'page identifier'),o)
 elif cmd=='new-source':out=new_source(p[0],p[1],o)
 elif cmd=='source-call':out=call(p[0],p[1],p[2],o)
 elif cmd=='source-budget':out=budget(p[0],p[1],p[2])
 elif cmd=='source-ready':out=ready(p[0],p[1],p[2])
 elif cmd=='guidelines':out=guidelines(p[0],p[1],o)
 elif cmd=='inventory':out=inventory(p[0],p[1],p[2],o)
 elif cmd=='spec-compact':out=compact(p[0],p[1],p[2])
 elif cmd=='spec-pattern-map':out=patternmap(p[0],p[1],p[2])
 elif cmd=='source-delta':out=sourcedelta(p[0],p[1],p[2])
 elif cmd=='source-patch':out=patch(p[0],p[1],p[2],o)
 elif cmd=='new-run':out=newrun(p[0],p[1],o)
 elif cmd=='convert-source':out=convertsource(p[0],p[1],o)
 elif cmd=='new-conversion-run':out=newconversionrun(p[0],p[1],o)
 elif cmd=='transition':out=transition(p[0],p[1],p[2],p[3])
 elif cmd=='new-candidate':out=candidate(p[0],p[1],p[2],o)
 elif cmd=='candidate-result':out=result(p[0],p[1],p[2],p[3],o)
 elif cmd=='qa-record':out=qarecord(p[0],p[1],p[2],p[3],o)
 elif cmd=='qa-summary':out=summary(p[0],p[1],p[2])
 elif cmd=='release-check':out=releasecheck(p[0],p[1],p[2],o)
 elif cmd=='release':out=release(p[0],p[1],p[2])
 elif cmd=='new-pdf-export':out=newpdfexport(p[0],p[1],p[2],o)
 elif cmd=='pdf-result':out=pdfresult(p[0],p[1],p[2],p[3],o)
 elif cmd=='pdf-qa-record':out=pdfqarecord(p[0],p[1],p[2],p[3],p[4],o)
 elif cmd=='pdf-qa-summary':out=pdfqasummary(p[0],p[1],p[2],p[3])
 elif cmd=='pdf-release':out=pdfrelease(p[0],p[1],p[2],p[3])
 elif cmd=='new-materialization':out=newmaterialization(p[0],p[1],p[2],o)
 elif cmd=='materialization-result':out=materializationresult(p[0],p[1],p[2],p[3],o)
 elif cmd=='release-materialize':out=releasematerialize(p[0],p[1],p[2])
 elif cmd=='resolve-question':out=resolve(p[0],p[1],p[2],o)
 elif cmd=='source-fail':out=srcfail(p[0],p[1],p[2],o.get('message'))
 elif cmd=='next-repair':out=nextrepair(p[0],p[1],p[2])
 elif cmd=='needs-review':out=terminal(p[0],p[1],p[2],'NEEDS_REVIEW',o.get('message'))
 elif cmd=='fail':out=terminal(p[0],p[1],p[2],'FAILED',o.get('message'))
 elif cmd=='status':out=report(p[0],p[1] if len(p)>1 else None)
 else:bad(f'Unknown command: {cmd}')
 print(out if isinstance(out,str) else dump(out,cmd in COMPACT_OUT))
if __name__=='__main__':
 try:main()
 except Exception as e:print(e,file=sys.stderr);sys.exit(1)
