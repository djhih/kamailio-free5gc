# HSS 併入 UDM 介面規格（W8a＋W8b）

| 項目 | 內容 |
|---|---|
| 版本／狀態 | v0.3／審查中（2026-10-22：新增 §8A HSS 主動通知（W8b）） |
| 適用範圍 | W8a 與 W8b（RTR、PPR）；N70 只列在附錄 D |
| 設計理由 | [design.md](design.md)、[adr/](adr/) |
| 驗證方式 | [test-plan.md](test-plan.md)（每條需求對應的測試見該文件 §2） |

## 1. 範圍與用語

### 1.1 範圍

本規格定義 free5gc UDM 內 HSS 子系統的行為，範圍包含：Cx（對 Kamailio I-CSCF、S-CSCF）、IMS AKA 認證向量與 SQN、User-Data、IMS 註冊狀態，以及 UDR 的非標準擴充 API。

部署 profile：home network only；一個 SUPI 對一個 IMPI、一個 IMPU（SIP URI）；認證方式只有 IMS AKA；一台 I-CSCF、一台 S-CSCF；Diameter 走 TCP。

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
| HSS 子系統 | UDM 內處理 Cx 的程式（`internal/cx`），以及它用到的共用認證向量函式 |
| IMPI | Private User Identity（`<IMSI>@ims.mnc<MNC>.mcc<MCC>.3gppnetwork.org`，TS 23.003 §13.3） |
| IMPU | Public User Identity，本規格只支援 SIP URI（TS 23.003 §13.4） |
| canonical IMPU | TS 23.003 §13.4 的 canonical form `sip:username@domain` |
| 註冊狀態 | TS 29.228 的 NOT_REGISTERED、REGISTERED、UNREGISTERED（UNREGISTERED 指「因為來電而由 S-CSCF 服務，但用戶沒註冊」） |
| authPending | TS 29.228 的 authentication pending flag，以（IMPU, IMPI）為單位；本 profile 一個 IMPU 只有一個 IMPI，所以存在 IMPU 的紀錄上 |
| 已存 S-CSCF | 註冊紀錄裡保存的 Server-Name |
| 取號 | 為一組認證向量取得一個從未發出過的 SQN |
| Result-Code／Experimental-Result | 前者是 Diameter base（RFC 6733）的結果欄；後者帶 Vendor-Id 10415，值由 TS 29.229 §6.2 定義。**同一個數字在兩個欄位的意思不同**（例如 5012） |
| UAR、UAA、MAR、MAA、SAR、SAA、LIR、LIA | Cx 指令，見附錄 C |

## 2. 參考文件

### 2.1 規範性參考

計畫的研究方向是 Rel-17（`specs/3gpp-r17/`）。核對狀態為「未核對」的項目，在 D02 關閉前不能當成符合性的依據。

| 文件 | 本規格用到的部分 | 版本 | 核對狀態 |
|---|---|---|---|
| 3GPP TS 29.228 | §6.1.1.1 UAR、§6.1.2.1 SAR、§6.1.4.1 LIR、§6.3.1 MAR 的 HSS 行為；§6.6 User profile 下載 | V17.1.0（2022-03） | 已讀上述章節 |
| 3GPP TS 29.229 | §6.1 指令碼、§6.2 Experimental-Result 值、§6.3 AVP code 與列舉值 | V17.3.0（2024-09） | 指令碼、AVP code、§6.2 值、Server-Assignment-Type／User-Authorization-Type／User-Data-Already-Available 列舉已核對；AVP flag 未核對 |
| 3GPP TS 33.203 | §8.2 USIM 與 IMS 共用 key、演算法與 SQN；附錄 G SQN 管理 | Rel-17（檔名 33203-h10） | 已讀 §8.2、附錄 G |
| 3GPP TS 33.102 | 附錄 C SQN 產生、C.2.2 USIM 新鮮度檢查、C.3.4 IND 配置；附錄 H AMF separation bit | Rel-17（檔名 33102-h00） | 已讀 C.1、C.2.2、C.3.4；附錄 H 只讀到「指向 TS 33.401」 |
| 3GPP TS 35.206／35.208 | Milenage 演算法與測試資料 | Rel-17 | 未核對（測試時讀） |
| 3GPP TS 23.003 | §13.3 IMPI、§13.4 IMPU 與 canonical form | V17.11.0（2026-06） | 已讀 |
| 3GPP TS 23.228 | 附錄 Y.0「HSS as part of UDM」 | V17.3.0（2021-12） | 已讀 |
| IETF RFC 6733 | Diameter base：CER／DWR／DPR、M-bit、base Result-Code | — | 未核對 |
| IETF RFC 3261 | §19.1.4 SIP URI 比較 | — | 未核對 |
| IETF RFC 8174 | 需求用語 | — | — |

### 2.2 參考資料

TS 29.505（UDR，Rel-17 沒有 IMS 用戶資料）、TS 29.562（N70，非目標）、TS 23.632／29.563（UDM／HSS 互通，本機沒有）、free5gc UDM v1.4.6 與 UDR v1.4.4 原始碼、`kamailio-free5gc` 的 Kamailio 設定與 `scscf/CxDataType_Rel7.xsd`。

## 3. 總則

- **REQ-GEN-01** UDM **必須**以 Diameter server 角色提供 Cx（Application-Id 16777216、Vendor-Id 10415），處理 UAR、MAR、SAR、LIR。
- **REQ-GEN-02** HSS 子系統**必須**能以設定關閉（`cx.enable`）；關閉時 UDM **不得**開啟 Cx 監聽，Nudm 的行為**必須**與未修改的 UDM 相同。開啟時，Nudm 的對外行為**必須**維持不變（SQN 取號方式的內部改動除外，見 REQ-AUTH-03）。
- **REQ-GEN-03** HSS 子系統**不得**解析 SIP，**不得**替 I-CSCF 挑選 S-CSCF（只回 capabilities，見 [ADR-0006](adr/0006-uaa-capabilities-on-first-registration.md)）。
- **REQ-GEN-04** 對本 profile 不支援的功能（restoration、emergency registration、非 IMS AKA 的認證方式、shared／wildcarded IMPU、PSI、Tel URI；`cx.w8b.enable` 為 false 時的 RTR、PPR）**不得**回成功；**必須**依 §10 回失敗。
- **REQ-GEN-05** 回成功之前，該指令要求的 UDR 寫入（註冊狀態、已存 S-CSCF、authPending、SQN 取號）**必須**都已確認完成。
- **REQ-GEN-06** 回覆**必須**依 §10 區分 Result-Code 與 Experimental-Result；**不得**把 TS 29.229 §6.2 的值放進 Result-Code，也**不得**把 base 的值放進 Experimental-Result。

## 4. Diameter peer

