# SMF 網路發起的 QoS flow 修改介面規格（W5a＋W5b＋W5c＋W5d＋W6）

| 項目 | 內容 |
|---|---|
| 版本／狀態 | v0.3／審查中（2026-10-22：v0.3 新增 §8B 修改與延後同步（W5b）、§8C QoS notification control（W5d）；v0.2 新增 §8A 回報 PCF（W5c）） |
| 適用範圍 | W5a（通知 RAN／UE）、W5b（修改與延後同步）、W5c（回報 PCF）、W5d（QoS notification control）與 W6（free-ran-ue 回應器）；alternative QoS 只列在附錄 C |
| 設計理由 | [design.md](design.md)、[adr/](adr/) |
| 驗證方式 | [test-plan.md](test-plan.md)（每條需求對應的測試見該文件 §2） |

## 1. 範圍與用語

### 1.1 範圍

本規格定義 free5gc SMF（fork）在收到 PCF 的 SM policy 更新後，執行網路發起 PDU Session Modification 的行為：觸發條件、N1 與 N2 內容、N1N2 傳送、回應處理、程序狀態、計時器與衝突；以及實驗用 free-ran-ue 的最小回應行為。

部署 profile：單一 PDU session（`ims` DNN、IPv4）；3GPP access；UE 在通話期間為 CM-CONNECTED；新增或刪除的都是非預設 QoS flow。

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
| 程序 | 一次網路發起的 PDU Session Modification（TS 23.502 §4.3.3.2 步驟 3b～11） |
| 程序序號 | SMF 為每個程序配的遞增編號，用來辨認晚到的回應 |
| 差異 | 這次要新增（TO_ADD）與刪除（TO_DELETE）的 QoS flow 集合 |
| 同步狀態 | design §5.2 的 TO_ADD、ADDING、SYNCED、TO_DELETE、DELETING、TO_SYNC |
| N1 | PDU SESSION MODIFICATION COMMAND（TS 24.501 §8.3.9） |
| N2 | PDU Session Resource Modify Request Transfer（TS 38.413） |
| N1N2 | Namf_Communication_N1N2MessageTransfer |
| Complete、Reject | PDU SESSION MODIFICATION COMPLETE、PDU SESSION MODIFICATION COMMAND REJECT |

## 2. 參考文件

### 2.1 規範性參考

| 文件 | 本規格用到的部分 | 版本 | 核對狀態 |
|---|---|---|---|
| 3GPP TS 23.502 | §4.3.3.2 步驟 1b、2a、3b、4～11 | V17.15.0（2025-12） | 已讀 |
| 3GPP TS 24.501 | §6.3.2.2 網路發起修改的啟動（QoS rule、flow description、PTI）、§6.3.2.3、§6.3.2.4、§6.3.2.5 網路端異常（T3591、衝突）；§8.3.9 訊息定義 | V17.18（檔名 24501-hi1） | §6.3.2.2、§6.3.2.5 已讀；§8.3.9 只讀了 IE 目錄；§9.11.4.12、§9.11.4.13 編碼未讀（由 `free5gc/nas` v1.3.0 實作） |
| 3GPP TS 38.413 | PDU Session Resource Modify Request／Response、QosFlowAddOrModifyRequestList、QosFlowToReleaseList | — | **本機沒有**，D02 |
| 3GPP TS 29.518 | N1N2MessageTransfer 與 cause | — | **本機沒有**，D02 |
| 3GPP TS 29.502 | Nsmf_PDUSession_UpdateSMContext 的 n2SmInfoType | — | **本機沒有**，D02 |
| 3GPP TS 23.501 | §5.7 QoS 模型（GBR、QFI） | V17.15（檔名 23501-hf0） | 未核對 |

### 2.2 參考資料

free5gc SMF v1.4.6、AMF、PCF v1.4.5 原始碼；`free5gc/nas` v1.3.0、`free5gc/ngap` v1.2.0；free-ran-ue v2.5.0（本機 v2.5.0-26）；`kamailio-free5gc/config/smfcfg.yaml`。

## 3. 總則

