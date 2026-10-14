# Rx／N5 Adapter 設計

> 狀態：設計草案（2026-10-14），尚未實作
> 上層計畫：`vonr-ims-nf-plan.md`的 W3（W3a 對應 Phase 1、W3b 對應 Phase 3、W3c 對應 Phase 4）
> 依據：TS 29.214（Rx）、TS 29.514（N5）、TS 29.513 附錄 B；Kamailio `ims_qos` 原始碼；free5gc v4.3.0 的 PCF、CHF 與 `free5gc/openapi` v1.3.0

## 1. Adapter 做什麼

把 Kamailio P-CSCF 送來的 **Rx（Diameter）** 請求轉成 **N5（HTTP/2）** 呼叫 PCF；PCF 的回呼再轉回 Rx 送給 Kamailio。本身不做 policy 決策。

```
Kamailio P-CSCF                    Adapter                          free5gc PCF
(ims_qos + cdp)
   AAR ───────────────▶  解析 → 對應 → POST/PATCH app-sessions ───▶
   ◀─────────────── AAA  ◀───────────────────────────── 201/200
   STR ───────────────▶  ──────────── POST .../delete ────────────▶
   ◀─────────────── STA
   ◀─────────────── ASR  ◀──────── POST {notifUri}/terminate ──────
   ◀─────────────── RAR  ◀──────── POST {evNotifUri}（事件）────────
```

## 2. 兩端介面速查

### 2.1 Rx 端（TS 29.214）

- Application-Id **16777236**，Vendor-Id **10415**（3GPP）
- Adapter 是 Diameter **server**（Kamailio 的 cdp 主動連進來），需處理 CER／CEA、DWR／DWA（由 Diameter 函式庫處理）

| 指令 | Code | 方向 | Adapter 要做的 |
|---|---|---|---|
| AA-Request／Answer（AAR／AAA） | 265 | Kamailio → Adapter | 建立或更新 app session |
| Session-Termination（STR／STA） | 275 | Kamailio → Adapter | 刪除 app session |
| Re-Auth（RAR／RAA） | 258 | Adapter → Kamailio | 轉送 5GC 事件 |
| Abort-Session（ASR／ASA） | 274 | Adapter → Kamailio | PDU session 沒了，要 Kamailio 結束 session |

要處理的 AVP（code 與型別取自 TS 29.214 第 5.3 節；base 協定的 AVP 來自 RFC 6733／4006）：

| AVP | Code | 型別 | 用途 |
|---|---|---|---|
| Session-Id | 263 | UTF8String | Rx session 的 key |
| Framed-IP-Address | 8 | OctetString | UE IP → `ueIpv4` |
| Subscription-Id（Type 450、Data 444） | 443 | Grouped | 推導 SUPI |
| Called-Station-Id | 30 | UTF8String | DNN |
| AF-Application-Identifier | 504 | OctetString | `afAppId` |
| Media-Component-Description | 517 | Grouped | 一個媒體元件 |
| ├ Media-Component-Number | 518 | Unsigned32 | `medCompN` |
| ├ Media-Type | 520 | Enumerated | `medType` |
| ├ Max-Requested-Bandwidth-UL／DL | 516／515 | Unsigned32（bps） | `marBwUl`／`marBwDl` |
| ├ RR-／RS-Bandwidth | 521／522 | Unsigned32 | `rrBw`／`rsBw` |
| ├ Codec-Data | 524 | OctetString | `codecs` |
| ├ Flow-Status | 511 | Enumerated | `fStatus` |
| └ Media-Sub-Component | 519 | Grouped | 一條 flow |
| 　├ Flow-Number | 509 | Unsigned32 | `fNum` |
| 　├ Flow-Description | 507 | IPFilterRule | `fDescs` |
| 　└ Flow-Usage | 512 | Enumerated | `flowUsage` |
| Specific-Action | 513 | Enumerated | 要訂閱的事件 |
| Rx-Request-Type | 533 | Enumerated | INITIAL_REQUEST(0)／UPDATE_REQUEST(1) |
| Abort-Cause | 500 | Enumerated | ASR 的原因 |

### 2.2 Kamailio `ims_qos` 實際送出的內容（看過原始碼）

