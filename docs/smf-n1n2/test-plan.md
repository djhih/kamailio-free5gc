# SMF 網路發起的 QoS flow 修改測試計畫（W5a～W5d＋W6）

| 項目 | 內容 |
|---|---|
| 版本／狀態 | v0.3／審查中（2026-10-22：v0.3 新增 T33–T42，W5b、W5d；v0.2 新增 T27–T32，W5c） |
| 驗證對象 | [interface-spec.md](interface-spec.md) 的 REQ-* |
| 門檻 | G0–G4，見 [../overview/vonr-ims-nf-plan.md](../overview/vonr-ims-nf-plan.md) W5 |

## 1. 測試案例

**層級**：U＝單元（`qos_flow_diff.go`、`nwmod.go` 的轉移函式、N1／N2 builder；AMF 用可注入延遲與 cause 的 stub；T3591 用假時鐘）；I＝整合（真的 SMF、AMF、PCF、UPF，加上 patch 過的 free-ran-ue）；E＝端到端（Kamailio＋兩支 UE 打一通電話）。並行相關測試必須開 Go race detector。

| ID | 情境 | 層級 | 必須觀察到的結果 |
|---|---|---|---|
| T01 | 差異計算：只新增；PCF 刪除通知只帶 `PccRules[id]=nil`（不帶 QosDecs）；同時新增與刪除；無變化；既有 flow 的 5QI 改變 | U | 依序得到 {TO_ADD}、{TO_DELETE}、兩者、空集合；參數改變被記錄並略過，不出現在差異裡 |
| T02 | PFCP 修改失敗 | U | AMF stub 收到的 N1N2 次數為 0；同步狀態不變 |
| T03 | 刪除 QFI 2 的程序進行中，又新增一條 PCC rule | U | 新 flow 不會配到 QFI 2；刪除程序結束後 QFI 2 才可再被配置 |
| T04 | AMF stub 延遲 10 秒才回 N1N2 | I | SMF 對 PCF 的 204 在 1 秒內送出 |
| T05 | N1 編碼（用 `free5gc/nas` 解碼檢查） | U | PTI＝0；新增有 create QoS rule（packet filter 與 PCC flow info 一致）、新配的 rule ID 已記在 `PCCRuleIDToQoSRuleID`；刪除用 delete 與原 rule ID；flow description 新增帶 5QI，GBR 另帶 GFBR／MFBR；刪除帶 `QFD_Del`；沒有 Session-AMBR、沒有預設 QoS rule |
| T06 | 新增後 packet filter 總數超過 UE 上限 | U | 不送 N1N2；記錄原因 |
| T07 | N2 編碼（用 `free5gc/ngap` 解碼檢查）：只新增、只刪除、兩者都有 | U | 新增在 AddOrModify 清單、含 5QI、ARP、GBR QoS information；刪除在 ToRelease 清單；只新增時沒有 ToRelease 清單，只刪除時沒有 AddOrModify 清單 |
| T08 | GBR flow 的 QosData 沒有 GbrUl／GbrDl | U | 依 D04 之前的規則：不送出、記錄；不會出現 GFBR 為 0 的 N2 |
| T09 | N1N2 請求內容（AMF stub 檢查） | I | 一次請求同時有 N1（class SM）與 N2（`PDU_RES_MOD_REQ`）與正確的 PDU session ID |
| T10 | AMF 回 `N1_N2_TRANSFER_INITIATED`、`ATTEMPTING_TO_REACH_UE`、`N1_MSG_NOT_TRANSFERRED`、HTTP 500、逾時 | U | 第一種進 PENDING 並標 ADDING／DELETING、啟動 T3591；其餘回 IDLE、差異標 TO_SYNC、沒有啟動 T3591 |
| T11 | AMF stub 延遲期間送進同一 session 的 UpdateSMContext | U、I | UpdateSMContext 不被卡住；race detector 乾淨 |
| T12 | N2 回應與 Complete：兩種到達順序；N2 回應中 QFI 2 失敗 | U | 兩種順序都在第二個到達時完成；成功的新增變 SYNCED，刪除的 flow 被移除且 QFI 釋放；失敗的 QFI 變 TO_SYNC，並自動發起第二個程序把它從 UE 刪掉 |
| T13 | 序號不符（前一個程序）的 N2 回應與 Complete | U | 狀態不變，只有 log |
| T14 | UE 回 Reject | U | T3591 停止；`inFlight` 變 TO_SYNC；回 IDLE；有排隊的差異則開始下一個程序 |
| T15 | UE 不回應（假時鐘推進） | U | 第 1～4 次逾時各重送一次相同的 N1；第 5 次逾時中止、標 TO_SYNC、告警；UPF 規則不變 |
| T16 | PENDING 期間收到新增與刪除；design §5.4 的競態（新增未完成就刪除） | U | 不在 PENDING 期間送第二個 N1N2；完成後一次送出合併的差異；新增已在途時，刪除等新增完成後才送 |
| T17 | PENDING 期間：UE 要求釋放 PDU session；UE 要求修改；網路發起釋放 | U | 第一、三種中止程序並進入釋放流程；第二種忽略 UE 的請求，程序繼續 |
| T18 | §9.2 轉移表逐列的表格驅動測試 | U | 每列至少一個案例；動作與下一狀態相符 |
| T19 | 設定：`enable` false；`enable` true 但 `t3591.enable` false；`maxRetryTimes` 3 | U、I | false 時 policy 更新後沒有 N1N2（與上游相同）；第二種拒絕啟動；第三種 G3 檢查不通過 |
| T20 | UE 發起修改的既有路徑 | U | free5gc SMF 既有測試通過；`PDUSessModReq` 的回應與上游相同 |
| T21 | free-ran-ue 回應器（patch） | I | gNB 收到 Modify Request 後轉 NAS、回 Modify Response（新增 QFI 都在成功清單）；UE 回 Complete；UE log 有 QFI、operation、5QI |
| T22 | free-ran-ue 故障注入：Reject、不回應、指定 QFI 失敗 | I | SMF 分別走 T14、T15、T12 的路徑，抓包可對應 |
| T23 | free-ran-ue 回歸 | E | patch 後註冊、PDU session 建立、經 GTP-U ping DN 都照常 |
| T24 | 端到端：`03-call-test.sh`（patch 過的 free-ran-ue、W3a 的 Adapter） | E | 200 OK 之後，兩支 UE 各有一組 N2 Modify Request（QFI 新增、5QI 1）／Response 與 Modification Command／Complete；BYE 之後各有一組刪除；UPF 規則、SMF log、UE log 的 QFI 一致 |
| T25 | log 與指標 | I | REQ-OBS-01 的欄位齊全；SUPI 有遮蔽；REQ-OBS-02 的指標數值與 T24 的動作一致 |
| T26 | G0 基準：現行 SMF（未修改）跑 `03-call-test.sh` | E | 記錄 policy 更新後沒有 N1N2；通話結束後 `AdditionalQosFlows` 與 QFI 是否殘留（D03 的證據） |
| T27 | W5c：N2 回應中 QFI 2 新增失敗（PCF stub） | U、I | 程序完成後送一次 SMPolicyControl_Update，`ruleReports` 含 QFI 2 的所有 PCC rule ID、INACTIVE、RES_ALLO_FAIL；SMF 自行移除這些 PCC rule 與 UPF 規則；另發程序把 QoS rule 從 UE 刪除 |
| T28 | W5c：IDLE 與 PENDING 時各收到一次 `PDU_RES_NTY`（QFI 2 已被 RAN 釋放） | U | 回報 PCF；本地移除；IDLE 時立刻開始只送 N1 的程序，PENDING 時排隊；兩者的 N2 都沒有 QFI 2 的 ToRelease |
| T29 | W5c：PCF policy 更新造成的刪除 | U | 沒有任何 ruleReports |
| T30 | W5c：回報時 PCF 回 500、逾時 | U | 依 `reportToPcf.retry` 重試後告警；本地移除不回退 |
| T31 | W5c：`reportToPcf.enable` false | U | 不送回報、不做本地移除（同 W5a 行為） |
| T32 | W5c 故障注入（d）與端到端鏈 | I、E | free-ran-ue gNB 依設定送 PDU Session Resource Notify；SMF 回報 PCF；PCF 送 FAILED_RESOURCES_ALLOCATION 給 Adapter；Adapter 送 ASR，通話結束（對應 rx-n5 的 T44） |
| T33 | W5b：PCF 修改語音規則的 MFBR（QoS data ID 不變） | U、I | QFI 不變；N1 有 `QFD_Mod`、E bit＝1、完整參數，沒有 QoS rule；N2 AddOrModify 帶新參數；完成後同步內容更新 |
| T34 | W5b：只改 packet filter；QoS data ID 改變（Delete＋Create） | U | 前者 N1 用 `OpCode_ModifyReplaceAllPktFilters`、沒有 flow description；後者是刪除舊 QFI＋新增新 QFI |
| T35 | W5b：UP 連線不是 ACTIVATED 時收到 policy 更新；AMF 回 `ATTEMPTING_TO_REACH_UE` | U | 都沒有啟動 T3591；差異標 TO_SYNC |
| T36 | W5b：UP 啟動完成（PDU_RES_SETUP_RSP）時有 TO_SYNC；Setup Response 拒絕一個 QFI | U、I | 送只帶 N1 的程序（N1N2 沒有 N2），Complete 後 TO_SYNC 變 SYNCED；被拒的 QFI 走 W5c 回報；log 標 `deferred-sync` |
| T37 | W5d：`qnc` true／false 的 GBR flow，Setup 與 Modify 兩條路徑 | U | true 時 GBR QoS information 帶 Notification Control；false 時沒有 |
| T38 | W5d：`PDU_RES_NTY` 的 QosFlowNotifyList（not fulfilled、fulfilled），PCF 有／沒有下 QOS_NOTIF trigger | U | 有 trigger 時送 `qncReports`（refPccRuleIds、NOT_GUARANTEED／GUARANTEED）；沒有 trigger 時不送；QoS flow 不被釋放 |
| T39 | W5d：故障注入（e）端到端到 PCF | I | 抓包看到 SMF → PCF 的 `qncReports` |
| T40 | W5d：PCF → AF 的 QOS_NOTIF | I | 未修 PCF 時通知沒有 `qncReports`，標 BLOCKED（D13）；修 PCF 後帶 `notifType` 與 `flows` |
| T41 | W5b、W5d 設定關閉 | U | `w5b.enable` false 時修改依 REQ-GEN-04 略過；`w5d.enable` false 時不帶 Notification Control、不處理 QosFlowNotifyList |
| T42 | free-ran-ue（f）：UE 收到 QoS rule modify 與 `QFD_Mod` | I | UE 回 Complete；log 有 operation 與新參數 |

