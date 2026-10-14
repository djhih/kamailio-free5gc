import json
D='/home/jjd/genoffice/f5gc-kamailio-integration/'
N='#14213D'; M='#5B6575'; B='#0F4C81'; BT='#E3ECF6'; O='#E8742A'; OT='#FCEBDD'; W='#FFFFFF'; NV='#0B1B2E'; BD='#D5DAE1'; LT='#C9D3E0'
def run(t,s=14,c=N,b=False,i=False,f=None):
    r={"text":t,"sizePt":s,"color":c}
    if b:r["bold"]=True
    if i:r["italic"]=True
    if f:r["font"]=f
    return r
def para(*runs,**kw): d={"runs":list(runs)}; d.update(kw); return d
def text(x,y,w,h,*paras): return {"type":"text","x":x,"y":y,"w":w,"h":h,"paragraphs":list(paras)}
def box(x,y,w,h,fill=None,stroke=None,shape="roundRect",paras=None,valign=None,**kw):
    e={"type":"shape","shape":shape,"x":x,"y":y,"w":w,"h":h}
    if fill:e["fill"]=fill
    if stroke:e["stroke"]={"color":stroke,"widthPt":1}
    if paras:e["paragraphs"]=paras
    if valign:e["valign"]=valign
    e.update(kw); return e
def node(x,y,w,label,fill,tc=W,h=50,size=15): return box(x,y,w,h,fill=fill,paras=[para(run(label,size,tc,True),align="center")])
def line(x,y,w,h,c=N,flipV=False,arrow=False,dash=False):
    e={"type":"shape","shape":"lineArrow" if arrow else "line","x":x,"y":y,"w":w,"h":h,"stroke":{"color":c,"widthPt":1.5}}
    if flipV:e["flipV"]=True
    return e
def hrule(x,y,w,c=N,t=2): return box(x,y,w,t,fill=c,shape="rect")
def vrule(x,y,h,c=N,t=2): return box(x,y,t,h,fill=c,shape="rect")
def badge(x,y,n): return box(x,y,30,30,fill=O,shape="ellipse",paras=[para(run(n,13,W,True),align="center")])
def title(t,sub=None,size=34):
    e=[text(70,40,1140,60,para(run(t,size,N,True)))]
    if sub:e.append(text(70,104,1140,30,para(run(sub,16,M))))
    return e
def bullets(items,s=15,c=N,sp=8):
    return [para(run(t,s,c),bullet=True,spaceAfterPt=sp) for t in items]
pages=[]; outline=[]
def add(t,typ,layout,brief,els,bg='#F6F7F9'):
    pages.append({"title":t,"type":typ,"layout":layout,"background":bg,"elements":els})
    outline.append({"title":t,"type":typ,"layout":layout,"brief":brief,"image_queries":[]})

# 1 cover
pts=["① 使用者面（N6）","② ims DNN 與預設 QoS","③ P-CSCF discovery","④ 用戶身分與金鑰","⑤ Policy／QoS"]
els=[box(768,0,512,720,fill=O,shape="rect"),
 text(80,110,620,36,para(run("kamailio-free5gc · 2026-10",16,LT))),
 text(80,200,660,200,para(run("free5gc",54,W,True),lineSpacingPct=105),para(run("× Kamailio 對接",54,O,True),lineSpacingPct=105)),
 text(80,440,640,44,para(run("5GC 與 IMS 怎麼接起來",22,W))),
 text(80,500,640,40,para(run("SIP 不經過 AMF／SMF，兩邊只在五個地方接觸",16,LT))),
 text(832,110,400,30,para(run("五個對接點",16,NV,True)))]
for i,p in enumerate(pts): els.append(box(832,160+i*92,384,72,fill=W,paras=[para(run("  "+p,19,B if i<4 else O,True),align="left")],valign="middle"))
add("free5gc × Kamailio 對接","cover","cover_split_color","Title, subtitle, five integration points listed on orange block.",els,bg=NV)

