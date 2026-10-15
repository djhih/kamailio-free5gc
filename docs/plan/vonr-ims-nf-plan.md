# VoNR 計畫：讓 Kamailio IMS 正確接上 free5GC

> 狀態：草案（2026-10-15 改版：HSS 併入 UDM，新增 W8），只有計畫，尚未實作
> 依據：HackMD〈[nf] NF modification plan〉、free5gc v4.3.0 原始碼查證、`specs/3gpp-r17/` 規格

## 0. 一頁摘要

**目標：** 一通 VoNR 電話從頭到尾符合標準：IMS 用標準 Rx 告訴 5GC 要多少資源，5GC 把語音 QoS flow 建到 UPF、gNB、UE，任何一邊斷線另一邊都知道。另外把 HSS 併入 free5gc UDM，IMS 與 5G 只用一份用戶資料、一個 SQN。

**要做的 8 件事：**

| # | 工作 | 類型 | 規模 |
|---|---|---|---|
| W1 | 端到端測試改成看抓包 | 改測試腳本 | 小 |
| W2 | AMF 宣告支援 IMS 語音（`imsVoPS: 1`） | 改設定 | 很小 |
| W3 | **Rx／N5 Adapter** | **新寫程式** | **大** |
| W4 | Kamailio P-CSCF 改用標準 `ims_qos` | 改設定 | 小 |
| W5 | **SMF 把 QoS flow 通知 gNB 與 UE** | **改 free5gc 程式** | **中** |
| W6 | 確認 free-ran-ue 能收 QoS flow 修改 | 驗證，可能要修 | 未知 |
| W7 | 確認部署版本（free5gc 4.2.3、Kamailio 6.1.4）與查證時看的版本行為相同 | 驗證 | 小 |
| W8 | **HSS 併入 UDM**：UDM 對 Kamailio 提供 Cx，IMS 資料存 UDR，取代 PyHSS | **改 free5gc 程式**（UDM、UDR） | **大** |

**時程：** 約 11–12 週，分 6 個階段（第 4 節）。

**不做：** 不讓 AMF／SMF 處理 SIP；不取代 Kamailio；不改 PCF、UPF；不做 N70（Kamailio 只支援 Cx）。

**會改的 free5gc NF：** SMF（W5）、UDM 與 UDR（W8）。

## 1. 設計原則

| 範圍 | 負責 |
|---|---|
| 5GC（free5GC） | UE 註冊、PDU session、QoS 控制、policy、user plane；**IMS 用戶資料與 IMS AKA（HSS 功能，實作在 UDM 裡）** |
| IMS（Kamailio） | SIP 註冊、SIP session 控制、呼叫路由、IMS session 狀態 |
| 語音媒體 | RTP 走 5GC 依 policy 建立的 QoS flow |

HSS 放進 UDM 是 TS 23.228 附錄 Y.0 允許的部署方式；規格要求 HSS 的 IMS 功能在邏輯上維持獨立，對 CSCF 的介面仍是 Cx。所以 UDM 裡的 HSS 是獨立的子系統，Kamailio 看到的仍是一個講 Cx 的 HSS。

## 2. 現況與缺口

| 環節 | 現況 | 缺口 | 由哪個工作處理 |
|---|---|---|---|
| UE 知道網路支援 IMS 語音 | AMF 設 `imsVoPS: 0` | 網路說不支援 | W2 |
| UE 找到 P-CSCF | SMF 用 PCO 回傳（IPv4） | 無 | — |
| IMS 告訴 5GC 要多少資源 | AF shim（自訂 HTTP） | 非標準、同步會卡住 Kamailio | W3 + W4 |
| PCF → SMF → UPF 裝語音規則 | 可運作 | 無 | — |
| SMF 通知 gNB 與 UE 新的 QoS flow | **沒做** | gNB／UE 不知道有 5QI 1 | W5（+ W6） |
| 5GC 告訴 IMS「PDU session 沒了」 | 終止通知送到 `/notify/terminate`，shim 沒接這個路徑（404） | 通話不會結束 | W3 |
| 證明以上都成功 | 測試依賴 Kamailio log 字串 | 換掉元件就不能測 | W1 |
| IMS 註冊時交換信令 flow 與事件訂閱 | 沒做 | 不符 TS 29.513 附錄 B.5–B.8 | W3c |
| P-CSCF 位址的 IPv6 | SMF 只支援 IPv4 | 沒有 IPv6 | 不在範圍內 |
| QER 真的限速／保證頻寬 | free5gc 只裝規則 | 無法驗證實際 QoS | 不在範圍內（free5gc 的限制） |
| 查證依據的版本 | 程式碼查證用 free5gc v4.3.0、Kamailio master | 部署是 4.2.3、6.1.4 | W7 |
| IMS 與 5G 的用戶資料 | PyHSS、UDR 各一份，靠開戶腳本對齊；SQN 各算各的 | 兩份資料可能不一致；SQN 分開與 USIM 實際行為不符 | W8 |

