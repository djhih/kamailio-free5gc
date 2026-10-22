# ADR-0006：網路發起的 Modification Command 使用「No procedure transaction identity assigned」

- 狀態：提案
- 日期：2026-10-22

## 背景

- TS 24.501 V17.18 §6.3.2.2：不是由 UE 要求觸發的網路發起修改，PTI 必須設為「No procedure transaction identity assigned」；由 UE 要求觸發時才沿用 UE 的 PTI。
- free5gc 的 `BuildGSMPDUSessionModificationCommand` 一律用 `smContext.Pti`，也就是 UE 最近一次 5GSM 程序的 PTI。

## 決定

builder 的 PTI 改由呼叫者傳入：UE 發起的路徑傳 UE 的 PTI（行為不變），PCF 觸發的路徑傳「未指派」。

## 後果

- 好處：符合 §6.3.2.2；UE 不會把網路發起的 Command 誤認成之前某個 UE 程序的回應。
- 代價：要改共用 builder 的介面；UE 發起路徑要回歸測試（T20）。
- 對應需求：REQ-N1-01、REQ-GEN-02；測試：T05、T20
