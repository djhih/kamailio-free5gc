# ADR-0001：HSS 功能實作在 free5gc UDM 內，對 Kamailio 提供 Cx

- 狀態：提案（使用者已在 2026-10-15 選定 B 計畫，待正式接受）
- 日期：2026-10-22
- 取代：[archive/design-v0.1.md](../archive/design-v0.1.md) §1、§2
- 相關：[vonr-ims-nf-plan.md](../../overview/vonr-ims-nf-plan.md) W8；[ADR-0004](0004-ims-data-in-udr-extension.md)

## 背景

- 現況是 PyHSS 提供 Cx，5G 用戶資料在 UDR，兩份資料靠開戶腳本對齊，SQN 各算各的（[design.md](../design.md) §2）。
- TS 23.228 V17.3.0 附錄 Y.0 允許「HSS as part of the UDM」，但要求 HSS 的 IMS 功能在邏輯上維持獨立；對 CSCF 的介面是 Cx 或 N70（附錄 AA）。
- Kamailio 的 `ims_icscf`、`ims_auth`、`ims_registrar_scscf` 只會講 Cx（`kamailio-free5gc` 的 cfg）。
- 2026-10-15 評估了四個選項：維持 PyHSS、併入 UDM、獨立 HSS NF、只統一開戶。使用者選了「併入 UDM」。

## 決定

在 free5gc UDM 內新增 HSS 子系統 `internal/cx`，以 Diameter server 角色對 I-CSCF、S-CSCF 提供 Cx（UAR、MAR、SAR、LIR），取代 PyHSS。Diameter 身分沿用 PyHSS 的 `hss.ims.mnc093.mcc208.3gppnetwork.org`，Kamailio 的 cdp 設定不用改。子系統可以用設定關閉，關閉時 UDM 與上游行為相同。

## 後果

- 好處：認證向量與 SQN 取號只有一套實作（[ADR-0002](0002-shared-auth-data-and-sqn.md)）；少了 PyHSS 的 4 個容器；Kamailio 不用改。
- 代價：要維護 UDM 的 fork，而且 UDR 也要 fork（[ADR-0004](0004-ims-data-in-udr-extension.md)）；Cx 進 UDM 不符合 free5gc 上游方向，不會發 PR；UDM 要同時接 corenet 與 dnnet。
- 與標準的關係：部署方式符合附錄 Y.0；介面用的是 Cx 而不是 5GS 的 N70。
- 保留的出路：狀態機（`statemachine.go`）不依賴 Diameter；之後要做 N70 時，在旁邊加 Nhss_ims producer 共用即可（[design.md](../design.md) §6 方案 A）。
- 對應需求：REQ-GEN-01、REQ-GEN-02、REQ-PEER-06；測試：T02、T26、T27
