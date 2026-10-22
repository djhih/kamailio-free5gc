# ADR-0010：W5d 在 SMF 端照規格做；端到端需要 PCF 補上 QOS_NOTIF 的通知內容

- 狀態：提案
- 日期：2026-10-22
- 相關：rx-n5 的 W5d 對應（Adapter 收到 QOS_NOTIF 的處理）

## 背景

- free5gc PCF 在 AF 訂閱 QOS_NOTIF 時，會把相關 QosData 的 `qnc` 設為 true，並下 `QOS_NOTIF` trigger（`policyauthorization.go`）。
- free5gc SMF 的 NGAP builder 沒有帶 Notification Control；不處理 `PDU_RES_NTY`；從不送 `qncReports`。
- free5gc PCF 收到 SMF 的 `qncReports` 時只複製 `notifType`，丟掉 `refPccRuleIds`；轉給 AF 的通知只有 `evNotifs: [{event: QOS_NOTIF}]`，**沒有** `qncReports`（`smpolicy.go` `sendSmPolicyRelatedAppSessionNotification` 的 QOS_NOTIF 分支是 TODO）。
- TS 29.514 V17.9.0 §4.2.5.4、§5.6.2.x：QOS_NOTIF 的通知必須帶 `qncReports`（含 `notifType`）。沒有它，AF 分不出是「無法保證」還是「恢復保證」。

## 決定

SMF 端依規格實作（Notification Control、處理 `PDU_RES_NTY`、送 `qncReports`）。PCF 的通知內容缺陷列為本計畫外的前提：在 PCF 修好之前，W5d 只驗證到「SMF 送出正確的 `qncReports`」，AF 端（rx-n5）收到沒有 `qncReports` 的 QOS_NOTIF 時只記錄、不轉送。

## 後果

- 好處：SMF 的行為符合規格，PCF 修好後端到端就通。
- 代價：在不改 PCF 的前提下，W5d 的端到端（L3c 延伸）無法通過，test-plan 標 BLOCKED。
- 保留的出路：若決定修 PCF，需要的改動見 [interface-spec.md](../interface-spec.md) 附錄 D。
- 對應需求：REQ-QNC-01～05、REQ-RAN-07；測試：T37～T40