## 2. 需求追溯

| 需求 | 測試 | 檢驗方式 |
|---|---|---|
| REQ-GEN-01 | T19 | 測試 |
| REQ-GEN-02 | T20 | 測試 |
| REQ-GEN-03 | T05 | 測試 |
| REQ-GEN-04 | T01、T41 | 測試 |
| REQ-TRIG-01 | T01、T24、T26 | 測試＋抓包 |
| REQ-TRIG-02 | T02 | 測試 |
| REQ-TRIG-03 | T03 | 測試 |
| REQ-TRIG-04 | T01 | 測試 |
| REQ-TRIG-05 | T04 | 測試 |
| REQ-N1-01～04 | T05 | 測試 |
| REQ-N1-05 | T06 | 測試 |
| REQ-N2-01、03、04 | T07 | 測試 |
| REQ-N2-02 | T07、T08 | 測試 |
| REQ-XFER-01 | T09 | 測試 |
| REQ-XFER-02 | T10、T35 | 測試 |
| REQ-XFER-03 | T11 | 測試 |
| REQ-RSP-01～03 | T12、T24 | 測試＋抓包 |
| REQ-RSP-04 | T13 | 測試 |
| REQ-RSP-05 | T14 | 測試 |
| REQ-ST-01、02 | T16 | 測試 |
| REQ-ST-03 | T11 | 測試 |
| REQ-ST-04 | T15、T18 | 測試 |
| REQ-ST-05 | T17、T18 | 測試 |
| REQ-CFG-01、02 | T19 | 測試 |
| REQ-RAN-01、02、04 | T21 | 測試 |
| REQ-RAN-03 | T22 | 測試 |
| REQ-RAN-05 | T23 | 測試 |
| REQ-OBS-01、02 | T25 | 測試 |
| REQ-RPT-01、04 | T27 | 測試 |
| REQ-RPT-02、03 | T28 | 測試 |
| REQ-RPT-05 | T29 | 測試 |
| REQ-RPT-06 | T30 | 測試 |
| REQ-RPT-07 | T31 | 測試 |
| REQ-RAN-06 | T32 | 測試 |
| REQ-RAN-07 | T39、T42 | 測試 |
| REQ-RAN-08 | T36 | 測試（D12 不支援時標 BLOCKED） |
| REQ-MOD-01～04、06 | T33、T34 | 測試 |
| REQ-MOD-05 | T36 | 測試 |
| REQ-SYNC-01 | T35 | 測試 |
| REQ-SYNC-02～04 | T36 | 測試 |
| REQ-QNC-01 | T37 | 測試 |
| REQ-QNC-02～05 | T38、T39、T40 | 測試（T40 依 D13） |