- **REQ-GEN-01** 功能**必須**能以 `networkInitiatedModification.enable` 關閉；關閉時 `HandleSMPolicyUpdateNotify` 的對外行為**必須**與上游相同（不送 N1N2）。
- **REQ-GEN-02** UE 發起的修改流程（`PDUSessModReq` 分支）的行為**不得**改變，只允許共用 builder 的重構。
- **REQ-GEN-03** 本程序**不得**修改預設 QoS rule、預設 QoS flow 與 Session-AMBR。
- **REQ-GEN-04** `w5b.enable` 為 false 時，既有 QoS flow 的參數修改**不得**被當成成功送出；**必須**記錄並略過。為 true 時依 §8B。

## 4. 觸發與差異

- **REQ-TRIG-01** `HandleSMPolicyUpdateNotify` 在 `ApplyPccRules` 與 PFCP 修改都成功之後，**必須**計算差異：
  - TO_ADD：有 QFI、被 PCC rule 參照、尚未同步給 RAN／UE 的 QoS flow；
  - TO_DELETE：已同步（SYNCED 或 ADDING）、但不再被任何 PCC rule 參照的 QoS flow。
  
  **不得**只依賴 decision 裡 QosDecs 為 nil 才判斷刪除（[ADR-0002](adr/0002-derive-qos-flow-diff-from-pcc-rules.md)）。
- **REQ-TRIG-02** PFCP 修改失敗時，**不得**送 N1N2；本次差異**不得**改變同步狀態。
- **REQ-TRIG-03** TO_DELETE 的 QFI **必須**等到刪除它的程序結束（完成或中止）才釋放；在那之前**不得**配給別的 QoS flow。
- **REQ-TRIG-04** 差異為空時**不得**送 N1N2。
- **REQ-TRIG-05** 對 PCF 的回應（204）**不得**等待 N1N2 或 UE 回應。

## 5. N1：PDU SESSION MODIFICATION COMMAND

- **REQ-N1-01** PTI **必須**設為「No procedure transaction identity assigned」（TS 24.501 §6.3.2.2）（[ADR-0006](adr/0006-pti-unassigned-for-network-initiated.md)）。
- **REQ-N1-02** Authorized QoS rules：每個 TO_ADD flow 的每條 PCC rule，**必須**有一條「create new QoS rule」，packet filter 由 PCC rule 的 flow information 產生（`PCCRule.BuildNasQoSRule`），QoS rule ID **必須**新配並記在 `PCCRuleIDToQoSRuleID`；每個 TO_DELETE flow 的 QoS rule **必須**有一條「delete existing QoS rule」（`OpCode_DelExistingQosRule`），用原本的 QoS rule ID。
- **REQ-N1-03** Authorized QoS flow descriptions：TO_ADD **必須**有「create new」描述，含 5QI；GBR flow **必須**含 GFBR 與 MFBR（上下行）（TS 24.501 §6.3.2.2 條件 a）；TO_DELETE **必須**有「delete」描述（`QFD_Del`）。
- **REQ-N1-04** **不得**帶 Session-AMBR、mapped EPS bearer contexts 或預設 QoS rule。
- **REQ-N1-05** 送出後 PDU session 上的 packet filter 總數**不得**超過 UE 能支援的最大值（TS 24.501 §6.3.2.2）；上限的取得方式依 D06。超過時**必須**中止這次差異並記錄。

## 6. N2：PDU Session Resource Modify Request Transfer

- **REQ-N2-01** TO_ADD **必須**放進 QosFlowAddOrModifyRequestList，含 QFI 與 QoS flow level 參數（5QI、ARP）；沿用 `BuildNgapQosFlowAddOrModifyRequestItem`。
- **REQ-N2-02** GBR flow **必須**帶 GBR QoS information（GFBR、MFBR 上下行）。PCF 沒給 GbrUl／GbrDl 時依 D04；D04 關閉前**不得**送出 GFBR 為 0 的 GBR flow，**必須**中止這次差異並記錄。
- **REQ-N2-03** TO_DELETE **必須**放進 QosFlowToReleaseList，cause 依 D07（候選）。
- **REQ-N2-04** 差異只有刪除時，QosFlowAddOrModifyRequestList **不得**出現；只有新增時，QosFlowToReleaseList **不得**出現。

## 7. N1N2 傳送