- **REQ-PEER-01** **必須**處理 CER／CEA、DWR／DWA、DPR／DPA。
- **REQ-PEER-02** CEA **必須**以 Vendor-Specific-Application-Id 宣告 Auth-Application-Id 16777216、Vendor-Id 10415。對端另外宣告的 Cx vendor（Kamailio cdp 會宣告 4491、13019、0，見附錄 B）**不得**導致拒絕連線。
- **REQ-PEER-03** **必須**只接受設定中允許的 Origin-Host、Origin-Realm 與來源位址；其他 peer 的 CER **必須**拒絕。
- **REQ-PEER-04** transport 為 TCP，綁在設定的 dnnet 位址；預設 port 3868。是否需要 TLS 依 D09。
- **REQ-PEER-05** 遇到不認識的 AVP：M-bit 為 1 **必須**依 RFC 6733 回錯誤並帶 Failed-AVP；M-bit 為 0 **必須**忽略並繼續處理。D03 錄到的 Kamailio 請求中，M-bit 為 1 的 AVP **必須**加進字典。
- **REQ-PEER-06** Origin-Host、Origin-Realm **必須**取自設定；預設沿用 PyHSS 的 `hss.ims.mnc093.mcc208.3gppnetwork.org` 與 `ims.mnc093.mcc208.3gppnetwork.org`。
- **REQ-PEER-07** peer 斷線**必須**記錄事件；**不得**因此改變任何註冊狀態。

## 5. 身分對應

- **REQ-ID-01** IMPI、IMPU 對應到 SUPI 時，**必須**查 UDR 擴充的身分索引（§12）；**不得**從字串推導（例如把 IMPU 的 user part 當 IMSI）。見 [ADR-0005](adr/0005-explicit-identity-mapping.md)。
- **REQ-ID-02** IMPU 在寫入與查詢前，**必須**轉成 canonical form；比較規則依 RFC 3261 §19.1.4（scheme 與 host 不分大小寫，user part 區分大小寫；待 D02 核對）。
- **REQ-ID-03** 一個 IMPU **必須**只屬於一個 IMPI 與一個 SUPI；開戶時違反**必須**拒絕（§12，HTTP 409）。
- **REQ-ID-04** Tel URI、wildcarded IMPU、PSI **必須**當成未知身分處理（Experimental-Result 5001）。

## 6. Cx 指令處理

每個指令**必須**依下列順序檢查，任一步失敗就停止並回對應的答案（TS 29.228 各節開頭的處理原則）。狀態的變化以 §9.2 的轉移表為準；本節與轉移表衝突時視為文件錯誤。

### 6.1 UAR（TS 29.228 §6.1.1.1）

- **REQ-UAR-01** IMPI 或 IMPU 不存在，或 IMPU 不是 distinct Public User Identity：Experimental-Result 5001 DIAMETER_ERROR_USER_UNKNOWN。
- **REQ-UAR-02** IMPU 不屬於該 IMPI：Experimental-Result 5002 DIAMETER_ERROR_IDENTITIES_DONT_MATCH。
- **REQ-UAR-03** IMPU 的 BarringIndication 為 1：Result-Code DIAMETER_AUTHORIZATION_REJECTED（本 profile 一個 IMPU 沒有其他可以 implicit register 的身分）。
- **REQ-UAR-04** User-Authorization-Type 為 REGISTRATION 或缺少、且 Visited-Network-Identifier 不在設定的允許清單：Experimental-Result 5004 DIAMETER_ERROR_ROAMING_NOT_ALLOWED。
- **REQ-UAR-05** User-Authorization-Type 為 REGISTRATION 或缺少：
  - REGISTERED 或 UNREGISTERED：回已存 S-CSCF＋Experimental-Result 2002 DIAMETER_SUBSEQUENT_REGISTRATION；**不得**帶 Server-Capabilities；
  - NOT_REGISTERED 但有已存 S-CSCF（authPending）：同上；
  - NOT_REGISTERED 且沒有已存 S-CSCF：回 Server-Capabilities（設定的 mandatory／optional capabilities）＋Experimental-Result 2001 DIAMETER_FIRST_REGISTRATION；**不得**帶 Server-Name。
- **REQ-UAR-06** User-Authorization-Type 為 DE_REGISTRATION：
  - REGISTERED 或 UNREGISTERED：回已存 S-CSCF＋Result-Code 2001 DIAMETER_SUCCESS；
  - NOT_REGISTERED 且 authPending：回已存 S-CSCF＋成功（TS 29.228 原文寫「Experimental-Result-Code set to DIAMETER_SUCCESS」，DIAMETER_SUCCESS 是 base 的值，本規格依 REQ-GEN-06 用 Result-Code 2001，待 D02 核對）；
  - 其他：Experimental-Result 5003 DIAMETER_ERROR_IDENTITY_NOT_REGISTERED，**不得**帶 Server-Name 或 capabilities。
- **REQ-UAR-07** User-Authorization-Type 為 REGISTRATION_AND_CAPABILITIES：回 Server-Capabilities＋Result-Code 2001；**不得**帶 Server-Name（本 profile 不支援 restoration）。
- **REQ-UAR-08** UAR-Flags 標示 IMS Emergency Registration 時，**不得**當成一般註冊處理；**必須**回失敗（Result-Code DIAMETER_UNABLE_TO_COMPLY，候選）。
- **REQ-UAR-09** UAR **不得**改變任何註冊狀態、已存 S-CSCF 或 authPending。
- **REQ-UAR-10** UDR 讀取失敗或逾時：Result-Code DIAMETER_UNABLE_TO_COMPLY；**不得**帶 Server-Name 或 capabilities。

### 6.2 MAR（TS 29.228 §6.3.1）

- **REQ-MAR-01** 身分檢查同 REQ-UAR-01、REQ-UAR-02。
- **REQ-MAR-02** SIP-Authentication-Scheme 為 `Digest-AKAv1-MD5` 才支援（TS 29.229 §6.3.9：AKAv1-MD5 與 AKAv2-SHA-256 都用這個值）。其他值，包含 `Unknown`：Experimental-Result 5006 DIAMETER_ERROR_AUTH_SCHEME_NOT_SUPPORTED。
- **REQ-MAR-03** 一般請求（SIP-Auth-Data-Item 裡沒有 SIP-Authorization）：
  - 已存 S-CSCF 與請求的 Server-Name 不同或沒有：存成請求的值；
  - 依 §9.2 設定 authPending；
  - 回 N 組向量，N = min(SIP-Number-Auth-Items, `cx.maxAuthItems`)，且 N ≥ 1；
  - Result-Code 2001。
