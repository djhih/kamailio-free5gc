# Rx／N5 Adapter 介面規格（W3a～W3d）

| 項目 | 內容 |
|---|---|
| 版本／狀態 | v0.6／審查中（2026-10-22：v0.6 新增 §8A.4 QoS notification、§8B IMS 註冊時與 BSF（W3c）、附錄 E；v0.5 新增 §5.4（W3d）；v0.4 新增 §8A（W3b）；v0.3 新增 §14（W4）） |
| 適用範圍 | W3a（通話資源）＋W3b（5GC 回報）＋W3c（IMS 註冊時、BSF）＋W3d（通話中修改）＋W4（Kamailio 設定）＋W5d 的 Adapter 端 |
| 設計理由 | [design.md](design.md)、[adr/](adr/) |
| 驗證方式 | [test-plan.md](test-plan.md)（每條需求對應的測試見該文件 §2） |

## 1. 範圍與用語

### 1.1 範圍

本規格定義 Adapter 在 Rx（對 Kamailio P-CSCF）與 N5（對 free5gc PCF）兩個介面上的行為、狀態機、設定與可觀測性。部署 profile：IPv4、AUDIO、單一 PCF、ims DNN。

### 1.2 需求用語

本規格的需求用語比照 RFC 2119／RFC 8174，**只有粗體時**才有下列意思：

| 用語 | 對應 | 意思 |
|---|---|---|
| **必須** | MUST | 沒有例外 |
| **不得** | MUST NOT | 沒有例外 |
| **應** | SHOULD | 有正當理由時可以不做，但要在實作說明寫出理由 |
| **不應** | SHOULD NOT | 同上，反向 |
| **可** | MAY | 選擇性 |

需求編號格式 `REQ-<區域>-<序號>`，序號不重用。刪除的需求保留編號並標「（已刪除）」。

### 1.3 名詞

| 名詞 | 意思 |
|---|---|
| Rx session | 一個 Diameter Session-Id 代表的授權關係；一通電話通常有兩個 |
| app session | PCF 上的一個 AppSessionContext，以資源 URI 識別 |
| 資源 URI | Create 回應的 `Location`，完整保存，不只存最後一段 ID |
| 重送 | 同一筆 Diameter 交易再送一次（依 RFC 6733 的重複偵測：Origin-Host＋End-to-End-Id，及 T flag） |
| 更新 | 同一 Session-Id 上內容不同的新 AAR |
| tombstone | session CLOSED 後短期保留的紀錄，用來回覆重送與區分「已關閉」與「從未存在」 |
| callbackKey | 放在 `notifUri` 路徑裡、隨機產生的 session 識別；不含使用者身分，也不是驗證憑證 |
| AAR、AAA、STR、STA、ASR、RAR | Rx 的 AA-Request／Answer、Session-Termination-Request／Answer、Abort-Session-Request、Re-Auth-Request |

## 2. 參考文件

### 2.1 規範性參考

版本欄為「TBD」的項目，在 D02 關閉前不能當成符合性的依據。計畫的研究方向是 Rel-17（`specs/3gpp-r17/`）。

| 文件 | 本規格用到的部分 | 版本 | 核對狀態 |
|---|---|---|---|
| 3GPP TS 29.214 | Rx AAR／STR、AVP（§5.3）、錯誤碼 | Rel-17，版本號 TBD | AVP code 已依 §5.3 列出；錯誤碼未核對 |
| 3GPP TS 29.514 | Npcf_PolicyAuthorization：資源、操作、ProblemDetails cause（§4.2.2） | Rel-17，版本號 TBD | 部分（cause 名稱） |
| 3GPP TS 29.513 | Rx 與 N5 的互通對應（附錄 B） | Rel-17，版本號 TBD | 未核對 |
| 3GPP TS 29.500／29.501 | SBI、apiRoot／apiPrefix、HTTP 用法 | TBD | 未核對 |
| IETF RFC 6733 | Diameter base：CER／DWR、M-bit、重複偵測、base Result-Code | — | 待核對相關章節 |
| IETF RFC 8174 | 需求用語 | — | — |

### 2.2 參考資料

TS 23.503（policy 架構、附錄 C）、TS 23.501／23.502（後續 QoS 程序）、Kamailio `ims_qos`／`cdp` 文件與原始碼、free5gc v4.3.0 PCF 原始碼、`free5gc/openapi` v1.3.0。

## 3. 總則

- **REQ-GEN-01** Adapter **必須**以 Diameter server 角色提供 Rx，以 N5 client 角色呼叫 PCF。
- **REQ-GEN-02** Adapter **不得**解析 SIP 或 SDP，**不得**自行決定 QoS（5QI、頻寬上限）。
- **REQ-GEN-03** Adapter **不得**對任何不支援的功能回覆成功（例如回 AAA 2001 但沒有建立對應資源）。
- **REQ-GEN-04** 在 AAA 回報成功前，Adapter **必須**已經取得 PCF 的成功回應**並**持久化資源 URI。

## 4. Diameter peer

- **REQ-PEER-01** **必須**處理 CER／CEA、DWR／DWA、DPR／DPA。
- **REQ-PEER-02** CER／CEA **必須**宣告 Rx 應用：Auth-Application-Id 16777236、Vendor-Id 10415（以 Vendor-Specific-Application-Id 表示）。
- **REQ-PEER-03** **必須**只接受設定中允許的 Origin-Host／Origin-Realm 與來源位址；其他 peer 的 CER **必須**拒絕（Result-Code 見 §10）。
- **REQ-PEER-04** 第一階段 transport 為 TCP 3868，綁在設定的 dnnet 位址。是否要 TLS 依 D04。
- **REQ-PEER-05** 遇到不認識的 AVP：M-bit 為 1 **必須**依 RFC 6733 回錯誤並帶 Failed-AVP；M-bit 為 0 **必須**忽略並繼續處理。Kamailio 實際送出的 AVP（D03）若 M-bit 為 1，**必須**加進字典。
- **REQ-PEER-06** peer 斷線**必須**記錄事件；**不得**因斷線刪除或改變既有 session 的狀態。

## 5. AAR 處理

### 5.1 輸入檢查

- **REQ-AAR-01** Session-Id **必須**存在且非空。
- **REQ-AAR-02** Framed-IP-Address **必須**是有效的 IPv4 位址。
- **REQ-AAR-03** SUPI **必須**由明確的開戶 mapping 取得。從 IMPU 的 user part 推出 IMSI **只有**在設定 `identity.supiFromImpu` 開啟、user part 為 15 位數字、且 realm 符合設定時才可使用。無法綁定時**必須**拒絕，**不得**改用只帶 UE IP 的綁定（[ADR-0003](adr/0003-reject-unbindable-identity.md)）。
- **REQ-AAR-04** 媒體 session 只接受 Media-Type 為 AUDIO 的媒體元件；含其他 Media-Type 的 AAR **必須**拒絕，**不得**建立 app session。信令 session（REQ-REG-01）依 §8B 的 `w3c.mode` 處理。
- **REQ-AAR-05** 同一 AAR 內 Media-Component-Number 重複、或同一元件內 Flow-Number 重複，**必須**拒絕。
- **REQ-AAR-06** 頻寬 AVP **必須**檢查範圍；超出 N5 schema 可表示的範圍時**必須**拒絕，**不得**截斷。
- **REQ-AAR-07** Called-Station-Id 存在時**必須**是允許的 DNN；不存在時使用設定的預設值。
- **REQ-AAR-08** AAR 帶的 Specific-Action 若含第一階段不處理的事件，Adapter **不得**在 AAA 中表示已訂閱。是拒絕整個 AAR，或記錄後只授權媒體，依 D03 的抓包結果決定，並在本條補上結論。
- **REQ-AAR-09** 所有檢查失敗的 AAR，**不得**呼叫 PCF。