- **REQ-XFER-01** **必須**以一次 Namf_Communication_N1N2MessageTransfer 同時帶 N1（N1MessageClass `SM`）與 N2（ngapIeType `PDU_RES_MOD_REQ`）及 PDU session ID。
- **REQ-XFER-02** 回應 cause 的處理（cause 名稱依 free5gc models；TS 29.518 待 D02 核對）：
  - `N1_N2_TRANSFER_INITIATED`：差異的同步狀態改為 ADDING／DELETING，啟動 T3591，程序進入 PENDING；
  - `ATTEMPTING_TO_REACH_UE`：**必須**視為沒有送達，差異改為 TO_SYNC，等 UP 連線重新啟動後依 §8B 同步。理由：free5gc AMF 會 paging，但 UE 做 Service Request 時只會轉送 `PDU_RES_SETUP_REQ` 類型的 N2，`PDU_RES_MOD_REQ` 的 N1 與 N2 都會被丟掉（`amf/internal/gmm/handler.go` `HandleServiceRequest`）；
  - `N1_MSG_NOT_TRANSFERRED`、HTTP 錯誤、逾時：中止，TO_ADD／TO_DELETE 改為 TO_SYNC，**不得**啟動 T3591。
- **REQ-XFER-03** 等待 AMF 的 HTTP 回應時，**不得**持有該 SM context 的 `SMLock`。

## 8. 回應處理

- **REQ-RSP-01** 收到 `PDU_RES_MOD_RSP`：QosFlowAddOrModifyResponseList 裡的 QFI 記為 RAN 成功；QosFlowFailedToAddOrModifyList 裡的 QFI 記為 RAN 失敗；釋放清單的回應記為 RAN 已刪。
- **REQ-RSP-02** 收到 Complete：停止 T3591。N2 回應與 Complete 都到齊時程序完成：RAN 成功的新增 → SYNCED；刪除 → 移除 flow 並釋放 QFI；RAN 失敗的新增 → TO_SYNC。
- **REQ-RSP-03** 程序完成後若有 TO_SYNC（RAN 拒絕的 QFI），SMF **必須**再發起一次程序，把對應的 QoS rule 與 flow description 從 UE 刪除（TS 23.502 §4.3.3.2 步驟 7）。
- **REQ-RSP-04** 回應**必須**以程序序號比對；不屬於目前程序的回應**不得**改變狀態，只記錄。
- **REQ-RSP-05** 收到 Reject：停止 T3591，程序中止，差異改為 TO_SYNC（TS 24.501 §6.3.2.4、§6.3.2.5）。

## 8A. 回報 PCF（W5c）

依據：TS 23.502 V17.15.0 §4.3.3.2 步驟 1e（RAN 釋放 QoS flow 時經 AMF 通知 SMF）與步驟 2（SMF 向 PCF 回報）；TS 29.514 V17.9.0 §4.2.5.5（PCF 據此通知 AF）。ruleReports 的語意依 TS 29.512，本機沒有，D10。設計理由見 [ADR-0007](adr/0007-report-inactive-rules-to-pcf.md)。

- **REQ-RPT-01** 程序完成時，RAN 新增失敗的 QFI（REQ-RSP-01 的失敗清單）：SMF **必須**送 Npcf_SMPolicyControl_Update，`ruleReports` 帶對應 QFI 的所有 PCC rule ID、`ruleStatus` INACTIVE、`failureCode` RES_ALLO_FAIL（候選，D10）。
- **REQ-RPT-02** **必須**處理 AMF 轉來的 `PDU_RES_NTY`（PDU Session Resource Notify Transfer）。其中 RAN 已釋放的 QFI：依 REQ-RPT-01 回報 PCF（`failureCode` 候選同上）；QFI 標為 TO_DELETE。
- **REQ-RPT-03** 因 REQ-RPT-02 而刪除的 QFI，後續程序**必須**只送 N1（刪除 QoS rule 與 flow description），**不得**再把它放進 N2 的 QosFlowToReleaseList（RAN 已經釋放）。
- **REQ-RPT-04** 送出回報後，SMF **必須**自行移除那些 PCC rule 與對應的 UPF 規則。free5gc PCF 收到 INACTIVE 時用 `RemovePccRule(pccRuleID, nil)` 刪除 PCC rule，**不會**再送通知給 SMF。
- **REQ-RPT-05** 因 PCF 的 policy 更新而刪除的 QoS flow（REQ-TRIG-01 的 TO_DELETE）**不得**回報為 INACTIVE。
- **REQ-RPT-06** 回報失敗（HTTP 錯誤、逾時）時，**必須**依 `reportToPcf.retry` 重試，用完告警；**不得**因此回退 REQ-RPT-04 的本地移除。
- **REQ-RPT-07** `reportToPcf.enable` 為 false 時，**不得**送回報，也**不得**做 REQ-RPT-04 的移除（行為同 W5a）。

