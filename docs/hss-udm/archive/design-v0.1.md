> **已封存（v0.1）。** 現行版本見 [../README.md](../README.md)。下文的相對連結是以原位置 `docs/plan/` 為準，可能已失效。

# HSS 併入 UDM 設計

> 狀態：設計草案（2026-10-15），尚未實作
> 上層計畫：`vonr-ims-nf-plan.md` 的 W8
> 依據：TS 23.228 附錄 Y.0、TS 29.228／29.229（Cx）、TS 33.203（IMS AKA）、TS 23.003 §13（IMS 身分）、TS 29.505（UDR）；free5gc UDM v1.4.6、UDR v1.4.4 原始碼；`kamailio-free5gc/` 的 Kamailio 與 PyHSS 設定

## 1. 做什麼、不做什麼

**做什麼：** 把 IMS 的 HSS 功能實作在 free5gc **UDM** 裡，取代 PyHSS。Kamailio 的 I-CSCF、S-CSCF 改連 UDM，協定仍是 **Cx（Diameter）**。IMS 用戶資料跟 5G 用戶資料都放在 UDR，**IMS AKA 與 5G-AKA 共用同一組 K／OPc／SQN**。

```
現況   I-CSCF ─Cx─┐                         UDM ─Nudr─ UDR
       S-CSCF ─Cx─┴─▶ PyHSS（SQLite，4 個容器）   （兩份用戶資料，SQN 各算各的）

計畫   I-CSCF ─Cx─┐
       S-CSCF ─Cx─┴─▶ UDM（內含 HSS 功能）─Nudr─▶ UDR（一份用戶資料，SQN 共用）
```

**不做：**
- 不改 Kamailio 的 SIP 路由邏輯，只改 Cx peer 的位址
- 不做 N70（Nhss_ims*，TS 29.562）：Kamailio 只支援 Cx
- 不做 Sh（沒有 AS）
- 不讓 AMF／SMF 處理 SIP

**規格依據：** TS 23.228 附錄 Y.0 允許「HSS as part of UDM」，但要求 HSS 的 IMS 功能在邏輯上維持獨立，對 CSCF 的介面仍是 Cx 或 N70。所以本設計在 UDM 裡把 HSS 寫成獨立的子系統（`internal/cx/`），不跟 Nudm 服務混在一起。

## 2. 為什麼這樣做

| 好處 | 說明 |
|---|---|
| 一份用戶資料 | 開戶只寫 UDR 一次，不再靠 `lib-keys.sh` 對齊兩邊 |
| SQN 共用 | 沒有 ISIM 的手機，5G-AKA 與 IMS AKA 用的是同一張 USIM 的 SQN；網路端也只該有一個計數器 |
| 少 4 個容器 | 移除 PyHSS 的 hss、api、diameter、redis |
| 5GC 掌握 IMS 註冊狀態 | 之後要做 T-ADS、IMS 註冊狀態連動時，資料已在 UDR |

代價：要 fork free5gc 的 **UDM 與 UDR**，而且 UDR 要加**非標準**的資源（Rel-17 的 Nudr 沒有 IMS 用戶資料）。上游接受的機會很低，之後每次 free5gc 升版都要 rebase。

## 3. Cx 介面速查（TS 29.229）

- Application-Id **16777216**，Vendor-Id **10415**
- UDM 是 Diameter **server**：I-CSCF、S-CSCF 的 cdp 主動連進來
- RTR／PPR 是 HSS 主動發出，需要 UDM 也能當 client 連到 S-CSCF（S-CSCF 的 cdp 在 3870 等連線）