## 3. 工作項目

### W1　端到端測試改成看抓包

- **做什麼：** `03-call-test.sh` 改成從抓包判斷（SIP 訊息、Cx 指令、Rx 訊息、N2 訊息），不再 grep Kamailio 的 log 字串
- **為什麼：** W3、W4 會改變 log；之後每個階段都要用同一套測試驗收
- **完成條件：** 在**現有**部署上通過
- **依賴：** 無

### W2　AMF 宣告支援 IMS 語音

- **做什麼：** `config/amfcfg.yaml` 的 `networkFeatureSupport5GS.imsVoPS` 改成 1
- **完成條件：** 抓包看到 Registration Accept 的 5GS network feature support 中 IMS VoPS = 1
- **依賴：** 無

### W3　Rx／N5 Adapter（主體）

- **做什麼：** 新寫一個 free5gc 風格的 NF，把 Kamailio 的 Rx 翻成 N5，並把 PCF 的回呼翻回 Rx
- **說明文件：** `rx-n5-adapter-explained.md`（它要做什麼）、`rx-n5-adapter-design.md`（怎麼寫）
- **分三段交付：**

| 段 | 內容 | 完成條件 |
|---|---|---|
| W3a 通話資源 | AAR → 建立 app session、STR → 刪除；NRF 註冊 | 搭配 W4，`03-call-test.sh`、`05-n5-qos-test.sh` 通過 |
| W3b 5GC 回報 | terminate → ASR；事件 → RAR；re-INVITE → PATCH | 通話中釋放被叫 PDU session，通話結束 |
| W3c 註冊時 | 信令 session、事件訂閱（TS 29.513 B.5–B.8）；BSF 找 PCF | 抓包看到註冊時的 AAR 與 app session |

- **依賴：** W1（才能驗收）

### W4　Kamailio P-CSCF 改用 `ims_qos`

- **做什麼：** 載入 `cdp`、`cdp_avp`、`ims_qos`；200 OK 時呼叫 `Rx_AAR`；刪掉 `AF_*` 路由與 `http_client`
- **完成條件：** 抓包看到 AAR／STR 送往 Adapter
- **依賴：** W3a 至少能回 AAA（可以先用假的 Diameter peer 抓包確認 AVP）

### W5　SMF 通知 gNB 與 UE 新的 QoS flow

- **做什麼：** PCF 更新 policy 後，SMF 除了更新 UPF，還要經 AMF 送 N1N2（PDU Session Modification Command、N2 PDU Session Resource Modify Request），依 TS 23.502 4.3.3.2
- **改哪裡：** `free5gc/smf` 的 `HandleSMPolicyUpdateNotify`；可重用現有的 `BuildPDUSessionResourceModifyRequestTransfer` 與 N1N2 consumer
- **完成條件：** 抓包看到 N2 Modify Request／Response，UE 收到 Modification Command
- **依賴：** W6（gNB／UE 要能回應）；可與 W3 平行進行
- **交付：** 依 free5gc 流程對 `free5gc/smf` 發 PR（是否發 PR 待決定）

### W6　確認 free-ran-ue 支援 QoS flow 修改

- **做什麼：** 確認 free-ran-ue 的 gNB 能處理 N2 PDU Session Resource Modify、UE 能處理 PDU Session Modification Command
- **完成條件：** 有結論；不支援時決定修 free-ran-ue，或 W5 只驗證 SMF 送出的訊息
- **依賴：** 無

### W7　確認部署版本與查證版本一致

