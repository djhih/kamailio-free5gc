# ADR-0008：UDM 以 Diameter client 角色送 RTR、PPR，目的地用 S-CSCF 的 Origin-Host

- 狀態：提案
- 日期：2026-10-22
- 取代：[ADR-0007](0007-no-rtr-ppr-in-w8a.md) 在 W8b（`cx.w8b.enable` 為 true）時的效力
- 相關：D15、D16

## 背景

- TS 29.229 V17.3.0 §5.5：HSS 發起的請求必須帶 Destination-Host 與 Destination-Realm；TS 29.228 Table 6.1.3.1、Table 6.2.2.1 也把 Destination-Host 列為 M，值取自更新 S-CSCF 名稱時那台 S-CSCF 的 Origin-Host。
- Server-Name 是 SIP URI（`sip:scscf…:6060`），Diameter 的 Origin-Host 是 `scscf.ims.mnc093.mcc208.3gppnetwork.org`（`scscf.xml`），兩者不同。
- S-CSCF 的 cdp 在 3870 收連線（`AcceptUnknownPeers="1"`），也主動連 HSS 的 3868。用哪條連線送 RTR／PPR、Kamailio 是否處理 304／305，本機沒有原始碼可查。

## 決定

註冊紀錄多存 `scscfDiameterHost`、`scscfDiameterRealm`、`sarImpi`。RTR、PPR 的 Destination-Host、User-Name 一律取自這些欄位。連線方式先實作「沿用 S-CSCF 連進來的連線」，G1 抓包驗證；不行再改主動連 3870（D15）。

## 後果

- 好處：符合 §5.5；不用從 SIP URI 猜 Diameter 身分。
- 代價：註冊紀錄多三個欄位；要支援雙向的 Diameter 請求。
- 對應需求：REQ-CLI-01～05；測試：T35、T36
