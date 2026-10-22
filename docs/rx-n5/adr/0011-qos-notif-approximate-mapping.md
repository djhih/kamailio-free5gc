# ADR-0011：QOS_NOTIF 以 Specific-Action 2／3 近似對應，沒有 qncReports 時不轉送

- 狀態：提案
- 日期：2026-10-22
- 相關：smf-n1n2 的 ADR-0010

## 背景

- TS 29.514 V17.9.0 §4.2.5.4：PCF 以 QOS_NOTIF 通知 AF，`qncReports` 的 `notifType` 為 NOT_GUARANTEED 或 GUARANTEED。
- TS 29.214 V17.6.0 §5.3.13 沒有「GFBR 無法保證」的 Specific-Action。最接近的是 INDICATION_OF_LOSS_OF_BEARER(2)（GBR bearer 頻寬降為 0）與 INDICATION_OF_RECOVERY_OF_BEARER(3)。手上的 TS 29.513、29.214 沒有找到正式的對應。
- free5gc PCF 轉給 AF 的 QOS_NOTIF 沒有 `qncReports`。

## 決定

AAR 訂閱了 2 或 3 時，Adapter 在 N5 訂閱 QOS_NOTIF。收到帶 `qncReports` 的通知：NOT_GUARANTEED 送 RAR(2)，GUARANTEED 送 RAR(3)。沒有 `qncReports` 時只記錄。預設關閉（`w5d.enable: false`），PCF 修好後再開。

## 後果

- 好處：Kamailio 訂閱的事件有機會被觸發；不會因 PCF 缺內容而誤報。
- 代價：這是語意近似，不能宣稱符合標準的互通對應；Kamailio 收到 RAR(2) 的反應未知（D10）。
- 對應需求：REQ-QOS-01～03；測試：T59、T60
