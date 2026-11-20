"""Render focused SVG, Mermaid and native Excalidraw views from one model.

Semantic IDs, positions, grouping and readiness are independent model fields.
No network service or diagram editor is required to build the assets.
"""
import argparse
from copy import deepcopy
from hashlib import sha256
from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'docs/diagrams/atlas.json'
TARGET = ROOT / 'src/franark/resources/diagrams'
INK = '#111111'
COLORS = {
    'pilot': ('#e7f1ff', '#326cb0', 'solid'),
    'existing': ('#edf7e8', '#587b42', 'solid'),
    'prepared': ('#fff4d7', '#986b21', 'dashed'),
    'proposed': ('#ffffff', '#788493', 'dashed'),
    'logical': ('#f2f4f7', '#687787', 'solid'),
}


def load_views():
    return json.loads(MODEL.read_text())['views']


def style(node):
    fill, stroke, line = COLORS[node.get('status', 'pilot')]
    return node.get('fill', fill), node.get('stroke', stroke), line


def node_lines(node):
    return node.get('lines', node['label'].split('\n'))


def anchor(node, side):
    x, y, w, h = (node[k] for k in ('x', 'y', 'w', 'h'))
    return {'N': (x + w / 2, y), 'S': (x + w / 2, y + h),
            'E': (x + w, y + h / 2), 'W': (x, y + h / 2)}[side]


def edge_points(view, edge):
    nodes = {n['id']: n for n in view['nodes']}
    return [anchor(nodes[edge['from']], edge.get('start', 'S')),
            *edge.get('via', []), anchor(nodes[edge['to']], edge.get('end', 'N'))]


def svg(view):
    w, h = view['width'], view['height']
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">',
           f'<title id="title">{escape(view["title"])}</title><desc id="desc">{escape(view["caption"])}</desc>',
           '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M 1 1 L 9 5 L 1 9" fill="none" stroke="#52677a" stroke-width="1.5"/></marker></defs>',
           f'<rect width="{w}" height="{h}" fill="white"/>']

    def text(x, y, lines, size=23, weight='normal', align='start', color=INK):
        out.append(f'<text x="{x}" y="{y}" text-anchor="{align}" font-family="DejaVu Sans,Arial,sans-serif" font-size="{size}" font-weight="{weight}" fill="{color}">')
        for i, line in enumerate(lines):
            out.append(f'<tspan x="{x}" dy="{0 if not i else size * 1.25}">{escape(line)}</tspan>')
        out.append('</text>')

    text(42, 38, [f'{view["number"]:02d} / FRANARK / {view["notation"].upper()}'], 17, color='#4a5664')
    text(42, 88, [view['title']], 36, 'bold')
    text(42, 123, [view['caption']], 20)
    for group in view.get('groups', []):
        dash = ' stroke-dasharray="8 6"' if group.get('dashed') else ''
        out.append(f'<rect x="{group["x"]}" y="{group["y"]}" width="{group["w"]}" height="{group["h"]}" rx="10" fill="{group.get("fill", "#f8fafc")}" stroke="#cbd5df" stroke-width="1.4"{dash}/>')
        text(group['x'] + 20, group['y'] + 32, [group['label']], 21, 'bold')
    for edge in view.get('edges', []):
        points = edge_points(view, edge)
        dash = ' stroke-dasharray="8 6"' if edge.get('dashed') else ''
        out.append(f'<polyline points="{" ".join(f"{x},{y}" for x, y in points)}" fill="none" stroke="#52677a" stroke-width="1.8" stroke-linejoin="round" marker-end="url(#arrow)"{dash}/>')
    for node in view['nodes']:
        x, y, nw, nh = (node[k] for k in ('x', 'y', 'w', 'h'))
        fill, stroke, line = style(node)
        dash = ' stroke-dasharray="8 6"' if line == 'dashed' else ''
        attrs = f'fill="{fill}" stroke="{stroke}" stroke-width="1.8"{dash}'
        shape = node.get('shape', 'rectangle')
        if shape == 'diamond':
            out.append(f'<polygon points="{x+nw/2},{y} {x+nw},{y+nh/2} {x+nw/2},{y+nh} {x},{y+nh/2}" {attrs}/>')
        elif shape == 'ellipse':
            out.append(f'<ellipse cx="{x+nw/2}" cy="{y+nh/2}" rx="{nw/2}" ry="{nh/2}" {attrs}/>')
        elif shape == 'database':
            out.append(f'<path d="M{x},{y+10} C{x},{y-3} {x+nw},{y-3} {x+nw},{y+10} L{x+nw},{y+nh-10} C{x+nw},{y+nh+3} {x},{y+nh+3} {x},{y+nh-10} Z" {attrs}/>')
            out.append(f'<path d="M{x},{y+10} C{x},{y+20} {x+nw},{y+20} {x+nw},{y+10}" fill="none" stroke="{stroke}" stroke-width="1.4"/>')
        elif shape == 'document':
            out.append(f'<path d="M{x},{y} H{x+nw} V{y+nh-10} C{x+nw*0.65},{y+nh-28} {x+nw*0.35},{y+nh+8} {x},{y+nh-10} Z" {attrs}/>')
        else:
            radius = 20 if shape == 'state' else 8
            out.append(f'<rect x="{x}" y="{y}" width="{nw}" height="{nh}" rx="{radius}" {attrs}/>')
        lines, size = node_lines(node), node.get('font_size', 23)
        text(x + nw/2, y + nh/2 - (len(lines)-1)*size*0.625 + size*0.35, lines, size, align='middle')
    for edge in view.get('edges', []):
        if edge.get('label'):
            x, y = edge['label_at']
            out.append(f'<rect x="{x-4}" y="{y-19}" width="{len(edge["label"])*10.8+8}" height="26" rx="3" fill="white"/>')
            text(x, y, [edge['label']], 18)
    for note in view.get('notes', []):
        text(note['x'], note['y'], note['text'].split('\n'), note.get('size', 19), color='#354352')
    out.append(f'<line x1="42" y1="{h-78}" x2="{w-42}" y2="{h-78}" stroke="#d2d9e0"/>')
    text(42, h-48, [view['legend']], 17)
    text(42, h-21, [view.get('footnote', 'SFC tenant target / Synthetic pilot / External connections remain unverified')], 16, color='#4a5664')
    out.append('</svg>')
    return '\n'.join(out) + '\n'