新增或修改需求時，必須同時更新這張表；沒有測試也沒有審查方式的需求不能進入 G2。

## 3. 分層判定

| 層級 | PASS 需要的證據 | 本階段 |
|---|---|---|
| L1 SMF 送出正確的 N1、N2 | 抓包解碼 N1N2 內的 NAS 與 NGAP，內容符合 §5、§6（T05、T07、T09、T24） | 必須 |
| L2 程序完成 | patch 過的 free-ran-ue 回應，SMF 依 §9.2 完成或中止（T12、T14、T15、T21、T22） | 必須（ADR-0005 已接受） |
| L3 跨元件一致 | 一通電話中，UPF、SMF、RAN、UE 的 QFI 新增與刪除一致（T24） | 必須 |
| L3c 回報鏈（W5c） | RAN 拒絕或釋放 QFI 時，SMF → PCF → Adapter → Kamailio 的回報在抓包中可對應，通話結束（T27、T28、T32） | 必須（W5c） |
| L3d 修改與延後同步（W5b） | 修改的 N1、N2 內容正確；UP 啟動後只送 N1 的同步完成（T33、T36） | 必須（W5b；T36 依 D12） |
| L3e QoS notification control（W5d） | SMF 送出正確的 `qncReports`（T38、T39）；AF 端依 D13 | 必須到 SMF；AF 端依 D13 |
| L4 真實 RAN／UE | 真 gNB 建立無線資源、真手機套用 QoS rule | 後續（沒有設備） |
| L5 傳輸品質 | 有負載時語音 flow 的延遲與丟包 | 後續 |

