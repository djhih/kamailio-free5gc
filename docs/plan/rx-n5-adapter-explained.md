# Rx／N5 Adapter 到底要做什麼

> 這份文件用一通實際的電話，一步一步解釋 Adapter 的工作。實作細節（AVP 代碼、程式結構、對應表）在 `rx-n5-adapter-design.md`。
> 文中的 IP、IMSI 取自本專案；Adapter 自己的位址與 Session-Id 是示意值。

## 1. 一句話

**Adapter 是翻譯員：把 Kamailio 用 Diameter Rx 說的「這通電話需要什麼網路資源」，翻成 free5gc PCF 聽得懂的 N5（HTTP/2），再把 PCF 回報的狀況翻回 Rx 告訴 Kamailio。** 它自己不決定給不給資源，決定權在 PCF。

## 2. 為什麼需要它

| | 會講什麼 |
|---|---|
| Kamailio P-CSCF（`ims_qos` 模組） | 只會 4G 的 **Rx**（Diameter），原本是對 PCRF 講的 |
| free5gc PCF | 只會 5G 的 **N5**（HTTP/2 + JSON） |

兩邊講不同的語言，中間一定要有人翻譯。3GPP 也預期這種情況：TS 23.503 附錄 C 規定 5GC 要能接受以 Rx 介接的 IMS。

**現在的 AF shim 為什麼不夠：**
- Kamailio 沒有用標準的 `ims_qos`，而是在設定檔裡手寫路由，把 SDP 用 base64 塞進自訂 JSON 送給 shim
- 只有 IMS → 5GC 一個方向：PCF 說「PDU session 沒了」時，shim 只寫 log，通話還掛著
- 呼叫是同步的，PCF 慢的時候會卡住 Kamailio

Adapter 改成兩邊都用標準介面，而且雙向都通。

## 3. Adapter 會跟誰說話

```
                 ┌─────────── Rx（Diameter，TCP 3868）───────────┐
                 │                                                │
Kamailio P-CSCF ◀┘                                                └▶ Adapter ─── N5（HTTP/2）──▶ PCF
10.100.100.10                                                          │
                                                                       ├── NRF：開機時註冊自己是 AF
                                                                       └── BSF：（之後）用 UE IP 查該找哪台 PCF
```

| 對象 | 誰先開口 | 內容 |
|---|---|---|
| Kamailio | Kamailio 主動連進來 | AAR（要資源）、STR（不要了） |
| Kamailio | Adapter 主動送 | ASR（session 被中止）、RAR（有事件） |
| PCF | Adapter 主動送 | 建立、修改、刪除 app session |
| PCF | PCF 主動回呼 | terminate（PDU session 沒了）、事件通知 |
| NRF | Adapter 主動送 | 註冊、取 token |

## 4. 用一通電話走一遍

**場景：** UE1（`imsi-208930000000001`，IP 10.62.0.1，RTP port 6000）打給 UE2（`imsi-208930000000002`，IP 10.62.0.2，RTP port 6002）。兩支 UE 共用 P-CSCF 10.100.100.10。

### 4.1 開機

1. Adapter 向 NRF 註冊，宣告自己是 AF（之後呼叫 PCF 時才拿得到 token）
2. Kamailio 的 cdp 模組連到 Adapter，雙方交換 CER／CEA（介紹自己，確認都支援 Rx），之後定期 DWR／DWA 確認對方還活著

到這裡還沒有任何電話，Adapter 的 session 表是空的。

### 4.2 UE1 撥號，UE2 接聽（200 OK）

SIP 照常走 P-CSCF → I-CSCF → S-CSCF → P-CSCF → UE2，**Adapter 完全看不到 SIP**。

UE2 回 200 OK，P-CSCF 這時手上有兩份 SDP（UE1 的 offer、UE2 的 answer），知道語音要走哪兩個 IP 和 port。

**① 主叫那一段（UE1 的 PDU session）**：Kamailio 送 AAR 給 Adapter，內容大致如下（示意）：

