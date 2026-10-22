# VoNR 計畫：讓 Kamailio IMS 正確接上 free5GC

> 狀態：草案（2026-10-22 整併：與現況文件合併到 `docs/overview/`，所有工作項都已有規格），只有計畫與規格，尚未實作
> 依據：free5gc 原始碼查證、`specs/3gpp-r17/` 規格、各規格組（`docs/rx-n5/`、`docs/smf-n1n2/`、`docs/hss-udm/`、`docs/e2e-harness/`）

## 0. 一頁摘要

**目標：** 一通 VoNR 電話從頭到尾符合標準：IMS 用標準 Rx 告訴 5GC 要多少資源，5GC 把語音 QoS flow 建到 UPF、gNB、UE，任何一邊斷線另一邊都知道。另外把 HSS 併入 free5gc UDM，IMS 與 5G 只用一份用戶資料、一個 SQN。

**工作項：**

| # | 工作 | 子階段 | 類型 | 規模 | 規格 |
|---|---|---|---|---|---|
| W1 | 端到端測試改成看抓包 | — | 改測試 | 小～中 | [e2e-harness](../e2e-harness/README.md) |
| W2 | AMF 宣告支援 IMS 語音 | — | 改設定 | 很小 | [w2-w7-checklists.md](w2-w7-checklists.md) |
| W3 | **Rx／N5 Adapter** | W3a 通話資源、W3b 5GC 回報、W3c 註冊時、W3d 通話中修改 | **新寫程式** | **大** | [rx-n5](../rx-n5/README.md) |
| W4 | Kamailio P-CSCF 改用 `ims_qos` | — | 改設定 | 小 | rx-n5 interface-spec §14 |
| W5 | **SMF 通知 gNB 與 UE** | W5a 新增與刪除、W5b 修改與延後同步、W5c 回報 PCF、W5d QoS notification control | **改 free5gc 程式** | **中～大** | [smf-n1n2](../smf-n1n2/README.md) |
| W6 | free-ran-ue 回應器 patch | — | 改 free-ran-ue | 小～中 | smf-n1n2 interface-spec §12 |
| W7 | 部署版本與查證版本一致 | — | 驗證 | 小 | [w2-w7-checklists.md](w2-w7-checklists.md) |
| W8 | **HSS 併入 UDM** | W8a 取代 PyHSS、W8b RTR／PPR | **改 free5gc 程式**（UDM、UDR） | **大** | [hss-udm](../hss-udm/README.md) |

**時程：** 約 12 週，分 7 個階段（第 4 節）。估計值，未含審查與 G1 查證的不確定性。

**不做：** 不讓 AMF／SMF 處理 SIP；不取代 Kamailio；不改 PCF、UPF；不做 N70（Kamailio 只支援 Cx）。計畫外的功能（IPsec、緊急通話、SMS 等）見 [vonr-3gpp-conformance.md](vonr-3gpp-conformance.md) §5。

**會改的元件：** SMF（W5）、UDM 與 UDR（W8）、free-ran-ue（W6）、Kamailio P-CSCF 設定（W4）。

**有條件的部分：** W3c 的 `n5` 模式與 W5d 的端到端，需要修改 free5gc PCF（與「不改 PCF」衝突），預設不做（第 7 節第 4 項）。

## 1. 設計原則

| 範圍 | 負責 |
|---|---|
| 5GC（free5GC） | UE 註冊、PDU session、QoS 控制、policy、user plane；**IMS 用戶資料與 IMS AKA（HSS 功能，實作在 UDM 裡）** |
| IMS（Kamailio） | SIP 註冊、SIP session 控制、呼叫路由、IMS session 狀態 |
| 語音媒體 | RTP 走 5GC 依 policy 建立的 QoS flow |

