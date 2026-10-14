"""Compile the reviewed storyboard into GenOffice native animation operations."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
read = json.loads((ROOT/'metadata/deck-read.json').read_text())['detail']
ops=[]
notes=[
"""第一幕：講者可在每次點擊後停下來說明，共 7 次點擊。
前提：5G 註冊、ims PDU session 和 P-CSCF 探索已完成；這不是 5G-AKA 的動畫。
1. 小明向 P-CSCF 發 REGISTER，P 加 Path，再轉 I-CSCF。
2. I-CSCF 以 UAR/UAA 查 HSS，選定 S-CSCF 後把 REGISTER 轉過去。為保持畫面簡潔，此段轉送用對白及 S-CSCF 強調表示。
3. S-CSCF 用 MAR/MAA 向 HSS 取得 IMS AKA 向量。
4. S-CSCF 回 401，挑戰中的 nonce 承載 RAND、AUTN；這是正常的認證流程。回程經 I、P。
5. SIM 驗 AUTN、算 RES，以 RES 產生 AKAv1-MD5 的 Digest response，再放入 Authorization 送第二次 REGISTER；不是裸送 RES。圖省略各跳重傳與 SIM 計算細節。
6. 認證通過後 SAR/SAA 登記 serving S-CSCF 並取 profile；S-CSCF 保存 IMPU、Contact、Path。
7. 200 OK 經 I、P 回 UE，P-CSCF 也記錄成功的註冊。小華先完成同樣流程，接著才進入下一幕。
安全概念：K 只留在 SIM/HSS；HSS 的 XRES 不送到 UE。標準服務邏輯與簡化專案路由有差異。
依據：原簡報第 7、9、10 頁；kamailio-free5gc/pcscf/kamailio.cfg、icscf/kamailio.cfg、scscf/kamailio.cfg。
官方參考：https://www.kamailio.org/docs/modules/stable/modules/ims_registrar_pcscf.html
""",
"""第二幕：共 6 次點擊。雙方已註冊；在此只教一通成功通話。
1. 小明發 INVITE，body 的 SDP offer 帶媒體位址、埠及 codec 提案；P-CSCF 依本專案配置送 I-CSCF。
2. I-CSCF 以 LIR/LIA 查 HSS 的被叫 serving S-CSCF 資料。HSS 查詢是 Diameter Cx，不是 SIP。
3. I 轉 INVITE 到 S；S 用被叫 IMPU 找 Contact，沿註冊保存的 Path 經被叫 P-CSCF 送小華。
4. 180 Ringing 回主叫，代表響鈴；省略 100 Trying。
5. 小華接聽回 200 OK + SDP answer，P-CSCF 此時收齊 offer/answer，觸發下一幕的 N5 預留。
6. 小明回 ACK。應答沿 Via；ACK 與之後的 BYE 依對話 route set 路由。
畫面中兩個 P-CSCF 是同一個 Kamailio 程序分別處理主叫、被叫兩個 leg；每端有自己的 PDU session，因此兩端各申請 QoS。
本圖忠實呈現 PoC 的主叫 P→I→S 路由。標準 IMS 主叫一般先依 Service-Route 到主叫 S-CSCF，再處理被叫側；不要把這個 PoC 當所有營運商網路的完整通話流程。
省略 183、PRACK、preconditions、AS/TAS 與跨網互通。
依據：原簡報第 14、23、24 頁；kamailio-free5gc/pcscf/kamailio.cfg request_route 與 INVITE_REPLY；icscf/kamailio.cfg TERMINATING、LIR_REPLY；scscf/kamailio.cfg LOOKUP。
官方架構參考：https://www.etsi.org/deliver/etsi_ts/123200_123299/123228/18.05.00_60/ts_123228v180500p.pdf
""",
"""第三幕：共 3 次點擊；本幕將前一幕的 200 OK 觸發點放大說明。
1. P-CSCF 在 200 OK 看到 SDP answer，經本專案 AF shim 建 N5 App Session。PCF 以 N7 通知 SMF，SMF 以 N4 修改 UPF 的 PDR/QER。兩個 leg 各申請一次。媒體語音使用 5QI 1；信令仍使用 5QI 5，不是把整個 IMS session 從 5 改成 1。QoS 失敗時本專案仍允許通話。
2. 此處示意 ACK 後的 RTP 雙向傳送；真實 SIP 可有 early media，本 PoC 不呈現。藍色兩個封包反向移動，代表兩人說話；UPF 內 hairpin 轉到另一個 UE。圖省略 UE 與 UPF 之間的 gNB/N3，RTP 不經 CSCF。本專案沒有 IMS-AGW/SBC，勿泛化成所有部署都沒有媒體錨點。
3. 小明掛斷，BYE 走既有對話路由，對端回 200 OK；P-CSCF 於 BYE 釋放兩端 QoS App Session，控制链撤除媒體規則。動畫收起 RTP 路徑、強調控制群及 UPF。圖為控制群示意，不意指 BYE 重新作 LIR。通話結束不等於 IMS deregistration；原 IMS 註冊及 ims PDU session 仍可保留。
本專案只驗證規則存在，未驗證實際 GBR 頻寬保證或限速。
依據：原簡報第 14–17、23 頁；kamailio-free5gc/pcscf/kamailio.cfg AF_RESERVE、AF_RELEASE；AF shim 與 QoS 測試。
"""
]

for n,slide in enumerate(read['pages'],1):
    spec=json.loads((ROOT/'pages'/f'{n:02}.json').read_text())
    meta=json.loads((ROOT/'metadata'/f'{n:02}.json').read_text())
    # Match read-back IDs by geometry, never guess generated e_* identifiers.
    ids={}
    for key,index in meta['keys'].items():
        e=spec['elements'][index]
        matches=[a for a in slide['elements'] if abs(a['box']['x']/9525-e['x'])<0.02
                 and abs(a['box']['y']/9525-e['y'])<0.02
                 and abs(a['box']['cx']/9525-e['w'])<0.02]
        assert len(matches)==1,(n,key,matches)
        ids[key]=matches[0]['id']
        # The spec builder requires a >=1 px box, but OOXML lines support zero
        # width/height. Snap their actual geometry to an exact axis after build.
        if e.get('shape') in ['line','lineArrow']:
            box=dict(matches[0]['box'])
            if e['h']==1: box['cy']=0
            if e['w']==1: box['cx']=0
            ops.append(dict(op='setTransform',target=dict(slide=n-1,el=ids[key]),box=box))
    meta['ids']=ids
    (ROOT/'metadata'/f'{n:02}.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    ops.extend([dict(op='setTransition',target=dict(slide=n-1),kind='fade'),
                dict(op='setNotes',target=dict(slide=n-1),text=notes[n-1])])
    for step in meta['steps']:
        events=[]
        def event(key,effect,time=0,duration=300,**fields):
            events.append((time,dict(op='addAnimation',target=dict(slide=n-1,el=ids[key]),
                                    effect=effect,duration=duration,**fields)))
        for key in step['show']:
            event(key,'fade',duration=280)
        for key in step.get('hide',[]):
            event(key,'fadeOut',duration=300)
        latest=0
        for packet in step['packets']:
            k=packet['key'];d=packet['duration']
            path=' '.join(('M' if i==0 else 'L')+f' {x/1280:.7f} {y/720:.7f}'
                          for i,(x,y) in enumerate(packet['path']))
            event(k,'appear',duration=1)
            event(k,'motionPath',time=300,duration=d,motionPath=path)
            event(k,'disappear',time=300+d,duration=1)
            latest=max(latest,300+d)
        for key in step.get('pulse',[]):
            event(key,'pulse',time=latest,duration=420)
        events.sort(key=lambda a:a[0])
        last=0
        for i,(time,op) in enumerate(events):
            op.update(trigger='onClick' if i==0 else 'withPrev',delay=time-last)
            last=time
            ops.append(op)

(ROOT/'animation-ops.json').write_text(json.dumps(ops,ensure_ascii=False,indent=2)+'\n')
print(f'{len(ops)} GenOffice operations; 7 + 6 + 3 click groups.')
