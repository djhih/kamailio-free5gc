# ADR-0001：在 SMF（fork）實作 PCF 觸發的網路發起 PDU Session Modification

- 狀態：提案
- 日期：2026-10-22
- 取代：[vonr-ims-nf-plan.md](../../overview/vonr-ims-nf-plan.md) W5 的「改哪裡」（原本寫「可重用現有的 builder」，本 ADR 寫明哪些要改）
- 相關：[ADR-0002](0002-derive-qos-flow-diff-from-pcc-rules.md)、[ADR-0005](0005-patch-free-ran-ue-responder.md)

## 背景

- TS 23.502 V17.15.0 §4.3.3.2：PCF 發起 SM Policy Association Modification（步驟 1b）後，SMF 更新 UPF（2a），再以 Namf_Communication_N1N2MessageTransfer 送 N2 SM information 與 PDU Session Modification Command（3b）。
- free5gc SMF v1.4.6 的 `HandleSMPolicyUpdateNotify` 只做到 2a；`BuildGSMPDUSessionModificationCommand` 沒有 QoS rule、flow description；N2 builder 沒有釋放清單（[design.md](../design.md) §2）。
- AMF 已能轉送 `PDU_RES_MOD_REQ`，SMF 已能處理 `PDU_RES_MOD_RSP` 與 Complete。

## 決定

在 SMF 的 fork 中，於 PCC rule 與 PFCP 都套用成功之後，依 [interface-spec.md](../interface-spec.md) 組出 N1 與 N2，以一次 N1N2 送出，並用獨立的程序狀態機處理回應、T3591 與衝突。功能有開關，關閉時與上游相同。

## 後果

- 好處：UPF、RAN、UE 的 QoS flow 一致，符合 23.502 的流程。
- 代價：多維護一個 SMF fork（與 W8 的 UDM／UDR 同一個 free5gc 版本，D01）；`QoSFlow` 要加同步狀態。
- 保留的出路：程序狀態機與差異計算是純函式，之後發 PR 回上游時可以單獨拿出來（D09）。
- 對應需求：REQ-GEN-01～04、REQ-N1-01～05、REQ-N2-01～04、REQ-XFER-01～03；測試：T05、T07、T09、T19、T24
