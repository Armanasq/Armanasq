#!/usr/bin/env python3
"""Render public GitHub research visuals as safe standalone SVG files."""
import argparse
import html
import json
import math
import os
import urllib.request
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path

BG = '#0b0f19'
WHITE = '#f3f5fb'
MUTED = '#b9c2d4'
EDGE = '#29394e'
VIOLET = '#baa8fc'
GREEN = ['#30374b','#b3ecd5','#7ee0be','#4dcc9f','#31a981']
LEFT = ['#21293b','#488876','#287b67','#226a5c','#1b5b4d']
RIGHT = ['#283349','#6ba993','#3c9880','#2d886e','#21735c']
TITLES = {
 'TE-PINN-Transformer-Enhanced-Physics-Informed-Neural-Network-Quaternion-Orientation-Estimation':'TE-PINN',
 'End-to-End-Deep-Learning-Framework-for-Real-Time-Inertial-Attitude-Estimation-using-6DoF-IMU':'6DoF IMU',
 'The-Health-and-Medicine-OxML-competition-track':'OxML Health',
 'Recent-Advancements-in-Deep-Learning-Applications-and-Methods-for-Autonomous-Navigation':'Navigation survey',
 '3D-Attention-U-Net-for-Multiple-Sclerosis-Lesion-Segmentation':'3D Attention U-Net',
 'phd_tracker':'PhD Tracker', 'Deep-VO':'Deep-VO', 'OpenSLAM':'OpenSLAM',
}


def esc(v):
    return html.escape(str(v), quote=True)


def text(x,y,value,size=16,color=WHITE,bold=False,align='start'):
    return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{align}" fill="{color}" '
            f'font-family="Arial,Helvetica,sans-serif" font-size="{size}" '
            f'font-weight="{700 if bold else 400}">{esc(value)}</text>')


def svg(title,description,body,w=1200,h=600):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" '
            'aria-labelledby="title description">'
            f'<title id="title">{esc(title)}</title><desc id="description">{esc(description)}</desc>'
            '<defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#141b30"/>'
            '<stop offset="1" stop-color="#0b0f19"/></linearGradient></defs>'
            f'<rect width="{w}" height="{h}" rx="18" fill="url(#bg)"/>'
            f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="18" fill="none" stroke="{EDGE}"/>'
            f'{body}</svg>\n')


def cube(x,y,h,scale,level):
    a=7.1*scale; b=4.4*scale
    side1=f'{x:.1f},{y-h:.1f} {x+a:.1f},{y-h+b:.1f} {x+a:.1f},{y+b:.1f} {x:.1f},{y:.1f}'
    side2=f'{x+a:.1f},{y-h+b:.1f} {x+2*a:.1f},{y-h:.1f} {x+2*a:.1f},{y:.1f} {x+a:.1f},{y+b:.1f}'
    top=f'{x:.1f},{y-h:.1f} {x+a:.1f},{y-h-b:.1f} {x+2*a:.1f},{y-h:.1f} {x+a:.1f},{y-h+b:.1f}'
    return (f'<polygon points="{side1}" fill="{LEFT[level]}"/>'
            f'<polygon points="{side2}" fill="{RIGHT[level]}"/>'
            f'<polygon points="{top}" fill="{GREEN[level]}"/>')


