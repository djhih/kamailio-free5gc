# ADR-0005：IMS 身分到 SUPI 一律查開戶時寫入的索引，不由字串推導

- 狀態：提案
- 日期：2026-10-22
- 取代：無（把 [archive/design-v0.1.md](../archive/design-v0.1.md) §5.3 的作法定為決策）
- 相關：Rx／N5 Adapter 的 [ADR-0003](../../rx-n5/adr/0003-reject-unbindable-identity.md)

## 背景

- 實驗的開戶規則讓 IMPU 的 user part 剛好是 IMSI（`04-add-ims-subscribers.sh`），所以「從 IMPU 推出 SUPI」在這裡能用。
- 但這只是開戶慣例，不是規格保證。TS 23.003 §13.3 只規定「沒有 ISIM 時 IMPI 由 IMSI 推導」；IMPU 可以是任何 SIP URI 或 Tel URI（§13.4）。
- Rx／N5 Adapter 也需要 IMPU → SUPI 的對應，它的 ADR-0003 提到 W8 完成後可以改由 UDM／UDR 提供。

## 決定

Cx 收到的 IMPI、IMPU 一律查 UDR 的身分索引（開戶時寫入、以 canonical IMPU 為 key）找 SUPI。查不到就回 DIAMETER_ERROR_USER_UNKNOWN，不嘗試推導。

## 後果

- 好處：換開戶規則（例如加 MSISDN 形式的 IMPU）不用改程式；錯誤是明確的「找不到」，不是綁錯人。
- 代價：開戶必須寫索引；多一次 UDR 查詢。
- 保留的出路：身分索引可以開放給 Rx／N5 Adapter 查詢，取代它自己的推導規則。
- 對應需求：REQ-ID-01～04、REQ-DATA-02、REQ-DATA-03；測試：T04、T25