- **REQ-MAR-04** 每組向量**必須**包含：SIP-Item-Number（1…N）、SIP-Authentication-Scheme、SIP-Authenticate＝RAND‖AUTN（32 bytes）、SIP-Authorization＝XRES、Confidentiality-Key＝CK、Integrity-Key＝IK（TS 29.229 §6.3）。
- **REQ-MAR-05** 重新同步（SIP-Authorization 為 30 bytes，即 RAND‖AUTS）：請求的 Server-Name 與已存 S-CSCF 相同時，依 REQ-AUTH-05 重新同步後產生新向量；不同或沒有已存 S-CSCF：Result-Code DIAMETER_UNABLE_TO_COMPLY（依 §6.3.1 結尾「其他情況視為錯誤」，候選）。
- **REQ-MAR-06** AUTS 的 MAC-S 驗證失敗：**不得**改變 SQN；回 Result-Code DIAMETER_UNABLE_TO_COMPLY（候選）。
- **REQ-MAR-07** 缺少 Server-Name：Result-Code DIAMETER_MISSING_AVP（候選；TS 29.228 Table 6.3.1 把 S-CSCF name 列為 M）。

### 6.3 SAR（TS 29.228 §6.1.2.1）

- **REQ-SAR-01** IMPI 或 IMPU 不存在：Experimental-Result 5001；IMPI 與 IMPU 不相屬：Experimental-Result 5002。
- **REQ-SAR-02** Server-Assignment-Type 是只適用單一身分的類型（TS 29.228 Table 6.1.2.1：除 TIMEOUT_DEREGISTRATION、USER_DEREGISTRATION、DEREGISTRATION_TOO_MUCH_DATA、兩種 *_STORE_SERVER_NAME、ADMINISTRATIVE_DEREGISTRATION 以外），但帶了多個 Public-Identity：Result-Code DIAMETER_AVP_OCCURS_TOO_MANY_TIMES，**不得**回 User-Data。
- **REQ-SAR-03** REGISTRATION（1）、RE_REGISTRATION（2）：已存 S-CSCF 存在且與請求不同時，回 Experimental-Result 5005 DIAMETER_ERROR_IDENTITY_ALREADY_REGISTERED，並**必須**帶已存 S-CSCF 的 Server-Name。其他情況：存 S-CSCF、狀態設為 REGISTERED、清 authPending、依 REQ-UD-03 帶 User-Data，Result-Code 2001。
- **REQ-SAR-04** UNREGISTERED_USER（3）：已存 S-CSCF 不同時同 REQ-SAR-03 回 5005＋已存 S-CSCF；其他情況：存 S-CSCF、狀態設為 UNREGISTERED（從 REGISTERED 進來時也一樣，本 profile 不支援 restoration）、帶 User-Data，Result-Code 2001。
- **REQ-SAR-05** TIMEOUT_DEREGISTRATION（4）、USER_DEREGISTRATION（5）、ADMINISTRATIVE_DEREGISTRATION（8）、DEREGISTRATION_TOO_MUCH_DATA（11）：
  - REGISTERED 或 UNREGISTERED → NOT_REGISTERED，清已存 S-CSCF 與 authPending；
  - 沒有 Public-Identity 時，用 User-Name（IMPI）找出所屬的 IMPU；兩者都沒有：Result-Code DIAMETER_MISSING_AVP；
  - Result-Code 2001；**不得**帶 User-Data。
- **REQ-SAR-06** TIMEOUT_DEREGISTRATION_STORE_SERVER_NAME（6）、USER_DEREGISTRATION_STORE_SERVER_NAME（7）：本 profile 選擇**不保存** S-CSCF 名稱，依 REQ-SAR-05 處理，但回 Experimental-Result 2004 DIAMETER_SUCCESS_SERVER_NAME_NOT_STORED（TS 29.228 §6.1.2.1 允許 HSS 決定不保存）。
- **REQ-SAR-07** AUTHENTICATION_FAILURE（9）、AUTHENTICATION_TIMEOUT（10）：註冊狀態不變；清 authPending；狀態為 NOT_REGISTERED 時清已存 S-CSCF；Result-Code 2001。
- **REQ-SAR-08** NO_ASSIGNMENT（0）：請求的 S-CSCF 與已存 S-CSCF 不同：Result-Code DIAMETER_UNABLE_TO_COMPLY；相同：帶 User-Data，Result-Code 2001；狀態不變。
- **REQ-SAR-09** 值 12、13、14（只用於 SWx）或未定義的值：Experimental-Result 5007 DIAMETER_ERROR_IN_ASSIGNMENT_TYPE（候選）；狀態不變。
- **REQ-SAR-10** UDR 失敗或逾時：Result-Code DIAMETER_UNABLE_TO_COMPLY；**不得**改變狀態，**不得**帶 User-Data。

### 6.4 LIR（TS 29.228 §6.1.4.1）

- **REQ-LIR-01** IMPU 不存在：Experimental-Result 5001。
- **REQ-LIR-02** REGISTERED 或 UNREGISTERED：回已存 S-CSCF，Result-Code 2001；**不得**帶 Server-Capabilities。
- **REQ-LIR-03** NOT_REGISTERED：
  - IMS subscription 的 `unregisteredServices` 為 true，或請求帶 Originating-Request：有已存 S-CSCF 時回它＋Result-Code 2001；沒有時回 Server-Capabilities＋Experimental-Result 2003 DIAMETER_UNREGISTERED_SERVICE；
  - 其他：Experimental-Result 5003 DIAMETER_ERROR_IDENTITY_NOT_REGISTERED。
- **REQ-LIR-04** LIR 帶的 User-Authorization-Type **必須**忽略（REGISTRATION_AND_CAPABILITIES 只在支援 restoration 時才有作用）。
- **REQ-LIR-05** LIR **不得**改變任何狀態；UDR 失敗或逾時：Result-Code DIAMETER_UNABLE_TO_COMPLY，不帶 Server-Name 或 capabilities。

## 7. 認證向量與 SQN

### 7.1 資料來源

- **REQ-AUTH-01** IMS AKA **必須**使用 UDR `authenticationSubscription` 的 K、OPc、AMF、SQN；**不得**另存一份（TS 33.203 §8.2，見 [ADR-0002](adr/0002-shared-auth-data-and-sqn.md)）。
- **REQ-AUTH-07** AMF：依 D14 的結論。D14 關閉前沿用 UDR 裡的值（實驗為 `8000`），與 PyHSS 現況相同。

### 7.2 向量產生

- **REQ-AUTH-06** Milenage **必須**依 TS 35.206，並通過 TS 35.208 的測試資料。
- **REQ-AUTH-08** 每次 MAR **必須**產生新的向量；向量**不得**保存或重用（TS 33.203：USIM 會拒絕重用的向量）。

### 7.3 SQN 取號