def skyline(snapshot):
    rows=snapshot.get('featured',[])
    if not rows:
        raise ValueError('No verified public projects for skyline')
    rows=sorted(rows,key=lambda r:(-int(r.get('stars',0)),r.get('name','')))[:8]
    m=max(1,max(int(r.get('stars',0)) for r in rows))
    p=[text(38,48,'RESEARCH SOFTWARE / OPEN SOURCE',14,VIOLET,True),
       text(38,94,'The project skyline',42,WHITE,True),
       text(38,126,'Tower height is proportional to public repository stars; labels show exact values.',16,MUTED),
       f'<path d="M38 151H1160" stroke="{EDGE}"/>']
    for i in range(8):
        p.append(f'<path d="M62 {332+i*20} H1150" stroke="{EDGE}" stroke-opacity=".5"/>')
    for i,r in enumerate(rows):
        x=80+140*i; y=412+(i%2)*10; stars=int(r.get('stars',0))
        h=175*stars/m
        p.append(f'<polygon points="{x-16},{y+3} {x+5},{y-9} {x+66},{y+21} {x+42},{y+35}" fill="#151e30" stroke="{EDGE}"/>')
        p.append(cube(x+6,y,4,3.1,0))
        if stars:
            p.append(cube(x+6,y-13,h,3.1,1+(i%4)))
        col=GREEN[1+(i%4)]
        p.append(text(x+28,max(171,y-h-38) if stars else y-34,f'{stars} stars',18,col,True,'middle'))
        title=TITLES.get(r.get('name',''),r.get('name','')[:15])
        p.append(text(x+28,490,title,15,WHITE,True,'middle'))
    p += [f'<path d="M40 546H1160" stroke="{EDGE}"/>',
          text(40,577,'PUBLIC REPOSITORY METADATA · NO PRIVATE PROJECTS',13,MUTED),
          text(1160,577,snapshot.get('generated_at_utc','')[:10]+' UTC',13,MUTED,False,'end')]
    return svg('GitHub project skyline','An isometric skyline of verified public repository star counts. Heights have a linear scale.',''.join(p),1200,601)


class CalendarHTML(HTMLParser):
    def __init__(self):
        super().__init__();self.days={}
    def handle_starttag(self,tag,attrs):
        if tag!='td':return
        d=dict(attrs)
        if 'data-date' not in d or 'data-level' not in d:return
        try:level=int(d['data-level']);date.fromisoformat(d['data-date'])
        except (ValueError,TypeError):return
        if 0<=level<=4:self.days[d['data-date']]={'date':d['data-date'],'level':level,'count':None}


def get_calendar(login,token):
    now=datetime.now(timezone.utc)
    if token:
        start=now-timedelta(days=364)
        q=('query($name:String!,$start:DateTime!,$end:DateTime!){user(login:$name){'
           'contributionsCollection(from:$start,to:$end){contributionCalendar{totalContributions '
           'weeks{contributionDays{date contributionCount contributionLevel}}}}}}')
        payload=json.dumps({'query':q,'variables':{'name':login,'start':start.isoformat(),
                           'end':now.isoformat()}}).encode()
        req=urllib.request.Request('https://api.github.com/graphql',data=payload,
                headers={'Authorization':'Bearer '+token,'Content-Type':'application/json',
                'Accept':'application/vnd.github+json','User-Agent':'Armanasq-Profile'})
        try:
            with urllib.request.urlopen(req,timeout=20) as response:result=json.load(response)
            cal=result['data']['user']['contributionsCollection']['contributionCalendar']
            codes={'NONE':0,'FIRST_QUARTILE':1,'SECOND_QUARTILE':2,
                   'THIRD_QUARTILE':3,'FOURTH_QUARTILE':4}
            days=[{'date':d['date'],'level':codes[d['contributionLevel']],
                   'count':int(d['contributionCount'])}
                  for week in cal['weeks'] for d in week['contributionDays']]
            if len({d['date'] for d in days})>=300:
                return {'status':'verified','source':'GitHub GraphQL contribution calendar',
                        'granularity':'daily-count','days':days,
                        'total_reported':cal['totalContributions'],'generated_at_utc':now.isoformat()}
        except (OSError,KeyError,TypeError,ValueError):pass
    try:
        req=urllib.request.Request('https://github.com/users/'+login+'/contributions',
                 headers={'User-Agent':'Mozilla/5.0','Accept':'text/html'})
        with urllib.request.urlopen(req,timeout=20) as response:
            html_page=response.read(500000).decode('utf-8','replace')
        p=CalendarHTML();p.feed(html_page)
        days=sorted(p.days.values(),key=lambda x:x['date'])
        if len(days)>=300:
            return {'status':'verified','source':'GitHub public contribution calendar',
                    'granularity':'intensity-level','days':days,'total_reported':None,
                    'generated_at_utc':now.isoformat()}
    except (OSError,ValueError):pass
    return {'status':'unavailable','source':None,'granularity':None,'days':[],'total_reported':None,
            'generated_at_utc':now.isoformat()}