| 指令 | Code | 誰送 | 時機 | UDM 要做的 |
|---|---|---|---|---|
| UAR／UAA | 300 | I-CSCF | 收到 REGISTER | 檢查 IMPI／IMPU 是否存在且相符；回 Server-Name（已指派過的 S-CSCF）或 Server-Capabilities |
| SAR／SAA | 301 | S-CSCF | 註冊成功、解除註冊、逾時 | 記錄或清除指派的 S-CSCF 與註冊狀態；註冊時回 User-Data（XML profile） |
| LIR／LIA | 302 | I-CSCF | 有來電 | 回被叫 IMPU 目前的 Server-Name |
| MAR／MAA | 303 | S-CSCF | 註冊要認證 | 產生 IMS AKA 向量；處理 AUTS 重新同步 |
| RTR／RTA | 304 | UDM → S-CSCF | 營運端強制解除註冊 | 第二階段 |
| PPR／PPA | 305 | UDM → S-CSCF | profile 改了 | 第二階段 |

要處理的 AVP（皆為 3GPP vendor 10415）：

| AVP | Code | 用在 | 說明 |
|---|---|---|---|
| User-Name（RFC 6733） | 1 | UAR、SAR、MAR | IMPI |
| Public-Identity | 601 | 全部 | IMPU |
| Visited-Network-Identifier | 600 | UAR | 本專案只有 home network |
| User-Authorization-Type | 623 | UAR | REGISTRATION(0)／DE_REGISTRATION(1)／REGISTRATION_AND_CAPABILITIES(2) |
| Server-Name | 602 | UAA、SAR、LIA、MAR | S-CSCF 的 SIP URI |
| Server-Capabilities | 603 | UAA | 還沒指派 S-CSCF 時回傳 |
| Server-Assignment-Type | 614 | SAR | REGISTRATION、RE_REGISTRATION、USER_DEREGISTRATION、TIMEOUT_DEREGISTRATION、UNREGISTERED_USER 等 |
| User-Data | 606 | SAA、PPR | IMS Subscription XML（依 CxDataType XSD） |
| User-Data-Already-Available | 624 | SAR | S-CSCF 已有 profile 時不用再回 |
| SIP-Number-Auth-Items | 607 | MAR、MAA | 要幾組向量 |
| SIP-Auth-Data-Item | 612 | MAR、MAA | Grouped，一組向量 |
| ├ SIP-Item-Number | 613 | MAA | 序號 |
| ├ SIP-Authentication-Scheme | 608 | MAR、MAA | `Digest-AKAv1-MD5` |
| ├ SIP-Authenticate | 609 | MAA | RAND ‖ AUTN，共 32 bytes |
| ├ SIP-Authorization | 610 | MAR、MAA | MAR：RAND ‖ AUTS（30 bytes，重新同步用）；MAA：XRES |
| ├ Confidentiality-Key | 625 | MAA | CK |
| └ Integrity-Key | 626 | MAA | IK |
| Deregistration-Reason | 615 | RTR | 第二階段 |

Experimental-Result-Code：

| 名稱 | 值 | 何時回 |
|---|---|---|
| DIAMETER_FIRST_REGISTRATION | 2001 | UAA：此 IMPU 還沒有 S-CSCF |
| DIAMETER_SUBSEQUENT_REGISTRATION | 2002 | UAA：已有 S-CSCF |
| DIAMETER_UNREGISTERED_SERVICE | 2003 | LIA：未註冊但有 unregistered service |
| DIAMETER_ERROR_USER_UNKNOWN | 5001 | 查無此 IMPI／IMPU |
| DIAMETER_ERROR_IDENTITIES_DONT_MATCH | 5002 | IMPI 與 IMPU 不屬於同一個用戶 |
| DIAMETER_ERROR_IDENTITY_NOT_REGISTERED | 5003 | LIA：被叫沒註冊 |
| DIAMETER_ERROR_ROAMING_NOT_ALLOWED | 5004 | 不在允許的網路 |
| DIAMETER_ERROR_IDENTITY_ALREADY_REGISTERED | 5005 | SAR：已由別的 S-CSCF 服務 |

本專案的 Kamailio 實際用到的只有 UAR、LIR（I-CSCF）與 MAR、SAR（S-CSCF）。第一階段只做這四種。

## 4. 程式放在 UDM 的哪裡