### 5.2 欄位對應（AAR → `AppSessionContextReqData`）

第一階段必須支援的對應。AVP code 與型別見附錄 C。「狀態」欄：**定**＝已依原始碼或規格確認；**待**＝要在 D02／D05 關閉時確認。

| N5 欄位 | 來源 | 轉換 | 狀態 |
|---|---|---|---|
| `supi` | Subscription-Id | REQ-AAR-03 | 定（規則）；mapping 待 D05 |
| `ueIpv4` | Framed-IP-Address | 4 bytes → 點分字串 | 定 |
| `dnn` | Called-Station-Id | REQ-AAR-07 | 定 |
| `afAppId` | AF-Application-Identifier | 不存在時用設定值 | 定 |
| `notifUri` | — | `{callback.advertisedBase}/rx-n5/notify/{callbackKey}` | 定 |
| `suppFeat` | — | `"0"`（必填欄位） | 待 D02 |
| `medComponents` | Media-Component-Description | key 為 Media-Component-Number 的十進位字串 | 定 |
| └ `medCompN` | Media-Component-Number | 直接 | 定 |
| └ `medType` | Media-Type | AUDIO(0) → `AUDIO`；其他依 REQ-AAR-04 | 定 |
| └ `marBwUl`／`marBwDl` | Max-Requested-Bandwidth-UL／DL（bps） | 整數 → `"<n> bps"`（free5gc PCF `ConvertBitRateToKbps` 接受的格式） | 定 |
| └ `rrBw`／`rsBw` | RR-／RS-Bandwidth | 同上 | 定 |
| └ `codecs` | Codec-Data | 字串複製 | 待 D02 |
| └ `fStatus` | Flow-Status | 名稱相同（ENABLED-UPLINK／ENABLED-DOWNLINK／ENABLED／DISABLED／REMOVED） | 待 D02 |
| └ `medSubComps` | Media-Sub-Component | key 為 Flow-Number | 定 |
| 　└ `fNum` | Flow-Number | 直接 | 定 |
| 　└ `fDescs` | Flow-Description | 見 REQ-AAR-10 | **待 D05** |
| 　└ `flowUsage` | Flow-Usage | NO_INFORMATION → `NO_INFO`、RTCP → `RTCP`、AF_SIGNALLING → `AF_SIGNALLING` | 待 D02 |

- **REQ-AAR-10** Flow-Description 在 D05 關閉前**必須**原樣複製，**不得**改成 `permit inout`（free5gc PCF 會只當成上行）。D05 若證實上行方向錯誤，改寫規則**必須**寫進本條，並由 T16 驗證。

### 5.3 重送與更新

- **REQ-AAR-11** 對同一 Rx session 的處理**必須**序列化（§9.3）。
- **REQ-AAR-12** 重送（§1.3）**必須**回覆與第一次相同的答案；第一次還在處理中時，**必須**等它完成後回覆同一個答案。重送**不得**觸發新的 Create。
- **REQ-AAR-13** `w3d.enable` 為 false 時，同一 Session-Id 上的更新**必須**拒絕並保持原有 app session 不變（[ADR-0006](adr/0006-no-aar-update-in-phase1.md)）。**不得**把更新當成重送回覆成功，**不得**改成 Delete＋Create。`w3d.enable` 為 true 時依 §5.4。
- **REQ-AAR-14** session 處於 `CREATE_UNKNOWN` 時，任何 AAR **必須**回失敗，**不得**自動重送 Create（[ADR-0004](adr/0004-no-blind-create-retry.md)）。

### 5.4 AAR 更新（W3d）

本節在 `w3d.enable` 為 true 時適用。依據：TS 29.513 V17.14.0 B.3（IMS session modification）；free5gc PCF 的 PATCH 行為見 [ADR-0009](adr/0009-patch-or-replace-on-aar-update.md)。

- **REQ-UPD-01** ACTIVE 時收到更新（§1.3），**必須**比較新舊內容並分類：
  - **只改頻寬或 codec**：media component 集合、每個 Flow-Number 的 Flow-Description 與 Flow-Status 都沒變，只有 Max-Requested-Bandwidth、RR／RS-Bandwidth 或 Codec-Data 改變；
  - **其他**：flow、Flow-Status 或 media component 有任何增減或改變。
- **REQ-UPD-02** 只改頻寬或 codec：**必須**對原 app session 送 PATCH（`AppSessionContextUpdateData`），只帶改變的 media component。
- **REQ-UPD-03** PATCH **必須**帶上 session 保存的 `evSubsc`（free5gc PCF 在 PATCH 沒帶 `evSubsc` 時會清掉訂閱）。
- **REQ-UPD-04** 其他變更：**必須**先 Delete 原 app session，確認刪除後再以新內容 Create 一個新的 app session（break-before-make），並更新 `resourceUri`。**不得**先 Create 再 Delete（flow 相同時 PCF 會共用同一條 PCC rule，刪舊的會連新的一起刪）。
- **REQ-UPD-05** 失敗處理：
  - PATCH 失敗：回 AAA 失敗；session 標 `resourceUncertain`（free5gc PCF 在 PATCH 中途出錯時，可能已移除舊規則）並告警；之後的 STR 照常刪除；
  - Delete 失敗：回 AAA 失敗，原 app session 不變（ACTIVE）；
  - Delete 成功但 Create 失敗：回 AAA 失敗，session 轉 NO_RESOURCE（Rx session 仍在、沒有 app session）；之後的 STR 直接回 STA 成功；
  - Create 結果不明：依 W3a 的 CREATE_UNKNOWN 處理（REQ-AAR-14）。
- **REQ-UPD-06** 更新的重送**必須**依 REQ-AAR-12 回同一答案，**不得**再 PATCH 或再 Delete／Create。
- **REQ-UPD-07** 更新進行中（UPDATING、REPLACING）收到 terminate、事件或 STR：**必須**等目前的 N5 操作有結果，再依 §9.2 處理。

## 6. STR 處理

- **REQ-STR-01** 收到 STR 時，ACTIVE 的 session **必須**先持久化 DELETING 與終止意圖，再呼叫 PCF 刪除。
- **REQ-STR-02** 只有在 PCF 確認刪除後才可轉為 CLOSED。刪除逾時或可重試錯誤**必須**轉為 `DELETE_PENDING`，保留資源 URI 並依 §11 重試（[ADR-0005](adr/0005-keep-resource-until-delete-confirmed.md)）。
- **REQ-STR-03** PCF 回 404 時，只有在 ProblemDetails 表示該資源不存在、且請求的 URI 正是本 session 保存的 URI，才可視為已清理。其他 404（例如路徑錯誤）**必須**當成錯誤處理。
- **REQ-STR-04** 收到不存在的 Session-Id：有 tombstone 的**必須**回覆 tombstone 保存的答案；沒有 tombstone 的回覆依 D02 決定（候選見 §10），**不得**預設一律成功。
- **REQ-STR-05** session 在 CREATING 時收到 STR，**必須**記錄 `pendingTermination`；Create 成功後**必須**先保存 URI，再立刻刪除。
- **REQ-STR-06** STA 的回覆時機（刪除確認後才回，或收到 STR 就回）依 D02 決定。無論哪一種，**不得**在 STA 中表示遠端資源已清除，除非已確認刪除。

## 7. N5 client