# 2 overview diagram
els=[box(470,70,350,600,fill=BT),box(860,70,370,600,fill=OT),
 text(490,84,310,24,para(run("corenet 10.100.200.0/24",12,B,True))),text(880,84,330,24,para(run("dnnet 10.100.100.0/24",12,O,True))),
 vrule(574,184,116),hrule(640,326,125),line(640,354,160,186,flipV=True),hrule(915,326,35),vrule(1014,184,116),hrule(640,157,310,O,3),
 vrule(1014,354,76),vrule(1014,484,76),line(1080,457,30,60,M),line(1080,532,30,55,M,flipV=True),
 box(573,354,4,206,fill=B,shape="rect"),
 node(510,130,130,"PCF",B),node(510,300,130,"SMF",B),box(510,560,130,50,fill=W,stroke=B,paras=[para(run("UE + gNB",15,B,True),align="center")]),
 node(765,300,150,"UPF",NV),box(680,606,120,44,fill=W,stroke=B,paras=[para(run("UDR",14,B,True),align="center")]),
 box(950,130,130,50,fill=W,stroke=O,paras=[para(run("AF shim",15,O,True),align="center")]),
 node(950,300,130,"P-CSCF",O),node(950,430,130,"I-CSCF",O),node(950,560,130,"S-CSCF",O),
 box(1110,495,100,50,fill=W,stroke=O,paras=[para(run("PyHSS",14,O,True),align="center")]),
 text(584,226,60,20,para(run("N7",12,N,True))),text(650,302,110,20,para(run("N4",12,N,True))),
 text(700,186,200,20,para(run("N5",12,O,True))),text(1024,226,100,20,para(run("HTTP",12,N))),
 text(1024,382,40,20,para(run("Mw",12,N,True))),text(1024,512,40,20,para(run("Mw",12,N,True))),text(1140,466,40,20,para(run("Cx",12,M,True))),
 text(584,440,60,20,para(run("PCO",12,B,True))),text(726,470,90,20,para(run("N3",12,N,True))),
 badge(915,340,"1"),badge(700,500,"2"),badge(540,440,"3"),badge(820,612,"4"),badge(780,112,"5"),
 text(50,56,390,60,para(run("五個對接點",32,N,True))),
 text(50,140,390,520,
   para(run("SIP 不經過 AMF、SMF；對 5GC 來說只是 user plane 的 IP 封包。",15,M),spaceAfterPt=14),
   para(run("① ",16,O,True),run("使用者面：UPF 是唯一的橋",16,N,True),spaceAfterPt=10),
   para(run("② ",16,O,True),run("ims DNN 與預設 QoS",16,N,True),spaceAfterPt=10),
   para(run("③ ",16,O,True),run("P-CSCF discovery（PCO）",16,N,True),spaceAfterPt=10),
   para(run("④ ",16,O,True),run("用戶身分與金鑰（開戶時對齊）",16,N,True),spaceAfterPt=10),
   para(run("⑤ ",16,O,True),run("Policy／QoS（N5）",16,N,True),spaceAfterPt=10))]
add("五個對接點","content","left_text_right_image","Left list of five points; right topology diagram with numbered badges.",els)

# 3 user plane
els=title("① 使用者面：UPF 是唯一的橋","SIP 與 RTP 都是 user plane 封包：UE → gNB →（GTP-U）→ UPF → N6 → P-CSCF")+[
 box(70,160,450,300,fill=BT),box(760,160,450,300,fill=OT),node(545,280,190,"UPF（雙網卡）",NV,h=60,size=16),
 text(96,180,400,270,para(run("corenet",22,B,True)),para(run("10.100.200.0/24",14,M),spaceAfterPt=10),*bullets(["AMF、SMF、PCF…","gNB","UPF 的 N3、N4"],15)),
 text(786,180,400,270,para(run("dnnet",22,O,True)),para(run("10.100.100.0/24",14,M),spaceAfterPt=10),*bullets(["P／I／S-CSCF","PyHSS、AF shim","UPF 的 N6"],15)),
 box(70,490,1140,170,fill=W,stroke=BD,valign="middle",paras=[
   para(run("   往 dnnet 不做 NAT（config/upf-n6.sh）",18,O,True),align="left",spaceAfterPt=8),
   para(run("   • Kamailio 看到 UE 的真實 IP；否則兩支 UE 會變成同一個位址，SIP 需要 NAT 輔助",15,N),align="left",spaceAfterPt=4),
   para(run("   • PCF 用 UE IP 綁定 PDU session，位址被改掉就綁不到",15,N),align="left",spaceAfterPt=4),
   para(run("   • 兩個網段互不相通：UE 到 IMS 一定經過 UPF；RTP 在 UPF 內直接轉給對方",15,N),align="left")])]
add("① 使用者面：UPF 是唯一的橋","content","two_column_comparison","corenet vs dnnet columns with UPF bridging; no NAT box.",els)

