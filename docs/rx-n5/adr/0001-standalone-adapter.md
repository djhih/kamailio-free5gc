# ADR-0001：Adapter 是獨立程序，不把 Rx 加進 free5gc PCF

- 狀態：提案
- 日期：2026-10-22

## 背景

Kamailio `ims_qos` 只會講 Rx，free5gc PCF 只會講 N5。3GPP 預期由 PCF 自己支援 Rx（TS 23.503 附錄 C，章節待 D02 核對），所以「在 PCF 加 Rx」最接近標準。但計畫的設計原則是不改 PCF（[vonr-ims-nf-plan.md](../../overview/vonr-ims-nf-plan.md) §0），而且 SMF（W5）、UDM／UDR（W8）已經要維護 fork。其他選項見 [design.md](../design.md) §6。

## 決定

新寫一個獨立的 Adapter 程序：對 Kamailio 是 Rx server，對 PCF 是 N5 client（AF）。Rx ↔ N5 的對應寫成不碰網路的純函式（`mapper/`），狀態機獨立成 `processor/`。

## 後果

- 好處：PCF 與 Kamailio 都不用改程式；Adapter 可以單獨測試、單獨替換；PCF 升版不受影響。
- 代價：多一個程序與一份狀態。Rx 的失敗語意與 N5 的失敗語意要由 Adapter 自己對齊，這是 `CREATE_UNKNOWN`、`DELETE_PENDING` 存在的原因。
- 保留的出路：`mapper/` 與 `processor/` 不依賴 Adapter 的程序結構，之後若決定把 Rx 放進 PCF，可以整包搬過去。
- 與標準的關係：對外看起來，Adapter＋PCF 合起來扮演「支援 Rx 的 PCF」。文件不能宣稱 free5gc PCF 本身支援 Rx。