```
AA-Request
  Session-Id:            pcscf.ims...;1001;1         ← 這段通話這一端的 Rx session
  Framed-IP-Address:     10.62.0.1                   ← 要預留資源的 UE
  Subscription-Id:       SIP_URI  sip:208930000000001@ims.mnc093.mcc208.3gppnetwork.org
  Media-Component-Description
    Media-Component-Number:  1
    Media-Type:              AUDIO
    Max-Requested-Bandwidth-UL/DL: 64000 (bps)
    Media-Sub-Component
      Flow-Number: 1
      Flow-Description: permit out 17 from 10.62.0.2 6002 to 10.62.0.1 6000   ← 下行
      Flow-Description: permit in  17 from 10.62.0.1 6000 to 10.62.0.2 6002   ← 上行
```

**Adapter 要做的事：**

| 步驟 | 做什麼 | 這次的結果 |
|---|---|---|
| 1 | 解出 AAR，檢查必要欄位 | 有 UE IP、有媒體元件 |
| 2 | 判斷是通話還是註冊用的 session | 媒體是 AUDIO → 通話 |
| 3 | 從 IMPU 推出 SUPI | `sip:208930000000001@…` → `imsi-208930000000001` |
| 4 | 決定找哪台 PCF | 先用設定值；之後改問 BSF |
| 5 | 翻成 N5 的 `AppSessionContext` | 見下方 |
| 6 | `POST /npcf-policyauthorization/v1/app-sessions` | PCF 回 201，`Location` 裡有 app session ID |
| 7 | 記下「Rx session ↔ app session」 | 存進 session 表 |
| 8 | 回 AAA，Result-Code 2001（成功） | Kamailio 繼續處理通話 |

翻好的 N5 內容（示意）：

```json
{
  "ascReqData": {
    "supi": "imsi-208930000000001",
    "ueIpv4": "10.62.0.1",
    "dnn": "ims",
    "afAppId": "IMS-voice",
    "notifUri": "http://<adapter>/rx-n5/notify/<sessionKey>",
    "suppFeat": "0",
    "medComponents": {
      "1": {
        "medCompN": 1,
        "medType": "AUDIO",
        "marBwUl": "64000 bps",
        "marBwDl": "64000 bps",
        "medSubComps": {
          "1": { "fNum": 1, "fDescs": ["permit out 17 from …", "permit in 17 from …"] }
        }
      }
    }
  }
}
```

**之後的事 Adapter 不用管：** PCF 看到 AUDIO 就給 5QI 1，經 N7 通知 SMF，SMF 經 N4 在 UPF 裝上規則（Phase 2 完成後也會經 AMF 通知 gNB 與 UE）。

**② 被叫那一段（UE2 的 PDU session）**：P-CSCF 對 UE2 也送一個 AAR，Session-Id 不同、Framed-IP 是 10.62.0.2。Adapter 照同樣步驟再建一個 app session。

這時 session 表：

| Rx Session-Id | 類型 | SUPI | UE IP | app session |
|---|---|---|---|---|
| pcscf…;1001;1 | 通話 | imsi-…001 | 10.62.0.1 | 1 |
| pcscf…;1001;2 | 通話 | imsi-…002 | 10.62.0.2 | 2 |

**一通電話會有兩筆**，因為兩支 UE 各有自己的 PDU session，QoS 要各自預留。

### 4.3 通話中改 codec（re-INVITE）

Kamailio 用**同一個 Session-Id** 再送 AAR。Adapter 查表發現已經存在，改用 `PATCH /app-sessions/{id}`，不是再建一個。

### 4.4 正常掛斷（BYE）

`ims_qos` 看到 BYE，對兩段各送一個 STR。Adapter 對每個 STR：

1. 查表找到 app session
2. `POST /app-sessions/{id}/delete`
3. 從表中刪掉，回 STA 2001

PCF 會叫 SMF 把 UPF 上的語音規則拿掉。

### 4.5 異常：UE2 的 PDU session 突然沒了

這是現在的 shim 做不到的情況。

1. SMF 釋放 UE2 的 PDU session，PCF 發現 app session 2 已失去依據
2. PCF 送 `POST {notifUri}/terminate` 給 Adapter
3. Adapter 查表找到 Rx session `…;1001;2`，先回 PCF 204
4. Adapter 送 **ASR**（Abort-Cause = BEARER_RELEASED）給 Kamailio
5. Kamailio 結束這通電話：對 UE1 送 BYE，並對兩段送 STR
6. Adapter 照 4.4 清掉兩筆