# 4 ims DNN
k=[("ims","DNN","UE 只建這一個 PDU session（free-ran-ue 的限制）"),("10.62/16","位址池","與 internet 分開，來源 IP 就能看出 DN"),("5QI 5","預設 QoS","IMS 信令，ARP 1；internet 是 5QI 9"),("10 Mbps","Session AMBR","上下行各 10 Mbps")]
els=title("② ims DNN 與預設 QoS","設在 UDR 的訂閱資料（scripts/subscriber-template.json）與 smfcfg.yaml")
for i,(big,lab,d) in enumerate(k):
    x=70+i*292; els+= [box(x,160,268,330,fill=OT if i==2 else W,stroke=None if i==2 else BD),
      text(x+22,184,226,290,para(run(big,40,O if i==2 else B,True),spaceAfterPt=6),para(run(lab,17,N,True),spaceAfterPt=12),para(run(d,15,M),lineSpacingPct=125))]
els.append(box(70,520,1140,110,fill=NV,valign="middle",paras=[para(run("   SIP 信令一開始就走 5QI 5 的預設 QoS flow；",17,W),run("語音的 5QI 1",17,O,True),run(" 由 ⑤ 在通話接通時才加上。",17,W),align="left")]))
add("② ims DNN 與預設 QoS","data","kpi_cards_row","Four KPI cards: ims, 10.62/16, 5QI 5, 10 Mbps; footer about 5QI 1.",els)

# 5 PCO
st=[("UE 要位址","PDU Session Establishment Request 的 ePCO 帶「P-CSCF IPv4 request」（free-ran-ue 靠 pcscf-discovery.patch 補上）",B),
    ("SMF 查設定","smfcfg.yaml 中 ims DNN 的 pcscf：10.100.100.10",B),
    ("PCO 回傳","PDU Session Establishment Accept 的 PCO（container 000Ch）",B),
    ("UE 開始 SIP","把這個位址當 SIP outbound proxy，送出 REGISTER",O)]
els=title("③ P-CSCF discovery","UE 不寫死 P-CSCF，由 5GC 在建 PDU session 時告訴它")+[hrule(170,203,940,BD,4)]
for i,(h,d,c) in enumerate(st):
    x=70+i*290; els+=[box(x+112,177,56,56,fill=c,shape="ellipse",paras=[para(run(str(i+1),20,W,True),align="center")]),
       box(x,260,270,260,fill=W if i<3 else OT,stroke=BD if i<3 else None),
       text(x+20,280,230,230,para(run(h,19,c,True),spaceAfterPt=10),para(run(d,15,N),lineSpacingPct=125))]
els.append(text(70,560,1140,60,para(run("檢查方式：",15,O,True),run("03-call-test.sh 會先確認 UE 設定檔裡沒有寫 P-CSCF，否則拒絕執行；確保位址真的是從網路學來的。",15,N))))
add("③ P-CSCF discovery","content","timeline_horizontal","Four steps of PCO-based discovery.",els)

# 6 identities
els=title("④ 用戶身分與金鑰","兩邊各有一份用戶資料、沒有介面；一致性靠開戶腳本從同一個 IMSI 推導")+[
 box(70,160,360,420,fill=BT),box(460,160,360,420,fill=OT),box(850,160,360,420,fill=NV),
 text(96,182,310,380,para(run("5GC：UDR",22,B,True),spaceAfterPt=12),para(run("SUPI",15,M)),para(run("imsi-208930000000001",15,N,True),spaceAfterPt=12),
   para(run("開戶",15,M)),para(run("02-add-subscribers.sh",15,N,True),spaceAfterPt=12),para(run("認證",15,M)),para(run("5G-AKA（AUSF／UDM）",15,N,True))),
 text(486,182,310,380,para(run("IMS：PyHSS",22,O,True),spaceAfterPt=12),para(run("IMPI／IMPU",15,M)),para(run("208930000000001@ims.mnc093.mcc208.3gppnetwork.org",13,N,True),spaceAfterPt=12),
   para(run("開戶",15,M)),para(run("04-add-ims-subscribers.sh",15,N,True),spaceAfterPt=12),para(run("認證",15,M)),para(run("IMS AKA（S-CSCF）",15,N,True))),
 text(876,182,310,380,para(run("金鑰：同一個 OP",22,W,True),spaceAfterPt=12),para(run("lib-keys.sh 推導 OPc",15,LT),spaceAfterPt=10),
   *bullets(["UDR、free-ran-ue、PyHSS：OPc","SIPp：OP（自己算 OPc）","SQN 兩邊各自計數，都從 0x23 開始"],15,W)),
 text(70,604,1140,50,para(run("結果：",15,O,True),run("過了 5G 認證，還要再過一次 IMS 認證；兩份資料對不上時，錯誤會在很後面才以 AUTN MAC 失敗出現。",15,N)))]