HSS 放進 UDM 是 TS 23.228 附錄 Y.0 允許的部署方式；規格要求 HSS 的 IMS 功能在邏輯上維持獨立，對 CSCF 的介面仍是 Cx。所以 UDM 裡的 HSS 是獨立的子系統，Kamailio 看到的仍是一個講 Cx 的 HSS。

## 2. 從現況到目標

現在的部署、測試實際驗證了什麼、缺口清單，見 [free5gc-kamailio-integration.md](free5gc-kamailio-integration.md)。那份的「缺口」表每一列都標了由哪個工作項處理；本文件只列工作項本身。

## 3. 工作項目

所有工作項的門檻採同一套格式：G0 基準（現況證據）→ G1 設計核對（關閉規格的待解問題）→ G2 元件（單元與整合測試）→ G3 整合（端到端）→ G4 交付。前一個門檻沒過不進下一個；G1 之前可以做原型，但不能宣稱相容。測試 ID 都指向該規格組的 test-plan。

### W1　端到端測試改成看抓包

- **做什麼：** `03-call-test.sh`、`05-n5-qos-test.sh` 改成從 host 的 `br-poc-core`、`br-poc-dn` 抓包與 UPF 規則快照判斷；SKIP、BLOCKED 不算 PASS
- **為什麼：** 現行測試真正影響判定的只有 sipp 退出碼、GTP-U 封包數、BYE 與 LIR 計數，而且依賴 log 字串；QoS 檢查 SKIP 時也會 PASS
- **完成條件：** 在**現有**部署上，e2e-harness §8.1 的檢查全部 PASS（e2e-harness T01–T15）
- **依賴：** 無。之後每個工作項的 G3 都用它驗收

### W2　AMF 宣告支援 IMS 語音

- **做什麼：** `config/amfcfg.yaml` 的 `configuration.nasIE.networkFeatureSupport5GS.imsVoPS` 改成 1
- **時機：** **W5 的 G3 通過之後才打開**（TS 23.501 §5.16.3.2：要有支援語音的 5G QoS flow 才能宣告）。Phase 0 只確認設定可用
- **完成條件：** e2e-harness CHK-W2-01（Registration Accept 中 IMS VoPS＝1）
- **已知限制：** AMF 送給 UDM 的 `ImsVoPs` 寫死成不支援，W2 改不到（[w2-w7-checklists.md](w2-w7-checklists.md) W2-4）

### W3　Rx／N5 Adapter

- **做什麼：** 新寫一個 free5gc 風格的 NF：對 Kamailio 是 Rx server，對 PCF 是 N5 client；PCF 的回呼轉回 Rx
- **規格：** [../rx-n5/](../rx-n5/README.md)（v0.6）

| 子階段 | 內容 | 完成條件 |
|---|---|---|
| W3a 通話資源 | AAR → Create、STR → Delete；NRF 註冊 | 搭配 W4：CHK-W3A-01～03 PASS；shim 移除 |
| W3b 5GC 回報 | terminate → Delete＋ASR；資源全部失效 → ASR，部分失效 → RAR（rx-n5 §8A） | 釋放被叫 PDU session 或 gNB 拒絕語音 QFI（W5c），通話都會結束（rx-n5 T43、T44） |
| W3c 註冊時 | 信令 session（off／local／n5，預設 local）、BSF 找 PCF（rx-n5 §8B） | `local`：註冊時的 AAR／AAA 成功，PCF 上沒有多出的規則（rx-n5 T58）；`n5` 需要 rx-n5 附錄 E 的 PCF／SMF 修改 |
| W3d 通話中修改 | re-INVITE：只改頻寬用 PATCH，其他 Delete 再 Create（rx-n5 §5.4、ADR-0009） | re-INVITE 前後沒有殘留規則（rx-n5 T48、T51） |