照 free5gc CHF 放 Diameter 的方式（`NFs/chf/ccs_diameter/`：字典寫成 Go 字串、以 `dict.Default.Load()` 載入、用帶 `avp:"..."` tag 的 struct 解碼）。

```
udm/
├── pkg/
│   ├── factory/config.go            # 新增 cx 區塊（第 8 節）
│   └── service/init.go              # 啟動順序加上 cx.Server
└── internal/
    ├── cx/                          # HSS 子系統，跟 Nudm 分開
    │   ├── dict.go                  # Cx 字典（XML 字串），只列第 3 節的 AVP
    │   ├── types.go                 # UAR、SAR、LIR、MAR 等 struct
    │   ├── server.go                # Diameter server：CER/DWR、依 command code 分派
    │   ├── handler_uar.go
    │   ├── handler_sar.go
    │   ├── handler_lir.go
    │   ├── handler_mar.go
    │   ├── userdata.go              # 產生 IMS Subscription XML
    │   └── *_test.go
    ├── sbi/processor/
    │   ├── generate_auth_data.go    # 抽出共用的「取向量 + 更新 SQN」函式，5G-AKA 與 IMS AKA 都用
    │   └── ims_auth.go              # 新增：IMS AKA 向量（RAND、AUTN、XRES、CK、IK）
    └── sbi/consumer/
        └── udr_service.go           # 新增：讀寫第 5 節的 IMS 資源
```

**IMS AKA 向量重用現有程式：** `generate_auth_data.go` 已經會取 K／OPc／SQN、處理 AUTS 重新同步、遞增 SQN 寫回 UDR，再呼叫 `milenage.GenerateAKAParameters` 得到 IK、CK、RES、AUTN。IMS AKA 要的是同一組值（不必再推導 5G 的 K_AUSF），所以把「取 SQN → 必要時重新同步 → 遞增寫回 → 跑 Milenage」抽成共用函式，兩邊呼叫。

## 5. 資料（UDR）

### 5.1 認證資料：直接共用

沿用 `subscriptionData.authenticationData.authenticationSubscription`（K、OPc、AMF、SQN），**不另外存一份**。IMS AKA 與 5G-AKA 遞增的是同一個 SQN。

### 5.2 IMS 資料：UDR 的非標準擴充

Rel-17 的 Nudr（TS 29.505）沒有 IMS 用戶資料，只有 UDM↔HSS 互通用的 `HssSubscriptionInfo`。所以要在 UDR 加資源。為了不跟未來的標準路徑衝突，放在**獨立的 API 前綴** `/nudr-ims-ext/v1`：

| 資源 | 方法 | 內容 | MongoDB collection |
|---|---|---|---|
| `/subscription-data/{supi}/ims-subscription` | GET、PUT、DELETE | IMPI、IMPU 清單、MSISDN、service profile（含 iFC，可以先是空的） | `subscriptionData.imsData.imsSubscription` |
| `/ims-identities/{impu 或 impi}` | GET | 由 IMS 身分查 SUPI | `subscriptionData.imsData.imsIdentities`（索引） |
| `/subscription-data/{supi}/context-data/ims-registration` | GET、PUT、PATCH、DELETE | 每個 IMPU 的註冊狀態、指派的 S-CSCF、IMPI | `subscriptionData.contextData.imsRegistration` |

- HSS 的動態狀態（誰註冊了、由哪台 S-CSCF 服務）存在 UDR，UDM 本身保持無狀態，重啟不會遺失
- `ims-subscription` 寫入時，UDR 同步更新 `imsIdentities` 索引

### 5.3 身分對應

| Cx 帶來的 | 怎麼找到 SUPI |
|---|---|
| IMPI（User-Name） | 查 `ims-identities/{impi}` |
| IMPU（Public-Identity） | 查 `ims-identities/{impu}` |

找不到就回 DIAMETER_ERROR_USER_UNKNOWN。**不靠「IMPU 的 user part 就是 IMSI」這條規則推導**，因為它只在本專案的開戶方式下成立；對應關係一律由開戶時寫入。