add("④ 用戶身分與金鑰","content","three_column_cards","UDR vs PyHSS vs keys columns.",els)

# 7 policy chain
ch=[("P-CSCF","Kamailio",O,"200 OK 時，帶 offer、answer 兩份 SDP"),("AF shim","af/main.go",NV,"HTTP POST /call → 解析 SDP"),("PCF","free5gc",B,"h2c POST /npcf-policyauthorization/v1/app-sessions"),("SMF","free5gc",B,"N7：SM Policy Update Notify"),("UPF","gtp5g",NV,"N4：PFCP 裝上 PDR + QER")]
els=[text(50,56,400,60,para(run("⑤ Policy／QoS",32,N,True))),
 text(50,140,400,520,para(run("觸發點",16,O,True)),para(run("200 OK：offer 與 answer 都確定，才知道 RTP 的 IP 與 port",15,N),spaceAfterPt=12),
  para(run("一通電話預留兩次",16,O,True)),para(run("主叫、被叫各有自己的 PDU session，P-CSCF 兩端各送一次",15,N),spaceAfterPt=12),
  para(run("掛斷",16,O,True)),para(run("BYE → /call/delete → 刪除 app session → UPF 移除規則",15,N),spaceAfterPt=12),
  para(run("結果",16,O,True)),para(run("語音 flow 從 5QI 5 升到 5QI 1（GBR）",15,N)))]
for i,(n,s,c,d) in enumerate(ch):
    y=70+i*122; els+=[box(480,y,190,80,fill=c,paras=[para(run(n,17,W,True),align="center"),para(run(s,12,LT),align="center")]),
       text(700,y+18,510,50,para(run(d,15,N)))]
    if i<4: els.append(box(563,y+82,24,38,fill=M,shape="downArrow"))
add("⑤ Policy／QoS","content","left_text_right_image","Vertical chain P-CSCF→AF shim→PCF→SMF→UPF with labels; left notes.",els)

# 8 AppSessionContext
cells=[("session binding",B,["supi：imsi-…（一定要帶）","ueIpv4：PDU session 的位址","dnn：ims"]),
       ("媒體",O,["medType：AUDIO → 5QI 1","fDescs：permit out／in 17 from <peer> to <ue>","marBwUl／Dl、codecs"]),
       ("控制",B,["afAppId：IMS-voice","notifUri：http://af:8090/notify","suppFeat：\"0\""]),
       ("生命週期",O,["/call → POST app-sessions","/call/delete → 刪除 app session","啟動時向 NRF 註冊為 AF"])]