- **做什麼：** 本計畫的幾個關鍵判斷是讀 free5gc **v4.3.0**（PCF v1.4.5）與 Kamailio **master** 的原始碼得來，但部署跑的是 free5gc **4.2.3**、Kamailio **6.1.4**。要確認下列行為在部署版本上相同：
  - SMF 收到 policy 更新時沒有送 N1N2（W5 的前提）
  - AMF 有 `networkFeatureSupport5GS.imsVoPS` 設定（W2）
  - PCF 支援 PATCH、DELETE、events 與 `SendAppSessionTermination`，終止通知送到 `{notifUri}/terminate`（W3b）。注意：PATCH 有實作但有限制（重複 PATCH 刪不掉舊規則、沒帶 `evSubsc` 會清掉訂閱），見 `rx-n5-adapter-design.md` §6.2
  - `ims_qos` 預設送 IMPU、上行 Flow-Description 寫成 `from <UE> to <對方>`（W3a）
  - UDM 的認證向量產生與 SQN 更新流程（`generate_auth_data.go`），W8 要從這裡抽出共用函式
- **完成條件：** 每一項都有結論；有差異時更新對應工作項
- **依賴：** 無

### W8　HSS 併入 UDM

- **做什麼：** 在 free5gc UDM 裡實作 HSS 的 Cx 功能（UAR、LIR、MAR、SAR），I-CSCF、S-CSCF 改連 UDM；IMS 用戶資料與註冊狀態存在 UDR；IMS AKA 與 5G-AKA 共用 K／OPc／SQN；移除 PyHSS
- **說明文件：** [hss-in-udm-design.md](hss-in-udm-design.md)
- **改哪裡：** `free5gc/udm`（新增 `internal/cx/`、抽出認證向量的共用函式）、`free5gc/udr`（非標準擴充 `/nudr-ims-ext/v1`）、`kamailio-free5gc` 的 compose 與開戶腳本
- **分兩段交付：**

| 段 | 內容 | 完成條件 |
|---|---|---|
| W8a 取代 PyHSS | UDR 擴充、Cx server、UAR／LIR／MAR／SAR、User-Data、開戶腳本 | PyHSS 容器移除後 `03-call-test.sh` 通過；UDR 裡只有一個 SQN 且 5G-AKA、IMS AKA 都會遞增它 |
| W8b HSS 主動通知 | RTR、PPR | 改 profile 抓到 PPR；強制解除註冊抓到 RTR（是否納入範圍待決定） |

- **依賴：** W1（抓包驗收 Cx）；W7 確認要 fork 的 free5gc 版本
- **交付：** 自己的 fork。Cx 進 UDM 不符合 free5gc 上游的方向，不以發 PR 為目標

## 4. 時程

```
週   1   2   3   4   5   6   7   8   9   10  11  12
W1  ██
W2  █
W6  ██
W7  ██
W3a     ██████
W4          ███
W5      ████████                          （與 W3 平行）
W3b                 ████
W3c                     ████
W8a                 ████████████████      （與 W3b、W3c 平行）
W8b                                 ████
```

| 階段 | 包含 | 完成時能證明什麼 |
|---|---|---|
| Phase 0（第 1 週） | W1、W2、W6、W7 | 測試不依賴實作；網路宣告支援 IMS 語音 |
| Phase 1（第 2–4 週） | W3a、W4 | 用標準 Rx 預留通話資源，shim 退役 |
| Phase 2（第 2–5 週，平行） | W5 | 語音 QoS flow 到達 gNB 與 UE |
| Phase 3（第 5–6 週） | W3b | 5GC 斷線時 IMS 會結束通話 |
| Phase 4（第 7–8 週） | W3c | 註冊時也交換資訊，符合 TS 29.513 附錄 B |
| Phase 5（第 5–12 週，與 Phase 3、4 平行） | W8a、W8b | PyHSS 退役；IMS 與 5G 共用一份用戶資料與 SQN |

## 5. 每個階段怎麼驗收