| 項目 | 實際行為 | 對 Adapter 的影響 |
|---|---|---|
| Subscription-Id | 預設型別是 **SIP URI（IMPU）**，原始碼註解「we only do IMPU now」 | 要從 IMPU 推出 SUPI（見 4.2） |
| Framed-IP-Address | 用收到 SIP 的來源 IP | 直接當 `ueIpv4`；本專案不做 NAT 所以正確 |
| 其他 AVP | 會帶 Service-Info-Status、Authorization-Lifetime、ETSI 的 Reservation-Priority | 字典要能**忽略不認識的 AVP**，不能因此拒絕 |
| 註冊時的 AAR（`Rx_AAR_Register`） | 媒體元件的 Media-Type 預設 `control`，Flow-Description 用 `af_signaling_ip` | 要辨識成「信令」類型的 session |
| 收到 ASR | 結束對應的 session（`terminate_dialog_on_rx_failure` 預設 1） | ASR 就能讓通話結束 |

### 2.3 N5 端（TS 29.514、free5gc PCF）

- 用 `github.com/free5gc/openapi/pcf/PolAuth` 的 client，**不要自己拼 JSON**：
  - `ApplicationSessionsCollectionApi.PostAppSessions`：建立，回 201，`Location` header 裡有 appSessionId
  - `IndividualApplicationSessionContextDocumentApi.ModAppSession`：修改（PATCH）
  - `IndividualApplicationSessionContextDocumentApi.DeleteAppSession`：刪除（`POST .../{id}/delete`）
  - `EventsSubscriptionDocumentApi.UpdateEventsSubsc`：之後修改事件訂閱
- 資料型別用 `models.Pcf_PolAuth_*`
- PCF 的回呼（Adapter 要提供的 HTTP 端點）：
  - 終止：PCF 送到 **`{ascReqData.notifUri}/terminate`**（free5gc 的 `SendAppSessionTermination` 就是這樣組 URL）
  - 事件：PCF 送到 **`evSubsc.notifUri`**
- 錯誤：session binding 失敗 → 500，cause `PDU_SESSION_NOT_AVAILABLE`；服務被拒 → 403，cause `REQUESTED_SERVICE_NOT_AUTHORIZED`（TS 29.514 4.2.2）
- 頻寬字串：free5gc PCF 的 `ConvertBitRateToKbps` 接受 `"<數字> bps|Kbps|Mbps|Gbps|Tbps"`

> 現有 AF shim 的 `notifUri` 是 `http://af:8090/notify`，但只註冊了 `/notify` 這個精確路徑，所以 PCF 送到 `/notify/terminate` 會得到 404。Adapter 要把 `/terminate` 子路徑也接住。

## 3. 程式結構

照 free5gc NF 骨架（`vonr-ims-dev-process.md` 第 1.2 節）。Diameter 部分參考 free5gc **CHF** 的作法：CHF 也用 `github.com/fiorix/go-diameter`，把字典 XML 寫成 Go 字串、以 `dict.Default.Load()` 載入，再用帶 `avp:"..."` tag 的 struct 解碼（見 `NFs/chf/ccs_diameter/`）。

```
rx-n5-adapter/
├── cmd/main.go
├── pkg/
│   ├── app/app.go                  # App 介面
│   ├── factory/config.go           # 設定（第 7 節）
│   └── service/init.go             # context → consumer → processor → rx.Server → sbi.Server
└── internal/
    ├── context/
    │   ├── context.go              # AdapterContext：設定值、NF instance ID、token
    │   └── session.go              # SessionStore 介面 + 記憶體實作（第 4.1 節）
    ├── rx/
    │   ├── dict.go                 # Rx 字典（XML 字串），只列第 2.1 節的 AVP
    │   ├── types.go                # AAR、STR 等 struct（avp tag）
    │   ├── server.go               # Diameter server：CER/DWR、依 command code 分派
    │   ├── handler.go              # AAR／STR → 呼叫 processor
    │   └── sender.go               # 送 RAR／ASR 給 Kamailio
    ├── mapper/                     # 純函式：Rx ↔ N5（第 5 節），不碰網路
    │   ├── to_n5.go
    │   ├── to_rx.go
    │   └── *_test.go               # 表格驅動測試
    ├── sbi/
    │   ├── server.go               # gin：/rx-n5/notify/{sessionKey}/terminate、/rx-n5/events/{sessionKey}
    │   ├── api_callback.go
    │   ├── processor/              # 流程（第 6 節）：查 session、呼叫 mapper 與 consumer
    │   └── consumer/
    │       ├── nrf_service.go      # 註冊為 AF、取 token
    │       ├── pcf_service.go      # PolAuth client
    │       └── bsf_service.go      # Phase 4：以 UE IP 找 PCF
    ├── logger/
    └── util/
```

