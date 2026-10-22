# 抓包版端到端測試（W1）文件

> 對應計畫：[vonr-ims-nf-plan.md](../overview/vonr-ims-nf-plan.md) 的 W1
> 狀態：設計審查中（v0.1，2026-10-22），尚未實作

這組文件規定的是**測試工具**：其他規格組（[rx-n5](../rx-n5/README.md)、[hss-udm](../hss-udm/README.md)、[smf-n1n2](../smf-n1n2/README.md)）test-plan 裡標「抓包」的驗收，都用這裡的機制判定。

## 先看哪份

| 文件 | 回答什麼問題 | 性質 | 給誰看 |
|---|---|---|---|
| [design.md](design.md) | 為什麼改成抓包判定？抓哪裡、看得到什麼？ | 設計文件 | 指導者、評審 |
| [interface-spec.md](interface-spec.md) | 工具必須怎麼表現？有哪些檢查（CHK-*）？ | 規格（normative） | 實作者 |
| [test-plan.md](test-plan.md) | 怎麼證明工具本身是對的？ | 測試計畫 | 測試者 |
| [adr/](adr/) | 關鍵決策 | 決策紀錄 | 評審 |

**以哪份為準：** 行為以 interface-spec 為準；理由以 design 與 ADR 為準；衝突時視為文件錯誤。

## 決策紀錄

| # | 決策 | 狀態 |
|---|---|---|
| [0001](adr/0001-capture-on-host-bridges.md) | 在 host 的兩個 docker bridge 抓包，用 tshark 判定 | 提案 |
| [0002](adr/0002-skip-and-blocked-never-pass.md) | SKIP 與 BLOCKED 永遠不算 PASS | 提案 |

ADR 狀態：提案 → 接受 → （被取代／廢止）。

## 文件版本

| 版本 | 日期 | 變更 |
|---|---|---|
| v0.1 | 2026-10-22 | 第一版。原本只有計畫 W1 的幾行描述 |
