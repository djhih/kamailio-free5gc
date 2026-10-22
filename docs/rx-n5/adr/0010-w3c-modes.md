# ADR-0010：W3c 分成 off、local、n5 三種模式，預設 local

- 狀態：提案
- 日期：2026-10-22
- 相關：[interface-spec.md](../interface-spec.md) §8B、附錄 E

## 背景

TS 29.513 B.5～B.8 規定 P-CSCF 在 IMS 註冊時，可以向 PCF 訂閱信令路徑狀態、提供 SIP 信令 flow、訂閱 access type 與 PLMN 變更（都是 optional）。讀 free5gc 原始碼發現，在現有 PCF、SMF 上照規格做會造成傷害（附錄 E）：

- 照 TS 29.514 §4.2.6.7 用 `fNum` 0 訂閱，會產生一條沒有 flow 的 PCC rule，使 SMF 之後每一次 policy 更新都失敗，語音 QoS 全部失效。
- 照 §4.2.2.16 提供 SIP 信令 flow，PCF 會建 5QI 9 的規則，把 SIP 從 5QI 5 的預設 flow 搬走。
- SMF 從不回報 access type、PLMN 變更，所以訂閱只拿得到現值。

## 決定

- `off`：拒絕註冊時的 AAR（W3a 的行為）。
- `local`（預設）：Adapter 接受註冊時的 AAR、回成功，但不呼叫 PCF；同 UE 的媒體 session 被 terminate 時，對信令 session 送 ASR。
- `n5`：照規格建立 app session、訂閱事件，只有在附錄 E 的 PCF／SMF 修改完成並在設定宣告後才可啟用。

## 後果

- 好處：Kamailio 可以照常呼叫 `Rx_AAR_Register`，不會因 Adapter 拒絕而註冊失敗；不會傷到語音 QoS；PCF 修好後可以直接切到 `n5`。
- 代價：`local` 模式在 UE 沒有通話時，得不到 PDU session 結束的通知；AAA 不帶 access type 與 PLMN。這不符合 B.5～B.8 的完整意圖，只是避免傷害的折衷。
- 對應需求：REQ-REG-01～10、REQ-KAM-11；測試：T53～T58