## 4. 核心資料結構

### 4.1 Session 表

```go
type SessionKind int // Media（通話）或 Signalling（註冊時）

type RxSession struct {
    RxSessionID  string      // Diameter Session-Id，主 key
    Kind         SessionKind
    PeerHost     string      // 送 RAR/ASR 時的 Destination-Host（Kamailio）
    PeerRealm    string
    AppSessionID string      // PCF 回的 ID（Location 最後一段）
    ResourceURI  string      // 完整 Location
    PcfBaseURI   string
    Supi         string
    UeIPv4       string
    Events       []models.Pcf_PolAuth_AfEvent
    State        SessionState // Creating → Active → Terminating → Gone
}

type SessionStore interface {
    Put(*RxSession)
    ByRxID(id string) (*RxSession, bool)
    ByAppSessionID(id string) (*RxSession, bool)
    Delete(rxID string)
}
```

- 回呼 URL 帶 Rx Session-Id 的雜湊作為 `{sessionKey}`，收到回呼時不必再反查
- 狀態轉換只由該 session 所屬的 worker 執行（`vonr-ims-dev-process.md` 第 3 節），所以不需要鎖

### 4.2 SUPI 推導

| Subscription-Id 型別 | 範例 | SUPI |
|---|---|---|
| END_USER_IMSI（1） | `208930000000001` | `imsi-208930000000001` |
| END_USER_SIP_URI（2，Kamailio 預設） | `sip:208930000000001@ims.mnc093.mcc208.3gppnetwork.org` | user part 若是 15 位數字 → `imsi-<user>` |
| 其他或推不出來 | — | 不帶 `supi`，只用 `ueIpv4` 綁定 |

> 一定要盡量帶 `supi`：free5gc PCF 只靠 UE IP 找 session 時，搜尋迴圈找到後不會停，多 UE 時可能綁錯（`af/main.go` 已記錄這個問題）。
> 「IMPU 的 user part 就是 IMSI」只在本專案的開戶規則下成立（`04-add-ims-subscribers.sh`），要做成可設定的規則。

## 5. 對應規則（mapper，全部是純函式）

### 5.1 AAR → `AppSessionContextReqData`

| N5 欄位 | 來源 |
|---|---|
| `supi` | 4.2 |
| `ueIpv4` | Framed-IP-Address |
| `dnn` | Called-Station-Id；沒有就用設定的預設值 `ims` |
| `afAppId` | AF-Application-Identifier；沒有就用設定值 |
| `notifUri` | `http://<adapter>/rx-n5/notify/{sessionKey}`（PCF 會再加 `/terminate`） |
| `suppFeat` | `"0"`（必填） |
| `medComponents` | 每個 Media-Component-Description 一筆，key 是 Media-Component-Number |
| `evSubsc` | Specific-Action 不為空時：`events` 依 5.3 對應，`notifUri` = `http://<adapter>/rx-n5/events/{sessionKey}` |

### 5.2 Media-Component-Description → `MediaComponent`

| N5 欄位 | Rx | 轉換 |
|---|---|---|
| `medCompN` | Media-Component-Number | 直接 |
| `medType` | Media-Type | AUDIO(0)→AUDIO、VIDEO(1)→VIDEO、DATA(2)→DATA、APPLICATION(3)→APPLICATION、CONTROL(4)→CONTROL、TEXT(5)→TEXT、MESSAGE(6)→MESSAGE、OTHER→OTHER |
| `marBwUl`／`marBwDl` | Max-Requested-Bandwidth-UL／DL | bps 整數 → `"<n> bps"` |
| `rrBw`／`rsBw` | RR-／RS-Bandwidth | 同上 |
| `codecs` | Codec-Data | 字串複製 |
| `fStatus` | Flow-Status | ENABLED-UPLINK／ENABLED-DOWNLINK／ENABLED／DISABLED／REMOVED，名稱相同 |
| `medSubComps` | Media-Sub-Component | key 是 Flow-Number |
| └ `fDescs` | Flow-Description | **原樣複製**（兩邊都是 IPFilterRule）；不得改成 `permit inout`，PCF 會只當成上行 |
| └ `flowUsage` | Flow-Usage | NO_INFORMATION→NO_INFO、RTCP→RTCP、AF_SIGNALLING→AF_SIGNALLING |