def calendar_svg(data):
    days=data.get('days') or []
    if data.get('status')!='verified' or len(days)<300:
        content=(text(35,47,'CONTRIBUTIONS / ISOMETRIC CALENDAR',14,VIOLET,True)
          +text(35,121,'Verified daily data unavailable',32,WHITE,True)
          +text(35,163,'No synthetic contribution bars have been drawn.',18,MUTED)
          +text(35,218,'GitHub contribution API will populate this component once available.',15,MUTED))
        return svg('Contribution calendar data unavailable','No fabricated bars displayed.',content,1200,265)
    cells=[];dated=[]
    for d in days:
        try:dated.append((date.fromisoformat(d['date']),d))
        except (KeyError,ValueError):continue
    dated.sort(key=lambda x:x[0])
    if len(dated)<300:
        raise ValueError('Invalid dates in calendar response')
    first=dated[0][0]-timedelta(days=(dated[0][0].weekday()+1)%7)
    maxcount=max(1,max(int(r.get('count') or 0) for _,r in dated))
    for dt,r in dated:
        week=(dt-first).days//7;weekday=(dt.weekday()+1)%7
        if not 0<=week<55:continue
        level=int(r['level'])
        if not 0<=level<=4:continue
        n=r.get('count')
        h=4+65*math.log1p(n)/math.log1p(maxcount) if isinstance(n,int) and n>=0 else 4+15*level
        x=126+week*17.3-weekday*7.7;y=355+week*1.15+weekday*8
        cells.append((y,x,cube(x,y,h,1,level)))
    iscount=data.get('granularity')=='daily-count'
    meta=data.get('total_reported')
    title=(f'{meta:,} contributions' if iscount and isinstance(meta,int) else 'Public activity levels')
    content=(text(38,48,'CONTRIBUTIONS / ISOMETRIC CALENDAR',14,VIOLET,True)
             +text(38,96,'365 days in perspective',42,WHITE,True)
             +text(38,127,'Observed GitHub activity; each block represents one day.',17,MUTED)
             +text(1157,91,title,21,GREEN[2],True,'end'))
    content+=f'<path d="M39 149H1161" stroke="{EDGE}"/>'
    content+=''.join(c[2] for c in sorted(cells,key=lambda c:(c[0],c[1])))
    content+=text(41,526,'LOW ACTIVITY',13,MUTED)
    content+=''.join(cube(163+i*38,518,8+i*4,.85,i) for i in range(5))
    content+=text(391,526,'HIGH ACTIVITY',13,MUTED)
    content+=text(1152,526,data.get('source','GitHub'),13,MUTED,False,'end')
    content+=f'<path d="M39 547H1161" stroke="{EDGE}"/>'
    content+=text(39,577,'Daily values: '+('counts' if iscount else 'intensity only')+' · No repository details or synthetic observations.',13,MUTED)
    return svg('GitHub 3D isometric contributions','Verified GitHub daily data projected into three-dimensional SVG blocks.',content,1200,598)


def write_assets(snapshot,contrib,outdir):
    dest=Path(outdir);dest.mkdir(parents=True,exist_ok=True)
    files={'project-skyline.svg':skyline(snapshot),'contributions-3d.svg':calendar_svg(contrib)}
    for name,content in files.items():
        (dest/name).write_text(content,encoding='utf-8')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--snapshot',default='data/public-snapshot.json')
    parser.add_argument('--contributions',default='data/contributions.json')
    parser.add_argument('--output',default='assets/visuals')
    parser.add_argument('--user',default='Armanasq')
    parser.add_argument('--offline',action='store_true')
    args=parser.parse_args()
    snap=json.loads(Path(args.snapshot).read_text(encoding='utf-8'))
    store=Path(args.contributions)
    prior=json.loads(store.read_text(encoding='utf-8')) if store.exists() else None
    fetched={'status':'unavailable','days':[],'total_reported':None,'source':None,'granularity':None}
    if not args.offline:
        fetched=get_calendar(args.user,os.environ.get('GH_TOKEN',''))
    if fetched.get('status')=='verified':
        data=fetched
    elif prior and prior.get('status')=='verified' and len(prior.get('days',[]))>=300:
        data=prior
    else:
        data=fetched
    store.parent.mkdir(parents=True,exist_ok=True)
    store.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    write_assets(snap,data,args.output)
    print('Refreshed 3D profile assets:',data['status'],len(data.get('days',[])),'days')


if __name__=='__main__':main()
