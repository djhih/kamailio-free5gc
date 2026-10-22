# ADR-0004：IMS 資料與註冊狀態存在 UDR 的非標準擴充（獨立 API 前綴）

- 狀態：提案
- 日期：2026-10-22
- 取代：[archive/design-v0.1.md](../archive/design-v0.1.md) §5.2（資源改成以 IMPU 為單位的註冊紀錄，加入版本號與 SQN 取號）
- 相關：[ADR-0001](0001-hss-in-udm-over-cx.md)；D10

## 背景

- TS 29.505 V17.13.0 的 Nudr 沒有 IMS 用戶資料（IMPU、service profile、iFC），只有 UDM 與 HSS 互通用的 `HssSubscriptionInfo`。
- HSS 是有狀態的：要記住每個 IMPU 的註冊狀態、已存 S-CSCF、authPending（TS 29.228 §6.1.1.1、§6.3.1）。
- free5gc 的分工是 UDM 無狀態、資料在 UDR。

## 決定

在 UDR 新增獨立前綴 `/nudr-ims-ext/v1`，提供 ims-subscription、身分索引、ims-registrations（以 IMPU 為單位、帶版本號）、sqn-allocations。UDM 的 HSS 子系統不保存任何只在記憶體的業務狀態。

## 後果

- 好處：UDM 重啟不會遺失註冊狀態（REQ-ST-03）；擴充與標準路徑分開，未來標準加入 IMS 資源時比較不會撞名。
- 代價：要 fork UDR；資源是非標準的，其他 free5gc 部署不能直接用；每個 Cx 請求至少一次 UDR 往返。
- 不採用的替代：UDM 直接連 MongoDB（[design.md](../design.md) §6 方案 E），會讓 UDM 變成有狀態，也破壞分工。
- 對應需求：REQ-DATA-01～06、REQ-ST-01、REQ-ST-03；測試：T23、T24、T25
