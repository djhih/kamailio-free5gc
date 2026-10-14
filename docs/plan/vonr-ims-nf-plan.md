# VoNR 計畫：讓 Kamailio IMS 正確接上 free5GC

> 狀態：草案（2026-10-14 改寫），只有計畫，尚未實作
> 依據：HackMD〈[nf] NF modification plan〉、free5gc v4.3.0 原始碼查證、`specs/3gpp-r17/` 規格

## 0. 一頁摘要

**目標：** 一通 VoNR 電話從頭到尾符合標準：IMS 用標準 Rx 告訴 5GC 要多少資源，5GC 把語音 QoS flow 建到 UPF、gNB、UE，任何一邊斷線另一邊都知道。

**要做的 6 件事：**

| # | 工作 | 類型 | 規模 |
|---|---|---|---|
| W1 | 端到端測試改成看抓包 | 改測試腳本 | 小 |
| W2 | AMF 宣告支援 IMS 語音（`imsVoPS: 1`） | 改設定 | 很小 |
| W3 | **Rx／N5 Adapter** | **新寫程式** | **大** |
| W4 | Kamailio P-CSCF 改用標準 `ims_qos` | 改設定 | 小 |
| W5 | **SMF 把 QoS flow 通知 gNB 與 UE** | **改 free5gc 程式** | **中** |
| W6 | 確認 free-ran-ue 能收 QoS flow 修改 | 驗證，可能要修 | 未知 |

**時程：** 約 6–8 週，分 5 個階段（第 4 節）。

**不做：** 不讓 AMF／SMF 處理 SIP；不取代 Kamailio、PyHSS；不改 PCF、UPF、UDM、UDR。

## 1. 設計原則

| 範圍 | 負責 |
|---|---|
| 5GC（free5GC） | UE 註冊、PDU session、QoS 控制、policy、user plane |
| IMS（Kamailio + PyHSS） | SIP 註冊、SIP session 控制、呼叫路由、IMS 用戶與 session 狀態 |
| 語音媒體 | RTP 走 5GC 依 policy 建立的 QoS flow |

## 2. 現況與缺口

| 環節 | 現況 | 缺口 | 由哪個工作處理 |
|---|---|---|---|
| UE 知道網路支援 IMS 語音 | AMF 設 `imsVoPS: 0` | 網路說不支援 | W2 |
| UE 找到 P-CSCF | SMF 用 PCO 回傳（IPv4） | 無 | — |
| IMS 告訴 5GC 要多少資源 | AF shim（自訂 HTTP） | 非標準、同步會卡住 Kamailio | W3 + W4 |
| PCF → SMF → UPF 裝語音規則 | 可運作 | 無 | — |
| SMF 通知 gNB 與 UE 新的 QoS flow | **沒做** | gNB／UE 不知道有 5QI 1 | W5（+ W6） |
| 5GC 告訴 IMS「PDU session 沒了」 | shim 只寫 log | 通話不會結束 | W3 |
| 證明以上都成功 | 測試依賴 Kamailio log 字串 | 換掉元件就不能測 | W1 |

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

## 4. 時程

```
週   1     2     3     4     5     6     7     8
W1  ███
W2  █
W6  ███
W3a       ██████████
W4              █████
W5        ███████████████              （與 W3 平行）
W3b                         ██████
W3c                               ██████
```

| 階段 | 包含 | 完成時能證明什麼 |
|---|---|---|
| Phase 0（第 1 週） | W1、W2、W6 | 測試不依賴實作；網路宣告支援 IMS 語音 |
| Phase 1（第 2–4 週） | W3a、W4 | 用標準 Rx 預留通話資源，shim 退役 |
| Phase 2（第 2–5 週，平行） | W5 | 語音 QoS flow 到達 gNB 與 UE |
| Phase 3（第 5–6 週） | W3b | 5GC 斷線時 IMS 會結束通話 |
| Phase 4（第 7–8 週） | W3c | 註冊時也交換資訊，符合 TS 29.513 附錄 B |

## 5. 每個階段怎麼驗收

| 階段 | 驗收方式 |
|---|---|
| 0 | 抓包版 `03-call-test.sh` 在現有部署通過；Registration Accept 裡 IMS VoPS = 1 |
| 1 | `03-call-test.sh` 通過，抓包看到 AAR／AAA、STR／STA；`05-n5-qos-test.sh` 改用 Rx client 觸發也通過；AF shim 容器移除 |
| 2 | 通話時抓到 N2 PDU Session Resource Modify Request 與 Response |
| 3 | 通話中用 free-ran-ue 釋放 UE2 的 PDU session → 抓到 ASR → 兩支 UE 都收到 BYE |
| 4 | UE 註冊後抓到 AAR（信令）與對應的 app session；PCF 的位址由 BSF 查出 |

## 6. 風險

| 風險 | 影響 | 對策 |
|---|---|---|
| free-ran-ue 不支援 QoS flow 修改 | W5 無法完整驗證 | W6 先確認；必要時只驗 SMF 送出的訊息 |
| Flow-Description 上行寫法與 shim 不同（見 `rx-n5-adapter-explained.md` 第 6 節） | UPF 上行規則可能反向 | Phase 1 抓包看 PDR；必要時 Adapter 改寫 |
| `ims_qos` 送 IMPU 而非 IMSI | PCF 綁錯 UE | Adapter 從 IMPU 推 SUPI |
| SMF 修改要進上游 | 審查時間不可控 | 先在自己的 fork 完成並驗證 |
| NRF 開 OAuth 時 PCF → SMF scope 不一致（現有問題） | QoS 流程斷掉 | 維持 OAuth 關閉 |

## 7. 待決定

1. Adapter 的名稱
2. W5 是否以發 PR 回 `free5gc/smf` 為目標

## 8. 文件索引

| 文件 | 內容 |
|---|---|
| [rx-n5-adapter-explained.md](rx-n5-adapter-explained.md) | Adapter 要做什麼（用一通電話說明） |
| [rx-n5-adapter-design.md](rx-n5-adapter-design.md) | Adapter 怎麼寫（介面、結構、對應表、實作順序） |
| [vonr-ims-dev-process.md](vonr-ims-dev-process.md) | 開發流程與程式慣例 |
| [../current/free5gc-kamailio-integration.md](../current/free5gc-kamailio-integration.md) | 目前的五個對接點 |
| [../background/3gpp-ims-standards.md](../background/3gpp-ims-standards.md) | 相關 3GPP 規格 |