## 8B. QoS flow 修改與延後同步（W5b）

本節在 `w5b.enable` 為 true 時適用；為 false 時依 REQ-GEN-04 略過修改。依據：TS 24.501 V17.18 §6.3.2.2、§9.11.4.12（QoS flow description 操作碼：001 create、010 delete、011 modify）、§9.11.4.13（QoS rule 操作碼：011～110 為四種 modify）；TS 23.502 V17.15.0 §4.3.3.2 步驟 1d、§4.2.3.2。設計理由見 [ADR-0008](adr/0008-track-synced-snapshot.md)、[ADR-0009](adr/0009-defer-until-up-active.md)。

### 8B.1 修改

- **REQ-MOD-01** SMF **必須**為每個已同步的 QFI 保存「最後同步給 RAN／UE 的內容」：5QI、ARP、GFBR、MFBR（上下行）、每條 QoS rule 的 packet filter 與 precedence。理由：free5gc 的 `ApplyPccRules` 修改規則時會用 `AddQosFlow` 把 QoS flow 重建成 `QoSFlowUnset`，`QoSFlowToBeModify` 從未被指派，SMF 本身分不出「新增」與「修改」。
- **REQ-MOD-02** 差異計算**必須**多一類 TO_MODIFY：QFI 不變、已同步，但與 REQ-MOD-01 的內容不同。QFI 改變（例如 rx-n5 ADR-0009 的 Delete＋Create）**必須**視為刪除舊 QFI＋新增新 QFI，不是修改。
- **REQ-MOD-03** N1：QoS 參數改變時，Authorized QoS flow descriptions **必須**帶 `QFD_Mod`，E bit 為 1（取代全部參數）並帶完整參數；packet filter 改變時，Authorized QoS rules **必須**用「modify existing QoS rule and replace all packet filters」（`OpCode_ModifyReplaceAllPktFilters`）；packet filter 沒變時**不得**送該 QoS rule。
- **REQ-MOD-04** N2：TO_MODIFY 的 QFI **必須**放進 QosFlowAddOrModifyRequestList，帶新的 QoS 參數。
- **REQ-MOD-05** RAN 對修改回失敗時，該 QFI 標 TO_SYNC，並依 REQ-RPT-01 回報 PCF。
- **REQ-MOD-06** 修改成功（N2 回應＋Complete）後，**必須**更新 REQ-MOD-01 的內容。

### 8B.2 延後同步

- **REQ-SYNC-01** 要發起程序時，PDU session 的 UP 連線不是 ACTIVATED（`UpCnxState`）時，**不得**送 N1N2；差異**必須**標為 TO_SYNC。理由同 REQ-XFER-02：free5gc AMF 在 Service Request 之後會丟掉 `PDU_RES_MOD_REQ`。
- **REQ-SYNC-02** UP 連線重新啟動、處理完 PDU Session Resource Setup Response 之後，如果有 TO_SYNC 項目，SMF **必須**發起一個只帶 N1 的程序（N1N2 不帶 N2），把 TO_SYNC 的 QoS rule 與 flow description 同步給 UE。RAN 端不需要另外送：Setup Request Transfer 已經帶了全部 `AdditionalQosFlows` 與最新參數（`ngap_build.go` `BuildPDUSessionResourceSetupRequestTransfer`）。
- **REQ-SYNC-03** TS 23.502 §4.3.3.2 步驟 1d 只為「刪除未同步」定義了這個機制；新增與修改的延後同步是本規格的延伸，**必須**在 log 中標明程序的原因（`deferred-sync`）。
- **REQ-SYNC-04** Setup Response 中 RAN 拒絕的 QFI **必須**依 W5c 處理（回報 PCF、從 UE 刪除），對應 TS 23.502 §4.2.3.2 Service Request 結束後的修正。

