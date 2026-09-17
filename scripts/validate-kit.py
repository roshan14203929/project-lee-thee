#!/usr/bin/env python3
import json,re,sys
from pathlib import Path
root=Path(__file__).resolve().parent.parent
required=['README.md','AGENTS.md','requirements.txt','scripts/kit.py','scripts/render-page.py','scripts/verify-output.py','.claude/skills/codemap/scripts/codemap.py']
bad=[x for x in required if not(root/x).exists()]
for f in root.rglob('*.json'):
 if any(p in {'.git','.venv','node_modules'} for p in f.parts):continue
 try:json.loads(f.read_text(encoding='utf-8-sig'))
 except Exception:bad.append(f'Invalid JSON {f.relative_to(root)}')

# --- Rule-ID gates -----------------------------------------------------------
# The prefix->home map and the retired list are parsed from docs/rule-ids.md so
# there is exactly one source of truth; docs/ is never delivered to an agent.
ID=r'[A-Z0-9]{2,4}-\d{3}'
DECL=re.compile(rf'^\s*[-|]\s*({ID})[ |]')   # bullet or first table column
ANY=re.compile(rf'\b{ID}\b')
reg=root/'docs'/'rule-ids.md'
homes,retired={},set()
if not reg.exists():bad.append('Missing or invalid: docs/rule-ids.md (rule-ID registry)')
else:
 txt=reg.read_text(encoding='utf-8')
 head,_,tail=txt.partition('## Retired IDs')
 for pre,home in re.findall(r'^\|\s*`([A-Z0-9]{2,4})`\s*\|\s*`([^`]+)`\s*\|',head,re.M):
  homes[pre]=home
 retired={m for m in re.findall(rf'^\|\s*({ID})\s*\|',tail,re.M)}
 if not homes:bad.append('docs/rule-ids.md declares no prefix->home rows')

gdir=root/'guidelines'
declared={}
if homes and gdir.is_dir():
 files=sorted(p for p in gdir.rglob('*.md') if p.is_file())
 for f in files:
  rel=f.relative_to(root).as_posix();isqa='qa' in f.relative_to(gdir).parts
  for n,line in enumerate(f.read_text(encoding='utf-8').splitlines(),1):
   m=DECL.match(line)
   if not m:continue
   rid=m.group(1);pre=rid.rsplit('-',1)[0]
   if pre not in homes:continue               # not a rule ID; a ticket or similar
   # Gate 4: QA files cite, never declare.
   if isqa:bad.append(f'Rule ID declared in a QA file (QA cites, never declares): {rid} at {rel}:{n}');continue
   # Gate 3: an ID may only be declared in the file its prefix owns.
   if homes[pre]!=rel:bad.append(f'Rule ID {rid} declared in {rel}:{n} but prefix {pre} owns {homes[pre]}');continue
   # Gate 1: one declaration per ID.
   if rid in declared:bad.append(f'Duplicate rule ID {rid}: {declared[rid]} and {rel}:{n}');continue
   declared[rid]=f'{rel}:{n}'
 # Gate 2: every citation must resolve to a declared or retired ID.
 for f in files:
  rel=f.relative_to(root).as_posix()
  for n,line in enumerate(f.read_text(encoding='utf-8').splitlines(),1):
   for rid in ANY.findall(line):
    if rid.rsplit('-',1)[0] not in homes:continue
    if rid in declared or rid in retired:continue
    bad.append(f'Rule ID {rid} cited at {rel}:{n} is neither declared nor retired')

if bad:print('\n'.join(f'- {x}' if x.startswith(('Invalid','Rule','Duplicate','docs/')) else f'- Missing or invalid: {x}' for x in bad),file=sys.stderr);raise SystemExit(1)
print(f'Layerlift Python kit structure is valid. Rule IDs: {len(declared)} declared, {len(retired)} retired.')
