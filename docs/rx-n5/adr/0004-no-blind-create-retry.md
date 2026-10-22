# ADR-0004：Create 結果不明時不自動重送

- 狀態：提案
- 日期：2026-10-22

## 背景

Create（`POST /app-sessions`）逾時時，PCF 可能已經建立 app session，只是回覆遺失。N5 的 Create 不是冪等操作，PCF 也沒有提供依 Adapter 自訂 key 查詢或列出 app session 的 API。自動重送可能在 PCF 上留下第二個、沒有人知道 URI 的 app session，它的 PCC rule 會一直留在 SMF／UPF 上。

## 決定

逾時、回覆不完整或 `Location` 不合法時，session 轉為 `CREATE_UNKNOWN`：

- 回 AAA 失敗，告警；
- 之後同一 session 的 AAR 都回失敗，不再 Create；
- 由人工依 runbook 在 PCF／UPF 上確認並清理後，才轉為 CLOSED。

## 後果

- 不會因為重送而產生不可追蹤的資源。
- PCF 短暫變慢時，那通電話會建立失敗，不會自動恢復。實驗環境可以接受；正式部署需要 PCF 端的冪等支援或查詢 API，屬於未來工作。
- 需要可操作的清理 runbook（D08）。
- 對應需求：REQ-AAR-14、REQ-N5-02；測試：T09。