- **REQ-N5-01** **必須**使用與部署 PCF 相符版本的 `free5gc/openapi` PolAuth client 與 model（版本記在 manifest，D01）；**不得**手組 JSON。
- **REQ-N5-02** Create 為 `POST {pcf.serviceBase}/app-sessions`。成功回應**必須**是 201 且帶 `Location`；`Location` **必須**以 URL resolver 解析（支援絕對與合法相對形式），完整保存。缺 `Location` 或無法解析時**必須**當成「回覆不完整」（→ `CREATE_UNKNOWN`）。
- **REQ-N5-03** `Location` 解析後的 scheme、host、port 與路徑前綴**必須**落在設定的 PCF service base 之下；否則**必須**當成回覆不完整，**不得**對該位址發任何請求。
- **REQ-N5-04** 釋放**必須**用 `POST {資源 URI}/delete`，**不得**用 HTTP DELETE。
- **REQ-N5-05** 第一階段**不得**送 PATCH 或修改事件訂閱。
- **REQ-N5-06** **不得**假設 API 位於主機根路徑；service base 由設定提供完整 apiRoot＋apiPrefix。
- **REQ-N5-07** 每個 PCF 請求**必須**有逾時（§11），逾時值**必須**小於 Kamailio 端的等待預算減去處理時間。
- **REQ-N5-08** 啟動時**必須**向 NRF 註冊為 AF。OAuth 開啟時**必須**帶 token；關閉時依 REQ-SEC-02 記錄。

## 8. PCF callback

- **REQ-CB-01** **必須**在 `{notifUri}/terminate` 提供可達的 handler（free5gc PCF 在 `notifUri` 後加 `/terminate`）。
- **REQ-CB-02** callbackKey **必須**是至少 128 bit 的隨機值，**不得**由 Session-Id、SUPI 或 IMPU 推出。
- **REQ-CB-03** `w3b.enable` 為 false 時收到 terminate：**必須**記錄並關聯到 session、回 PCF 204、在 session 上標記 `terminateNotified`；**不得**改變 app session 的狀態，**不得**記錄成已送 ASR。`w3b.enable` 為 true 時依 §8A。
- **REQ-CB-04** callbackKey 不存在時**必須**回 404 並記錄；重複通知**必須**冪等。
- **REQ-CB-05** `callback.advertisedBase` **必須**是 PCF 連得到的位址，**不得**是 0.0.0.0 或 loopback；啟動時**應**檢查並警告。

## 8A. 5GC 回報（W3b）

本節在 `w3b.enable` 為 true 時適用。依據：TS 29.214 V17.6.0 §4.4.6.1（IP-CAN session 終止 → 對每個 Rx session 送 ASR）、§4.4.6.2（部分 SDF 失效 → RAR；全部失效 → ASR）；TS 29.514 V17.9.0 §4.2.5.3（terminate：回 204 後呼叫 Delete）、§4.2.5.5（SDF 失效 → FAILED_RESOURCES_ALLOCATION）。設計理由見 [ADR-0007](adr/0007-delete-then-asr-on-terminate.md)、[ADR-0008](adr/0008-map-failed-resources-to-rar-or-asr.md)。

### 8A.1 事件訂閱

- **REQ-EVT-01** AAR 的 Specific-Action 含 INDICATION_OF_LOSS_OF_BEARER(2)、INDICATION_OF_RELEASE_OF_BEARER(4) 或 INDICATION_OF_FAILED_RESOURCES_ALLOCATION(9) 任一個時，Create **必須**帶 `evSubsc`：`events` 含 FAILED_RESOURCES_ALLOCATION，`notifUri` 為 `{callback.advertisedBase}/rx-n5/events/{callbackKey}`。session 紀錄**必須**保存 AAR 訂閱了哪些 Specific-Action（`subscribedActions`）。
- **REQ-EVT-02** 2、4、9 以外的 Specific-Action，W3b 仍依 REQ-AAR-08 處理，**不得**在 N5 訂閱，**不得**在 AAA 中表示已訂閱。
- **REQ-EVT-03** **必須**在 `{callback.advertisedBase}/rx-n5/events/{callbackKey}/notify` 提供 handler（PCF 會在 `evSubsc.notifUri` 後加 `/notify`：TS 29.514 V17.9.0 §5.5 的 callback 表「Event Notification｜{notifUri}/notify」；free5gc openapi PolAuth 的 callback 也是這樣組）：callbackKey 不存在回 404；存在時回 204，再依 §8A.3 處理。同一個通知重複送達**必須**冪等。
- **REQ-EVT-04** 收到 FAILED_RESOURCES_ALLOCATION 以外的事件（PCF 可能送 SUCCESSFUL_RESOURCES_ALLOCATION、ACCESS_TYPE_CHANGE 等）**必須**回 204、記錄，**不得**送 RAR。

### 8A.2 terminate → ASR

- **REQ-ASR-01** 收到 terminate（ACTIVE）：**必須**先持久化「已收到 terminate」與 termCause，回 PCF 204，再呼叫 N5 Delete（TS 29.514 §4.2.5.3）。free5gc PCF 送完 terminate 就已刪除 app session，Delete 回 404＋`APPLICATION_SESSION_CONTEXT_NOT_FOUND` 時依 REQ-STR-03 視為已清理。
- **REQ-ASR-02** Delete 有結論（成功或視為已清理）後，**必須**對該 session 的 peer（`peerHost`／`peerRealm`）送 ASR：Session-Id、Auth-Application-Id 16777236、Abort-Cause 依 §10.3。Delete 進入 DELETE_PENDING 時，ASR 照送，清理依 REQ-STR-02 繼續。
- **REQ-ASR-03** ASA 為成功時，`asrState` 記為 ACKED，等 Kamailio 送 STR（TS 29.214 §4.4.6.1：AF 回 ASA 後發起 STR）。收到 STR 時**必須**回 STA 成功（app session 已在 REQ-ASR-01 處理），session 轉 CLOSED。
- **REQ-ASR-04** ASA 逾時或錯誤時，**必須**依 `w3b.asr.retry` 重送 ASR（同一 Session-Id）；用完**必須**告警，session 標 CLOSED 並保留 tombstone。**不得**因 ASR 失敗而重新建立 app session。
- **REQ-ASR-05** 送 ASR 之後 `w3b.strWait` 內沒有收到 STR：**必須**記錄並把 session 轉 CLOSED（app session 已刪除），保留 tombstone，之後到達的 STR 依 tombstone 回 STA 成功。
- **REQ-ASR-06** terminate 在其他狀態的處理**必須**依 §9.2：CREATING 時，Create 完成後不回 AAA 成功（改回失敗，不送 ASR）；DELETING、DELETE_PENDING、CLOSED 時只回 204，不送 ASR；CREATE_UNKNOWN 時回 204、送 ASR，並記錄供人工清理。

### 8A.3 資源失敗 → RAR 或 ASR

- **REQ-RAR-01** 收到 FAILED_RESOURCES_ALLOCATION 時，**必須**判斷受影響的範圍：通知裡沒有 `flows`，或 `flows` 涵蓋本 session 所有的 media component／flow 時，視為「全部失效」；否則為「部分失效」。
- **REQ-RAR-02** 全部失效：**必須**依 REQ-ASR-01～05 處理（N5 Delete、ASR，Abort-Cause BEARER_RELEASED(0)；TS 29.214 §5.3.1：「also used when all the resource allocation corresponding to an AF session fails」）。差別是 app session 在 PCF 仍存在，Delete 應回成功。
- **REQ-RAR-03** 部分失效：**必須**送 RAR，帶受影響的 Flows（Media-Component-Number、Flow-Number 取自通知的 `flows`），Specific-Action 依 `subscribedActions` 選擇：有 9 用 9；否則有 4 用 4（TS 29.214 §5.3.13 Note 2a：由實作決定）；兩者都沒有就不送 RAR，只記錄。app session **不得**改變。
- **REQ-RAR-04** RAA 逾時或錯誤時，**必須**依 `w3b.rar.retry` 重送；用完告警。RAR 的結果**不得**改變 session 狀態。
- **REQ-RAR-05** ASR、RAR **必須**送往該 session 的 peer。peer 未連線時**必須**排隊，`w3b.peerWait` 內連上就送出；逾時告警並依 REQ-ASR-04 或 REQ-RAR-04 的「用完」處理。

