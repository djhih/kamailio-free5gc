# ADR-0009：UP 連線未啟動時不送 N1N2，等 UP 啟動後只送 N1 同步

- 狀態：提案
- 日期：2026-10-22

## 背景

- free5gc AMF 收到 N1N2MessageTransfer 而 UE 是 CM-IDLE 時，回 `ATTEMPTING_TO_REACH_UE` 並 paging，把請求存在單一槽位（`amf/internal/sbi/processor/n1n2message.go`）。
- UE 做 Service Request 時，`HandleServiceRequest` 只轉送 `PDU_RES_SETUP_REQ` 類型的 N2；`PDU_RES_MOD_REQ` 的 N1 與 N2 都不送，最後把槽位清空。也就是訊息會遺失。
- SMF 在 UP 啟動時送的 PDU Session Resource Setup Request Transfer 已經包含全部 `AdditionalQosFlows` 與最新參數，但不送 N1。
- TS 23.502 V17.15.0 §4.3.3.2 步驟 1d：UP 啟動且有「刪除未同步」的 QoS flow 時，SMF 可以發起修改。

## 決定

UP 連線不是 ACTIVATED 時，不送 N1N2，差異標 TO_SYNC；`ATTEMPTING_TO_REACH_UE` 也視為沒送達。UP 啟動完成後，SMF 發起只帶 N1 的修改，把 TO_SYNC 的 QoS rule 與 flow description 同步給 UE。

## 後果

- 好處：不依賴 AMF 的 paging 與緩衝行為；RAN 端由 Setup 自然同步。
- 代價：新增與修改的延後同步不在規格明文範圍（步驟 1d 只講刪除），要在 log 標明；UE 閒置期間，UE 端的 QoS rule 與網路不一致。
- 對應需求：REQ-XFER-02、REQ-SYNC-01～04；測試：T10、T35、T36
