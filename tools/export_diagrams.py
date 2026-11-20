"""Export the same diagram model as a vector PDF and portable editor bundle."""
import argparse
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import reportlab
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A3, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from render_diagrams import ROOT, TARGET, edge_points, load_views, node_lines, style


def draw_view(document, view):
    height=view['height']
    def text(x,y,lines,size=23,bold=False,align='left',color='#111111'):
        document.setFillColor(HexColor(color));document.setFont('AtlasBold' if bold else 'AtlasRegular',size)
        for i,line in enumerate(lines):
            if align=='center':document.drawCentredString(x,height-y-i*size*1.25,line)
            else:document.drawString(x,height-y-i*size*1.25,line)
    def rect(x,y,w,h,fill,stroke,radius=8,dashed=False):
        document.setFillColor(HexColor(fill));document.setStrokeColor(HexColor(stroke));document.setLineWidth(1.8)
        document.setDash([8,6] if dashed else [])
        document.roundRect(x,height-y-h,w,h,radius,fill=1,stroke=1)
        document.setDash([])
    text(42,38,[f'{view["number"]:02d} / FRANARK / {view["notation"].upper()}'],17,color='#4a5664')
    text(42,88,[view['title']],36,True);text(42,123,[view['caption']],20)
    for group in view.get('groups',[]):
        rect(group['x'],group['y'],group['w'],group['h'],group.get('fill','#f8fafc'),'#cbd5df',10,group.get('dashed',False))
        text(group['x']+20,group['y']+32,[group['label']],21,True)
    for edge in view.get('edges',[]):
        pts=edge_points(view,edge);document.setStrokeColor(HexColor('#52677a'));document.setLineWidth(1.8)
        document.setDash([8,6] if edge.get('dashed') else [])
        path=document.beginPath();path.moveTo(pts[0][0],height-pts[0][1])
        for x,y in pts[1:]:path.lineTo(x,height-y)
        document.drawPath(path);document.setDash([])
        px,py=pts[-2];x,y=pts[-1];dx,dy=x-px,y-py;length=(dx*dx+dy*dy)**.5
        if length:
            ux,uy=dx/length,dy/length
            path=document.beginPath();path.moveTo(x-ux*11-uy*5,height-(y-uy*11+ux*5));path.lineTo(x,height-y);path.lineTo(x-ux*11+uy*5,height-(y-uy*11-ux*5));document.drawPath(path)
    for node in view['nodes']:
        x,y,w,h=(node[k] for k in ('x','y','w','h'));fill,stroke,line=style(node);shape=node.get('shape')
        document.setFillColor(HexColor(fill));document.setStrokeColor(HexColor(stroke));document.setLineWidth(1.8);document.setDash([8,6] if line=='dashed' else [])
        if shape=='diamond':
            path=document.beginPath();path.moveTo(x+w/2,height-y);path.lineTo(x+w,height-y-h/2);path.lineTo(x+w/2,height-y-h);path.lineTo(x,height-y-h/2);path.close();document.drawPath(path,stroke=1,fill=1)
        elif shape=='ellipse':document.ellipse(x,height-y-h,x+w,height-y,stroke=1,fill=1)
        elif shape=='database':
            path=document.beginPath();path.moveTo(x,height-y-10);path.curveTo(x,height-y+3,x+w,height-y+3,x+w,height-y-10);path.lineTo(x+w,height-y-h+10);path.curveTo(x+w,height-y-h-3,x,height-y-h-3,x,height-y-h+10);path.close();document.drawPath(path,stroke=1,fill=1)
            path=document.beginPath();path.moveTo(x,height-y-10);path.curveTo(x,height-y-20,x+w,height-y-20,x+w,height-y-10);document.drawPath(path)
        elif shape=='document':
            path=document.beginPath();path.moveTo(x,height-y);path.lineTo(x+w,height-y);path.lineTo(x+w,height-y-h+10);path.curveTo(x+w*.65,height-y-h+28,x+w*.35,height-y-h-8,x,height-y-h+10);path.close();document.drawPath(path,stroke=1,fill=1)
        else:rect(x,y,w,h,fill,stroke,20 if shape=='state' else 8,line=='dashed')
        document.setDash([])
        lines=node_lines(node);size=node.get('font_size',23)
        text(x+w/2,y+h/2-(len(lines)-1)*size*.625+size*.35,lines,size,align='center')
    for edge in view.get('edges',[]):
        if edge.get('label'):
            x,y=edge['label_at'];document.setFillColor(HexColor('#ffffff'));document.rect(x-4,height-y-7,len(edge['label'])*10.8+8,26,fill=1,stroke=0)
            text(x,y,[edge['label']],18)
    for note in view.get('notes',[]):text(note['x'],note['y'],note['text'].split('\n'),note.get('size',19),color='#354352')
    document.setStrokeColor(HexColor('#d2d9e0'));document.line(42,78,view['width']-42,78)
    text(42,height-48,[view['legend']],17)
    text(42,height-21,[view.get('footnote','SFC tenant target / Synthetic pilot / External connections remain unverified')],16,color='#4a5664')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=ROOT/'output/pdf/Franark_SFC_System_Atlas.pdf')
    parser.add_argument('--bundle',type=Path)
    args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    font_dir=Path(reportlab.__file__).parent/'fonts'
    for name,file in [('AtlasRegular','Vera.ttf'),('AtlasBold','VeraBd.ttf')]:pdfmetrics.registerFont(TTFont(name,str(font_dir/file)))
    size=landscape(A3);document=canvas.Canvas(str(args.output),pagesize=size)
    document.setTitle('Franark - SFC System Atlas');document.setAuthor('Ozlem Polat')
    for view in load_views():
        scale=min(size[0]/view['width'],size[1]/view['height'])
        document.saveState();document.translate((size[0]-view['width']*scale)/2,(size[1]-view['height']*scale)/2);document.scale(scale,scale)
        document.bookmarkPage(view['id']);document.addOutlineEntry(view['title'],view['id'],0,False)
        draw_view(document,view);document.restoreState();document.showPage()
    document.save();print(args.output)
    if args.bundle:
        from render_diagrams import combined_scene
        args.bundle.parent.mkdir(parents=True,exist_ok=True)
        with ZipFile(args.bundle,'w',ZIP_DEFLATED) as archive:
            archive.writestr('Franark_SFC_Architecture.excalidraw',json.dumps(combined_scene(),ensure_ascii=False,separators=(',',':'))+'\n')
            archive.write(ROOT/'docs/diagrams/atlas.json','model/atlas.json')
            for view in load_views():
                for suffix in ('.excalidraw','.mmd','.svg'):
                    archive.write(TARGET/(view['id']+suffix),'views/'+view['id']+suffix)
            archive.writestr('README.md', '# Franark SFC architecture views\n\nI open Franark_SFC_Architecture.excalidraw for the full board, or one views/*.excalidraw file for a single view. Every concept and label is a native editable element. Arrows are bound to their target nodes.\n\nThe .mmd files use Mermaid notation appropriate to each relationship. SVG files are scalable previews. The model retains stable concept IDs for later organizational mapping. Diagram edits do not implement the proposed functionality.\n\nBlue: implemented synthetic pilot. Green: existing external/manual process. Amber dashed: prepared connection awaiting verification. Gray dashed: proposed option. Gray solid: logical concept.\n')
        print(args.bundle)


if __name__=='__main__':main()
