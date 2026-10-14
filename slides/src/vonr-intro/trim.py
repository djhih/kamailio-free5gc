import json,re
D='/home/jjd/genoffice/vonr-ims-intro-v3/pages/'
X=None
E={
'01':[("從 IMS 基礎","IMS 基礎、kamailio-free5gc 的做法、重建計畫")],
'02':[("對 5GC 來說，語音封包",X),("VoLTE 與 VoNR 背後都是 IMS",["VoLTE、VoNR 背後都是 IMS；","對 5GC 來說，它只是 N6 後面的一台 server。"])],
'03':[("3GPP 在 Release 5","3GPP 定義、以 SIP 為核心的通話服務平台"),("跟接取技術無關","與接取無關：同一套 IMS 服務 VoLTE、VoNR、VoWiFi"),
      ("手機內建撥號器","手機撥號器打的電話，在 4G／5G 上就是 IMS 的 SIP 通話"),("5GC 是公路","5GC 是公路，IMS 是電話公司的總機"),("總機與客服",X),
      ("TAS 補充服務","TAS 補充服務、語音信箱、會議"),("P-CSCF / I-CSCF / S-CSCF：","P / I / S-CSCF：SIP 註冊與路由")],
'04':[("只是一般數據","一般數據，跟下載搶頻寬（5QI 9）"),("網路知道這是語音","保證頻寬的語音通道（5QI 1）"),("App 帳號","App 帳號密碼"),
      ("SIM 卡裡的金鑰","SIM 卡金鑰（IMS AKA）"),("只能打給同一個","只限同 App 使用者"),("用電話號碼","任何電話號碼，可漫遊"),
      ("必須支援","支援且優先"),("另外安裝 App","另裝 App"),("手機內建撥號器","內建撥號器"),("關鍵差別",["關鍵差別：","網路知道這是通話，才能特別照顧它。"])],
'05':[("一通電話用到三個協定","信令走 proxy，聲音兩端直送"),("回應碼",X),("一路經過","經 P / I / S-CSCF 轉送"),
      ("本專案中在 UPF","本專案在 UPF 內轉給對方"),("IMS 用的是 3GPP",X)],
'06':[("動作＋對象","動作＋對象（被叫的 IMPU），像 HTTP 的 GET 網址"),("回程路徑","回程路徑，每過一個 proxy 疊一層"),
      ("「之後直接","之後找我的位址；註冊時 S-CSCF 記的就是它"),("聲音要送去哪","聲音的 IP、port、codec；P-CSCF 讀它來要 QoS"),
      ("• Path","• Path / Service-Route：之後要經過的 proxy"),("• P-Asserted","• P-Asserted-Identity：網路擔保的來電身分"),
      ("• P-Visited","• P-Visited-Network-ID：漫遊政策用"),("• Authorization","• Authorization：AKA 答案（HTTP Digest 格式）"),
      ("收到了","處理中"),("對方響鈴中","響鈴"),("接聽（帶","接聽＋SDP answer"),("請先證明身分","要先認證"),("找不到這個人","找不到人")],
'07':[("UE 唯一直接","UE 的唯一入口（Gm）"),("通話時扮演 AF","扮演 AF，依 SDP 向 PCF 要 QoS"),("home network","網路入口，不存狀態"),
      ("UAR：","UAR：該由哪台 S-CSCF 服務"),("LIR：","LIR：被叫在哪台 S-CSCF"),("MAR 拿","MAR → 401 → IMS AKA 認證"),
      ("SAR 登記","SAR 登記並取回 profile"),("來電時沿 Path","來電沿 Path 送回 P-CSCF"),("被 I-CSCF","CSCF 經 Cx（Diameter）查詢"),
      ("與 5G 的 UDR","與 UDR 分開"),("三個 CSCF 都是","三個 CSCF 都是 Kamailio，只差在模組與 kamailio.cfg。")],
'08':[("USIM 上的號碼","MCC 208 + MNC 93 + 用戶編號"),("存在 UDR","存在 UDR，5G 註冊用"),("綁著認證金鑰","綁認證金鑰，只有 HSS、S-CSCF 看得到"),
      ("別人撥的","別人撥的號碼，可以有多個"),("沒有 ISIM","無 ISIM 時依 TS 23.003 從 IMSI 推導（MNC 補成三位：mnc093）"),
      ("UDR 與 PyHSS","UDR 與 PyHSS 各存一份金鑰、SQN 各自計數，所以要認證兩次")],
'09':[("像考試","像考試：只傳題目和答案，金鑰不上網；手機也會驗證網路"),("SIM 卡與 HSS","SIM 與 HSS 存同一把金鑰 K"),("K 永遠","K 不上網"),
      ("S-CSCF 向 HSS","S-CSCF 向 HSS 要向量："),("S-CSCF 回 401","401 帶 RAND + AUTN"),("XRES 留在","XRES 不送出"),
      ("SIM 用 K 驗","SIM 驗 AUTN，假網路就拒絕"),("驗過了","再算出答案 RES"),("第二次 REGISTER","REGISTER 帶 RES"),
      ("通過 →","通過 → SAR → 200 OK"),("技術名詞",["技術名詞：","Milenage；SIP 中稱 AKAv1-MD5。SQN 不同步時 UE 回 AUTS，觸發重新同步。"])],
'10':[("REGISTER 不帶憑證","不帶憑證，只為換到 401 題目"),("帶著答案","帶 RES 再送；對了就 SAR 登記"),
      ("S-CSCF 記住 Path","來電靠它繞回 P-CSCF；少了它，被叫端無法要 QoS"),("四種 Cx",X)],
'11':[("其餘各自獨立",X),("專用 ims DNN","ims DNN 經 UPF 到 P-CSCF；不做 NAT，PCF 靠 UE IP 綁定 session"),
      ("UE 在 PDU","UE 建 PDU session 時要求，SMF 在 Accept 回傳"),("應用層回頭","語音 flow 從 5QI 5 升到 5QI 1（GBR）"),
      ("UDR 與 HSS 之間","其餘各自獨立：UDR 與 HSS 無介面，各自認證")],
'12':[("兩個 Docker","兩個網段互不相通，UE 只能經 UPF 到 IMS"),("P-CSCF 10.100",X),("PyHSS 存","PyHSS：IMS 用戶資料"),
      ("AF shim（","AF shim：把 P-CSCF 的請求轉成 N5"),("free-ran-ue 模擬","free-ran-ue 模擬 gNB、UE；UE 內跑 SIPp")],
'13':[("比喻",X),("談通話","註冊與通話信令"),("電信界","CSCF 向 HSS 查用戶、拿認證向量"),("語音本身","語音封包，兩端直接互送"),
      ("5GC 內部","5GC 內部的 REST API；N5 要 QoS 也走它"),("SMF 指揮","SMF 對 UPF 下封包規則（PDR、QER）"),
      ("把 UE 的 IP","把 UE 封包包進隧道送到 UPF"),("橘色是 IMS","橘：IMS 側；藍：5GC 側")],
'14':[("兩支 UE","主叫出去、被叫靠 Path 繞回，兩端各要一次 QoS"),("這時 offer","offer、answer 到齊，RTP 位址才完整"),
      ("SIP 一路","SIP 經三個 CSCF；RTP 在 UPF 內直接轉"),("商用網路",X)],
'15':[("每一跳","200 OK 觸發，每一跳翻譯成下一層的格式"),("兩端的 c=","c= 與 m=audio → RTP 5-tuple"),("medType AUDIO、","medType AUDIO、flow、位元率"),
      ("用 UE IP","依 UE IP 綁定；AUDIO → 5QI 1"),("PCF 以","PCF 通知 SMF"),("把 PCC rule","PCC rule → PDR + QER"),("核心模組","依 PDR 比對語音封包"),
      ("注意：",["   注意：","free5gc 只裝規則、不真的限速；測試只驗證規則存在。"]),("掛斷（BYE）","   BYE 時沿同一條鏈釋放。")],
'16':[("5QI 是一個編號","TS 23.501 的標準服務等級；VoNR 用後兩種"),("比喻",X),("為什麼語音",["   語音錯誤率較寬：","掉 1% 聽不出來，延遲聽得出來；要的是準時，不是一包不漏。"]),("所以語音",X)],
'17':[("同一件事","AF 向 PCF 要 QoS：4G 與 5G 協定不同，專案用 shim 接起來"),("內建 SDP",X),("P-CSCF 不用","P-CSCF 用 http_client 送自訂 JSON"),
      ("shim 解析","shim 轉成 N5"),("事件經",X),("本專案相對","刻意簡化的地方"),("RTP 不錯定","RTP 直接在 UPF 轉")],
'18':[("能動，但",X),("SDP 先 base64","換掉任一端都要重寫"),("主被叫方向","寫在 SIP 路由腳本，難測試"),("PDU session 被","PDU session 沒了，通話還掛著"),
      ("PCF 回得慢","PCF 慢就卡住 worker"),("只在 200 OK","只預留媒體，信令沒有"),("根本原因",["根本原因：","AF 邏輯拆在 cfg 與 shim，兩邊都不是標準介面"])],
'21':[("Kamailio 的 I-CSCF","CSCF 只會用 Cx 查用戶，free5gc 沒有 HSS，需要另一個會講 Cx 的資料庫"),("開源（","開源，支援 Cx"),("有 REST","REST API 開戶"),
      ("有現成","現成容器映像"),("實驗室規模","SQLite，免架資料庫"),("同一個用戶存兩份","用戶存兩份（UDR、PyHSS），SQN 各自計數"),
      ("跟自己做 NF","跟重建計畫的關係"),("若做「跑在","Phase 4 以走 N70 的獨立 HSS NF 取代右邊整塊"),("10.100.100.20","Cx 端點"),
      ("pyhss-redis：","pyhss-redis：請求佇列"),("放在 pyhss-db","三個容器共用"),("沒有獨立",X)],
'22':[("上排：","上：四種 Cx 問題。下：開一個用戶要的四筆資料"),("PyHSS 也能",X),("每次 MAR","外洩就能冒充 SIM"),("MAR 把 IMPI","MAR 先查這筆"),
      ("SAR 後記下","記下目前的 S-CSCF，供 LIR 查詢"),("MSISDN 清單","IMPU 清單、realm、iFC 範本"),("IMSI ↔ AUC","IMSI ↔ AUC、MSISDN、啟用狀態"),
      ("記下由哪台","登記 S-CSCF，回 profile"),("算認證向量","算向量、推進 SQN"),("這人該給","給哪台 S-CSCF？"),("被叫現在","被叫在哪台？")],
'23':[("UE 唯一的入口",["   UE 唯一入口（Gm）",""]),("加上 Path","加 Path：來電會先經過我"),("加上 P-Visited","加 P-Visited-Network-ID"),
      ("不查 HSS","不認證，一律轉 I-CSCF"),("只有看到 200 OK","200 OK 才記下 IMPU ↔ contact"),("看來源 IP","依來源 IP 判斷主叫／被叫"),
      ("record_route","Record-Route，讓 BYE 也經過"),("先存下 SDP","200 OK 時帶兩份 SDP 經 shim 要 QoS"),("BYE 時釋放","BYE 時釋放；兩個 leg 各一次"),
      ("QoS 要不到","要不到 QoS 也不擋通話"),("為什麼需要 AF shim",["   為什麼需要 AF shim：","PCF 只開 h2c，Kamailio 的 http_client 講不了；"]),
      ("另外 http_client_query","   而且是同步呼叫，最多卡住 worker 2 秒。")],
'24':[("網路的大門","只回答：這人該交給哪台 S-CSCF？"),("問 HSS：這個","問 HSS 由哪台 S-CSCF 服務"),("從回答與","選一台後轉送"),
      ("遇到 401","401 後保留，第二次不再 UAR"),("問 HSS：被叫","問 HSS 被叫在哪台 S-CSCF"),("把答案也放","設為下一跳轉送"),("忘了 select",X),
      ("為什麼需要它","角色"),("自己不記","答案全來自 HSS"),("S-CSCF 清單放",X),("商用網路有","多台 S-CSCF 時負責分流、隱藏拓撲"),
      ("跟標準的差異",["   跟標準的差異：","主叫 INVITE 直送 I-CSCF；"]),("標準作法","   標準是先依 Service-Route 到主叫的 S-CSCF。")],
'25':[("IMS 的大腦","認證、註冊、路由都在這"),("第一次 REGISTER","第一次 REGISTER"),("ims_www_challenge","MAR 拿認證向量"),("回 401，","回 401"),
      ("第二次 REGISTER","比對 RES"),("收到 AUTS","收到 AUTS 就重新同步"),("save()","SAR 告訴 HSS「我服務他」"),
      ("把 IMPU","存 IMPU ↔ contact、Path、profile"),("只放記憶體","只在記憶體，重啟要重新註冊"),("拿掉 I-CSCF","移除 I-CSCF 加的 Route"),
      ("lookup()","IMPU → 註冊時的 contact"),("標準 S-CSCF",["   標準 S-CSCF 還會：","依 iFC 經 ISC 把請求交給 AS（如 TAS）。"]),("本專案沒有 AS","   本專案沒有 AS。")],
}
miss=[]
for f,rules in E.items():
    p=json.load(open(D+f+'.json')); used=set()
    for e in p['elements']:
        if 'paragraphs' not in e: continue
        keep=[]
        for para in e['paragraphs']:
            t=''.join(r['text'] for r in para['runs']).strip()
            rule=next((r for r in rules if t.startswith(r[0])),None)
            if rule is None: keep.append(para); continue
            used.add(rule[0]); new=rule[1]
            if new is None: continue
            if isinstance(new,str):
                lead=re.match(r'\s*',para['runs'][0]['text']).group(0)
                para['runs']=[dict(para['runs'][0],text=lead+new.lstrip())]
            else:
                runs=[]
                for r,txt in zip(para['runs'],new):
                    if txt: runs.append(dict(r,text=txt))
                para['runs']=runs
            keep.append(para)
        e['paragraphs']=keep
    p['elements']=[e for e in p['elements'] if not (e['type']=='text' and not e.get('paragraphs'))]
    for e in p['elements']:
        if e['type']=='shape' and 'paragraphs' in e and not e['paragraphs']: del e['paragraphs']
    for r in rules:
        if r[0] not in used: miss.append((f,r[0]))
    json.dump(p,open(D+f+'.json','w'),ensure_ascii=False)
print('unmatched:',miss)