### 5.3 Specific-Action ↔ AfEvent

| Specific-Action（Rx） | AfEvent（N5） | 確定度 |
|---|---|---|
| CHARGING_CORRELATION_EXCHANGE(1) | CHARGING_CORRELATION | 高 |
| IP-CAN_CHANGE(6) | ACCESS_TYPE_CHANGE | 高 |
| INDICATION_OF_SUCCESSFUL_RESOURCES_ALLOCATION(8) | SUCCESSFUL_RESOURCES_ALLOCATION | 高 |
| INDICATION_OF_FAILED_RESOURCES_ALLOCATION(9) | FAILED_RESOURCES_ALLOCATION | 高 |
| USAGE_REPORT(11) | USAGE_REPORT | 高 |
| ACCESS_NETWORK_INFO_REPORT(12) | ANI_REPORT | 高 |
| PLMN_CHANGE(16) | PLMN_CHG | 高 |
| EPS_FALLBACK(17) | EPS_FALLBACK | 高 |
| SUCCESSFUL_QOS_UPDATE(19)／FAILED_QOS_UPDATE(20) | 同名 | 高 |
| INDICATION_OF_LOSS_OF_BEARER(2)／RECOVERY_OF_BEARER(3) | 沒有直接對應；候選 QOS_NOTIF | **待確認**（TS 29.513） |
| INDICATION_OF_RELEASE_OF_BEARER(4) | 沒有對應；由 `terminate` 處理 | 待確認 |

### 5.4 N5 回應 → AAA Result-Code

| N5 | AAA |
|---|---|
| 201／200 | Result-Code 2001（DIAMETER_SUCCESS） |
| 500 + `PDU_SESSION_NOT_AVAILABLE` | Experimental-Result 5065（IP-CAN_SESSION_NOT_AVAILABLE） |
| 403 + `REQUESTED_SERVICE_NOT_AUTHORIZED` | Experimental-Result 5063（REQUESTED_SERVICE_NOT_AUTHORIZED） |
| 400 等格式錯誤 | Experimental-Result 5061（INVALID_SERVICE_INFORMATION） |
| PCF 無回應或逾時 | Result-Code 3002（DIAMETER_UNABLE_TO_DELIVER） |

## 6. 每種訊息的處理流程

### 6.1 AAR（新 Session-Id）

1. 解碼 AAR；缺 Framed-IP-Address → AAA 5061
2. 判斷類型：媒體元件的 Flow-Usage 是 AF_SIGNALLING，或 Media-Type 是 CONTROL → `Signalling`，否則 `Media`
3. 推 SUPI（4.2）；決定 PCF（Phase 1 用設定值，Phase 4 改用 BSF）
4. `mapper.ToAppSessionContext(aar)`
5. `PostAppSessions`（帶 NRF token，OAuth 關閉時不帶）
6. 成功：存 session（State=Active），回 AAA 2001；失敗：依 5.4 回 AAA，不存

### 6.2 AAR（已存在的 Session-Id，re-INVITE）

1. 找到 session → `mapper.ToAppSessionContextUpdate(aar)` → `ModAppSession`
2. 依結果回 AAA

### 6.3 STR

1. 找 session；找不到也回 STA 2001（冪等）
2. `DeleteAppSession`；PCF 失敗只記 log
3. 刪除 session，回 STA 2001

### 6.4 PCF `terminate` 回呼（PDU session 被釋放）

1. 依 `{sessionKey}` 找 session，State=Terminating
2. 回 PCF 204
3. 送 ASR 給 Kamailio（Abort-Cause = BEARER_RELEASED(0)）
4. Kamailio 回 ASA 後結束通話，接著送 STR → 走 6.3

### 6.5 PCF 事件回呼

1. 找 session，把 N5 事件依 5.3 反向對應成 Specific-Action
2. 送 RAR（帶 Specific-Action，必要時帶 Flows）
3. 回 PCF 204

## 7. 設定檔（草案）

