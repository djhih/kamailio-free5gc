# ADR-0002：要刪除的 QoS flow 由 PCC rule 的差異推導，不依賴 PCF 送 QosDecs=nil

- 狀態：提案
- 日期：2026-10-22
- 相關：D03

## 背景

- PCF 刪除 app session 時呼叫 `RemovePccRule`，送給 SMF 的通知只把 `PccRules[id]` 設為 nil；QoS data 只從 PCF 自己的 decision 刪掉，不會在通知裡標成 nil（`pcf/internal/context/ue.go`）。
- SMF 的 `ApplyPccRules` 只在 `decision.QosDecs[id] == nil` 時呼叫 `RemoveQFI`；PCC rule 被刪時只拆 data path，不動 `AdditionalQosFlows` 與 QFI（`smf/internal/context/sm_context_policy.go`）。
- 兩者合起來：通話結束後，SMF 很可能保留語音 QoS flow、不釋放 QFI。這是讀原始碼的推論，G0 要實測（D03）。

## 決定

每次套用 policy 之後，SMF 以「QoS flow 是否仍被任何 PCC rule 參照」計算差異：已同步但不再被參照的就是 TO_DELETE。QFI 等刪除程序結束才釋放。不修改 PCF。

## 後果

- 好處：不依賴 PCF 的通知格式；PCF 之後若改成會送 QosDecs=nil，結果也一樣。
- 代價：差異計算要看全部 PCC rule，不能只看這次通知的內容。
- 對應需求：REQ-TRIG-01、REQ-TRIG-03；測試：T01、T03、T26
