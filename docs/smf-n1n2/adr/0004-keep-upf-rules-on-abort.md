# ADR-0004：程序中止時保留 UPF 已套用的規則，把差異標為 TO_SYNC，不回退

- 狀態：提案
- 日期：2026-10-22

## 背景

- TS 24.501 V17.18 §6.3.2.5 a：T3591 第 5 次逾時，SMF 中止程序；之後「may continue to use the previous configuration of the PDU session or initiate the network-requested PDU session release procedure」，並可把 QoS rule 標成「to be synchronised with the UE」。
- 本設計在送 N1N2 之前就已經更新 UPF（TS 23.502 §4.3.3.2 步驟 2a）。PCF 那邊，app session 也已經建立或刪除。

## 決定

中止時不回退 UPF，也不釋放 PDU session；把這次的新增與刪除標成 TO_SYNC，在下一次程序一起送。

## 後果

- 好處：與 PCF 的 policy 一致；不會因為 UE 一次沒回應就讓整個 PDU session 被釋放。
- 代價：中止到下一次程序之間，UPF 與 UE／RAN 不一致。實驗中只影響 QoS 標記，因為 free-ran-ue 的 GTP-U 不看 QFI。
- 保留的出路：W5b 可以加上「中止後一段時間仍無法同步就釋放 PDU session」的策略。
- 對應需求：REQ-ST-04、REQ-XFER-02、REQ-RSP-05；測試：T10、T14、T15
