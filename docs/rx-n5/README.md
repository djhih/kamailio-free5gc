# Rx／N5 Adapter 文件

> 對應計畫：[vonr-ims-nf-plan.md](../overview/vonr-ims-nf-plan.md) 的 W3 與 W4（本組文件涵蓋 W3a～W3d、W4，以及 W5d 的 Adapter 端）
> 狀態：設計審查中（v0.2，2026-10-22），尚未實作

## 先看哪份

| 文件 | 回答什麼問題 | 性質 | 給誰看 |
|---|---|---|---|
| [explained.md](explained.md) | Adapter 要做什麼？用一通電話走一遍 | 說明（informative） | 第一次接觸的人 |
| [design.md](design.md) | 為什麼這樣設計？考慮過哪些替代方案？有什麼風險？ | 設計文件 | 指導者、評審 |
| [interface-spec.md](interface-spec.md) | Adapter 必須怎麼表現？每一條需求是什麼？ | 規格（normative，需求有編號） | 實作者 |
| [test-plan.md](test-plan.md) | 怎麼證明需求都做到了？ | 測試計畫 | 測試者、驗收者 |
| [adr/](adr/) | 每個關鍵決策的背景、決定與代價 | 決策紀錄 | 想知道「為什麼不用 X」的人 |

**以哪份為準：** 行為以 [interface-spec.md](interface-spec.md) 為準；理由以 [design.md](design.md) 與 ADR 為準；兩者衝突時視為文件錯誤，要開 issue 修正，不自行挑一份照做。工作順序與時程在 [vonr-ims-nf-plan.md](../overview/vonr-ims-nf-plan.md) W3。

## 決策紀錄

| # | 決策 | 狀態 |
|---|---|---|
| [0001](adr/0001-standalone-adapter.md) | Adapter 是獨立程序，不把 Rx 加進 free5gc PCF | 提案 |
| [0002](adr/0002-one-app-session-per-rx-session.md) | 一個 Rx session 對應一個 PCF app session | 提案 |
| [0003](adr/0003-reject-unbindable-identity.md) | 身分無法安全綁定時拒絕，不退回只用 UE IP | 提案 |
| [0004](adr/0004-no-blind-create-retry.md) | Create 結果不明時不自動重送 | 提案 |
| [0005](adr/0005-keep-resource-until-delete-confirmed.md) | 刪除未確認前保留資源 URI 並有限重試 | 提案 |
| [0006](adr/0006-no-aar-update-in-phase1.md) | 第一階段不支援 AAR 更新（PATCH） | 提案 |
| [0007](adr/0007-delete-then-asr-on-terminate.md) | 收到 terminate 後先回 204 並刪除 app session，再送 ASR | 提案 |
| [0008](adr/0008-map-failed-resources-to-rar-or-asr.md) | 資源全部失效送 ASR，部分失效依訂閱送 RAR（4 或 9） | 提案 |
| [0009](adr/0009-patch-or-replace-on-aar-update.md) | AAR 更新：只改頻寬或 codec 用 PATCH，其他變更先 Delete 再 Create | 提案 |
| [0010](adr/0010-w3c-modes.md) | W3c 分成 off、local、n5 三種模式，預設 local | 提案 |
| [0011](adr/0011-qos-notif-approximate-mapping.md) | QOS_NOTIF 以 Specific-Action 2／3 近似對應 | 提案 |

ADR 狀態：提案 → 接受 → （被取代／廢止）。接受後不改內容，要改就新增一張取代它。

## 文件版本

| 版本 | 日期 | 變更 |
|---|---|---|
| v0.1 | 2026-10-14 | 原 `docs/overview/rx-n5-adapter-design.md`：介面、程式結構、對應表（[archive/design-v0.1.md](archive/design-v0.1.md)） |
| v0.1 spec | 2026-10-22 | 原 `docs/rx-n5-adapter-spec-v0.1.md`：補異常處理、狀態機、分層驗收（[archive/spec-v0.1.md](archive/spec-v0.1.md)） |
| v0.2 | 2026-10-22 | 拆成 design／interface-spec／test-plan／ADR；需求編號化並與測試對應；補替代方案、狀態轉移表、時序圖、安全考量、風險 |
| v0.3 | 2026-10-22 | W4（Kamailio P-CSCF 改用 `ims_qos`）從參考附錄改成正式需求：interface-spec §14 REQ-KAM-01～09、test-plan T30–T34、design D09 |
| v0.4 | 2026-10-22 | 納入 W3b（5GC 回報）：interface-spec §8A（REQ-EVT、REQ-ASR、REQ-RAR）、§9.2 新增 ABORTING 與 W3b 的轉移、§10.3 對應表；ADR-0007、0008；test-plan T35–T45、L2b；re-INVITE 改列為 W3d |
| v0.5 | 2026-10-22 | 納入 W3d（通話中修改）：interface-spec §5.4（REQ-UPD-01～07）、REQ-KAM-10、新狀態 UPDATING／REPLACING／RECREATING／NO_RESOURCE；ADR-0009；test-plan T46–T52、L2c；design D12 |
| v0.6 | 2026-10-22 | 納入 W3c（§8B，REQ-REG、REQ-BSF，附錄 E）與 W5d 的 Adapter 端（§8A.4，REQ-QOS）；REQ-EVT-03 的路徑補上 `/notify`；REQ-KAM-11；ADR-0010、0011；test-plan T53–T62、L2d；design D13～D15 |