- **REQ-AUTH-02** 取號**必須**是原子操作：同一個 SUPI 的並行請求（5G-AKA 與 IMS AKA 任意組合）**不得**拿到相同的 SQN。見 [ADR-0003](adr/0003-atomic-sqn-allocation.md)。
- **REQ-AUTH-03** UDM 原有的 5G-AKA 路徑（`GenerateAuthDataProcedure`）**必須**改用同一個取號機制；否則 REQ-AUTH-02 不成立。
- **REQ-AUTH-04** 遞增規則**必須**與現行 UDM 相同：每組向量 SQN + 1（IND 循環配置，TS 33.102 C.3.4 一般規則）。IMS 是否使用專屬 IND 範圍依 D07。
- **REQ-AUTH-05** 重新同步**必須**與現行 UDM 的 5G-AKA 用同一個函式：先用 AUTS 驗 MAC-S、取出 SQN_MS，再以 SQN_MS + 33 為新的 SQN（現行 `aucSQN` 與 `ind + 1`），並以原子操作寫回。
- **REQ-AUTH-09** 取號以後，如果後續步驟失敗（例如註冊狀態寫入失敗），該 SQN **必須**視為已用掉；**不得**退回或重用。SQN 出現跳號是允許的。

## 8. User-Data

- **REQ-UD-01** User-Data **必須**能通過部署中 S-CSCF 使用的 XSD（`scscf/CxDataType_Rel7.xsd`）驗證。
- **REQ-UD-02** 內容：`IMSSubscription` → `PrivateID`＝IMPI；一個 `ServiceProfile` → 一個 `PublicIdentity`（`Identity`＝canonical IMPU；BarringIndication 為 1 時才輸出）。W8a **不得**輸出 `InitialFilterCriteria`。
- **REQ-UD-03** 什麼時候帶 User-Data：REGISTRATION、RE_REGISTRATION 且 User-Data-Already-Available 為 USER_DATA_NOT_AVAILABLE（0）或缺少；UNREGISTERED_USER；NO_ASSIGNMENT（同一台 S-CSCF）。其他類型**不得**帶。User-Data-Already-Available 為 1 時**可**省略（D08）。
- **REQ-UD-04** W8a **不得**帶 Charging-Information（沒有 CCF）。

## 8A. HSS 主動通知（W8b）

本節在 `cx.w8b.enable` 為 true 時適用。依據：TS 29.228 V17.1.0 §6.1.3、§6.1.3.1（RTR）、§6.2.2、§6.2.2.1（PPR）、§6.5.2.1、§8.1.1；TS 29.229 V17.3.0 §5.5（HSS 發起的請求必須帶 Destination-Host 與 Destination-Realm）、§6.1.9～§6.1.12（RTR／RTA 304、PPR／PPA 305）、§6.3.17（Reason-Code）。設計理由見 [ADR-0008](adr/0008-udm-as-diameter-client.md)～[ADR-0010](adr/0010-rta-ppa-failure-policy.md)。

### 8A.1 共通

- **REQ-CLI-01** UDM **必須**能以 Diameter client 角色對 S-CSCF 送 RTR、PPR。連線方式（沿用 S-CSCF 連進來的連線，或主動連 S-CSCF 的 3870）依 D15；**不得**同時用兩條連線送同一個 S-CSCF。
- **REQ-CLI-02** Destination-Host **必須**是該 S-CSCF 送 MAR／SAR 時的 Origin-Host（記在註冊紀錄的 `scscfDiameterHost`），**不得**用 Server-Name（SIP URI）推導；Destination-Realm 用 `scscfDiameterRealm`。
- **REQ-CLI-03** User-Name **必須**是該 S-CSCF 經 SAR 已知的 IMPI（記在 `sarImpi`）。
- **REQ-CLI-04** RTR、PPR **必須**帶 Auth-Session-State NO_STATE_MAINTAINED(1)，並使用新的 Session-Id；本 profile 一個 IMPU 只有一個 IMPI，**不得**帶 Associated-Identities。
- **REQ-CLI-05** 狀態為 NOT_REGISTERED、或沒有 `scscfDiameterHost` 時，**不得**送 RTR、PPR。

### 8A.2 RTR

- **REQ-RTR-01** 經擴充 API 刪除 ims-subscription 時，若有 REGISTERED 或 UNREGISTERED 的 IMPU，**必須**先送 RTR，Reason-Code PERMANENT_TERMINATION(0)，再依 REQ-DATA-06 刪除資料（取代 W8a「不通知 S-CSCF」的行為）。
- **REQ-RTR-02** **必須**提供管理操作 `POST {apiPrefix}/subscription-data/{supi}/ims-registrations/{impu}/deregister`（body 帶 Reason-Code 與選用的 Reason-Info），觸發 RTR；結果回給呼叫者。
- **REQ-RTR-03** REGISTERED 時收到另一台 S-CSCF 的 MAR（§9.2「REG｜MAR 一般，Y≠X」），**應**對原 S-CSCF 送 RTR，Reason-Code NEW_SERVER_ASSIGNED(1)，並帶 Public-Identity（TS 29.228 §8.1.1；原 S-CSCF 與新 S-CSCF 的 Diameter 位址相同時不送）。
- **REQ-RTR-04** RTR 的 Deregistration-Reason **必須**帶 Reason-Code；有給 Reason-Info 時才帶。原因為 NEW_SERVER_ASSIGNED 時**必須**帶 Public-Identity。
- **REQ-RTR-05** 狀態更新：PERMANENT_TERMINATION 與 SERVER_CHANGE **必須**在收到成功的 RTA 之後，才把 IMPU 設為 NOT_REGISTERED 並清除已存 S-CSCF（TS 29.228 §6.1.3.1 依 RTA 決定）；NEW_SERVER_ASSIGNED 不改狀態（新的 S-CSCF 已由 MAR 存入）。
- **REQ-RTR-06** RTA 失敗或逾時的處理依 [ADR-0010](adr/0010-rta-ppa-failure-policy.md)：依 `cx.w8b.retry` 重送；用完後，若觸發來源是刪除開戶資料，照樣刪除並告警；若是管理操作，狀態不變、回錯誤給呼叫者並告警。
- **REQ-RTR-07** RTA 回 DIAMETER_UNABLE_TO_COMPLY 或 DIAMETER_LIMITED_SUCCESS 並帶 Identity-with-Emergency-Registration 時（緊急註冊，非目標），**必須**記錄並依 REQ-RTR-06 的「失敗」處理。

### 8A.3 PPR