### 8A.4 QoS notification（W5d 的 Adapter 端）

- **REQ-QOS-01** 媒體 session 的 AAR 訂閱了 INDICATION_OF_LOSS_OF_BEARER(2) 或 INDICATION_OF_RECOVERY_OF_BEARER(3) 時，`w5d.enable` 為 true 的 Adapter **必須**在 Create 的 `evSubsc` 加上 QOS_NOTIF。
- **REQ-QOS-02** 收到 QOS_NOTIF 且帶 `qncReports`：`NOT_GUARANTEED` → RAR，Specific-Action 2；`GUARANTEED` → RAR，Specific-Action 3；Flows 取自 `flows`，沒有時為該 session 所有 flow（TS 29.514 §5.6.2.x：`flows` 省略代表全部）。這是語意近似的對應，不是標準對應（[ADR-0011](adr/0011-qos-notif-approximate-mapping.md)）。
- **REQ-QOS-03** 收到 QOS_NOTIF 但沒有 `qncReports`（free5gc PCF 目前的行為）時，**必須**回 204、記錄，**不得**送 RAR。

## 8B. IMS 註冊時（W3c）

依據：TS 29.513 V17.14.0 B.5～B.8；TS 29.514 V17.9.0 §4.2.6.7（訂閱信令路徑，`medCompN` 0、單一 `flowUsage` AF_SIGNALLING、`fNum` 0）、§4.2.2.16（提供 SIP 信令 flow）、§4.2.2.2（201 的 `evsNotif` 帶目前的 access type 與 PLMN）、§4.2.5.10（信令路徑中斷用 FAILED_RESOURCES_ALLOCATION）；TS 29.214 V17.6.0 §4.4.5、§4.4.5A、§4.4.6.3、§5.3.13（非一次性的 Specific-Action 只能放在初始 AAR）。模式選擇的理由見 [ADR-0010](adr/0010-w3c-modes.md)。

### 8B.1 辨識與模式

- **REQ-REG-01** 下列 AAR **必須**視為「信令 session」：Media-Component-Number 0、Media-Sub-Component 的 Flow-Usage 為 AF_SIGNALLING(2)；或 Media-Type 為 CONTROL(4)。
- **REQ-REG-02** `w3c.mode` 為 `off` 時，信令 session 依 REQ-AAR-04 拒絕（現行 W3a 行為）。
- **REQ-REG-03** `w3c.mode` 為 `local` 時，Adapter **必須**接受信令 session、回 AAA 成功，**不得**呼叫 PCF；session 紀錄的 `kind` 記為 SIGNALLING、沒有 `resourceUri`。
- **REQ-REG-04** `w3c.mode` 為 `n5` 時，Adapter **必須**以 Create 建立 app session：`medComponents` 只有 `medCompN` 0、一個 `flowUsage` AF_SIGNALLING 的子元件；AAR 沒有 Flow-Description 時用 `fNum` 0 且不帶其他屬性（§4.2.6.7）；有 Flow-Description 時帶 `fDescs`、`fStatus` ENABLED、`afSigProtocol` SIP（§4.2.2.16）。設定**必須**明確宣告附錄 E 的前提已滿足（`w3c.n5PrerequisitesMet: true`），否則拒絕啟動。

### 8B.2 事件訂閱與 AAA 內容（`n5` 模式）

- **REQ-REG-05** 信令 session 的 Specific-Action 對應：INDICATION_OF_LOSS_OF_BEARER(2)、INDICATION_OF_RELEASE_OF_BEARER(4) → FAILED_RESOURCES_ALLOCATION；IP-CAN_CHANGE(6) → ACCESS_TYPE_CHANGE；PLMN_CHANGE(16) → PLMN_CHG。其他值依 REQ-AAR-08。
- **REQ-REG-06** 非一次性的 Specific-Action 只出現在初始 AAR；同一 Rx session 後續 AAR 帶新的非一次性 Specific-Action 時**必須**忽略並記錄（TS 29.214 §5.3.13）。
- **REQ-REG-07** Create 回應的 `evsNotif` 帶 access type、RAT type 或 PLMN 時，AAA **必須**帶對應的 Rx AVP（IP-CAN-Type、RAT-Type、3GPP-SGSN-MCC-MNC；TS 29.214 附錄 E 表 E.2-1：3GPP NR → IP-CAN-Type 3GPP-5GS、RAT-Type NR）。這三個 AVP 的 code 與列舉值定義在 TS 29.212／29.061，未核對（D13），核對前**不得**送出。

### 8B.3 信令路徑中斷

- **REQ-REG-08** 信令 session 收到 terminate（`n5` 模式）：依 REQ-ASR-01～05 處理（TS 29.214 §4.4.6.1：IP-CAN session 結束時對每個 Rx session 送 ASR）。
- **REQ-REG-09** 信令 session 收到 FAILED_RESOURCES_ALLOCATION（`n5` 模式）：**必須**送 RAR，Specific-Action 依訂閱用 4 或 2（§4.4.6.3），帶受影響的 Flows；**不得**自行送 ASR，由 Kamailio 決定是否結束（§4.4.6.3：AF「may」terminate）。
- **REQ-REG-10** `local` 模式下，Adapter 收到同一 UE（以 UE IP 與 SUPI 比對）任一媒體 session 的 terminate 時，**必須**對該 UE 的信令 session 送 ASR。UE 沒有通話時，`local` 模式**無法**得知 PDU session 結束；這個限制**必須**寫在啟動 log。

### 8B.4 以 BSF 找 PCF

- **REQ-BSF-01** `pcf.discovery` 為 `bsf` 時，每個新的 Rx session（媒體或信令）**必須**先以 `GET {bsf}/nbsf-management/v1/pcfBindings?ipv4Addr=<UE IP>&dnn=<DNN>` 查 PCF；路徑與參數依 free5gc BSF 實作（TS 29.521 本機沒有，D14）。
- **REQ-BSF-02** BSF 回 204（查無）時**必須**回 AAA 失敗（候選 Experimental-Result 5065 IP-CAN_SESSION_NOT_AVAILABLE），**不得**改用設定的預設 PCF。
- **REQ-BSF-03** **必須**用回應的 `pcfIpEndPoints` 組 PCF 的位址；**不得**依賴 `pcfFqdn`（free5gc PCF 在這個欄位填的是 API 前綴的 URL）。
- **REQ-BSF-04** 查到的 PCF **必須**記在 session（`pcfServiceBase`）；同一 session 之後的操作**必須**用同一個 PCF。

## 9. Session 狀態與並行

### 9.1 Session 紀錄

| 欄位 | 用途 |
|---|---|
| `rxSessionId` | 主 key |
| `peerHost`／`peerRealm` | 驗證後續訊息來源；W3b 送 ASR／RAR 用 |
| `callbackKey` | callback 反查（REQ-CB-02） |
| `resourceUri` | PCF 原始資源 URI（完整） |
| `pcfServiceBase` | 此 session 實際用的 PCF |
| `supi`／`ueIpv4`／`dnn` | 綁定與除錯；輸出到 log 時遮蔽 |
| `requestFingerprint`／交易識別 | 區分重送與更新 |
| `mediaComponents` | 保留 component／flow number |
| `state`／`generation`／`operationId`／`pendingTermination`／`terminateNotified` | 狀態機與晚到回覆 |
| `lastOutcome`／`cachedAnswer`／`retryCount`／時間戳 | 重送回覆、重試、稽核 |
| `subscribedActions` | AAR 訂閱的 Specific-Action（REQ-EVT-01、REQ-RAR-03） |
| `kind` | MEDIA 或 SIGNALLING（REQ-REG-01） |
| `termCause`／`asrState`／`asrAttempts` | W3b：收到的 termCause、ASR 進度（NONE／PENDING／SENT／ACKED／FAILED）與次數 |