| 門檻 | W3a | W3b | W3c | W3d |
|---|---|---|---|---|
| G0 | 固定版本、manifest；用 shim 跑抓包版測試，確認 PCF 的 Create／Delete | 沿用 W3a 的 G0 | 沿用 | 沿用 |
| G1 | 關閉 rx-n5 D01～D09；用假的 Diameter peer 錄 Kamailio 的 AAR／STR | 關閉 D10、D11：抓 Kamailio 對 ASR、RAR 的反應 | 關閉 D13～D15：`Rx_AAR_Register` 的時機與內容；BSF 的 API | 關閉 D12：re-INVITE 時的 AAR |
| G2 | T01–T15、T19–T28 | T35–T42、T45 | T53–T57、T59–T62 | T46–T50、T52 |
| G3 | T16–T18、T29–T34（含 W4）；L1–L3 | T43、T44；L2b | T58；L2d | T51；L2c |
| G4 | README、設定範例、清理 runbook、切回 shim 的程序 | 同左（增補） | 同左 | 同左 |

- **依賴：** W1；W4（W3a 的 G3）；W5c（W3b 的 T44）

### W4　Kamailio P-CSCF 改用 `ims_qos`

- **做什麼：** 載入 `cdp`、`cdp_avp`、`ims_qos`；200 OK 時呼叫 `Rx_AAR`；刪掉 `AF_*` 路由與 `http_client`；W3c 時呼叫 `Rx_AAR_Register`、W3d 時 re-INVITE 沿用原 Rx session
- **規格：** rx-n5 interface-spec §14（REQ-KAM-01～11）、test-plan T30–T34
- **完成條件：** 在 W3a 的 G3 套用並通過 T30–T34
- **待決定：** AAR 失敗時 SIP 要繼續還是失敗（rx-n5 D09）

### W5　SMF 通知 gNB 與 UE

- **做什麼：** PCF 更新 policy 後，SMF 除了更新 UPF，還經 AMF 送 N1N2（TS 23.502 §4.3.3.2 步驟 3b），並處理回應、T3591、衝突
- **規格：** [../smf-n1n2/](../smf-n1n2/README.md)（v0.3）

| 子階段 | 內容 | 完成條件 |
|---|---|---|
| W5a 新增與刪除 | Modification Command 補 QoS rule、flow description，PTI 改「未指派」；N2 補釋放清單；由 PCC rule 差異推導要刪的 QoS flow | CHK-W5-01、02（smf-n1n2 T24） |
| W5b 修改與延後同步 | `QFD_Mod` 與 AddOrModify；UP 連線未啟動時不送，啟動後只送 N1 | smf-n1n2 T33、T36 |
| W5c 回報 PCF | RAN 拒絕或釋放語音 QFI 時送 ruleReports（INACTIVE）；處理 `PDU_RES_NTY` | CHK-W5-03（smf-n1n2 T32） |
| W5d QoS notification control | N2 帶 Notification Control；`qncReports` 回報 PCF | SMF 端：smf-n1n2 T38、T39；AF 端需要 PCF 修正（D13） |

| 門檻 | 內容 | 通過條件 |
|---|---|---|
| G0 | 用現行 SMF 跑一通電話：確認沒有 N1N2、通話後 QoS flow／QFI 是否殘留（D03） | smf-n1n2 T26 |
| G1 | 取得並核對 TS 38.413、29.502、29.518、29.512（D02、D10、D11）；關閉 D04～D07、D12 | interface-spec §2、§10 的核對欄填完 |
| G2 | 依序：同步狀態 → 差異計算 → N1／N2 builder → 程序狀態機 → T3591 → 衝突與排隊 → W5c → W5b → W5d → free-ran-ue patch（W6） | T01–T22、T25、T27–T31、T33–T38、T41、T42 |
| G3 | 自己 build 的 SMF、patch 過的 free-ran-ue；T3591 重送改 4 次 | T23、T24、T32、T36、T39；L1–L3、L3c、L3d |
| G4 | 設定範例、已知限制；決定 D08、D09 | 完成定義 |

- **依賴：** W6；W3a（PCF 才會真的發出新增與刪除；G2 之前可以直接打 N5 觸發）；W3b（L3c）