## 8C. QoS notification control（W5d）

本節在 `w5d.enable` 為 true 時適用。依據：TS 23.501 V17.15.0 §5.7.2.4.1、§5.7.2.4.1a；TS 23.502 V17.15.0 §4.3.3.2 步驟 1e（AN initiated notification control）與步驟 2；TS 29.514 V17.9.0 §4.2.5.4。設計理由見 [ADR-0010](adr/0010-qnc-needs-pcf-fix.md)。

- **REQ-QNC-01** PCC rule 的 QosData `qnc` 為 true 且為 GBR flow 時，N2 的 GBR QoS information **必須**帶 Notification Control＝notification requested（`free5gc/ngap` v1.2.0 `GBRQosInformation.NotificationControl`）；Setup 與 Modify 兩條路徑都要。`qnc` 為 false 時**不得**帶（TS 23.501 §5.7.2.4.1：只在 PCC rule 設定時才啟用）。
- **REQ-QNC-02** `PDU_RES_NTY` 的 QosFlowNotifyList：NotificationCause「not fulfilled」對應 `NOT_GUARANTEED`、「fulfilled」對應 `GUARANTEED`；以 QFI 找出對應的 PCC rule ID。
- **REQ-QNC-03** PCF 在 policy decision 中下了 `QOS_NOTIF` trigger 時，SMF **必須**送 SMPolicyControl_Update：`repPolicyCtrlReqTriggers` 含 `QOS_NOTIF`，`qncReports` 帶 `refPccRuleIds` 與 `notifType`；沒有下 trigger 時**不得**送。
- **REQ-QNC-04** 收到 not fulfilled 時，SMF **不得**因此釋放該 QoS flow（TS 23.501 §5.7.2.4.1a：RAN 保留 QoS flow）。
- **REQ-QNC-05** `PDU_RES_NTY` 同時帶 QosFlowReleasedList 時，被釋放的部分依 REQ-RPT-02 處理。

## 9. 程序狀態與並行

### 9.1 紀錄欄位

| 欄位 | 用途 |
|---|---|
| `procState` | IDLE／PENDING |
| `procSeq` | 程序序號（REQ-RSP-04） |
| `inFlight` | 這個程序送出的新增與刪除（QFI、QoS rule ID） |
| `n2Done`、`n1Done` | 兩種回應是否到齊 |
| `t3591Count` | 已逾時次數 |
| `queued` | PENDING 期間累積的差異 |
| 每個 QoS flow 的同步狀態 | design §5.2 |

### 9.2 狀態轉移表

「—」表示該事件在該狀態不會發生，或直接忽略並記錄。

