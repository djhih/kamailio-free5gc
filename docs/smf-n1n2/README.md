# SMF 網路發起的 QoS flow 修改（N1／N2）文件

> 對應計畫：[vonr-ims-nf-plan.md](../overview/vonr-ims-nf-plan.md) 的 W5 與 W6（本組文件涵蓋 W5a～W5d 與 W6；alternative QoS（W5e）只列在後續工作）
> 狀態：設計審查中（v0.3，2026-10-22），尚未實作

## 先看哪份

| 文件 | 回答什麼問題 | 性質 | 給誰看 |
|---|---|---|---|
| [explained.md](explained.md) | SMF 要多做什麼？用一通電話走一遍，並指出 free-ran-ue 卡在哪 | 說明（informative） | 第一次接觸的人 |
| [design.md](design.md) | 為什麼這樣設計？考慮過哪些替代方案？有什麼風險？ | 設計文件 | 指導者、評審 |
| [interface-spec.md](interface-spec.md) | SMF 與 free-ran-ue 必須怎麼表現？每一條需求是什麼？ | 規格（normative，需求有編號） | 實作者 |
| [test-plan.md](test-plan.md) | 怎麼證明需求都做到了？ | 測試計畫 | 測試者、驗收者 |
| [adr/](adr/) | 每個關鍵決策的背景、決定與代價 | 決策紀錄 | 想知道「為什麼不用 X」的人 |

**以哪份為準：** 行為以 [interface-spec.md](interface-spec.md) 為準；理由以 [design.md](design.md) 與 ADR 為準；兩者衝突時視為文件錯誤，要修正，不自行挑一份照做。工作順序與時程在 [vonr-ims-nf-plan.md](../overview/vonr-ims-nf-plan.md) W5。

## 決策紀錄

| # | 決策 | 狀態 |
|---|---|---|
| [0001](adr/0001-network-initiated-modification-in-smf.md) | 在 SMF（fork）實作 PCF 觸發的網路發起 PDU Session Modification | 提案 |
| [0002](adr/0002-derive-qos-flow-diff-from-pcc-rules.md) | 要刪除的 QoS flow 由 PCC rule 差異推導 | 提案 |
| [0003](adr/0003-one-procedure-per-session.md) | 每個 PDU session 同時只一個程序，差異排隊合併 | 提案 |
| [0004](adr/0004-keep-upf-rules-on-abort.md) | 程序中止時保留 UPF 規則，標 TO_SYNC，不回退 | 提案 |
| [0005](adr/0005-patch-free-ran-ue-responder.md) | 以 patch 讓 free-ran-ue 回應 Modify Request 與 Modification Command | 接受（2026-10-22） |
| [0006](adr/0006-pti-unassigned-for-network-initiated.md) | 網路發起的 Command 使用「No procedure transaction identity assigned」 | 提案 |
| [0007](adr/0007-report-inactive-rules-to-pcf.md) | RAN 拒絕或釋放語音 QFI 時以 ruleReports 回報 PCF，並自行移除規則 | 提案 |
| [0008](adr/0008-track-synced-snapshot.md) | SMF 自行保存最後同步的內容來偵測 QoS flow 修改 | 提案 |
| [0009](adr/0009-defer-until-up-active.md) | UP 連線未啟動時不送 N1N2，啟動後只送 N1 同步 | 提案 |
| [0010](adr/0010-qnc-needs-pcf-fix.md) | W5d 在 SMF 照規格做；端到端需要 PCF 補 QOS_NOTIF 內容 | 提案 |

ADR 狀態：提案 → 接受 → （被取代／廢止）。接受後不改內容，要改就新增一張取代它。

## 文件版本

| 版本 | 日期 | 變更 |
|---|---|---|
| v0.1 | 2026-10-22 | 第一版。原本只有 [vonr-ims-nf-plan.md](../overview/vonr-ims-nf-plan.md) W5、W6 的幾行描述，沒有獨立設計文件 |
| v0.2 | 2026-10-22 | 納入 W5c：interface-spec §8A（REQ-RPT-01～07）、REQ-RAN-06、轉移表新列；ADR-0007；test-plan T27–T32、L3c；D04 補上 TS 29.513 Table 7.3.2-1；D10 |
| v0.3 | 2026-10-22 | 納入 W5b、W5d：interface-spec §8B（REQ-MOD、REQ-SYNC）、§8C（REQ-QNC）、REQ-RAN-07、08、附錄 D；REQ-XFER-02 改為 `ATTEMPTING_TO_REACH_UE` 視為沒送達；ADR-0008～0010；test-plan T33–T42、L3d、L3e；D11～D13 |