### W6　free-ran-ue 回應器

- **結論：** free-ran-ue v2.5.0 不處理 PDU Session Resource Modify Request，UE 不處理 Modification Command（原始碼）。已決定 patch（smf-n1n2 ADR-0005，已接受）
- **做什麼：** 照 `ran/pcscf-discovery.patch` 的方式再加一個 patch：gNB 轉 NAS 並回 Modify Response；UE 解 Command 並回 Complete；故障注入（a）～（f）；可能的話支援 CM-IDLE 與 Service Request（D12）
- **規格：** smf-n1n2 interface-spec §12（REQ-RAN-01～08）
- **完成條件：** smf-n1n2 T21–T23、T42
- **依賴：** 無；是否送回上游待決定（smf-n1n2 D08）

### W7　部署版本與查證版本一致

- **做什麼：** 逐項比對 [w2-w7-checklists.md](w2-w7-checklists.md) 的 W7-1～W7-11（用 `git diff <v4.2.3 釘的版本>..HEAD` 比對函式，加上抓包佐證），並先處理 W7-A～C（鎖定 Kamailio 小版本、記錄映像 digest、決定 fork 的基礎版本）
- **完成條件：** 每一項都有結論；有差異時更新對應規格
- **依賴：** 無；W5、W8 的 G0 需要 W7-C 的結論

### W8　HSS 併入 UDM

- **做什麼：** 在 free5gc UDM 裡實作 HSS 的 Cx，I-CSCF、S-CSCF 改連 UDM；IMS 資料與註冊狀態存在 UDR 的非標準擴充；IMS AKA 與 5G-AKA 共用 K／OPc／SQN（原子取號）；移除 PyHSS
- **規格：** [../hss-udm/](../hss-udm/README.md)（v0.3）

| 子階段 | 內容 | 完成條件 |
|---|---|---|
| W8a 取代 PyHSS | UDR 擴充、Cx server、UAR／LIR／MAR／SAR、User-Data、開戶腳本 | CHK-W8-01、02；USIM 模型與並行取號測試（hss-udm T13、T14） |
| W8b HSS 主動通知 | RTR、PPR（hss-udm §8A） | CHK-W8-03（hss-udm T43） |

| 門檻 | W8a | W8b |
|---|---|---|
| G0 | 在現有 PyHSS 部署抓 Cx 樣本（D03）；manifest（D01） | 沿用 |
| G1 | 關閉 D02、D04～D10、D13、D14；用 stub HSS 驗證 I-CSCF 能吃「只有 Server-Capabilities」的 UAA | 關閉 D15、D16：RTR／PPR 走哪條連線、Kamailio 是否處理 |
| G2 | T01–T25、T29–T34 | T35–T42 |
| G3 | T26–T28；L1–L4 | T43、T44；L6 |
| G4 | README、清理 runbook、切回 PyHSS 的程序；決定 D11 | 同左（增補） |

- **依賴：** W1；W7（D01）
- **交付：** 自己的 fork，不以發 PR 為目標

## 4. 時程

```
週   1   2   3   4   5   6   7   8   9   10  11  12
W1  ████
W7  ████
W6  ████    ████████                          （結論在第 1 週；patch 在第 3–4 週）
W3a     ████████
W4              ████
W5a     ████████████████
W3b                 ████████
W5c                 ████████
W2                      ████                  （W5 的 G3 之後才打開）
W3c                         ████
W3d                         ████████
W5b                         ████████
W5d                                 ████████
W8a                 ████████████████████████
W8b                                         ████████
```