- **REQ-PPR-01** 經擴充 API 修改 ims-subscription，且影響 User-Data 的內容（IMPU、BarringIndication）時，對 REGISTERED 或 UNREGISTERED 的 IMPU **必須**送 PPR，帶完整的 User-Data（與 SAA 相同的 XML，REQ-UD-01、02）。
- **REQ-PPR-02** PPR **不得**帶 Charging-Information、SIP-Auth-Data-Item、Allowed-WAF-WWSF-Identities（本 profile 不使用）。
- **REQ-PPR-03** 修改會改變 IMPU 本身（本 profile 只有一個 IMPU，等於改 default IMPU）時，**必須**改送 RTR，Reason-Code SERVER_CHANGE(2)（候選，TS 29.228 §6.5.2.1 要求改用 RTR，但沒有指定原因）。
- **REQ-PPR-04** PPA 的處理（TS 29.228 §6.2.2.1）：成功 → 完成；Experimental-Result 5008 或 5009 → 送 RTR SERVER_CHANGE；5001 → 本 profile 沒有其他 IMPI，把 IMPU 設為 NOT_REGISTERED 並清除已存 S-CSCF；其他錯誤或逾時 → 依 `cx.w8b.retry` 重送，用完告警。

## 9. 註冊狀態與並行

### 9.1 紀錄欄位

每個 IMPU 一筆註冊紀錄（§12）：

| 欄位 | 用途 |
|---|---|
| `impu`、`impi`、`supi` | 身分 |
| `state` | NOT_REGISTERED／REGISTERED／UNREGISTERED |
| `scscfName` | 已存 S-CSCF；沒有時為空 |
| `scscfDiameterHost`／`scscfDiameterRealm` | 該 S-CSCF 送 MAR／SAR 時的 Origin-Host／Origin-Realm（REQ-CLI-02） |
| `sarImpi` | 該 S-CSCF 經 SAR 已知的 IMPI（REQ-CLI-03） |
| `authPending` | 認證進行中 |
| `version` | 條件式更新用（REQ-ST-01） |
| `updatedAt`、`lastCommand` | 稽核與除錯 |

沒有紀錄的 IMPU 視為 NOT_REGISTERED、沒有已存 S-CSCF。

### 9.2 狀態轉移表

狀態縮寫：**NR0**＝NOT_REGISTERED、沒有已存 S-CSCF；**NR1**＝NOT_REGISTERED、有已存 S-CSCF 且 authPending；**REG**；**UNREG**。「X」表示已存 S-CSCF，「Y」表示請求裡的 Server-Name。§6 的身分、AVP、UDR 失敗檢查先於本表。

| 目前狀態 | 事件 | 動作與答案 | 下一狀態 |
|---|---|---|---|
| NR0 | UAR REGISTRATION | capabilities＋Exp 2001 | NR0 |
| NR1 | UAR REGISTRATION | X＋Exp 2002 | NR1 |
| REG、UNREG | UAR REGISTRATION | X＋Exp 2002 | 不變 |
| NR0 | UAR DE_REGISTRATION | Exp 5003 | NR0 |
| NR1 | UAR DE_REGISTRATION | X＋RC 2001 | NR1 |
| REG、UNREG | UAR DE_REGISTRATION | X＋RC 2001 | 不變 |
| 任何 | UAR REGISTRATION_AND_CAPABILITIES | capabilities＋RC 2001 | 不變 |
| NR0 | MAR 一般 | 存 Y、設 authPending、向量 | NR1 |
| NR1 | MAR 一般，Y＝X | 向量 | NR1 |
| NR1 | MAR 一般，Y≠X | 改存 Y、向量 | NR1（S-CSCF＝Y） |
| REG | MAR 一般，Y＝X | 向量（不設 authPending） | REG |
| REG | MAR 一般，Y≠X | 改存 Y、設 authPending、向量；W8b 時對原 S-CSCF 送 RTR NEW_SERVER_ASSIGNED（REQ-RTR-03） | REG（S-CSCF＝Y） |
| UNREG | MAR 一般 | 存 Y、設 authPending、向量 | UNREG（S-CSCF＝Y） |
| 任何 | MAR 重新同步，Y＝X | 重新同步 SQN、向量 | 不變 |
| 任何 | MAR 重新同步，Y≠X 或沒有 X | RC 5012 | 不變 |
| NR0、NR1（Y＝X） | SAR REGISTRATION | 存 Y、清 authPending、User-Data、RC 2001 | REG |
| UNREG（Y＝X） | SAR REGISTRATION | 清 authPending、User-Data、RC 2001 | REG |
| REG（Y＝X） | SAR RE_REGISTRATION 或 REGISTRATION | 依 REQ-UD-03、RC 2001 | REG |
| NR1、REG、UNREG（Y≠X） | SAR REGISTRATION／RE_REGISTRATION／UNREGISTERED_USER | Exp 5005＋Server-Name＝X | 不變 |
| NR0、NR1（Y＝X）、UNREG（Y＝X） | SAR UNREGISTERED_USER | 存 Y、User-Data、RC 2001 | UNREG |
| REG（Y＝X） | SAR UNREGISTERED_USER | User-Data、RC 2001 | UNREG |
| REG、UNREG | SAR 4／5／8／11 | 清 X 與 authPending、RC 2001 | NR0 |
| NR0、NR1 | SAR 4／5／8／11 | RC 2001（不改變；NR1 的 authPending 由 SAR 9／10 清） | 不變 |
| REG、UNREG | SAR 6／7 | 清 X 與 authPending、Exp 2004 | NR0 |
| NR0、NR1 | SAR 6／7 | Exp 2004 | 不變 |
| NR1 | SAR 9／10 | 清 authPending 與 X、RC 2001 | NR0 |
| REG、UNREG | SAR 9／10 | 清 authPending、RC 2001 | 不變 |
| NR0 | SAR 9／10 | RC 2001 | NR0 |
| 任何（Y＝X） | SAR NO_ASSIGNMENT | User-Data、RC 2001 | 不變 |
| 任何（Y≠X 或沒有 X） | SAR NO_ASSIGNMENT | RC 5012 | 不變 |
| 任何 | SAR 12／13／14 或未定義值 | Exp 5007 | 不變 |
| REG、UNREG | LIR | X＋RC 2001 | 不變 |
| NR1 | LIR，有 unregistered service 或 Originating-Request | X＋RC 2001 | NR1 |
| NR0 | LIR，有 unregistered service 或 Originating-Request | capabilities＋Exp 2003 | NR0 |
| NR0、NR1 | LIR，其他 | Exp 5003 | 不變 |
| 任何 | 條件式寫入衝突（版本不符） | 重讀紀錄、重新套用本表；超過 `cx.stateRetry` 次回 RC 5012 | 依重新套用的結果 |
| 任何 | UDR 失敗或逾時 | RC 5012；不帶向量、User-Data、Server-Name | 不變（寫入結果不明時，以下一次讀到的 UDR 內容為準） |
| 任何 | UDM 重啟 | 無（狀態都在 UDR） | 不變 |
| NR0、NR1 | 開戶資料被刪除（§12） | UDR 一併刪除註冊紀錄與索引 | （無紀錄）；之後的請求回 Exp 5001 |
| REG、UNREG | 開戶資料被刪除，`cx.w8b.enable` 為 false | 同上；不通知 S-CSCF | （無紀錄） |
| REG、UNREG | 開戶資料被刪除，`cx.w8b.enable` 為 true | 送 RTR PERMANENT_TERMINATION；RTA 成功或重試用完後刪除資料（REQ-RTR-01、06） | （無紀錄） |
| REG、UNREG | 管理操作 deregister（REQ-RTR-02） | 送 RTR | 等 RTA |
| 等 RTA | RTA 成功（PERMANENT_TERMINATION、SERVER_CHANGE） | 清已存 S-CSCF | NR0 |
| 等 RTA | RTA 失敗或逾時，重試用完 | 依 REQ-RTR-06 | 不變（管理操作）或（無紀錄）（刪除開戶） |
| REG、UNREG | 開戶資料修改影響 User-Data | 送 PPR（REQ-PPR-01）；改了 IMPU 時改送 RTR SERVER_CHANGE（REQ-PPR-03） | 不變（PPR）或等 RTA |
| REG、UNREG | PPA 5008／5009 | 送 RTR SERVER_CHANGE | 等 RTA |
| REG、UNREG | PPA 5001 | 清已存 S-CSCF | NR0 |
| 任何 | Diameter peer 斷線 | 記錄 | 不變 |

