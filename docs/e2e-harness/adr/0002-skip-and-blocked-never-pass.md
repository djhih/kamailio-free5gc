# ADR-0002：SKIP 與 BLOCKED 永遠不算 PASS

- 狀態：提案
- 日期：2026-10-22
- 取代：現行 `03-call-test.sh` 的 QoS 檢查（找不到 gtp5g 讀取工具時為 SKIP，且不影響 PASS）

## 背景

現行測試在工具缺失時跳過 QoS 檢查，最後仍可能印 PASS；註冊的 sipp 結果經過 `tail -3`，失敗也不影響判定。這讓「PASS」無法代表「每一項都被證明了」。

## 決定

每個檢查只能是 PASS、FAIL、SKIP、BLOCKED。整體 PASS 必須是所有啟用的必須檢查都 PASS；有 FAIL 就是 FAIL；其餘是 INCOMPLETE（退出碼 2）。

## 後果

- 好處：PASS 的意思明確；缺工具的環境不會產生假 PASS。
- 代價：環境不完整時會看到比較多 INCOMPLETE，需要先把工具裝好。
- 對應需求：REQ-VER-01、REQ-VER-02、REQ-UPF-03、REQ-RUN-06；測試：T02、T03、T04、T06