```yaml
info:
  version: 1.0.0
configuration:
  rx:
    bindAddr: 0.0.0.0
    port: 3868
    originHost: adapter.ims.mnc093.mcc208.3gppnetwork.org
    originRealm: ims.mnc093.mcc208.3gppnetwork.org
  sbi:
    scheme: http
    bindingIPv4: 0.0.0.0
    registerIPv4: 10.100.200.50
    port: 8000
  nrfUri: http://nrf.free5gc.org:8000
  pcf:
    uri: http://pcf:8000           # Phase 4 改由 BSF 決定
  defaults:
    dnn: ims
    afAppId: IMS-voice
  supiFromImpu: true               # IMPU user part 是 IMSI 時才開
logger:
  level: info
```

## 8. Kamailio 端要改的設定

`pcscf/kamailio.cfg`（只改設定，SIP 路由邏輯不動）：

1. 載入 `cdp.so`、`cdp_avp.so`、`ims_qos.so`；移除 `http_client.so`
2. `modparam("cdp", "config_file", ...)`：cdp 設定指向 Adapter（peer FQDN、realm，宣告 Auth-Application 16777236／Vendor 10415）
3. `modparam("ims_qos", "rx_dest_realm", "ims.mnc093.mcc208.3gppnetwork.org")`、`af_signaling_ip` 設為 P-CSCF 的 IP
4. INVITE 的 onreply route：200 OK 時依方向呼叫 `Rx_AAR("<resume route>", "orig")` 或 `"term"`，取代 `route(AF_RESERVE)`
5. 刪掉 `AF_READ_OFFER`、`AF_RESERVE`、`AF_RELEASE`、`AF_KEY`（STR 由 ims_qos 在 BYE 時自己送）
6. Phase 4：註冊時呼叫 `Rx_AAR_Register`（官方文件標示只能在 request route 用）

確切語法以 Kamailio 6.1 的 `ims_qos` 與 `cdp` 文件為準；Phase 0 先用假的 Diameter peer 抓包確認。

## 9. 實作順序

每一步都能單獨測，前一步沒過不做下一步：

| # | 做什麼 | 怎麼驗證 |
|---|---|---|
| 1 | 專案骨架（cmd、factory、app、logger），能讀設定、啟動、關閉 | `go build`、啟動後看 log |
| 2 | `rx/dict.go` + `types.go`：載入 Rx 字典，能解碼 AAR | 用錄下來的 AAR 封包做單元測試 |
| 3 | `mapper/to_n5.go` | 表格驅動測試：各種 AVP 組合 → 預期的 N5 JSON |
| 4 | Diameter server：CER／DWR、收 AAR 回固定的 AAA 2001 | 用 go-diameter 寫的小 client 打；Kamailio 的 cdp 能連上 |
| 5 | `consumer/nrf_service.go`：註冊為 AF、取 token | NRF 查得到這個 AF |
| 6 | `consumer/pcf_service.go` + 6.1：真的建 app session | `05-n5-qos-test.sh` 改成用 Rx client 觸發，UPF 上出現 PDR／QER |
| 7 | 6.3 STR | 規則消失 |
| 8 | Kamailio 改設定（第 8 節），拿掉 AF shim | `03-call-test.sh` 通過（**Phase 1 完成**） |
| 9 | 回呼 server + 6.4 terminate → ASR | 通話中釋放被叫 PDU session，通話結束（**Phase 3**） |
| 10 | 6.5 事件 → RAR、6.2 PATCH | 抓包看到 RAR；re-INVITE 後 app session 更新 |
| 11 | 信令 session、BSF（Phase 4） | 註冊時抓包看到 AAR 與對應的 app session |

## 10. 待確認（Phase 0）

1. go-diameter 遇到字典沒有的 AVP（例如 ETSI Reservation-Priority）會不會解碼失敗；必要時把它們加進字典
2. **Flow-Description 的上行寫法。** `ims_qos` 的上行是 `permit in … from <UE> to <對方>`（原始碼 `rx_avp.c`）；現有 shim 兩個方向都寫 `from <對方> to <UE>`，而且測試通過。free5gc PCF 的 `flowDescFromN5toN7` 只把 `permit in` 換成 `permit out`、地址不動。要抓包看 UPF 上的上行 PDR 是否正確；不正確就在 mapper 裡把上行規則的來源與目的對調
3. 5.3 中標「待確認」的事件對應，查 TS 29.513
4. Kamailio cdp 連 Adapter 時是否要求 TLS 或特定的 CER 內容