### 9.3 並行

- **REQ-ST-01** 註冊紀錄的每次更新**必須**是以 `version` 為條件的寫入；衝突時**必須**重讀並重新套用 §9.2，次數上限 `cx.stateRetry`。
- **REQ-ST-02** 同一個 IMPU 的兩個並行 SAR（不同 S-CSCF）**必須**恰好一個成功，另一個依 §9.2 回 5005。
- **REQ-ST-03** HSS 子系統**不得**保存只在記憶體、重啟就會遺失的業務狀態；重啟前後對同一請求序列的答案**必須**相同。
- **REQ-ST-04** 不同請求**必須**能並行處理；等待 UDR 時**不得**持有跨請求的全域鎖。

## 10. 結果代碼對應

### 10.1 Experimental-Result（Vendor-Id 10415）

值依 TS 29.229 V17.3.0 §6.2（已核對）。

| 名稱 | 值 | 本規格使用處 |
|---|---|---|
| DIAMETER_FIRST_REGISTRATION | 2001 | REQ-UAR-05 |
| DIAMETER_SUBSEQUENT_REGISTRATION | 2002 | REQ-UAR-05 |
| DIAMETER_UNREGISTERED_SERVICE | 2003 | REQ-LIR-03 |
| DIAMETER_SUCCESS_SERVER_NAME_NOT_STORED | 2004 | REQ-SAR-06 |
| DIAMETER_ERROR_USER_UNKNOWN | 5001 | REQ-UAR-01、REQ-MAR-01、REQ-SAR-01、REQ-LIR-01、REQ-ID-04 |
| DIAMETER_ERROR_IDENTITIES_DONT_MATCH | 5002 | REQ-UAR-02、REQ-MAR-01、REQ-SAR-01 |
| DIAMETER_ERROR_IDENTITY_NOT_REGISTERED | 5003 | REQ-UAR-06、REQ-LIR-03 |
| DIAMETER_ERROR_ROAMING_NOT_ALLOWED | 5004 | REQ-UAR-04 |
| DIAMETER_ERROR_IDENTITY_ALREADY_REGISTERED | 5005 | REQ-SAR-03、REQ-SAR-04 |
| DIAMETER_ERROR_AUTH_SCHEME_NOT_SUPPORTED | 5006 | REQ-MAR-02 |
| DIAMETER_ERROR_IN_ASSIGNMENT_TYPE | 5007 | REQ-SAR-09（候選用法） |
| DIAMETER_ERROR_TOO_MUCH_DATA／NOT_SUPPORTED_USER_DATA／FEATURE_UNSUPPORTED／SERVING_NODE_FEATURE_UNSUPPORTED | 5008、5009、5011、5012 | 不使用 |

### 10.2 Result-Code（RFC 6733 base）

D02 關閉前都是**候選值**。

| 名稱 | 候選值 | 本規格使用處 | 核對 |
|---|---|---|---|
| DIAMETER_SUCCESS | 2001 | 一般成功 | |
| DIAMETER_UNABLE_TO_COMPLY | 5012 | UDR 失敗、REQ-MAR-05／06、REQ-SAR-08、REQ-UAR-08 | |
| DIAMETER_AUTHORIZATION_REJECTED | 5003 | REQ-UAR-03 | |
| DIAMETER_MISSING_AVP | 5005 | REQ-MAR-07、REQ-SAR-05 | |
| DIAMETER_AVP_OCCURS_TOO_MANY_TIMES | 5009 | REQ-SAR-02 | |
| DIAMETER_AVP_UNSUPPORTED | 5001 | REQ-PEER-05 | |
| DIAMETER_UNKNOWN_PEER | 3010 | REQ-PEER-03 | |

注意：Result-Code 5012（UNABLE_TO_COMPLY）、5003（AUTHORIZATION_REJECTED）、5005（MISSING_AVP）、5001（AVP_UNSUPPORTED）與 Experimental-Result 的同號值意思完全不同（REQ-GEN-06）。

### 10.3 遠端回應 → 本端答案

HSS 子系統唯一的遠端是 UDR：

| UDR 回應 | Cx 答案 | 來源 |
|---|---|---|
| 2xx | 依 §6、§9.2 | — |
| 404（身分索引查無） | Exp 5001 | REQ-ID-01 |
| 412（版本不符） | 依 REQ-ST-01 重試；用完回 RC 5012 | REQ-ST-01 |
| 409（SQN 取號衝突用完重試，§12） | RC 5012 | REQ-AUTH-02 |
| 5xx、逾時、連線失敗 | RC 5012 | TS 29.228 各節「database error → DIAMETER_UNABLE_TO_COMPLY」 |

## 11. 設定