els=title("AF shim 送給 PCF 的內容","N5 的 AppSessionContext（af/main.go buildContext）")
for i,(h,c,it) in enumerate(cells):
    x=70+(i%2)*580; y=150+(i//2)*240
    els+=[box(x,y,560,220,fill=W,stroke=BD),text(x+26,y+20,510,190,para(run(h,20,c,True),spaceAfterPt=10),*bullets(it,15,N,6))]
add("AF shim 送給 PCF 的內容","data","two_by_two_grid","Four cells of AppSessionContext fields.",els)

# 9 gotchas
g=[("一定要帶 supi","沒帶時 PCF 掃所有 UE 找 IP，迴圈不會停，多 UE 時可能綁錯"),("不能用 permit inout","PCF 先比對 permit in，inout 會變成只有上行"),
   ("連 PCF 要用 h2c","free5gc SBI 只講不加密的 HTTP/2；Kamailio 的 http_client 做不到"),("NRF OAuth 關閉","開啟時 PCF → SMF 的 token scope 對不上"),("AF ID 不能亂取","要和 free5gc 產生的 AF 憑證對上")]
els=title("對接時踩到的細節")
for i,(h,d) in enumerate(g):
    x=70+i*233; els+=[box(x,140,213,400,fill=W,stroke=BD),text(x+18,160,177,370,para(run(f"0{i+1}",34,O,True),spaceAfterPt=8),para(run(h,17,N,True),spaceAfterPt=10),para(run(d,15,M),lineSpacingPct=125))]
els.append(box(70,566,1140,80,fill=NV,valign="middle",paras=[para(run("這些都寫在 af/main.go 與 docs/policy-and-qos.md 的註解裡；換實作時要一起帶走。",16,W),align="center")]))
add("對接時踩到的細節","data","kpi_cards_row","Five gotcha cards.",els)

# 10 verification
els=title("怎麼證明真的接上了")+[box(70,130,560,440,fill=BT),box(650,130,560,440,fill=OT),
 text(96,152,510,400,para(run("03-call-test.sh",22,B,True)),para(run("端到端：註冊、通話、媒體、QoS",15,M),spaceAfterPt=12),
   *bullets(["INVITE 依序經過 P → I → S → P","UAR、MAR、SAR、LIR 四種 Cx 都有用到","通話中 UPF 上有語音的 PDR／QER","抓 N3 封包：SIP 與 RTP 確實在 GTP-U 裡","UE 的 P-CSCF 位址來自 PCO"],15)),
 text(676,152,510,400,para(run("05-n5-qos-test.sh",22,O,True)),para(run("只測 ⑤：不經 SIP，直接打 AF",15,M),spaceAfterPt=12),
   *bullets(["每個方向一條 PDR，帶語音的 5-tuple","PDR 指向帶 GBR 的 QER","釋放後規則消失","這個過、03 不過 → 問題在 IMS；反之在 5GC"],15)),
 text(70,596,1140,50,para(run("刻意不測：",15,O,True),run("throughput。free5gc 不會真的限速，只能證明「規則裝上了」。",15,N)))]
add("怎麼證明真的接上了","content","two_column_comparison","03 vs 05 tests.",els)

# 11 gaps
gp=[("SMF 沒送 N1N2","policy 更新只改 UPF，gNB 與 UE 不知道語音 QoS flow"),("PCF 通知只寫 log","PDU session 斷了，通話還掛著"),("註冊時沒交換資訊","沒有信令 flow、事件訂閱（29.513 B.5–B.8）"),
    ("AMF imsVoPS = 0","網路告訴 UE 不支援 IMS 語音"),("PCO 只有 IPv4","沒有 IPv6 P-CSCF"),("QER 不真的限速","free5gc 的已知限制")]
els=[box(0,0,400,720,fill=B,shape="rect"),text(50,150,320,250,para(run("6",160,W,True))),
     text(50,430,320,140,para(run("個還沒打通的地方",24,W,True),spaceAfterPt=8),para(run("前兩個影響最大",15,LT)))]
for i,(h,d) in enumerate(gp):
    y=60+i*100
    els+=[text(450,y,760,80,para(run(h,19,O if i<2 else N,True),spaceAfterPt=4),para(run(d,15,M)))]
    if i<5: els.append(hrule(450,y+88,760,BD,1))
add("還沒打通的地方","content","hero_big_number","Big 6 with six gap rows.",els)

# 12 closing
els=[box(860,0,420,720,fill=B,shape="rect"),text(80,80,700,90,para(run("改善方向",46,W,True)))]
nx=[("Rx／N5 Adapter 取代 shim","Kamailio 改用標準的 ims_qos，PCF 事件可以回到 IMS"),("SMF 補 N1N2","語音 QoS flow 送到 gNB 與 UE"),("AMF imsVoPS 改 1","只改設定")]
for i,(h,d) in enumerate(nx):
    y=230+i*130; els+=[box(80,y,56,56,fill=O,shape="ellipse",paras=[para(run(str(i+1),20,W,True),align="center")]),text(160,y,640,90,para(run(h,22,W,True),spaceAfterPt=4),para(run(d,15,LT)))]
els.append(text(900,80,340,560,para(run("文件",20,W,True),spaceAfterPt=10),
  *[para(run(t,14,LT),spaceAfterPt=4) for t in ["free5gc-kamailio-integration.md","vonr-ims-nf-plan.md","kamailio-free5gc/docs/"]],
  para(run("規格",20,W,True),spaceBeforePt=16,spaceAfterPt=10),
  *[para(run(t,14,LT),spaceAfterPt=4) for t in ["TS 29.514  N5","TS 29.513  IMS 與 PCF","TS 23.503 附錄 C","TS 24.008  PCO"]]))
add("改善方向","closing","closing_cta","Three next steps and references.",els,bg=NV)

for i,p in enumerate(pages): json.dump(p,open(f'{D}pages/{i+1:02d}.json','w'),ensure_ascii=False)
json.dump({"topic":"free5gc 與 Kamailio 的對接","core_hook":"SIP 不經過 AMF／SMF：free5gc 與 Kamailio 只在五個地方接觸","pages":outline},open(D+'outline.json','w'),ensure_ascii=False,indent=1)
print(len(pages))
