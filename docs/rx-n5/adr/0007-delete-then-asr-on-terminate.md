# ADR-0007：收到 terminate 後，Adapter 先回 204 並刪除 app session，再送 ASR

- 狀態：提案
- 日期：2026-10-22
- 取代：v0.2 explained §4.5 的順序（「回 204 → 送 ASR → 等 STR 再清」）
- 相關：[ADR-0005](0005-keep-resource-until-delete-confirmed.md)、[ADR-0008](0008-map-failed-resources-to-rar-or-asr.md)

## 背景

- TS 29.514 V17.9.0 §4.2.5.3：N5 consumer 接受 terminate 時，「shall acknowledge … with a "204 No Content" response … and shall invoke the Npcf_PolicyAuthorization_Delete service operation」。
- TS 29.214 V17.6.0 §4.4.6.1：PCRF 對每個 Rx session 送 ASR；AF 回 ASA 後自己發起 STR。
- free5gc PCF 在 SM policy 刪除時，送完 terminate 就把 app session 從 pool 刪掉（`pcf/internal/sbi/processor/smpolicy.go` `HandleDeleteSmPolicyContextRequest`），所以之後的 Delete 會回 404。
- Kamailio 收到 ASR 後是否一定送 STR，要到 G1 才能確認（D10）。

## 決定

terminate 到達時：持久化 → 回 204 → Adapter 自己呼叫 N5 Delete（404＋`APPLICATION_SESSION_CONTEXT_NOT_FOUND` 視為已清理）→ 送 ASR → 等 STR，收到時直接回 STA 成功。STR 一直沒來就在 `strWait` 後關閉。

## 後果

- 好處：N5 端符合 §4.2.5.3；app session 的清理不依賴 Kamailio 的行為；PCF 若改成不自行刪除，流程也成立。
- 代價：多一次多半會 404 的 Delete；STR 與 N5 Delete 不再一一對應，STR 只負責收尾。
- 對應需求：REQ-ASR-01～06、REQ-CFG-03；測試：T35、T36、T37、T38