```yaml
configuration:
  cx:
    enable: true                       # REQ-GEN-02
    bindAddr: 10.100.100.20            # REQ-PEER-04、REQ-SEC-03：dnnet 上 UDM 的位址（沿用 PyHSS 的位址與別名）
    port: 3868                         # REQ-PEER-04
    transport: tcp                     # REQ-PEER-04；TLS 依 D09
    originHost: hss.ims.mnc093.mcc208.3gppnetwork.org   # REQ-PEER-06
    originRealm: ims.mnc093.mcc208.3gppnetwork.org      # REQ-PEER-06
    allowedPeers:                      # REQ-PEER-03
      - host: icscf.ims.mnc093.mcc208.3gppnetwork.org
        realm: ims.mnc093.mcc208.3gppnetwork.org
        addr: <I-CSCF 的 dnnet 位址>
      - host: scscf.ims.mnc093.mcc208.3gppnetwork.org
        realm: ims.mnc093.mcc208.3gppnetwork.org
        addr: 10.100.100.21
    mandatoryCapabilities: [0]         # REQ-UAR-05；與 icscf/seed.sql 的 capability 0 相同
    optionalCapabilities: []           # REQ-UAR-05
    allowedVisitedNetworks: []         # REQ-UAR-04；Kamailio 實際送的值待 D03，空清單表示不檢查
    maxAuthItems: 1                    # REQ-MAR-03；與 ims_auth av_request_at_once 1 相同
    udrTimeout: 2s                     # REQ-UAR-10、REQ-SAR-10；必須小於 cdp TransactionTimeout 5 秒
    stateRetry: 5                      # REQ-ST-01
    w8b:
      enable: false                    # REQ-GEN-04、§8A
      connect: reuse                   # reuse｜outbound（REQ-CLI-01，D15）
      scscfPort: 3870                  # outbound 時使用
      retry: {maxAttempts: 3, backoff: [1s, 2s, 4s]}   # REQ-RTR-06、REQ-PPR-04
      answerTimeout: 5s
  udrImsExt:
    apiPrefix: /nudr-ims-ext/v1        # REQ-DATA-01
```

- **REQ-CFG-01** 設定檢查**必須**在啟動時執行：`cx.enable` 為 true 時，`allowedPeers` 不得為空、`originHost` 必須是 FQDN、`maxAuthItems` ≥ 1、`udrTimeout` < 5 秒；不符合就拒絕啟動。
- **REQ-CFG-02** `bindAddr` 為 `0.0.0.0` 時**必須**輸出警告。
- **REQ-CFG-03** 設定**必須**在啟動 log 中輸出（不含秘密值）。

上面的數值是實驗初始值，不是標準規定。

## 12. UDR 擴充 API

非標準資源，見 [ADR-0004](adr/0004-ims-data-in-udr-extension.md)。路徑與 collection 名稱在 D10 關閉前是候選。

| 資源 | 方法 | 內容 | 候選 collection |
|---|---|---|---|
| `{apiPrefix}/subscription-data/{supi}/ims-subscription` | GET、PUT、DELETE | IMPI、IMPU、MSISDN、BarringIndication、`unregisteredServices` | `subscriptionData.imsData.imsSubscription` |
| `{apiPrefix}/ims-identities/{impi 或 canonical impu}` | GET | `{supi, impi, impu}` | `subscriptionData.imsData.imsIdentities` |
| `{apiPrefix}/subscription-data/{supi}/ims-registrations/{impu}` | GET、PUT（If-Match）、DELETE | §9.1 的紀錄 | `subscriptionData.contextData.imsRegistration` |
| `{apiPrefix}/subscription-data/{supi}/sqn-allocations` | POST | 回傳本次取得的 SQN（12 個 hex 字元）；body 可帶 AUTS 重新同步的結果 | 直接更新 `subscriptionData.authenticationData.authenticationSubscription` |

- **REQ-DATA-01** 擴充 API **必須**只放在 `apiPrefix` 底下；**不得**改變標準 Nudr 路徑的行為。
- **REQ-DATA-02** PUT ims-subscription **必須**檢查 IMPI 格式與 canonical IMPU，並在 IMPI 或 IMPU 已屬於其他 SUPI 時回 409（REQ-ID-03）。
- **REQ-DATA-03** 寫入或刪除 ims-subscription 時，身分索引**必須**同步更新；任何時候都**不得**出現指向不存在 subscription 的索引。
- **REQ-DATA-04** PUT ims-registrations **必須**支援以 `version` 為條件的寫入（If-Match），不符時回 412。
- **REQ-DATA-05** sqn-allocations **必須**以單一資料庫條件式更新完成取號（以目前 SQN 為條件）；衝突時在 UDR 內重試，用完回 409。
- **REQ-DATA-06** 刪除 ims-subscription **必須**一併刪除該 SUPI 的註冊紀錄與索引。

## 13. 安全

威脅模型見 [design.md](design.md) §7.1。

- **REQ-SEC-01** log、指標、錯誤訊息**不得**含 K、OP、OPc、CK、IK、XRES、AUTS；IMPI、IMPU、SUPI **必須**遮蔽（保留前 5 碼與後 2 碼）。
- **REQ-SEC-02** UDR 擴充 API **必須**只在 corenet 提供；OAuth 關閉時，UDM 與 UDR 啟動 log **必須**標示「實驗 profile：SBI 未授權」。
- **REQ-SEC-03** Cx **必須**只綁在設定的 `bindAddr`。

## 14. 可觀測性與維運

- **REQ-OBS-01** 每個 Cx 請求**必須**記錄：指令、Session-Id、遮蔽後的 IMPI／IMPU、答案代碼（標明 Result-Code 或 Experimental-Result）、狀態轉移（前→後）、UDR 延遲。
- **REQ-OBS-02** **必須**提供指標：各指令的請求數與答案代碼分布、SQN 取號重試與失敗次數、條件式寫入重試次數、UDR 錯誤數與延遲、peer 連線狀態。
- **REQ-OPS-01** UDR 不可用時，Cx peer 連線**可**建立，但所有指令**必須**回 RC 5012；readiness **必須**回報未就緒。
- **REQ-OPS-02** 切換時，PyHSS 與 UDM **不得**同時使用 `hss.ims.mnc093.mcc208.3gppnetwork.org` 別名或同一個 dnnet 位址。
- **REQ-OPS-03** **必須**能經擴充 API 刪除單一 IMPU 的註冊紀錄，作為卡在 authPending 時的清理手段。
- **REQ-OPS-04** **必須**提供切回 PyHSS 的回退程序（compose 與開戶步驟），並在 G4 前實測一次。
- **REQ-OPS-05** 開戶腳本**必須**只透過 §12 的擴充 API 寫入 IMS 資料（**不得**直接寫 MongoDB），而且可以重複執行，結果相同。

---

## 附錄 A（參考）對端要改的設定