| 階段 | 包含 | 完成時能證明什麼 |
|---|---|---|
| Phase 0（第 1 週） | W1、W7、W6 的結論、W2 的設定準備 | 測試不依賴實作；版本差距都有結論 |
| Phase 1（第 2–4 週） | W3a、W4 | 用標準 Rx 預留通話資源，shim 退役 |
| Phase 2（第 2–5 週，平行） | W5a、W6 的 patch | 語音 QoS flow 到達 gNB 與 UE（在 patch 過的 free-ran-ue 上） |
| Phase 3（第 5–6 週） | W3b、W5c、W2 打開 | 5GC 斷線或資源失效時 IMS 會結束通話；網路宣告支援 IMS 語音 |
| Phase 4（第 7–8 週） | W3c（local）、W3d、W5b | 註冊時的 AAR 不再被拒；通話中修改不留殘留規則；QoS 修改能同步到 UE |
| Phase 5（第 9–10 週） | W5d | SMF 回報 QoS notification（AF 端依 PCF 是否修正） |
| Phase 6（第 5–12 週，平行） | W8a、W8b | PyHSS 退役；一份用戶資料與 SQN；HSS 能主動解除註冊 |

## 5. 每個階段怎麼驗收

檢查 ID（CHK-*）定義在 [e2e-harness interface-spec](../e2e-harness/interface-spec.md) §8。

| 階段 | 驗收方式 |
|---|---|
| 0 | 現有部署上 CHK-PRE、REG、CX、SIP、RTP、UPF、AF 全部 PASS；W7-1～W7-11 都有結論 |
| 1 | CHK-W3A-01～03 PASS；rx-n5 L1–L3 PASS；AF shim 容器移除 |
| 2 | CHK-W5-01、02 PASS；smf-n1n2 L1–L3 PASS |
| 3 | rx-n5 T43、T44 與 smf-n1n2 T32：釋放被叫 PDU session、gNB 拒絕 QFI 時，兩支 UE 都收到 BYE；CHK-W2-01 PASS |
| 4 | CHK-W3C-01、CHK-W3D-01、CHK-W5-04 PASS；PCF 上沒有註冊造成的多餘規則 |
| 5 | CHK-W5-05 PASS（SMF 端）；AF 端在 PCF 未修正時標 BLOCKED |
| 6 | CHK-W8-01～03 PASS；hss-udm T13、T14（SQN 正確性，因為實驗 UE 不檢查 SQN 新鮮度） |

## 6. 風險

前幾項是「設計前提可能不成立」的風險，都要在各自的 G1 驗證。

| 風險 | 影響 | 對策 | 何時驗證 |
|---|---|---|---|
| **Kamailio 6.1.x 的行為沒有原始碼可查**：收到 ASR 是否結束 dialog 並送 STR（rx-n5 D10）、I-CSCF 能否吃只有 capabilities 的 UAA（hss-udm D04）、S-CSCF 是否處理 RTR／PPR（hss-udm D16）、`Rx_AAR_Register` 的時機（rx-n5 D15）、re-INVITE 的 AAR（rx-n5 D12） | W3b、W8a、W8b、W3c、W3d 的設計可能要改 | 各自的 G1 用 stub 抓包 | G1 |
| **free5gc PCF 的限制**：PATCH 只在 flow 不變時安全；全部失效只送事件不送 terminate；QOS_NOTIF 缺 `qncReports`；不依 TS 29.513 Table 7.3.2-1 給 GBR；照規格做 W3c 會讓 SMF 的 policy 更新全部失敗 | 各規格都已設計繞道；W3c `n5` 與 W5d 端到端需要修 PCF | 繞道見 rx-n5 ADR-0008～0010、smf-n1n2 ADR-0010；修不修見第 7 節 | G1 |
| free5gc AMF 在 Service Request 後丟掉 `PDU_RES_MOD_REQ` | UE 閒置時的修改會遺失 | UP 啟動後只送 N1（smf-n1n2 ADR-0009） | G2 |
| PCF 刪除通知不帶 QosDecs，SMF 不釋放 QoS flow（原始碼推論） | 刪除不會被觸發 | SMF 由 PCC rule 差異推導（smf-n1n2 ADR-0002）；G0 實測 | G0 |
| 部署版本與查證版本差距大（AMF 51、SMF 48 個 commit）；Kamailio 沒鎖版本 | 查證結論在部署上不成立 | W7；鎖定 Kamailio 小版本 | Phase 0 |
| 實驗 UE 不檢查 SQN 新鮮度 | 端到端證明不了 SQN 共用是對的 | USIM 模型單元測試（hss-udm T13） | G2 |
| Flow-Description 上行寫法與 shim 不同（rx-n5 D05） | UPF 上行規則可能反向 | 抓包看 PDR；必要時 Adapter 改寫 | G1 |
| `ims_qos` 送 IMPU 而非 IMSI | PCF 綁錯 UE | Adapter 查明確的身分對應（rx-n5 REQ-AAR-03；W8 後可用 hss-udm 的索引） | G1 |
| 三個 free5gc fork（SMF、UDM、UDR）的維護 | 升版要 rebase | 改動集中在獨立套件；W7-C 統一基礎版本 | 持續 |
| NRF 開 OAuth 時 PCF → SMF scope 不一致（現有問題） | QoS 流程斷掉 | 維持 OAuth 關閉（各規格的實驗 profile） | — |