## 6. 每種訊息的處理流程

### 6.1 UAR（I-CSCF，收到 REGISTER）

1. 用 IMPI、IMPU 查 SUPI；查不到 → 5001；兩者對到不同 SUPI → 5002
2. User-Authorization-Type 是 DE_REGISTRATION：有 S-CSCF 就回它的 Server-Name，回 2001（DIAMETER_SUCCESS）
3. 讀 `ims-registration`：已有 S-CSCF → 回 Server-Name + 2002；沒有 → 回 Server-Capabilities（或設定好的預設 Server-Name）+ 2001

### 6.2 MAR（S-CSCF，要認證）

1. 查 SUPI，比對 IMPI／IMPU
2. 沒有 SIP-Authorization：取一組向量（第 4 節的共用函式），回 SIP-Authenticate = RAND ‖ AUTN、SIP-Authorization = XRES、CK、IK
3. 有 SIP-Authorization（RAND ‖ AUTS）：先用 AUTS 重新同步 SQN（現有 `aucSQN`），再產生新向量
4. 把 MAR 的 Server-Name 記到 `ims-registration`，狀態設為「認證中」

### 6.3 SAR（S-CSCF，註冊結果）

| Server-Assignment-Type | 動作 |
|---|---|
| REGISTRATION、RE_REGISTRATION | `ims-registration` 寫入 Server-Name、狀態 REGISTERED；User-Data-Already-Available=0 時回 User-Data |
| UNREGISTERED_USER | 被叫未註冊但有來電：指派 S-CSCF、狀態 UNREGISTERED，回 User-Data |
| USER_DEREGISTRATION、TIMEOUT_DEREGISTRATION 等 | 清除 Server-Name，狀態 NOT_REGISTERED |

已由另一台 S-CSCF 服務 → 5005。

### 6.4 LIR（I-CSCF，有來電）

1. 用 IMPU 查 SUPI；查不到 → 5001
2. 讀 `ims-registration`：已註冊 → 回 Server-Name；未註冊但有 unregistered service → 回 Server-Capabilities + 2003；都沒有 → 5003

## 7. User-Data（IMS Subscription XML）

S-CSCF 會用 `scscf/CxDataType_Rel7.xsd` 驗證 SAA 帶回的 XML，格式錯就拒絕註冊。最小可用內容：

```xml
<IMSSubscription>
  <PrivateID>208930000000001@ims.mnc093.mcc208.3gppnetwork.org</PrivateID>
  <ServiceProfile>
    <PublicIdentity>
      <Identity>sip:208930000000001@ims.mnc093.mcc208.3gppnetwork.org</Identity>
    </PublicIdentity>
  </ServiceProfile>
</IMSSubscription>
```

- 先抓 PyHSS 現在回的 SAA 當對照樣本（第 10 節步驟 1）
- iFC 目前不需要（沒有 AS），欄位留著

## 8. 設定與部署

### 8.1 UDM 設定（草案）

```yaml
configuration:
  cx:
    enable: true
    bindAddr: 0.0.0.0
    port: 3868
    originHost: hss.ims.mnc093.mcc208.3gppnetwork.org   # 沿用 PyHSS 的身分，Kamailio 的 cdp 設定不用改名稱
    originRealm: ims.mnc093.mcc208.3gppnetwork.org
    defaultServerName: sip:scscf.ims.mnc093.mcc208.3gppnetwork.org:6060   # 等同 PyHSS 的 HSS_SCSCF_POOL
  udrExt:
    imsPrefix: /nudr-ims-ext/v1
```

### 8.2 部署（`kamailio-free5gc/`）