| 對象 | 改動 |
|---|---|
| `docker-compose.yaml` | 移除 `pyhss-hss`、`pyhss-api`、`pyhss-diameter`、`pyhss-redis`；UDM 改用自己 build 的映像，加上 dnnet 位址 10.100.100.20 與別名 `hss.ims…`；UDR 改用自己 build 的映像 |
| `icscf/icscf.xml`、`scscf/scscf.xml` | 不改（Peer FQDN 仍是 `hss.ims…`、port 3868） |
| `icscf/seed.sql` | 不改（capability 0） |
| `scripts/04-add-ims-subscribers.sh` | 改為呼叫 §12 的 PUT ims-subscription；不再寫 AUC（認證資料由 `02-` 寫入 UDR） |
| `hss/pyhss.env` | 移除（回退時恢復） |

## 附錄 B（參考）對端已知行為

| 項目 | 行為 | 來源 | 狀態 |
|---|---|---|---|
| I-CSCF 的 Cx 用法 | UAR（REGISTER）、LIR（來電）；用 `I_scscf_select` 從 `s_cscf` 表選 S-CSCF | `icscf/kamailio.cfg`、`icscf/seed.sql` | 設定已讀；收到只有 capabilities 的 UAA 時的行為待 D04 |
| S-CSCF 的 Cx 用法 | MAR（`ims_auth`）、SAR（`ims_registrar_scscf`） | `scscf/kamailio.cfg` | 設定已讀 |
| S-CSCF 認證設定 | `registration_default_algorithm AKAv1-MD5`、`av_request_at_once 1`、`av_request_at_sync 1`、`auth_vector_timeout 60` | 同上 | 設定已讀；實際 MAR 內容待 D03、D05 |
| S-CSCF profile 驗證 | `user_data_xsd CxDataType_Rel7.xsd`、`user_data_always 1` | 同上 | `user_data_always` 對 SAR 的影響待 D08 |
| cdp | 逾時 `TransactionTimeout="5"`；宣告 Cx vendor 10415、4491、13019、0；S-CSCF 在 3870 收連線、I-CSCF 在 3871 | `scscf.xml`、`icscf.xml` | 設定已讀 |
| PyHSS 第一次註冊的 UAA | 依 `pyhss.env` 註解，回 Server-Name（`HSS_SCSCF_POOL`），不符 TS 29.228 §6.1.1.1 | `hss/pyhss.env` 註解 | 待 D03 抓包確認 |
| free-ran-ue 的 SQN | 直接採用網路給的 SQN，不檢查新鮮度 | free-ran-ue `ue/security.go`（`GenerateKeysWithAUTN` 之後直接取代）；部署 v2.5.0，查證的本機版本 v2.5.0-26 | 已讀原始碼 |
| SIPp 的 AKA | 用 OP、K、AMF 計算 response | `ran/sipp/register_aka.xml` | 是否檢查 SQN 新鮮度待 D05 |
| `kamailio-free5gc` 文件引用的條款 | `pyhss.env`、`docs/identities.md` 把 IMPI 推導寫成 TS 23.003 §13.4B；實際上 IMPI 推導在 §13.3，§13.4B 是 temporary IMPU | TS 23.003 V17.11.0 | 已核對（submodule 文件的引用錯誤，非本規格範圍） |

## 附錄 C（參考）Cx 指令與 AVP

依 TS 29.229 V17.3.0 §6.1、§6.3（已核對 code；flag 未核對）。

| 指令 | Code | W8a |
|---|---|---|
| User-Authorization-Request／Answer（UAR／UAA） | 300 | 支援 |
| Server-Assignment-Request／Answer（SAR／SAA） | 301 | 支援 |
| Location-Info-Request／Answer（LIR／LIA） | 302 | 支援 |
| Multimedia-Auth-Request／Answer（MAR／MAA） | 303 | 支援 |
| Registration-Termination-Request／Answer（RTR／RTA） | 304 | W8b |
| Push-Profile-Request／Answer（PPR／PPA） | 305 | W8b |

| AVP | Code | 用在 |
|---|---|---|
| User-Name（RFC 6733） | 1 | IMPI |
| Visited-Network-Identifier | 600 | UAR |
| Public-Identity | 601 | 全部 |
| Server-Name | 602 | UAA、MAR、SAR、LIA |
| Server-Capabilities（Grouped：Mandatory-Capability 604、Optional-Capability 605、Server-Name） | 603 | UAA、LIA |
| User-Data | 606 | SAA |
| SIP-Number-Auth-Items | 607 | MAR、MAA |
| SIP-Authentication-Scheme | 608 | MAR、MAA |
| SIP-Authenticate | 609 | MAA（RAND‖AUTN） |
| SIP-Authorization | 610 | MAR（RAND‖AUTS）、MAA（XRES） |
| SIP-Auth-Data-Item | 612 | MAR、MAA |
| SIP-Item-Number | 613 | MAA |
| Server-Assignment-Type | 614 | SAR（0–14，見 REQ-SAR-03～09） |
| Deregistration-Reason（Grouped：{Reason-Code}、[Reason-Info]） | 615 | RTR |
| Reason-Code（PERMANENT_TERMINATION 0、NEW_SERVER_ASSIGNED 1、SERVER_CHANGE 2、REMOVE_S-CSCF 3） | 616 | RTR |
| Reason-Info | 617 | RTR |
| Associated-Identities | 632 | 不使用（單一 IMPI） |
| Identity-with-Emergency-Registration | 651 | RTA（只記錄） |
| RTR-Flags | 659 | 不使用 |
| User-Authorization-Type | 623 | UAR、LIR（0 REGISTRATION、1 DE_REGISTRATION、2 REGISTRATION_AND_CAPABILITIES） |
| User-Data-Already-Available | 624 | SAR（0、1） |
| Confidentiality-Key | 625 | MAA |
| Integrity-Key | 626 | MAA |
| Supported-Features | 628 | 不使用 |

Mandatory-Capability（604）、Optional-Capability（605）已依 TS 29.229 §6.3 的 AVP 表核對。UAR-Flags、Originating-Request、Wildcarded-Public-Identity 等 AVP 的 code 沒有在本機的 AVP 表中查到（可能定義在其他章節或 TS），待 D02 核對；字典加入前不得使用推測值。

## 附錄 D（參考，W8b 與後續）

- RTR、PPR 已納入 §8A。連線方式待 D15：`scscf.xml` 的 Acceptor 是 3870、`AcceptUnknownPeers="1"`，主動連過去在設定上可行，但要處理與 S-CSCF 反向連線的 election。
- 實驗環境的 P-CSCF 設定 `subscribe_to_reginfo 0`、`publish_reginfo 0`，S-CSCF 也沒有 SUBSCRIBE 的路由；RTR 之後 UE **不會**收到 reg-event NOTIFY。
- N70：TS 23.228 附錄 AA.2.2 有 Cx 指令與 Nhss 服務的對應表（例如 Cx-Query → Nhss_ImsUECM_Authorize、Cx-Put → Nhss_ImsUECM_Registration）；§9.2 的轉移表可以直接共用。
