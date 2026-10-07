"""Validate local architecture review links and seven-part chapter structure."""
from pathlib import Path
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from PIL import Image

HERE=Path(__file__).resolve().parent
DOC=HERE.parents[1]
p=DOC/'系统模块总览.md'
s=p.read_text(encoding='utf8')
modules=[m for m in re.finditer(r'^#{3,4} (\d[^\n]+)\n([\s\S]*?)(?=^#{1,4} |\Z)',s,re.M) if '##### 1.' in m[2]]
assert len(modules)==38
for m in modules:
    assert re.findall(r'^##### (\d)\.',m[2],re.M)==list('1234567'),m[1]
for file in [p,HERE/'模块与工程对应核查.md']:
    for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',file.read_text(encoding='utf8')):
        if link.startswith(('https:','http:','#','mailto:')):continue
        assert (file.parent/link.split('#')[0]).resolve().exists(),(file,link)
for name in ['系统架构总图-20261007','138K音视频候选架构-20261007']:
    assert Image.open(HERE/(name+'.png')).size==(1600,1200)
    svg=ET.parse(HERE/(name+'.svg')).getroot()
    assert (svg.get('width'),svg.get('height'))==('1600','1200')
report={'baseline':'3c14bb4e225c8971ab90c4f7c85c684dfb42d247',
        'evidence':'L0 static review only','functional_sections':38,'detail_subsections':266,
        'mermaid_blocks':len(re.findall(r'^```mermaid',s,re.M)),
        'source_project_hdl_entries':{'60K':32,'138K_L':45},'links_valid':True,
        'diagram_pixels':[1600,1200],'md_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
# Optional run-specific rendering/protection checks; absent when used elsewhere.
workspace=DOC.parent
backup=workspace/'confluence-audio-import/系统模块总览-架构核查前-20261007.md'
manifest=workspace/'confluence-audio-import/publish-diagrams-manifest.json'
if backup.exists():
    def midi(t):return re.search(r'^#### 3\.2\.2 [\s\S]*?(?=^### 3\.3 )',t,re.M)[0]
    assert midi(s)==midi(backup.read_text(encoding='utf8'))
    report['MIDI_section_preserved_exactly']=True
if manifest.exists():
    data=json.loads(manifest.read_text(encoding='utf8'))
    assert data['source_sha256']==report['md_sha256']
    assert len(data['items'])==38
    report['mermaid_rendered']=38
(HERE/'本地核查结果.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(report,ensure_ascii=False))
