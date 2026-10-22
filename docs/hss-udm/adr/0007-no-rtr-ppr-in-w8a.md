# ADR-0007：W8a 不做 RTR、PPR 與 IMS restoration

- 狀態：提案
- 日期：2026-10-22
- 取代：[archive/design-v0.1.md](../archive/design-v0.1.md) §3（把 RTR／PPR 列為「第一階段只做四種、第二階段再做」，本 ADR 寫明理由與限制）
- 相關：D12

## 背景

- `kamailio-free5gc` 的 I-CSCF 只用 UAR、LIR，S-CSCF 只用 MAR、SAR（cfg 已讀）。註冊與通話的端到端流程不需要 HSS 主動發起任何指令。
- RTR、PPR 由 HSS 主動送出，UDM 必須同時是 Diameter client，連到 S-CSCF 的 Acceptor（`scscf.xml` 的 3870）。
- IMS restoration（TS 23.380）需要 S-CSCF 也支援，實驗只有一台 S-CSCF。

## 決定

W8a 只做 UAR、MAR、SAR、LIR 的 server 端。不送 RTR、PPR；不支援 restoration 相關的旗標與分支（REQ-UAR-07、REQ-LIR-04、REQ-SAR-04 照「不支援 restoration」處理）。

## 後果

- 好處：W8a 範圍可控；UDM 只需要 server 角色。
- 代價：
  - 經擴充 API 刪除開戶資料時，S-CSCF 不會被通知，已註冊的用戶在 registrar 裡還會留到過期（REQ-DATA-06 只刪 UDR 裡的資料）；
  - 改 profile 要等用戶重新註冊才生效。
- 保留的出路：W8b 加 RTR、PPR；轉移表裡「開戶資料被刪除」一列屆時改為送 RTR。
- 對應需求：REQ-GEN-04、REQ-DATA-06；測試：T18、T25