### 9.2 狀態轉移表

「—」表示該事件在該狀態不會發生或直接忽略並記錄。`answer` 表示回給 Kamailio 的 Diameter 答案；代碼見 §10。標「W3b」的列只在 `w3b.enable` 為 true 時適用；為 false 時 terminate 依 REQ-CB-03。ABORTING 是 W3b 新增的狀態：app session 已處理，已送或正在送 ASR，等 Kamailio 的 STR。UPDATING、REPLACING、RECREATING、NO_RESOURCE 是 W3d 新增的狀態，只在 `w3d.enable` 為 true 時出現；為 false 時 AAR 更新依 REQ-AAR-13 拒絕（表中「ACTIVE｜AAR 更新｜answer 拒絕」那一列）。

| 目前狀態 | 事件 | 動作 | 下一狀態 |
|---|---|---|---|
| （無） | AAR 通過檢查 | 持久化紀錄與 operationId；送 Create | CREATING |
| （無） | AAR 檢查失敗 | answer 錯誤；不呼叫 PCF | （無，只記 log） |
| （無） | STR | 依 REQ-STR-04 | （無） |
| CREATING | AAR 重送 | 等第一次完成後回同一答案 | CREATING |
| CREATING | AAR 更新 | answer 拒絕 | CREATING |
| CREATING | STR | 設 `pendingTermination` | CREATING |
| CREATING | Create 201＋合法 Location，無 pendingTermination | 保存 URI；answer 成功 | ACTIVE |
| CREATING | Create 201＋合法 Location，有 pendingTermination | 保存 URI；送 Delete；AAR answer 失敗 | DELETING |
| CREATING | Create 明確失敗（4xx／5xx＋ProblemDetails） | answer 依 §10；快取答案 | CLOSED |
| CREATING | Create 逾時、回覆不完整、Location 不合法 | 告警；answer 失敗 | CREATE_UNKNOWN |
| CREATING | Create 成功但保存 URI 失敗 | 用記憶體中的 URI 補償刪除；answer 失敗 | DELETING（補償）；補償也失敗 → DELETE_PENDING |
| CREATING | 重啟 | 結果視為不明 | CREATE_UNKNOWN |
| ACTIVE | AAR 重送 | 回快取的成功答案 | ACTIVE |
| ACTIVE | AAR 更新 | answer 拒絕，資源不變 | ACTIVE |
| ACTIVE | STR | 持久化終止意圖；送 Delete | DELETING |
| ACTIVE | terminate callback | REQ-CB-03 | ACTIVE |
| CREATE_UNKNOWN | AAR（任何） | answer 失敗；不重送 Create | CREATE_UNKNOWN |
| CREATE_UNKNOWN | STR | 記錄終止意圖；answer 依 D02 | CREATE_UNKNOWN |
| CREATE_UNKNOWN | 人工確認並清理 | 記錄處置結果 | CLOSED |
| DELETING | STR 重送 | 等刪除完成後回同一答案 | DELETING |
| DELETING | Delete 2xx | 快取答案；answer 成功 | CLOSED |
| DELETING | Delete 404（符合 REQ-STR-03） | 同上 | CLOSED |
| DELETING | Delete 逾時／可重試錯誤 | 排程重試 | DELETE_PENDING |
| DELETING | Delete 不可重試錯誤 | 告警 | DELETE_PENDING（重試次數設為耗盡） |
| DELETING | 重啟 | 恢復為待清理 | DELETE_PENDING |
| DELETE_PENDING | 重試時間到 | 送 Delete | DELETING |
| DELETE_PENDING | 重試耗盡 | 告警；等人工 | DELETE_PENDING |
| DELETE_PENDING | 人工確認已清理 | 記錄 | CLOSED |
| CLOSED | AAR／STR 重送 | 回 tombstone 快取的答案 | CLOSED |
| CLOSED | 同一 Session-Id 的新 AAR（非重送） | answer 拒絕（Session-Id 不得重用） | CLOSED |
| CLOSED | tombstone 到期 | 刪除紀錄 | （無） |
| （無） | 信令 AAR，`w3c.mode`＝local | AAA 成功；不呼叫 PCF | ACTIVE（SIGNALLING，無 resourceUri） |
| ACTIVE（SIGNALLING，local） | STR | STA 成功 | CLOSED |
| ACTIVE（SIGNALLING，local） | 同 UE 的媒體 session 收到 terminate（REQ-REG-10） | 送 ASR | ABORTING |
| （無） | 信令 AAR，`w3c.mode`＝n5 | 同媒體 session 的 Create 流程（REQ-REG-04） | CREATING |
| ACTIVE（SIGNALLING，n5） | FAILED_RESOURCES_ALLOCATION | 回 204；RAR（REQ-REG-09）；不送 ASR | ACTIVE |
| ACTIVE（MEDIA） | QOS_NOTIF（W5d） | 回 204；依 REQ-QOS-02、03 | ACTIVE |
| ACTIVE | AAR 更新，只改頻寬或 codec（W3d） | PATCH（帶 `evSubsc`） | UPDATING |
| UPDATING | PATCH 2xx | 保存新內容；AAA 成功 | ACTIVE |
| UPDATING | PATCH 失敗或逾時 | AAA 失敗；標 `resourceUncertain`；告警 | ACTIVE |
| ACTIVE | AAR 更新，其他變更（W3d） | Delete 原 app session | REPLACING |
| REPLACING | Delete 2xx 或 404（符合 REQ-STR-03） | Create 新的 app session | RECREATING |
| REPLACING | Delete 失敗或逾時 | AAA 失敗；原 app session 不變 | ACTIVE |
| RECREATING | Create 201＋合法 Location | 保存新 URI；AAA 成功 | ACTIVE |
| RECREATING | Create 明確失敗 | AAA 失敗；告警 | NO_RESOURCE |
| RECREATING | Create 逾時或回覆不完整 | 告警；AAA 失敗 | CREATE_UNKNOWN |
| UPDATING、REPLACING、RECREATING | AAR 重送 | 等完成後回同一答案 | 不變 |
| UPDATING、REPLACING、RECREATING | STR、terminate、事件 | 記錄，等目前操作結束後依本表處理（REQ-UPD-07） | 不變 |
| NO_RESOURCE | STR | STA 成功 | CLOSED |
| NO_RESOURCE | AAR 更新 | 依新內容 Create | RECREATING |
| NO_RESOURCE | terminate 或事件 | 回 204（app session 已不存在）；W3b 開啟時送 ASR | ABORTING |
| CREATING | terminate（W3b） | 回 204；記錄 `terminateNotified`；Create 完成後依 REQ-ASR-06 回 AAA 失敗並刪除 | CREATING |
| ACTIVE | terminate（W3b） | 持久化；回 204；N5 Delete（REQ-ASR-01） | DELETING（`asrState`＝PENDING） |
| DELETING（`asrState`＝PENDING） | Delete 2xx 或 404（符合 REQ-STR-03） | 送 ASR（REQ-ASR-02） | ABORTING |
| DELETING（`asrState`＝PENDING） | Delete 逾時／可重試錯誤 | 送 ASR；排程重試 Delete | DELETE_PENDING（`asrState`＝SENT） |
| ABORTING | ASA 成功 | `asrState`＝ACKED；開始 `strWait` | ABORTING |
| ABORTING | ASA 逾時或錯誤 | 依 REQ-ASR-04 重送；用完告警 | ABORTING 或 CLOSED |
| ABORTING | STR | 回 STA 成功 | CLOSED |
| ABORTING | `strWait` 到期 | 記錄（REQ-ASR-05） | CLOSED |
| ABORTING | terminate 或事件（重複） | 回 204 | ABORTING |
| ACTIVE | 事件：FAILED_RESOURCES_ALLOCATION，全部失效 | 回 204；N5 Delete；之後同 terminate（REQ-RAR-02） | DELETING（`asrState`＝PENDING） |
| ACTIVE | 事件：FAILED_RESOURCES_ALLOCATION，部分失效 | 回 204；依 REQ-RAR-03 送 RAR 或只記錄 | ACTIVE |
| ACTIVE | 其他事件 | 回 204；記錄（REQ-EVT-04） | ACTIVE |
| DELETING、DELETE_PENDING | terminate 或事件 | 回 204；不送 ASR、RAR（Kamailio 已送 STR） | 不變 |
| CREATE_UNKNOWN | terminate | 回 204；送 ASR；記錄供人工清理 | CREATE_UNKNOWN（`asrState`＝SENT） |
| CLOSED | terminate 或事件 | tombstone 存在時回 204；否則依 REQ-CB-04 回 404 | CLOSED |

