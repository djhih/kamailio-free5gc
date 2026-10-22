# ADR-0006：第一次註冊的 UAA 只回 Server-Capabilities，不回 Server-Name

- 狀態：提案
- 日期：2026-10-22
- 取代：[archive/design-v0.1.md](../archive/design-v0.1.md) §6.1 第 3 點（「沒有 → 回 Server-Capabilities（或設定好的預設 Server-Name）」）與 §8.1 的 `defaultServerName`
- 相關：D03、D04

## 背景

- TS 29.228 V17.1.0 §6.1.1.1 步驟 6：IMS subscription 裡沒有任何 IMPU 有已存 S-CSCF 時，HSS「may return the Server-Capabilities AVP」、Experimental-Result 設為 DIAMETER_FIRST_REGISTRATION，而且「**shall not return any S-CSCF name**」。挑選 S-CSCF 是 I-CSCF 的工作。
- PyHSS 依 `hss/pyhss.env` 的註解，在 UAA 裡回 `HSS_SCSCF_POOL` 當 Server-Name（待 D03 抓包確認），等於由 HSS 指定 S-CSCF。
- `icscf/seed.sql` 已經準備了 capability 路徑：S-CSCF 宣告 mandatory capability 0，註解寫「HSS 回 capabilities 時，I-CSCF 從這張表挑」。但這條路徑在現有部署上可能從沒被走過。

## 決定

第一次註冊時，UAA 回 Server-Capabilities（設定的 mandatory capabilities，預設 `[0]`）＋DIAMETER_FIRST_REGISTRATION，不帶 Server-Name。不提供「預設 Server-Name」設定。

## 後果

- 好處：符合 §6.1.1.1；S-CSCF 的選擇留在 I-CSCF，之後加第二台 S-CSCF 不用改 HSS。
- 代價與風險：行為和 PyHSS 不同。如果 Kamailio I-CSCF 處理 capabilities 的路徑有問題，第一次註冊會失敗。這是本設計前提最可能失效的地方，列為 [design.md](../design.md) §9 的第一個風險，G1 用 stub HSS 先驗證（D04）。
- 如果 D04 證實 Kamailio 不能用：要另開一張 ADR 決定是否偏離 §6.1.1.1，不能直接在實作裡加回 Server-Name。
- 對應需求：REQ-GEN-03、REQ-UAR-05；測試：T05、T27