| 目前狀態 | 事件 | 動作 | 下一狀態 |
|---|---|---|---|
| IDLE | policy 更新，PFCP 失敗 | 不送 N1N2（REQ-TRIG-02） | IDLE |
| IDLE | policy 更新，差異為空、沒有 TO_SYNC | 無 | IDLE |
| IDLE | policy 更新，有差異或有 TO_SYNC | 組 N1、N2（含 TO_SYNC 項目），送 N1N2 | 依 N1N2 回應 |
| IDLE | N1N2 回 `N1_N2_TRANSFER_INITIATED` | 標 ADDING／DELETING，啟動 T3591，`procSeq`＋1 | PENDING |
| IDLE | N1N2 回 `ATTEMPTING_TO_REACH_UE` | 差異改為 TO_SYNC；等 UP 連線啟動後同步（§8B） | IDLE |
| IDLE | N1N2 回 `N1_MSG_NOT_TRANSFERRED`、HTTP 錯誤或逾時 | 差異改為 TO_SYNC | IDLE |
| IDLE | 收到不屬於任何程序的 N2 回應或 Complete | 記錄（REQ-RSP-04） | IDLE |
| PENDING | policy 更新 | 照常套用 PCC rule 與 PFCP；差異合併進 `queued`，不送 N1N2 | PENDING |
| PENDING | `PDU_RES_MOD_RSP`（序號相符） | 依 REQ-RSP-01 記錄；`n2Done`；若 `n1Done` 也到則完成 | PENDING 或 IDLE |
| PENDING | Complete（序號相符） | 停 T3591；`n1Done`；若 `n2Done` 也到則完成 | PENDING 或 IDLE |
| PENDING | 完成 | 依 REQ-RSP-02 更新；有 `queued` 或 TO_SYNC 就立刻開始下一個程序 | IDLE（或下一個 PENDING） |
| PENDING | Reject | 停 T3591；`inFlight` 改為 TO_SYNC；處理 `queued` | IDLE |
| PENDING | T3591 逾時，第 1～4 次 | 重送同一個 N1（N2 是否再帶依 D05）；`t3591Count`＋1 | PENDING |
| PENDING | T3591 第 5 次逾時 | 中止；`inFlight` 改為 TO_SYNC；UPF 規則保留；告警 | IDLE |
| PENDING | UE 要求釋放 PDU session | 中止程序（TS 24.501 §6.3.2.5 c）；停 T3591；進入現有的釋放流程 | （session 釋放） |
| PENDING | UE 要求修改 PDU session | 忽略該請求（§6.3.2.5 d），記錄 | PENDING |
| PENDING | 網路發起的 PDU session 釋放 | 中止程序；停 T3591；進入釋放流程 | （session 釋放） |
| PENDING | 序號不符的回應 | 記錄（REQ-RSP-04） | PENDING |
| PENDING | 完成，N2 回應有失敗的新增 QFI | 依 REQ-RSP-02、03 處理；另依 REQ-RPT-01 回報 PCF、REQ-RPT-04 移除規則 | IDLE（或下一個 PENDING） |
| IDLE | `PDU_RES_NTY`：RAN 釋放 QFI | 依 REQ-RPT-02、04 回報並移除；QFI 標 TO_DELETE，開始只送 N1 的程序（REQ-RPT-03） | PENDING |
| PENDING | `PDU_RES_NTY`：RAN 釋放 QFI | 依 REQ-RPT-02、04 回報並移除；刪除排進 `queued` | PENDING |
| 任何 | 回報 PCF 失敗 | 依 REQ-RPT-06 重試 | 不變 |
| IDLE | policy 更新有差異，但 UP 連線不是 ACTIVATED（W5b） | 不送 N1N2；差異標 TO_SYNC | IDLE |
| IDLE | UP 連線啟動完成且有 TO_SYNC（W5b） | 送只帶 N1 的程序（REQ-SYNC-02） | PENDING |
| PENDING（只帶 N1） | Complete | 停 T3591；TO_SYNC 項目改 SYNCED | IDLE |
| 任何 | `PDU_RES_NTY`：QosFlowNotifyList（W5d） | 依 REQ-QNC-02、03 回報 PCF；不改 QoS flow | 不變 |
| 任何 | SMF 重啟 | SM context 只在記憶體，全部遺失（非目標） | — |

### 9.3 並行

- **REQ-ST-01** 每個 PDU session 同時**必須**最多一個程序；PENDING 期間的差異**必須**排隊合併，程序結束後再送（[ADR-0003](adr/0003-one-procedure-per-session.md)）。
- **REQ-ST-02** 合併規則：同一個 QFI 先新增後刪除，若新增尚未送出則兩者抵銷；若新增已在 `inFlight`，刪除**必須**留在 `queued`，等新增完成後再送（design §5.4 的競態）。
- **REQ-ST-03** 同一個 SM context 的狀態變更**必須**在 `SMLock` 內完成；跨網路等待時**不得**持有它（REQ-XFER-03）。
- **REQ-ST-04** T3591 **必須**依 §9.2 處理：第 1～4 次逾時重送同一個 N1，第 5 次逾時中止程序、把 `inFlight` 標為 TO_SYNC、保留 UPF 規則（TS 24.501 §6.3.2.5 a；中止後沿用新設定的理由見 [ADR-0004](adr/0004-keep-upf-rules-on-abort.md)）。
- **REQ-ST-05** 衝突**必須**依 §9.2 處理：PENDING 期間 UE 或網路要求釋放 PDU session 時中止程序並改走釋放；UE 要求修改時忽略該請求（TS 24.501 §6.3.2.5 c、d）。

## 10. 結果與 cause 對應

D02 關閉前，下表的值都是**候選**，名稱取自 free5gc 程式碼。