### 9.3 並行

- **REQ-ST-01** 同一 session 的事件**必須**序列化處理（每 session 一個 worker 或等價的鎖）。跨 session 共用的索引（rxSessionId、callbackKey、peer 表）**必須**另外同步。等待網路時**不得**持有全域鎖。
- **REQ-ST-02** PCF 的回應**必須**以 operationId／generation 比對；不符合目前操作的晚到回應**不得**覆蓋狀態，只記錄。
- **REQ-ST-03** 正式驗收（G3）的 session store **必須**在重啟後保留 §9.1 的紀錄。只存在記憶體的實作只能標為開發 PoC，不能通過 T14。
- **REQ-ST-04** 重啟後**必須**依 §9.2 把 CREATING 轉成 CREATE_UNKNOWN、DELETING 轉成 DELETE_PENDING，並恢復重試排程。
- **REQ-ST-05** **不得**假設 PCF 能依自訂 key 查詢或列出 app session。

## 10. 結果代碼對應

D02 關閉前，下表的代碼都是**候選值**。來源欄說明候選值從哪裡來；「核對」欄在 D02 關閉時填入 TS 版本與章節。

### 10.1 PCF 回應 → AAA

| 情況 | 候選 AAA | 來源 | 核對 |
|---|---|---|---|
| 201 | Result-Code 2001 DIAMETER_SUCCESS | v0.1 設計 | |
| 500＋`PDU_SESSION_NOT_AVAILABLE` | Experimental-Result 5065 IP-CAN_SESSION_NOT_AVAILABLE | v0.1 設計；TS 29.514 §4.2.2 | |
| 403＋`REQUESTED_SERVICE_NOT_AUTHORIZED` | Experimental-Result 5063 REQUESTED_SERVICE_NOT_AUTHORIZED | 同上 | |
| 400 等格式錯誤 | Experimental-Result 5061 INVALID_SERVICE_INFORMATION | v0.1 設計 | |
| 逾時／回覆不完整（→ CREATE_UNKNOWN） | TBD。v0.1 用 3002 DIAMETER_UNABLE_TO_DELIVER，但 3002 是 relay 層的協定錯誤，語意不符；候選 5012 DIAMETER_UNABLE_TO_COMPLY | v0.1 設計／本版質疑 | |

### 10.2 本地判定 → Diameter 答案

| 情況 | 候選 | 核對 |
|---|---|---|
| 缺必要 AVP（REQ-AAR-01、02） | 5005 DIAMETER_MISSING_AVP（RFC 6733）；v0.1 對缺 Framed-IP 用 5061 | |
| 不認識的 M-bit AVP（REQ-PEER-05） | 5001 DIAMETER_AVP_UNSUPPORTED＋Failed-AVP | |
| 身分無法綁定（REQ-AAR-03） | TBD | |
| 不支援的 Media-Type（REQ-AAR-04）、重複編號（REQ-AAR-05） | 5061 INVALID_SERVICE_INFORMATION | |
| 第一階段不支援的更新（REQ-AAR-13） | TBD | |
| 不允許的 peer（REQ-PEER-03） | 3010 DIAMETER_UNKNOWN_PEER | |
| STR：未知 Session-Id、無 tombstone（REQ-STR-04） | 5002 DIAMETER_UNKNOWN_SESSION_ID；v0.1 回 2001 | |
| STR：DELETE_PENDING（REQ-STR-06） | TBD | |

### 10.3 W3b：N5 通知 → Rx

| N5 | Rx | 來源 | 核對 |
|---|---|---|---|
| terminate，termCause `PDU_SESSION_TERMINATION` | ASR，Abort-Cause BEARER_RELEASED(0) | TS 29.214 §5.3.1（bearer 因正常信令被停用） | 候選，D11 |
| terminate，termCause `ALL_SDF_DEACTIVATION` | ASR，Abort-Cause BEARER_RELEASED(0) | 同上（「all the resource allocation … fails」） | 候選，D11 |
| terminate，termCause `INSUFFICIENT_QOS_FLOW_RESOURCES` | ASR，Abort-Cause INSUFFICIENT_BEARER_RESOURCES(2) | TS 29.214 §5.3.1 | 候選，D11 |
| terminate，termCause `INSUFICIENT_SERVER_RESOURCES`（規格拼法） | ASR，Abort-Cause INSUFFICIENT_SERVER_RESOURCES(1) | 同上 | 候選，D11 |
| terminate，termCause `PS_TO_CS_HO` | ASR，Abort-Cause PS_TO_CS_HANDOVER(3) | 同上 | 候選，D11 |
| 其他或缺少 termCause | ASR，Abort-Cause BEARER_RELEASED(0) | 本規格的預設 | 候選，D11 |
| FAILED_RESOURCES_ALLOCATION，全部失效 | ASR，Abort-Cause BEARER_RELEASED(0) | TS 29.214 §4.4.6.2、§5.3.1 | 候選，D11 |
| FAILED_RESOURCES_ALLOCATION，部分失效 | RAR，Specific-Action 9 或 4（REQ-RAR-03）＋Flows | TS 29.214 §4.4.6.2、§5.3.13 Note 2a | 候選，D11 |

Abort-Cause 的 AVP code 500 與上列列舉值已依 TS 29.214 V17.6.0 §5.3.1 核對；termCause 的值依 TS 29.514 V17.9.0 §4.2.5.3。「候選」指的是對應關係，不是代碼本身。

## 11. 設定