def excalidraw(view):
    """Native bound text and arrows; no flattened SVG or image import."""
    elements = []
    prefix = view['id'] + '-'

    def base(eid, kind, x, y, w, h):
        seed = int(sha256((prefix + eid).encode()).hexdigest()[:7], 16)
        return dict(id=prefix+eid, type=kind, x=x, y=y, width=w, height=h,
                    angle=0, strokeColor=INK, backgroundColor='transparent', fillStyle='solid',
                    strokeWidth=1.8, strokeStyle='solid', roughness=0, opacity=100,
                    groupIds=[], frameId=None, roundness=None, seed=seed, version=1,
                    versionNonce=seed, isDeleted=False, boundElements=[], updated=0,
                    created=None, index=None, link=None, locked=False)

    def text(eid, x, y, value, size=23, w=None, container=None, align='left'):
        lines = value.split('\n')
        element = base(eid, 'text', x, y, w or max(len(s) for s in lines)*size*0.62, len(lines)*size*1.25)
        element.update(text=value, originalText=value, fontSize=size, baseFontSize=None,
                       fontFamily=2, textAlign=align, verticalAlign='middle' if container else 'top',
                       containerId=prefix+container if container else None, autoResize=False, lineHeight=1.25)
        return element

    elements += [text('eyebrow',42,20,f'{view["number"]:02d} / FRANARK / {view["notation"].upper()}',17),
                 text('heading',42,51,view['title'],36), text('caption',42,103,view['caption'],20)]
    for group in view.get('groups', []):
        item = base('group-'+group['id'], 'rectangle', group['x'], group['y'], group['w'], group['h'])
        item.update(strokeColor='#cbd5df', backgroundColor=group.get('fill', '#f8fafc'),
                    strokeStyle='dashed' if group.get('dashed') else 'solid', roundness={'type':3},
                    customData={'kind':'group-container', 'conceptId':group['id']})
        elements += [item, text('group-label-'+group['id'],group['x']+20,group['y']+10,group['label'],21)]
    node_map = {}
    for node in view['nodes']:
        nid, shape = node['id'], node.get('shape', 'rectangle')
        kind = shape if shape in {'diamond', 'ellipse'} else 'rectangle'
        box = base(nid,kind,node['x'],node['y'],node['w'],node['h'])
        fill, stroke, line = style(node)
        box.update(strokeColor=stroke, backgroundColor=fill, strokeStyle=line,
                   roundness={'type':3} if kind == 'rectangle' else None,
                   groupIds=[prefix+'concept-'+nid],
                   boundElements=[{'id':prefix+'text-'+nid,'type':'text'}],
                   customData={'conceptId':node.get('concept',nid),'status':node.get('status','pilot'),'shape':shape})
        label = '\n'.join(node_lines(node)); size=node.get('font_size',23)
        label_el = text('text-'+nid, node['x']+6, node['y']+(node['h']-len(label.split('\n'))*size*1.25)/2,
                        label,size,node['w']-12,nid,'center')
        label_el['groupIds'] = list(box['groupIds'])
        node_map[nid]=box
        elements += [box,label_el]
    for index, edge in enumerate(view.get('edges', [])):
        points = edge_points(view,edge); x,y=points[0]
        eid=f'edge-{index}'
        item=base(eid,'arrow',x,y,max(p[0] for p in points)-min(p[0] for p in points),max(p[1] for p in points)-min(p[1] for p in points))
        side_fraction={'N':[.5,0],'S':[.5,1],'E':[1,.5],'W':[0,.5]}
        item.update(points=[[px-x,py-y] for px,py in points], startArrowhead=None,endArrowhead='arrow',elbowed=False,
                    strokeColor='#52677a',strokeStyle='dashed' if edge.get('dashed') else 'solid',
                    startBinding={'elementId':prefix+edge['from'],'fixedPoint':side_fraction[edge.get('start','S')],'mode':'orbit'},
                    endBinding={'elementId':prefix+edge['to'],'fixedPoint':side_fraction[edge.get('end','N')],'mode':'orbit'})
        for nid in (edge['from'],edge['to']):
            node_map[nid]['boundElements'].append({'id':item['id'],'type':'arrow'})
        if edge.get('label'):
            lx,ly=edge['label_at']
            label=text(eid+'-label',lx,ly-19,edge['label'],18,container=eid)
            item['boundElements']=[{'id':label['id'],'type':'text'}]
            elements += [item,label]
        else:
            elements.append(item)
    for index,note in enumerate(view.get('notes',[])):
        elements.append(text(f'note-{index}',note['x'],note['y']-20,note['text'],note.get('size',19)))
    elements += [text('legend',42,view['height']-64,view['legend'],17),
                 text('footnote',42,view['height']-37,view.get('footnote','SFC tenant target / Synthetic pilot / External connections remain unverified'),16)]
    return {'type':'excalidraw','version':2,'source':'https://github.com/OzPol/franark',
            'elements':elements,'appState':{'viewBackgroundColor':'#ffffff','gridSize':None},'files':{}}