## 7. 待決定

| # | 事項 | 影響範圍 | 出處 |
|---|---|---|---|
| 1 | 各規格組的 ADR 是否接受：rx-n5 0001～0011、smf-n1n2 0001～0010（0005 已接受）、hss-udm 0001～0010、e2e-harness 0001～0002 | 全部 | 各組 README |
| 2 | 要實作哪些子階段（規格都已寫好，之後再刪減）：W3c、W3d、W5b、W5d、W8b | 時程 | 本文件第 3 節 |
| 3 | W5、W8 要 fork 的 free5gc 版本：沿用部署的 4.2.3，或一起升到 v4.3.0 | W5、W8 | W7-C；各組 D01 |
| 4 | 是否修改 free5gc PCF（解鎖 W3c `n5` 模式、W5d 端到端、GBR 推導），與「不改 PCF」衝突 | W3c、W5d、W5a | rx-n5 附錄 E、smf-n1n2 附錄 D、D04、D13 |
| 5 | Kamailio 是否鎖定小版本 | 全部 | W7-A |
| 6 | AAR 失敗時 P-CSCF 的 SIP 處理 | W4 | rx-n5 D09 |
| 7 | W5 是否發 PR 回 `free5gc/smf`；free-ran-ue patch 是否送回上游 | W5、W6 | smf-n1n2 D08、D09 |
| 8 | Adapter 的名稱 | W3 | — |

## 8. 文件索引

| 文件 | 內容 |
|---|---|
| [free5gc-kamailio-integration.md](free5gc-kamailio-integration.md) | 現況：五個對接點、測試實際驗證了什麼、缺口 |
| [vonr-3gpp-conformance.md](vonr-3gpp-conformance.md) | 端到端完整性與逐條 3GPP 對照；計畫外的待選項目 |
| [w2-w7-checklists.md](w2-w7-checklists.md) | W2、W7 檢查清單與版本差距 |
| [vonr-ims-dev-process.md](vonr-ims-dev-process.md) | 開發流程與程式慣例 |
| [../e2e-harness/](../e2e-harness/README.md) | W1：抓包版端到端測試 |
| [../rx-n5/](../rx-n5/README.md) | W3、W4：Rx／N5 Adapter |
| [../smf-n1n2/](../smf-n1n2/README.md) | W5、W6：SMF 的 N1／N2 與 free-ran-ue 回應器 |
| [../hss-udm/](../hss-udm/README.md) | W8：HSS 併入 UDM |
| [../background/3gpp-ims-standards.md](../background/3gpp-ims-standards.md) | 相關 3GPP 規格 |
| [../background/ims-af-thesis-comparison.md](../background/ims-af-thesis-comparison.md) | 2024 年碩論的 IMS-AF 與本計畫的差異 |