```yaml
info:
  version: 1.0.0
configuration:
  rx:
    bindAddr: 10.100.100.x            # dnnet；依 compose 指定
    port: 3868
    originHost: adapter.ims.mnc093.mcc208.3gppnetwork.org
    originRealm: ims.mnc093.mcc208.3gppnetwork.org
    allowedPeers:                     # REQ-PEER-03
      - host: pcscf.ims.mnc093.mcc208.3gppnetwork.org
        realm: ims.mnc093.mcc208.3gppnetwork.org
        addr: 10.100.100.10
  sbi:
    scheme: http
    bindingIPv4: 10.100.200.x         # corenet
    port: 8000
  callback:
    advertisedBase: http://10.100.200.x:8000   # REQ-CB-05：PCF 連得到的位址
  nrfUri: http://nrf.free5gc.org:8000
  pcf:
    serviceBase: http://pcf:8000/npcf-policyauthorization/v1   # REQ-N5-06：完整 apiRoot + apiPrefix
    discovery: static                 # static｜bsf（REQ-BSF-01）
    bsfUri: http://bsf:8000           # REQ-BSF-01
    requestTimeout: 3s                # REQ-N5-07
  security:
    oauth: false                      # REQ-SEC-02：false 時啟動記錄「實驗 profile」
  identity:
    mapping: /etc/rx-n5/identity.yaml # REQ-AAR-03：IMPU → SUPI 開戶 mapping
    supiFromImpu: false               # 預設關閉
    impuRealm: ims.mnc093.mcc208.3gppnetwork.org
  defaults:
    dnn: ims
    afAppId: IMS-voice
  allowedDnn: [ims]
  store:
    kind: memory                      # memory（PoC）或持久化實作（D06）
  retry:
    delete:
      maxAttempts: 5                  # 首次失敗後
      backoff: [1s, 2s, 4s, 8s, 16s]  # 加 jitter；只重試可重試錯誤
    create: none                      # REQ-AAR-14
  tombstoneTTL: 10m                   # 須涵蓋 Kamailio 的重送窗口（D06）
  pendingAlertAfter: 60s              # DELETE_PENDING／CREATE_UNKNOWN 超過即告警
  w3d:
    enable: true                      # REQ-AAR-13、§5.4
  w3c:
    mode: local                       # off｜local｜n5（REQ-REG-02～04）
    n5PrerequisitesMet: false         # REQ-REG-04：附錄 E 的 PCF／SMF 修改是否已完成
  w5d:
    enable: false                     # REQ-QOS-01；PCF 修好 QOS_NOTIF 前沒有作用
  w3b:
    enable: true                      # REQ-CB-03、§8A
    asr:
      retry: {maxAttempts: 3, backoff: [1s, 2s, 4s]}   # REQ-ASR-04
    rar:
      retry: {maxAttempts: 3, backoff: [1s, 2s, 4s]}   # REQ-RAR-04
    strWait: 30s                      # REQ-ASR-05
    peerWait: 10s                     # REQ-RAR-05
    diameterAnswerTimeout: 5s         # ASA／RAA 逾時
logger:
  level: info
```

上面的數值都是實驗初始值，不是 3GPP 規定。

- **REQ-CFG-01** 啟動時**必須**檢查設定完整性（allowedPeers 非空、advertisedBase 合法、serviceBase 可解析），不合法時**必須**拒絕啟動。
- **REQ-CFG-02** 待清理紀錄**不得**因 TTL 到期而自動刪除；`pendingAlertAfter` 只觸發告警。
- **REQ-CFG-03** `w3b.enable` 為 true 時，`tombstoneTTL` **必須**大於 `w3b.strWait`，否則拒絕啟動（ASR 之後晚到的 STR 才能依 tombstone 回答）。

## 12. 安全

- **REQ-SEC-01** log **不得**含 K、OP、OPc、認證向量、access token；SUPI 與 IMPU **必須**遮蔽或以內部 ID 取代。
- **REQ-SEC-02** OAuth、TLS 或 mTLS 任一關閉時，啟動 log **必須**明確記錄目前是實驗 profile。
- 其他安全相關需求：REQ-PEER-03（peer 白名單）、REQ-N5-03（Location 限制）、REQ-CB-02（callbackKey）、REQ-AAR-03（身分綁定）。威脅模型見 [design.md](design.md) §7.1。

## 13. 可觀測性與維運

- **REQ-OBS-01** 每個 Rx 與 N5 操作**必須**記錄 correlation ID、內部 session ID、方向、操作、前後狀態、PCF status／cause、耗時、retry 次數。
- **REQ-OBS-02** **必須**提供指標：Rx／N5 各操作的成功、失敗、逾時次數；各狀態的 session 數；`CREATE_UNKNOWN` 與 `DELETE_PENDING` 數；重試與重試耗盡次數；peer 連線狀態。
- **REQ-OBS-03** 健康檢查**必須**區分「程序存活」與「可處理新請求」（peer 已連線、PCF 可達、store 可寫）。
- **REQ-OPS-01** 優雅關閉時**必須**停收新 AAR、保存進行中狀態；無法完成的操作**必須**留下可在重啟後恢復的紀錄。
- **REQ-OPS-02** 切換到 Adapter 後，shim 與 Adapter **不得**同時為同一通電話預留資源；**必須**保留切回 shim 的程序。

---

## 14. Kamailio P-CSCF 設定（W4）

本節規定 W3a 的 G3 要套用到 `kamailio-free5gc/pcscf/` 的改動。只改模組、Diameter peer 與 QoS 相關的 route；SIP 路由邏輯不動。`ims_qos`、`cdp` 的確切參數名稱與函式介面以 Kamailio 6.1 的模組文件為準，G1 核對（D03）。

- **REQ-KAM-01** P-CSCF 映像**必須**包含 `cdp`、`cdp_avp`、`ims_qos` 模組。現行 Dockerfile 安裝 `kamailio-ims-modules`（kamailio61 套件庫），G1 **必須**在映像內確認三個模組檔存在。
- **REQ-KAM-02** 切換後，`kamailio.cfg` **必須**載入 `cdp`、`cdp_avp`、`ims_qos`，**不得**再載入 `http_client`，也**不得**保留 `AF_READ_OFFER`、`AF_RESERVE`、`AF_RELEASE`、`AF_KEY` 這幾個 route 與它們的呼叫點。
- **REQ-KAM-03** P-CSCF **必須**有自己的 cdp 設定檔：本身的 FQDN 與 realm、唯一的 peer 是 Adapter（FQDN、realm、port 3868），宣告 Auth-Application-Id 16777236、Vendor-Id 10415；**不得**列出 HSS（P-CSCF 不走 Cx）。
- **REQ-KAM-04** `ims_qos` **必須**設定 `rx_dest_realm` 為 `ims.mnc093.mcc208.3gppnetwork.org`，`af_signaling_ip` 為 P-CSCF 在 dnnet 的位址。
- **REQ-KAM-05** INVITE 收到 200 OK 時，P-CSCF **必須**對主叫與被叫兩段各呼叫一次 `Rx_AAR`（方向分別為 `orig`、`term`），取代原本的 `route(AF_RESERVE)`；同一段**不得**呼叫兩次。
- **REQ-KAM-06** `Rx_AAR` 回覆失敗時的 SIP 處理依 D09。D09 關閉前沿用現行 shim 的行為：記錄錯誤、通話繼續（`pcscf/kamailio.cfg` 的 `AF_RESERVE`）。
- **REQ-KAM-07** W3a **不得**呼叫 `Rx_AAR_Register`（註冊時的 AAR 會被 REQ-AAR-04 拒絕；屬 W3c）。
- **REQ-KAM-08** `terminate_dialog_on_rx_failure` 的值**必須**明確寫在設定中（不依賴預設），並記入 test-plan §5 的 manifest。
- **REQ-KAM-09** 除了 REQ-KAM-02～05 列出的改動，`kamailio.cfg` 的其他 route **不得**改變；G3 的 PR **必須**附上前後 diff。
- **REQ-KAM-11** W3c：`w3c.mode` 不是 `off` 時，P-CSCF **必須**在 UE 的 IMS 註冊成功後呼叫 `Rx_AAR_Register`（TS 29.513 B.5：註冊完成後才訂閱）；`ims_qos` 文件標示這個函式只能在 request route 使用，實際呼叫時機待 D15。
- **REQ-KAM-10** W3d：re-INVITE（dialog 內的 INVITE）收到 200 OK 時，P-CSCF **必須**在原本的 Rx session 上送更新的 AAR（同一個 Session-Id）。`ims_qos` 是否自動沿用原 Rx session 待 D12 確認；不是的話，cfg 要自行處理。

