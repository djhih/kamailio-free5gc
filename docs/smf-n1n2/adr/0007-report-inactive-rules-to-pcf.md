# ADR-0007：RAN 拒絕或釋放語音 QFI 時，SMF 以 ruleReports（INACTIVE）回報 PCF，並自行移除對應規則

- 狀態：提案
- 日期：2026-10-22
- 相關：rx-n5 的 [ADR-0008](../../rx-n5/adr/0008-map-failed-resources-to-rar-or-asr.md)；D10

## 背景

- TS 23.228 V17.3.0 Y.2.4.1：語音 QoS flow 遺失時，PCF 與 P-CSCF 要被通知，P-CSCF 結束通話。
- TS 23.502 V17.15.0 §4.3.3.2 步驟 1e：RAN 釋放 QoS flow 時經 AMF 通知 SMF；步驟 2：SMF 可向 PCF 回報。
- free5gc PCF 收到 SM policy update 的 `ruleReports`（狀態非 ACTIVE）時，會刪掉那些 PCC rule，並對訂閱了 FAILED_RESOURCES_ALLOCATION 的 AF 發通知（`pcf/internal/sbi/processor/smpolicy.go`）；刪除時用 `RemovePccRule(pccRuleID, nil)`，不會再通知 SMF。
- free5gc SMF 從不送 ruleReports，也沒有處理 `PDU_RES_NTY`。

## 決定

SMF 在兩種情況回報 INACTIVE：程序完成時 RAN 新增失敗的 QFI，以及 RAN 經 `PDU_RES_NTY` 主動釋放的 QFI。回報後 SMF 自行移除那些 PCC rule 與 UPF 規則，並把 QoS rule 從 UE 刪除（RAN 已釋放的 QFI 只送 N1）。PCF 自己刪除的規則不回報。

## 後果

- 好處：補上「RAN → SMF → PCF → Adapter → Kamailio」的鏈，讓 Y.2.4 的要求可以端到端驗證；不用改 PCF。
- 代價：SMF 與 PCF 對「誰刪規則」各做一半，要靠 REQ-RPT-04 保持一致；ruleReports 的細節要等 TS 29.512 核對（D10）。
- 對應需求：REQ-RPT-01～07、REQ-RAN-06；測試：T27～T32