| 來源 | 值 | SMF 的處理 | 核對 |
|---|---|---|---|
| N1N2 回應 cause | `N1_N2_TRANSFER_INITIATED` | REQ-XFER-02 | |
| N1N2 回應 cause | `ATTEMPTING_TO_REACH_UE` | REQ-XFER-02 | |
| N1N2 回應 cause | `N1_MSG_NOT_TRANSFERRED` | REQ-XFER-02 | |
| N2 回應 | QosFlowFailedToAddOrModifyList 的 cause | 記錄；QFI 標 TO_SYNC（REQ-RSP-01、03） | |
| N2 請求 | QosFlowToReleaseList 的 cause | D07 | |
| N1 Reject | 5GSM cause | 記錄；REQ-RSP-05 | |
| SMF → PCF ruleReports | `ruleStatus` INACTIVE、`failureCode` RES_ALLO_FAIL（free5gc openapi 有這兩個常數） | REQ-RPT-01、02 | D10 |

## 11. 設定

```yaml
configuration:
  networkInitiatedModification:
    enable: true          # REQ-GEN-01
  w5b:
    enable: true          # REQ-GEN-04、§8B
  w5d:
    enable: true          # §8C
  reportToPcf:
    enable: true          # REQ-RPT-07
    retry: {maxAttempts: 3, backoff: [1s, 2s, 4s]}   # REQ-RPT-06
  t3591:
    enable: true
    expireTime: 16s       # 部署現值
    maxRetryTimes: 4      # REQ-CFG-02：TS 24.501 §6.3.2.5 重送 4 次；部署現值為 3
```

- **REQ-CFG-01** `networkInitiatedModification.enable` 為 true 時，`t3591.enable` **必須**為 true，否則拒絕啟動。
- **REQ-CFG-02** `t3591.maxRetryTimes` **必須**為 4，使第 5 次逾時才中止；`kamailio-free5gc/config/smfcfg.yaml` 現值 3 **必須**在 G3 前改掉。

上面的數值是實驗初始值；重送次數依 TS 24.501 §6.3.2.5。

## 12. free-ran-ue 回應器（W6）

適用條件：[ADR-0005](adr/0005-patch-free-ran-ue-responder.md) 接受。patch 放在 `kamailio-free5gc/ran/`，build 時套用。

- **REQ-RAN-01** gNB **必須**處理 PDU Session Resource Modify Request：把其中的 NAS PDU 轉給 UE，並回 PDU Session Resource Modify Response，把請求中每個新增 QFI 放進 QosFlowAddOrModifyResponseList（故障注入另計），並確認釋放清單。
- **REQ-RAN-02** UE **必須**解析 PDU SESSION MODIFICATION COMMAND，依 QoS rule 與 flow description 的 operation 更新本地紀錄，並以 UL NAS Transport 回 Complete。
- **REQ-RAN-03** **必須**提供故障注入設定：（a）UE 回 Reject，（b）UE 不回應，（c）gNB 把指定 QFI 放進 QosFlowFailedToAddOrModifyList。預設全部關閉。
- **REQ-RAN-04** UE **必須**在 log 中輸出收到的 QoS rule 與 flow description（QFI、operation、5QI），作為 UE 端狀態的證據。
- **REQ-RAN-05** patch **不得**改變 free-ran-ue 既有的註冊、PDU session 建立與 GTP-U 行為。
- **REQ-RAN-06** **必須**再提供一種故障注入：（d）gNB 對指定 QFI 送 PDU Session Resource Notify，表示 RAN 已釋放該 QoS flow（W5c 的測試用）。
- **REQ-RAN-07** **必須**再提供：（e）gNB 對指定 QFI 送 PDU Session Resource Notify 的 QosFlowNotifyList（not fulfilled、fulfilled）；（f）UE 能處理 QoS rule 的 modify 操作與 QoS flow description 的 `QFD_Mod`，並在 log 輸出（W5b、W5d）。
- **REQ-RAN-08** **應**提供讓 UE 進入 CM-IDLE 再做 Service Request 的操作，以驗證 REQ-SYNC-01、02；free-ran-ue 是否支援待 D12。

## 13. 可觀測性