---

## 附錄 A（參考）Kamailio 端要改的設定

需求見 §14（REQ-KAM-01～09）；以下是對應的設定步驟，僅供參考。`pcscf/kamailio.cfg`，只改設定，SIP 路由邏輯不動。確切語法以 Kamailio 6.1 的 `ims_qos`、`cdp` 文件為準。

1. 載入 `cdp.so`、`cdp_avp.so`、`ims_qos.so`；移除 `http_client.so`
2. `modparam("cdp", "config_file", ...)`：peer 指向 Adapter（FQDN、realm），宣告 Auth-Application 16777236／Vendor 10415
3. `modparam("ims_qos", "rx_dest_realm", "ims.mnc093.mcc208.3gppnetwork.org")`；`af_signaling_ip` 設為 P-CSCF 的 IP
4. INVITE 的 onreply route：200 OK 時依方向呼叫 `Rx_AAR("<resume route>", "orig")` 或 `"term"`，取代 `route(AF_RESERVE)`
5. 刪掉 `AF_READ_OFFER`、`AF_RESERVE`、`AF_RELEASE`、`AF_KEY`（BYE 時 `ims_qos` 自己送 STR）
6. 第一階段**不呼叫** `Rx_AAR_Register`（會被 REQ-AAR-04 拒絕）；W3c 才加

## 附錄 B（參考）Kamailio `ims_qos` 已知行為

讀的是 Kamailio **master** 原始碼；部署是 **6.1.4**，D03 要用 6.1.4 抓包確認。

| 項目 | 行為 | 影響 |
|---|---|---|
| Subscription-Id | 預設型別 SIP URI（IMPU），原始碼註解「we only do IMPU now」 | REQ-AAR-03 |
| Framed-IP-Address | 用收到 SIP 的來源 IP | 本專案不做 NAT，可直接當 `ueIpv4` |
| 其他 AVP | 會帶 Service-Info-Status、Authorization-Lifetime、ETSI Reservation-Priority | REQ-PEER-05：要看 M-bit |
| 上行 Flow-Description | `permit in … from <UE> to <對方>`（`rx_avp.c`）；現有 shim 兩方向都寫 `from <對方> to <UE>` | REQ-AAR-10、D05 |
| 註冊時 `Rx_AAR_Register` | Media-Type 預設 CONTROL，Flow-Description 用 `af_signaling_ip` | REQ-AAR-04 |
| 收到 ASR | 結束對應 session（`terminate_dialog_on_rx_failure` 預設 1），之後送 STR | REQ-ASR-03；6.1.4 的實際行為待 D10 |
| 收到 RAR（Specific-Action 4 或 9） | 未讀到相關原始碼 | REQ-RAR-03；待 D10 |
| AAR 訂閱的 Specific-Action | 2024 年碩論的截圖是 1、2、3、4、6、12（不含 9） | REQ-EVT-01 依此訂閱；6.1.4 的實際值待 D03 |

## 附錄 C（參考）Rx 指令與 AVP

Application-Id 16777236，Vendor-Id 10415。AVP code 與型別取自 TS 29.214 §5.3；base AVP 來自 RFC 6733／4006。

| 指令 | Code | 方向 | 階段 |
|---|---|---|---|
| AAR／AAA | 265 | Kamailio → Adapter | W3a |
| STR／STA | 275 | Kamailio → Adapter | W3a |
| RAR／RAA | 258 | Adapter → Kamailio | W3b |
| ASR／ASA | 274 | Adapter → Kamailio | W3b |

| AVP | Code | 型別 |
|---|---|---|
| Session-Id | 263 | UTF8String |
| Framed-IP-Address | 8 | OctetString |
| Subscription-Id（Type 450、Data 444） | 443 | Grouped |
| Called-Station-Id | 30 | UTF8String |
| AF-Application-Identifier | 504 | OctetString |
| Media-Component-Description | 517 | Grouped |
| ├ Media-Component-Number | 518 | Unsigned32 |
| ├ Media-Type | 520 | Enumerated |
| ├ Max-Requested-Bandwidth-UL／DL | 516／515 | Unsigned32（bps） |
| ├ RR-／RS-Bandwidth | 521／522 | Unsigned32 |
| ├ Codec-Data | 524 | OctetString |
| ├ Flow-Status | 511 | Enumerated |
| └ Media-Sub-Component | 519 | Grouped |
| 　├ Flow-Number | 509 | Unsigned32 |
| 　├ Flow-Description | 507 | IPFilterRule |
| 　└ Flow-Usage | 512 | Enumerated |
| Specific-Action | 513 | Enumerated |
| Rx-Request-Type | 533 | Enumerated |
| Abort-Cause | 500 | Enumerated |

## 附錄 D（參考）Specific-Action ↔ AfEvent

W3b 只使用其中 2、4、9 與 FAILED_RESOURCES_ALLOCATION 的對應（§8A）；其他列屬 W3c 之後。

「確定度」只指名稱對應，不代表 free5gc PCF 會發通知（PCF 實際處理的事件見 [design.md](design.md) §13）。

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
| INDICATION_OF_LOSS_OF_BEARER(2)／RECOVERY_OF_BEARER(3) | 無直接對應；候選 QOS_NOTIF | 待確認（TS 29.513） |
| INDICATION_OF_RELEASE_OF_BEARER(4) | 無；由 terminate 處理 | 待確認 |

## 附錄 E（參考）`w3c.mode: n5` 的前提（本計畫外的 PCF、SMF 修改）

讀 free5gc PCF（`eb57557`）與 SMF v1.4.6 原始碼得到的限制，以及 `n5` 模式需要的修改：

| 現況 | 後果 | 需要的修改 |
|---|---|---|
| `fNum` 0、沒有 `fDescs` 的子元件會產生一條沒有 flow 也沒有 AppId 的 PCC rule；SMF 的 `applyFlowInfoOrPFD` 對它回錯，之後**每一次** policy 更新（包括語音規則）都失敗 | 照 §4.2.6.7 訂閱會讓通話的 QoS 全部失效 | PCF：沒有 flow 的 AF_SIGNALLING 子元件不產生 PCC rule；允許只帶 `evSubsc` 的 Create |
| `MediaTypeTo5qiMap` 把 CONTROL 對應到 5QI 9；PCF 沒有任何地方處理 AF_SIGNALLING | 送 SIP 信令 flow 會產生 5QI 9、precedence 高於預設規則的 PCC rule，SIP 被搬離 `ims` DNN 的 5QI 5 預設 flow | PCF：AF_SIGNALLING 的 flow 不另建規則，或對應到 5QI 5 並沿用預設 QoS flow |
| SMF 從不送 `AC_TY_CH`、`PLMN_CH`、ruleReports（W5c 之前） | 訂閱只拿得到 Create 時的現值，之後的變更不會通知 | SMF：回報 access type、PLMN 變更（不在本計畫） |
| PCF 的 PolicyAuthorization `suppFeat` 是 3，沒有 IMS_SBI（5）與 ProvAFsignalFlow（7） | 協商結果不含這兩個 feature | PCF 設定 |
| `SessionBinding` 沒有 SUPI／GPSI 時，多 UE 下可能綁錯 | 也影響 W3a；Adapter 一律帶 SUPI（REQ-AAR-03）可避開 | 已由 REQ-AAR-03 處理 |