**結果：** UE1 聽到通話結束，而不是對著一條死掉的線講話。

### 4.6 網路事件

如果 AAR 裡有 Specific-Action（例如「資源預留成功時通知我」），Adapter 在 N5 裡用 `evSubsc` 訂閱對應事件。PCF 通知時，Adapter 把事件翻回 Specific-Action，用 **RAR** 告訴 Kamailio。

### 4.7 IMS 註冊時（之後的階段）

UE 註冊成功後，P-CSCF 可以用 `Rx_AAR_Register` 為 SIP 信令本身建一個 Rx session，並訂閱「信令路徑還在不在」之類的事件。Adapter 照同樣方式建一個「信令」類型的 app session。

## 5. Adapter 要記住什麼

只有一張 session 表，每筆是一段通話（或一個 UE 的信令）：

| 欄位 | 用途 |
|---|---|
| Rx Session-Id | Kamailio 送 STR、AAR 更新時用它找 |
| app session ID | 呼叫 PCF 修改或刪除時用 |
| 回呼用的 key | PCF 回呼時用它找（放在 `notifUri` 路徑裡） |
| Kamailio 的 Origin-Host／Realm | 送 ASR、RAR 時要填 |
| SUPI、UE IP、PCF 位址 | 除錯、之後換 PCF 時用 |
| 訂閱了哪些事件 | 決定要不要轉 RAR |

不需要記 SIP、SDP、通話狀態，那些是 Kamailio 的事。

## 6. 翻譯時要特別小心的地方

| # | 地方 | 為什麼 |
|---|---|---|
| 1 | **身分** | Kamailio 預設送 IMPU（SIP URI），不是 IMSI。Adapter 要從 IMPU 推 SUPI；推不出來時只能靠 UE IP，而 free5gc PCF 只靠 IP 找 session 時多 UE 可能綁錯 |
| 2 | **Flow-Description 的方向** | Kamailio 的上行寫成 `permit in … from <UE> to <對方>`；現在可正常運作的 shim 是兩個方向都寫成 `from <對方> to <UE>`。free5gc PCF 只把 `permit in` 換成 `permit out`、地址不動，所以上行規則可能整個反過來。**Phase 0 要抓包確認 UPF 上的規則**，不對就由 Adapter 先把上行改寫成 shim 的格式 |
| 3 | **頻寬單位** | Rx 是 bps 整數；N5 是字串，例如 `"64000 bps"` |
| 4 | **不認識的 AVP** | Kamailio 會帶一些 Adapter 不需要的 AVP（例如 ETSI 的優先權），不能因此拒絕請求 |
| 5 | **回呼路徑** | PCF 會把終止通知送到 `notifUri` 後面加 `/terminate`。現在的 shim 只接 `/notify`，所以收不到 |
| 6 | **錯誤要翻對** | PCF 找不到 PDU session（500）要回 Kamailio 5065；服務被拒（403）回 5063。Kamailio 依這些代碼決定要不要擋掉通話 |
| 7 | **不能卡住** | 等 PCF 回應時不能讓其他請求排隊；每個 Rx session 由固定的 worker 處理 |

## 7. Adapter 不做的事

- 不看 SIP、不解析 SDP（`ims_qos` 已經把 SDP 變成 Flow-Description）
- 不決定 QoS（5QI、頻寬上限由 PCF 決定）
- 不碰 UPF、SMF、gNB
- 不存用戶資料（那是 PyHSS 與 UDR 的事）

## 8. 名詞對照

| Rx（Kamailio 那邊） | N5（PCF 那邊） | 意思 |
|---|---|---|
| AAR（新的 Session-Id） | `POST /app-sessions` | 我要資源 |
| AAR（既有 Session-Id） | `PATCH /app-sessions/{id}` | 資源需求改了 |
| STR | `POST /app-sessions/{id}/delete` | 不要了 |
| ASR | `terminate` 回呼 | 網路把你的 session 中止了 |
| RAR | 事件通知 | 網路發生了某件事 |
| Media-Component-Description | `medComponents` | 一路媒體（例如語音） |
| Flow-Description | `fDescs` | 一條封包流的過濾條件 |
| Specific-Action | `evSubsc.events` | 想被通知的事件 |