缺工具時輸出 SKIP 或 BLOCKED，不能算 PASS。

## 4. 要保存的證據

每次驗收保存：版本 manifest、測試命令與退出碼、帶時間的 log（SMF、AMF、gNB、UE）、pcap（N2 SCTP／NGAP、N4、SBI）、通話前中後的 UPF 規則快照、SMF 的 QoS flow 同步狀態傾印、逐案結果。G0 的基準（T26）一併保存。

## 5. 版本 manifest（G0 填寫）

| 項目 | 必填 | 目前 |
|---|---|---|
| 本 repo 與 `kamailio-free5gc` submodule | URL、commit | 待填 |
| free5gc SMF（fork）、AMF、PCF、UPF | release、commit | 部署 4.2.3；本機原始碼 SMF v1.4.6；待 D01 |
| `free5gc/nas`、`free5gc/ngap` | module 版本 | SMF v1.4.6 用 nas v1.3.0、ngap v1.2.0 |
| free-ran-ue | 版本、所有 patch 的 commit | v2.5.0＋`pcscf-discovery.patch`；新 patch 待填 |
| Kamailio、Adapter | 版本 | 見 [../rx-n5/test-plan.md](../rx-n5/test-plan.md) §5 |
| `smfcfg.yaml` | T3591 設定、開關 | 現值 maxRetryTimes 3 |
| gtp5g、Go、OS、kernel、Docker | 版本 | 待填 |
| 3GPP | 每份 TS 的版本與章節 | 見 [interface-spec.md](interface-spec.md) §2 |

只寫 main／master 不算填寫完成。

## 6. 完成定義

G0–G4 的證據齊全；必須的測試沒有未說明的 FAIL 或 SKIP；L1–L3 PASS。達成後只能使用 [design.md](design.md) §11 允許的說法：「W5a：SMF 依 TS 23.502 §4.3.3.2 通知 RAN／UE 的 QoS flow 新增與刪除，已在 patch 過的 free-ran-ue 上驗證」。
