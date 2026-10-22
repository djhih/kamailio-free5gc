# ADR-0002：一個 Rx session 對應一個 PCF app session

- 狀態：提案
- 日期：2026-10-22
- 相關：計畫 [vonr-ims-nf-plan.md](../../overview/vonr-ims-nf-plan.md) §7 第 1 項（ADR 是否接受）；與 2024 年碩論模型的比較見 [ims-af-thesis-comparison.md](../../background/ims-af-thesis-comparison.md)

## 背景

一通電話有主叫、被叫兩段，`ims_qos` 對每段各開一個 Rx session（不同 Session-Id、不同 Framed-IP）。2024 年實驗室碩論的 IMS-AF 改用「每支 UE 一個 app session」，把同一支 UE 的媒體合併（比較見 [ims-af-thesis-comparison.md](../../background/ims-af-thesis-comparison.md)）。

## 決定

一個 Rx session 對應一個 app session。不以 UE 身分、SIP Call-ID 當資源 key。

## 後果

- STR 與 app session 的刪除一一對應，清理一個 session 不會影響同一支 UE 的另一通電話（T13）。
- 與 TS 29.513 的 Rx ↔ N5 對應方式一致（待 D02 核對附錄 B）。
- 同一支 UE 同時兩通電話時，PCF 上會有兩個 app session；這是預期行為。
- 不需要在 Adapter 裡合併、拆分媒體元件，mapper 保持純對應。
