# HSS 併入 UDM 文件

> 對應計畫：[vonr-ims-nf-plan.md](../overview/vonr-ims-nf-plan.md) 的 W8（本組文件涵蓋 W8a 與 W8b）
> 狀態：設計審查中（v0.3，2026-10-22），尚未實作

## 先看哪份

| 文件 | 回答什麼問題 | 性質 | 給誰看 |
|---|---|---|---|
| [explained.md](explained.md) | UDM 怎麼取代 PyHSS？用一支手機從開機走到解除註冊 | 說明（informative） | 第一次接觸的人 |
| [design.md](design.md) | 為什麼這樣設計？考慮過哪些替代方案？有什麼風險？ | 設計文件 | 指導者、評審 |
| [interface-spec.md](interface-spec.md) | UDM 的 Cx 必須怎麼表現？每一條需求是什麼？ | 規格（normative，需求有編號） | 實作者 |
| [test-plan.md](test-plan.md) | 怎麼證明需求都做到了？ | 測試計畫 | 測試者、驗收者 |
| [adr/](adr/) | 每個關鍵決策的背景、決定與代價 | 決策紀錄 | 想知道「為什麼不用 X」的人 |

**以哪份為準：** 行為以 [interface-spec.md](interface-spec.md) 為準；理由以 [design.md](design.md) 與 ADR 為準；兩者衝突時視為文件錯誤，要修正，不自行挑一份照做。工作順序與時程在 [vonr-ims-nf-plan.md](../overview/vonr-ims-nf-plan.md) W8。

## 決策紀錄

| # | 決策 | 狀態 |
|---|---|---|
| [0001](adr/0001-hss-in-udm-over-cx.md) | HSS 功能實作在 free5gc UDM 內，對 Kamailio 提供 Cx | 提案（使用者已選定，待正式接受） |
| [0002](adr/0002-shared-auth-data-and-sqn.md) | IMS AKA 與 5G-AKA 共用同一組 K、OPc、AMF、SQN | 提案 |
| [0003](adr/0003-atomic-sqn-allocation.md) | SQN 取號改成 UDR 端的原子操作，5G-AKA 路徑一起改 | 提案 |
| [0004](adr/0004-ims-data-in-udr-extension.md) | IMS 資料與註冊狀態存在 UDR 的非標準擴充 | 提案 |
| [0005](adr/0005-explicit-identity-mapping.md) | IMS 身分到 SUPI 一律查索引，不由字串推導 | 提案 |
| [0006](adr/0006-uaa-capabilities-on-first-registration.md) | 第一次註冊的 UAA 只回 Server-Capabilities，不回 Server-Name | 提案 |
| [0007](adr/0007-no-rtr-ppr-in-w8a.md) | W8a 不做 RTR、PPR 與 IMS restoration | 提案 |
| [0008](adr/0008-udm-as-diameter-client.md) | UDM 以 Diameter client 角色送 RTR、PPR，目的地用 S-CSCF 的 Origin-Host | 提案 |
| [0009](adr/0009-update-state-after-rta.md) | PERMANENT_TERMINATION 與 SERVER_CHANGE 收到 RTA 後才更新狀態 | 提案 |
| [0010](adr/0010-rta-ppa-failure-policy.md) | RTA、PPA 失敗時有限重試；刪除開戶資料不因 RTA 失敗而停止 | 提案 |

ADR 狀態：提案 → 接受 → （被取代／廢止）。接受後不改內容，要改就新增一張取代它。

## 文件版本

| 版本 | 日期 | 變更 |
|---|---|---|
| v0.1 | 2026-10-15 | 原 `docs/overview/hss-in-udm-design.md`：Cx 速查、程式位置、UDR 擴充、實作順序（[archive/design-v0.1.md](archive/design-v0.1.md)） |
| v0.2 | 2026-10-22 | 拆成 design／interface-spec／test-plan／ADR。依 TS 29.228 逐條改寫 UAR、MAR、SAR、LIR 的行為與完整轉移表；第一次註冊不回 Server-Name；共用 SQN 改以 TS 33.203 §8.2 為依據；新增 SQN 原子取號；區分 Result-Code 與 Experimental-Result |
| v0.3 | 2026-10-22 | 納入 W8b：interface-spec §8A（REQ-CLI、REQ-RTR、REQ-PPR）、註冊紀錄新增 `scscfDiameterHost`／`sarImpi`、轉移表、附錄 C 的 AVP；ADR-0008～0010；test-plan T35–T44；design D15、D16 |
