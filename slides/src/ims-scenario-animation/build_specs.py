"""Create one reviewed GenOffice page specification at a time."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
C = dict(bg='#F6F7F9', ink='#14213D', muted='#5B6575', orange='#E8742A',
         blue='#2877B5', white='#FFFFFF', peach='#FCEBDD', pale='#E8F1F9', line='#D5DAE1')
FONT = 'Noto Sans CJK TC'

def build(n):
    # Each invocation rereads the agreed style and just this outline entry.
    print((ROOT / 'style.md').read_text())
    outline = json.loads((ROOT / 'outline.json').read_text())['pages'][n-1]
    print(json.dumps(outline, ensure_ascii=False))
    elements, keys, steps = [], {}, []
    def put(key, element):
        keys[key] = len(elements)
        elements.append(element)
        return key
    def para(text, size=14, color='ink', bold=False, align='left'):
        return dict(align=align, lineSpacingPct=105, spaceAfterPt=0,
                    runs=[dict(text=text,sizePt=size,color=C.get(color,color),bold=bold,font=FONT)])
    def text(key, x,y,w,h,s,size=14,color='ink',bold=False,align='left'):
        return put(key, dict(type='text',x=x,y=y,w=w,h=h,
                            paragraphs=[para(t,size,color,bold,align) for t in s.split('\n')]))
    def shape(key,x,y,w,h,fill='white',lines=None,stroke='line',kind='roundRect'):
        d=dict(type='shape',shape=kind,x=x,y=y,w=w,h=h,fill=C[fill])
        if stroke: d['stroke']=dict(color=C[stroke],widthPt=1)
        if lines: d['paragraphs']=[para(*p) for p in lines]
        return put(key,d)
    def line(key,a,b,y,color='orange',double=False):
        put(key,dict(type='shape',shape='lineArrow',x=min(a,b),y=y,w=abs(b-a),h=1,
                     flipH=b<a,stroke=dict(color=C[color],widthPt=1.6)))
        if double:
            put(key+'-return',dict(type='shape',shape='lineArrow',x=min(a,b),y=y+6,
                w=abs(b-a),h=1,flipH=b>a,stroke=dict(color=C[color],widthPt=1.6)))
    def token(key,x,y,color='orange'):
        shape(key,x-8,y-8,16,16,fill=color,stroke='white',kind='ellipse')
    def actor(key,x,title,role,w=134,fill='white'):
        shape(key,x-w//2,164,w,76,fill=fill,
              lines=[(title,17,'orange' if fill!='pale' else 'blue',True,'center'),
                     (role,12,'muted',False,'center')])
        put(key+'-life',dict(type='shape',shape='line',x=x,y=248,w=1,h=382,
                            stroke=dict(color=C['line'],widthPt=0.8)))
    def message(i,a,b,y,label,note,dest,double=False,duration=2200):
        k=f'm{i}'
        line(k+'-line',a,b,y,double=double)
        text(k+'-label',min(a,b)+12,y-28,abs(b-a)-18,25,label,13,'orange',True)
        text(k+'-note',961,y-28,276,46,note,12,'ink')
        token(k+'-dot',a,y)
        path=[(0,0),(b-a,0)]
        if double: path.extend([(b-a,6),(0,6)])
        steps.append(dict(label=label,show=[k+'-label',k+'-line']+([k+'-line-return'] if double else [])+[k+'-note'],
                          packets=[dict(key=k+'-dot',path=path,duration=duration)],pulse=dest))

    title=outline['title']
    text('title',60,34,1160,60,title,30,'ink',True)
    if n==1:
        text('subtitle',60,103,1160,33,'小明已連上 5G、取得 ims PDU session；現在向「電話公司的總機」報到。',15,'muted')
        for x,key,title,role,fill in [(115,'ue','小明 UE','我想用電話','pale'),(300,'p','P-CSCF','門口接待','white'),
            (485,'i','I-CSCF','總機','white'),(670,'s','S-CSCF','專屬承辦人','white'),(855,'h','HSS','客戶資料室','peach')]:
            actor(key,x,title,role,fill=fill)
        text('aside',966,181,265,42,'角色對白',18,'muted',True)
        message(1,115,485,292,'REGISTER','① 小明：我要報到。\n接待加 Path，再交給總機。',['p','i'])
        message(2,485,855,343,'UAR / UAA','② 總機：找哪位承辦人？\n查完 HSS，轉送 REGISTER。',['i','h','s'],True)
        message(3,670,855,394,'MAR / MAA','③ 承辦人：請給認證向量。\nHSS 產生題目與驗證資料。',['s','h'],True)
        message(4,670,115,445,'401：RAND + AUTN','④ 承辦人：先證明你是你。\n小明的 SIM 也驗證網路。',['ue'])
        message(5,115,670,496,'REGISTER + Authorization','⑤ 小明：這是我的回答。\nSIM 算 RES，再產生 Digest。',['s'])
        message(6,670,855,547,'SAR / SAA','⑥ 認證成功，登記承辦人。\n取回 profile、記住 Contact。',['s','h'],True)
        message(7,670,115,598,'200 OK：註冊完成','⑦ 承辦人：我找得到你了。\n小華也完成同樣的註冊。',['ue'])
        text('footer',60,666,1160,30,'逐次點擊 7 次｜橘色：IMS 訊息；Cx 查詢為雙向。SIM 金鑰 K 不上網；SIP 回傳 Digest 證明。',11,'muted')
    elif n==2:
        text('subtitle',60,103,1160,33,'雙方都已註冊。小明按下撥號鍵，SIP 請總機把電話送到小華。',15,'muted')
        for x,key,title,role,fill in [(100,'a','小明','主叫 UE','pale'),(260,'pa','P-CSCF','主叫側接待','white'),
            (420,'i','I-CSCF','總機','white'),(580,'s','S-CSCF','被叫承辦人','white'),
            (740,'pb','P-CSCF','被叫側接待','white'),(900,'b','小華','被叫 UE','pale')]:
            actor(key,x,title,role,w=124,fill=fill)
        shape('h',1010,164,200,76,'peach',[('HSS',17,'orange',True,'center'),('知道承辦人在哪',12,'muted',False,'center')])
        put('h-life',dict(type='shape',shape='line',x=1110,y=248,w=1,h=118,
                         stroke=dict(color=C['line'],widthPt=0.8)))
        message(1,100,420,300,'INVITE + SDP offer','① 小明：請幫我找小華。\nSDP 說明我的媒體位址。',['pa','i'])
        # LIR stops at the HSS's column, whose line is shown only for this query.
        line('m2-line',420,1110,360,double=True)
        text('m2-label',435,332,480,25,'LIR / LIA：小華在哪台 S-CSCF？',13,'orange',True)
        text('m2-note',981,244,252,25,'② HSS：找這台 S-CSCF。',12,'ink')
        token('m2-dot',420,360)
        steps.append(dict(label='LIR / LIA',show=['m2-label','m2-line','m2-line-return','m2-note'],
            packets=[dict(key='m2-dot',path=[(0,0),(690,0),(690,6),(0,6)],duration=2600)],pulse=['h','i']))
        message(3,420,900,420,'INVITE → S-CSCF → Path','③ 承辦人：我有她的地址。\n沿 Path 經接待送到小華。',['s','pb','b'])
        message(4,900,100,480,'180 Ringing','④ 小華的手機開始響鈴。\n小明得知對方正在響鈴。',['b','a'])
        message(5,900,100,540,'200 OK + SDP answer','⑤ 小華：喂，我接聽了。\n雙方媒體位址、codec 到齊。',['a'])
        message(6,100,900,600,'ACK','⑥ 小明：收到，開始說話。\n通話已建立。',['b'])
        text('footer',60,657,1160,46,'逐次點擊 6 次｜兩個 P 是本專案同一程序的兩個 leg。\n本頁依 PoC 路由；標準主叫先經 Service-Route 到主叫 S-CSCF。',11,'muted')
    else:
        text('subtitle',60,103,1160,33,'P-CSCF 看到 200 OK 的 SDP answer 後申請 QoS；接著示意 ACK 後的雙向語音。',15,'muted')
        shape('ims',430,165,420,88,'peach',[('P / I / S-CSCF',22,'orange',True,'center'),('通話控制：接通、掛斷',13,'ink',False,'center')])
        shape('qos',938,165,284,90,'pale',[('AF shim → PCF',17,'blue',True,'center'),('N5 → N7 / SMF → N4',12,'muted',False,'center'),('兩端各一份語音規則',12,'ink',False,'center')])
        for key,x,title,role in [('a',72,'小明 UE','「喂，聽得到嗎？」'),('upf',550,'UPF','轉送真正的語音'),('b',1028,'小華 UE','「聽到了！」')]:
            shape(key,x,345,180,97,'white',[(title,22,'blue',True,'center'),(role,12,'muted',False,'center')])
        # RTP lanes run below the device cards, leaving the words unobstructed.
        line('rtp-out',162,1118,466,'blue')
        line('rtp-back',1118,162,491,'blue')
        text('rtp-label',280,443,720,22,'RTP 語音：小明 ⇄ UPF ⇄ 小華（CSCF 不轉送聲音）',13,'blue',True,'center')
        token('rtp-dot1',162,466,'blue');token('rtp-dot2',1118,491,'blue')
        # Right-angle paths for signalling and policy control.
        def segment(key,x,y,w,h,color,arrow=False):
            put(key,dict(type='shape',shape='lineArrow' if arrow else 'line',x=x,y=y,w=w,h=h,
                         stroke=dict(color=C[color],widthPt=1.6)))
        segment('q1',850,210,88,1,'blue',True)
        segment('q2',1080,255,1,58,'blue')
        segment('q3',640,313,440,1,'blue')
        segment('q4',640,313,1,32,'blue',True)
        token('qdot',850,210,'blue')
        segment('bye1',162,268,1,77,'orange')
        segment('bye2',162,268,956,1,'orange',True)
        segment('bye3',1118,268,1,77,'orange',True)
        segment('bye-ims',640,253,1,15,'orange')
        text('bye-label',425,275,470,27,'BYE / 200 OK：仍經既有的 SIP 路徑',13,'orange',True,'center')
        token('byedot',162,345,'orange')
        shape('card1',60,536,367,103,'pale',[
            ('① 接聽：向 5GC 申請 QoS',17,'blue',True,'center'),
            ('P-CSCF 讀 SDP，經 AF shim 送 N5',12,'ink',False,'center'),
            ('媒體用 5QI 1，信令維持 5QI 5',12,'ink',False,'center')])
        shape('card2',457,536,367,103,'pale',[
            ('② 說話：RTP 雙向傳送',17,'blue',True,'center'),
            ('本專案在 UPF 內轉給另一個 UE',12,'ink',False,'center'),
            ('IMS 管通話，UPF 搬語音封包',12,'ink',False,'center')])
        shape('card3',854,536,367,103,'peach',[
            ('③ 掛斷：BYE 並釋放 QoS',17,'orange',True,'center'),
            ('結束通話，釋放兩端媒體預留',12,'ink',False,'center'),
            ('IMS 註冊與 PDU session 仍保留',12,'ink',False,'center')])
        steps.extend([
            dict(label='申請媒體 QoS',show=['card1','q1','q2','q3','q4'],
                 packets=[dict(key='qdot',path=[(0,0),(230,0),(230,103),(-210,103),(-210,135)],duration=2300)],pulse=['qos','upf']),
            dict(label='RTP 雙向語音',show=['card2','rtp-out','rtp-back','rtp-label'],
                 packets=[dict(key='rtp-dot1',path=[(0,0),(956,0)],duration=2200),
                          dict(key='rtp-dot2',path=[(0,0),(-956,0)],duration=2200)],pulse=['a','b']),
            dict(label='BYE 與釋放 QoS',show=['card3','bye1','bye2','bye3','bye-ims','bye-label'],
                 hide=['rtp-out','rtp-back','rtp-label'],
                 packets=[dict(key='byedot',path=[(0,0),(0,-77),(956,-77),(956,0),(956,-77),(0,-77),(0,0)],duration=2800)],pulse=['ims','qos','upf'])
        ])
        text('footer',60,666,1160,30,'逐次點擊 3 次｜省略 gNB／N3；本 PoC 驗證 QoS 規則存在，未驗證 GBR 實際限速。',11,'muted')
    page={k:outline[k] for k in ['title','type','layout']}
    page.update(background=C['bg'],elements=elements)
    (ROOT/'pages').mkdir(exist_ok=True)
    (ROOT/'metadata').mkdir(exist_ok=True)
    (ROOT/'pages'/f'{n:02}.json').write_text(json.dumps(page,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'metadata'/f'{n:02}.json').write_text(json.dumps(dict(keys=keys,steps=steps),ensure_ascii=False,indent=2)+'\n')
    print(f'Wrote page {n}: {len(elements)} elements, {len(steps)} clicks')

if __name__=='__main__':
    build(int(sys.argv[1]))
