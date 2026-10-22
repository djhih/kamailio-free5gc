# ADR-0005：以 patch 讓 free-ran-ue 回應 Modify Request 與 Modification Command

- 狀態：接受（2026-10-22，使用者決定 patch）
- 日期：2026-10-22
- 取代：[vonr-ims-nf-plan.md](../../overview/vonr-ims-nf-plan.md) W6 的「完成條件：有結論；不支援時決定修 free-ran-ue，或 W5 只驗證 SMF 送出的訊息」
- 相關：D08

## 背景

- W6 的結論（2026-10-22 讀原始碼）：free-ran-ue 的 gNB 不處理 PDU Session Resource Modify Request（`gnb/ngapDispatcher.go` 走 `default`），UE 不處理 PDU SESSION MODIFICATION COMMAND（`ue/ue.go` 只處理 Establishment Accept／Reject 與 Release Command）。
- 沒有回應時，SMF 的程序會停在 PENDING，T3591 必然逾時；回應處理、衝突、QFI 釋放時機都無法端到端驗證。
- 專案已經用 `ran/pcscf-discovery.patch` 修改 free-ran-ue，有現成的作法。

## 決定

寫一個最小的 patch：gNB 轉 NAS、回 Modify Response；UE 解 Command、記錄、回 Complete；加上三種故障注入。不實作無線資源，也不讓 GTP-U 依 QFI 分類。

## 後果

- 好處：L2、L3 可以驗證；故障注入讓異常路徑可測。
- 代價：要維護第二個 free-ran-ue patch；回應器的行為是我們寫的，不能拿來宣稱真實 RAN／UE 的相容性（[design.md](../design.md) §11）。
- 不採用的替代：只抓包看 SMF 送出的內容（[design.md](../design.md) §6 方案 E）。若本 ADR 不接受，L2、L3 標 BLOCKED。
- 對應需求：REQ-RAN-01～05；測試：T21、T22、T23