| 項目 | 改法 |
|---|---|
| UDM 容器 | 改用自己 build 的 image；**同時接 corenet（SBI）與 dnnet（Cx）**，在 dnnet 上取別名 `hss.ims.mnc093.mcc208.3gppnetwork.org` |
| UDR 容器 | 改用自己 build 的 image（第 5.2 節的擴充） |
| PyHSS | 移除 `pyhss-hss`、`pyhss-api`、`pyhss-diameter`、`pyhss-redis` 四個容器與 `hss/pyhss.env` |
| Kamailio | `icscf.xml`、`scscf.xml` 的 Peer FQDN 不變；只要 DNS 別名指到 UDM 就好 |
| 開戶 | `04-add-ims-subscribers.sh` 改成呼叫 UDR 的 `/nudr-ims-ext/v1` PUT；`02-add-subscribers.sh` 照舊寫 5G 資料 |
| Adapter（W3） | 也在 dnnet 用 3868，IP 不同，不衝突 |

## 9. 跟 free-ran-ue、SIPp 的 SQN 問題（要先驗證）

共用 SQN 之後，free-ran-ue（做 5G-AKA）和 SIPp（做 IMS AKA）是兩個各自追蹤 SQN 的「USIM」。網路端每做一次認證 SQN 就遞增，所以兩邊都會看到跳號。

- 規格上 USIM 接受比上次大的 SQN（在允許範圍內），理論上沒問題
- 要實測：free-ran-ue 有沒有檢查 SQN 範圍、SIPp 有沒有檢查 SQN；有問題時 UE 會回 AUTS，UDM 走重新同步
- 共用 SQN 也有並行問題：5G-AKA 與 IMS AKA 同時發生時，現有程式是「讀 SQN → 遞增 → 寫回」，可能互相覆蓋。第一階段先記錄，必要時改成 UDR 端的原子遞增

## 10. 實作順序

| # | 做什麼 | 怎麼驗證 |
|---|---|---|
| 1 | 在**現有** PyHSS 部署上抓 UAR／UAA、MAR／MAA、SAR／SAA、LIR／LIA 當樣本 | pcap 存進測試資料 |
| 2 | fork UDM、UDR，確認 build 與 free5gc 版本（第 11 節第 1 項） | 原本的 5G 註冊照樣通過 |
| 3 | UDR 擴充（第 5.2 節）+ 開戶腳本 | 用 curl PUT／GET IMS 資料 |
| 4 | `cx/dict.go`、`types.go`：能解碼步驟 1 的封包 | 單元測試 |
| 5 | Diameter server：CER／DWR | Kamailio 的 cdp 能連上 UDM |
| 6 | UAR、LIR | I-CSCF 抓包看到正確的 UAA、LIA |
| 7 | 抽出共用的認證向量函式 + MAR | 5G-AKA 測試照樣通過；SIPp 的 IMS AKA 成功；UDR 的 SQN 只有一個且持續遞增 |
| 8 | SAR + User-Data | S-CSCF 接受 profile，REGISTER 回 200 |
| 9 | 移除 PyHSS | `03-call-test.sh` 通過（**W8 完成**） |
| 10 | （第二階段）RTR、PPR | 改 profile 後抓到 PPR；強制解除註冊抓到 RTR |

## 11. 待確認與待決定

1. **要 fork 哪個 free5gc 版本**：部署是 4.2.3（UDM image `free5gc/udm:v4.2.3`），本機原始碼是 UDM v1.4.6／UDR v1.4.4（屬於 v4.3.0 之後）。要嘛一起升級到 v4.3.0，要嘛 fork 4.2.3 的 tag。牽涉 W5 的 SMF 也要用同一版
2. go-diameter 遇到 Kamailio 送來、但字典沒有的 AVP 會不會解碼失敗（跟 Adapter 設計 §10 第 1 項同一個問題）
3. 第 9 節的 SQN 跳號與並行問題
4. Kamailio `ims_auth` 一次要幾組向量（SIP-Number-Auth-Items），以及它對 SIP-Authorization 內容的期待
5. UDR 擴充的路徑與 collection 名稱（第 5.2 節）是否要跟實驗室其他人對齊
6. 開戶要不要做進 free5gc webconsole，或維持腳本
7. RTR／PPR 是否在本計畫範圍內