| 階段 | 驗收方式 |
|---|---|
| 0 | 抓包版 `03-call-test.sh` 在現有部署通過；Registration Accept 裡 IMS VoPS = 1 |
| 1 | `03-call-test.sh` 通過，抓包看到 AAR／AAA、STR／STA；`05-n5-qos-test.sh` 改用 Rx client 觸發也通過；AF shim 容器移除 |
| 2 | 通話時抓到 N2 PDU Session Resource Modify Request 與 Response |
| 3 | 通話中用 free-ran-ue 釋放 UE2 的 PDU session → 抓到 ASR → 兩支 UE 都收到 BYE |
| 4 | UE 註冊後抓到 AAR（信令）與對應的 app session；PCF 的位址由 BSF 查出 |
| 5 | PyHSS 容器移除後 `03-call-test.sh` 通過；抓包看到 UAR／LIR／MAR／SAR 由 UDM 回應；連續做 5G 註冊與 IMS 註冊，UDR 的 SQN 持續遞增、沒有 AUTS 重新同步以外的失敗 |

## 6. 風險

| 風險 | 影響 | 對策 |
|---|---|---|
| free-ran-ue 不支援 QoS flow 修改 | W5 無法完整驗證 | W6 先確認；必要時只驗 SMF 送出的訊息 |
| Flow-Description 上行寫法與 shim 不同（見 `rx-n5-adapter-explained.md` 第 6 節） | UPF 上行規則可能反向 | Phase 1 抓包看 PDR；必要時 Adapter 改寫 |
| `ims_qos` 送 IMPU 而非 IMSI | PCF 綁錯 UE | Adapter 從 IMPU 推 SUPI |
| SMF 修改要進上游 | 審查時間不可控 | 先在自己的 fork 完成並驗證 |
| NRF 開 OAuth 時 PCF → SMF scope 不一致（現有問題） | QoS 流程斷掉 | 維持 OAuth 關閉 |
| W8 要 fork UDM、UDR，UDR 還要加非標準資源 | free5gc 升版時要 rebase；別人的 free5gc 無法直接接 | 擴充集中在獨立的 API 前綴與 `internal/cx/`，減少衝突面 |
| SQN 共用後，free-ran-ue 與 SIPp 看到跳號 | 認證失敗或頻繁重新同步 | W8a 一開始就測；UDM 走 AUTS 重新同步 |
| 5G-AKA 與 IMS AKA 同時更新 SQN | SQN 被覆蓋 | 先記錄；必要時改成 UDR 端原子遞增 |
| UDM 回的 User-Data XML 不符合 Kamailio 的 XSD | S-CSCF 拒絕註冊 | 先抓 PyHSS 的 SAA 當樣本 |

## 7. 待決定

1. Adapter 的名稱
2. W5 是否以發 PR 回 `free5gc/smf` 為目標
3. app session 模型：維持「每個 Rx session 一個」（建議），或改採 2024 年碩論的「每支 UE 一個」。比較見 [../background/ims-af-thesis-comparison.md](../background/ims-af-thesis-comparison.md)
4. re-INVITE 時 PCF PATCH 的限制怎麼處理（`rx-n5-adapter-design.md` §10 第 5 項）
5. W5、W8 要 fork 的 free5gc 版本：沿用部署的 4.2.3，或一起升到 v4.3.0（`hss-in-udm-design.md` §11 第 1 項）
6. W8b（RTR、PPR）是否納入範圍

## 8. 文件索引

| 文件 | 內容 |
|---|---|
| [rx-n5-adapter-explained.md](rx-n5-adapter-explained.md) | Adapter 要做什麼（用一通電話說明） |
| [rx-n5-adapter-design.md](rx-n5-adapter-design.md) | Adapter 怎麼寫（介面、結構、對應表、實作順序） |
| [hss-in-udm-design.md](hss-in-udm-design.md) | HSS 併入 UDM 怎麼寫（Cx、UDR 擴充、共用 SQN、實作順序） |
| [vonr-ims-dev-process.md](vonr-ims-dev-process.md) | 開發流程與程式慣例 |
| [../current/free5gc-kamailio-integration.md](../current/free5gc-kamailio-integration.md) | 目前的五個對接點 |
| [../background/3gpp-ims-standards.md](../background/3gpp-ims-standards.md) | 相關 3GPP 規格 |
| [../background/ims-af-thesis-comparison.md](../background/ims-af-thesis-comparison.md) | 2024 年碩論的 IMS-AF 與本計畫的差異（含 free5gc PCF 的 PATCH 限制） |