- **REQ-OBS-01** 每個程序**必須**記錄：SUPI（遮蔽）、PDU session ID、程序序號、新增與刪除的 QFI 與 QoS rule ID、狀態轉移、N1N2 cause、N2 回應的成功與失敗清單、T3591 次數、結果。
- **REQ-OBS-02** **必須**提供指標：程序開始、完成、中止的次數（依原因）；TO_SYNC 的 flow 數；T3591 逾時次數。

---

## 附錄 A（參考）現有程式碼的位置

| 功能 | 位置（SMF v1.4.6） |
|---|---|
| policy 更新入口 | `internal/sbi/processor/notifier.go` `HandleSMPolicyUpdateNotify` |
| PCC rule 套用、QFI 配置與釋放 | `internal/context/sm_context_policy.go` `ApplyPccRules`；`sm_context.go` `AssignQFI`、`RemoveQFI` |
| N1 builder | `internal/context/gsm_build.go` `BuildGSMPDUSessionModificationCommand`（目前只有 PDU session ID、PTI）；Establishment Accept 的 QoS rule 組法 |
| N2 builder | `internal/context/ngap_build.go` `BuildPDUSessionResourceModifyRequestTransfer`（只有 AddOrModify 清單） |
| 送 N1N2、T3591 | `internal/sbi/processor/pdu_session.go` `sendGSMPDUSessionModificationCommand` |
| N2 回應處理 | `internal/context/ngap_handler.go` `HandlePDUSessionResourceModifyResponseTransfer` |
| Complete、Reject | `pdu_session.go` 的 `PDUSessModComplete`、`PDUSessModRej`（只停 T3591） |
| AMF 轉送 | `amf/internal/sbi/processor/n1n2message.go`（`PDU_RES_MOD_REQ` → `SendPDUSessionResourceModifyRequest`） |
| PCF 刪除通知 | `pcf/internal/context/ue.go` `RemovePccRule`（只把 `PccRules[id]` 設為 nil） |

## 附錄 B（參考）free-ran-ue 已知行為

| 項目 | 行為 | 來源 |
|---|---|---|
| gNB NGAP dispatcher | 只處理 DownlinkNASTransport、InitialContextSetupRequest、PDUSessionResourceSetupRequest、UEContextReleaseCommand、PDUSessionResourceModifyConfirm；其他走 `default` 記「Unknown NGAP PDU」 | `gnb/ngapDispatcher.go` |
| UE 5GSM | 只處理 PDUSessEstAccept、PDUSessRelCmd、PDUSessEstRej | `ue/ue.go` |
| GTP-U | 不看 QFI | `gnb`、`ue` 內沒有 QFI 的資料路徑處理 |
| 版本 | 部署 v2.5.0＋`pcscf-discovery.patch`；查證用本機 v2.5.0-26 | `ran/Dockerfile` |

## 附錄 C（參考，後續階段）

- W5b：QoS flow 參數修改用 `QFD_Mod`、`OpCode_ModifyReplaceAllPktFilters`；CM-IDLE 的延後同步（TS 23.502 §4.3.3.2 步驟 1d）。
- W5c 已納入本規格 §8A。補充：free5gc PCF 在 Create 時對 FAILED_RESOURCES_ALLOCATION 的 policy control trigger 是註解掉的，但事件訂閱本身有被記錄，收到 ruleReports 時仍會通知 AF（`policyauthorization.go`、`smpolicy.go`）。
- Alternative QoS profile（TS 23.501 §5.7.2.4.1b、§5.7.2.4.2、§5.7.2.4.3）、以 NAS 告知 UE 目前實際達到的 QoS（§5.7.2.4.1b 第 5 點）、handover 後的恢復規則：不在 W5d 範圍。

## 附錄 D（參考）W5d 端到端需要的 PCF 修正（本計畫外的前提）

在 `pcf/internal/sbi/processor/smpolicy.go`：

1. 收到 SMF 的 `qncReports` 時，保留 `refPccRuleIds`（目前只複製 `notifType`）。
2. `sendSmPolicyRelatedAppSessionNotification` 的 QOS_NOTIF 分支：用 `refPccRuleIds` 經 `PccRuleIdMapToCompId` 找出 media component 與 flow，填入 `EventsNotification.qncReports`（`notifType`、`flows`）；沒有對應到本 app session 的規則就不送。