def generated_files():
    result={}
    for view in load_views():
        name=view['id']
        result[TARGET/(name+'.svg')]=svg(view)
        result[TARGET/(name+'.excalidraw')]=json.dumps(excalidraw(view),ensure_ascii=False,separators=(',',':'))+'\n'
        result[TARGET/(name+'.mmd')]=view['mermaid'].rstrip()+'\n'
    result[TARGET/'index.json']=json.dumps([
        {key:view[key] for key in ('id','number','title','notation','caption')} for view in load_views()],indent=2)+'\n'
    result[ROOT/'src/franark/static/architecture.html']=architecture_html(load_views())
    return result


def architecture_html(views):
    """A focused view selector; no external rendering script or source upload."""
    options=''.join(f'<option value="{v["id"]}">{v["number"]:02d} - {escape(v["title"])}</option>' for v in views)
    sections=[]
    for index, view in enumerate(views):
        name=view['id']
        sections.append(f'''<section id="view-{name}" class="view" {'hidden' if index else ''}>
<h2>{escape(view['title'])}</h2><p>{escape(view['caption'])}</p>
<div class="downloads"><a href="/assets/diagrams/{name}.svg" target="_blank" rel="noopener">Open full-size SVG</a><a href="/assets/diagrams/{name}.excalidraw" download>Editable Excalidraw</a><a href="/assets/diagrams/{name}.mmd" download>Mermaid source</a></div>
<a href="/assets/diagrams/{name}.svg" target="_blank" rel="noopener"><img src="/assets/diagrams/{name}.svg" alt="{escape(view['title']+': '+view['caption'],quote=True)}"></a></section>''')
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Franark - System diagrams</title><style>
:root{font:16px/1.5 'Segoe UI',system-ui,sans-serif;color:#111;background:#f5f7fa}*{box-sizing:border-box}body{margin:0}header{padding:16px 28px;display:flex;gap:24px;flex-wrap:wrap;background:#fff;border-bottom:1px solid #cbd5df}header strong{font-size:22px}a{color:#075a9e}main{max-width:1550px;margin:auto;padding:24px}h1{font-size:30px;margin:8px 0}h2{font-size:24px;margin:0}p{max-width:1100px}.selector{padding:20px;background:#edf3fa;border:1px solid #cbd5df;border-radius:8px;display:flex;align-items:center;gap:16px;flex-wrap:wrap}select{min-height:44px;max-width:100%;font:inherit;color:#111;background:#fff;border:1px solid #8092a5;border-radius:4px;padding:8px 12px}.view{background:#fff;border:1px solid #cbd5df;border-radius:8px;margin:24px 0;padding:24px}.view[hidden]{display:none}.downloads{display:flex;gap:24px;flex-wrap:wrap}.downloads a{min-height:44px;display:inline-flex;align-items:center}img{display:block;width:100%;height:auto;margin-top:12px}.help{font-size:15px;color:#354352}a:focus-visible,select:focus-visible{outline:3px solid #326cb0;outline-offset:3px}@media(max-width:600px){main{padding:12px}.view{padding:12px}header{padding:12px;gap:16px}.selector{padding:12px}}
</style></head><body><header><strong>Franark</strong><a href="/portal">Assessment pilot</a><a href="/">Agent workbench</a><a href="/lab">Capabilities lab</a></header><main><h1>System diagrams</h1><p>Focused views with one concept per node. Groups identify related concepts; dashed nodes distinguish unverified connections and proposed options.</p><div class="selector"><label for="view-select">Choose a view</label><select id="view-select">'''+options+'''</select></div><p class="help">Open an Excalidraw file in the editor to move individual nodes and their bound connectors. Mermaid files use hierarchy, block, flow, state and entity-relationship notation. Downloading a source file does not send records to an external editor.</p>'''+''.join(sections)+'''<noscript><p>View selection requires JavaScript. Each source is also available under /assets/diagrams.</p></noscript></main><script>
const picker=document.getElementById('view-select');
function showView(id){const panel=document.getElementById('view-'+id);if(!panel)return;document.querySelectorAll('.view').forEach(item=>item.hidden=item!==panel);picker.value=id;history.replaceState(null,'','#'+id);}
picker.addEventListener('change',()=>showView(picker.value));
if(location.hash)showView(location.hash.slice(1));
</script></body></html>
'''


def combined_scene():
    elements=[]
    views=load_views()
    row_offsets=[]
    next_y=0
    for start in range(0,len(views),2):
        row_offsets.append(next_y)
        next_y+=max(view['height'] for view in views[start:start+2])+180
    for index,view in enumerate(views):
        ox,oy=(index%2)*1600,row_offsets[index//2]
        page=excalidraw(view)
        frame_id='view-frame-'+view['id']
        frame=deepcopy(page['elements'][0])
        for key in ('text','originalText','fontSize','fontFamily','textAlign','verticalAlign','containerId','autoResize','lineHeight','baseFontSize'):
            frame.pop(key,None)
        frame.update(id=frame_id,type='frame',x=ox,y=oy,width=view['width'],height=view['height'],name=view['title'],frameId=None,groupIds=[],boundElements=[])
        elements.append(frame)
        for element in page['elements']:
            element['x']+=ox; element['y']+=oy; element['frameId']=frame_id
            elements.append(element)
    return {'type':'excalidraw','version':2,'source':'https://github.com/OzPol/franark',
            'elements':elements,'appState':{'viewBackgroundColor':'#ffffff','gridSize':None},'files':{}}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--board',type=Path)
    args=parser.parse_args()
    stale=[]
    for path,content in generated_files().items():
        if args.check:
            if not path.exists() or path.read_text()!=content: stale.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content)
    if stale: raise SystemExit('Stale diagram assets: '+', '.join(stale))
    if args.board:
        args.board.parent.mkdir(parents=True,exist_ok=True)
        args.board.write_text(json.dumps(combined_scene(),ensure_ascii=False,separators=(',',':'))+'\n')
    print(f'{len(load_views())} focused views: '+('current' if args.check else 'rendered'))


if __name__ == '__main__':
    main()
