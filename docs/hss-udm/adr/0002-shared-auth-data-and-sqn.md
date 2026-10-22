# ADR-0002：IMS AKA 與 5G-AKA 共用同一組 K、OPc、AMF、SQN

- 狀態：提案
- 日期：2026-10-22
- 取代：[archive/design-v0.1.md](../archive/design-v0.1.md) §5.1（把共用 SQN 當成「好處」，本 ADR 改以規格要求為依據）
- 相關：[ADR-0003](0003-atomic-sqn-allocation.md)

## 背景

- TS 33.203 §8.2：用 USIM 做 IMS 存取時，唯一允許的選項是「authentication key、authentication functions 與 sequence number checking mechanism 都共用」；而且要求在 CS、PS、IMS 三個 domain 交錯認證時，同步失敗率要夠低（範例方法在附錄 G）。
- 實驗沒有 ISIM：IMPI 由 IMSI 推導（TS 23.003 §13.3），屬於 USIM-based IMS 存取。
- free5gc UDM 每產生一組向量就把 SQN 加 1（`generate_auth_data.go`），等於 TS 33.102 C.3.4 一般規則下的 IND 循環配置。USIM 的 array 機制（C.2.2）能容忍交錯。

## 決定

IMS AKA 直接使用 UDR `authenticationSubscription` 裡的 K、OPc、AMF、SQN，不另存一份。取號、重新同步與 Milenage 抽成 5G-AKA 與 IMS AKA 共用的函式。是否替 IMS 保留專屬的 IND 範圍（TS 33.203 附錄 G 的建議）留給 D07。

## 後果

- 好處：符合 TS 33.203 §8.2；開戶只寫一次；真實手機上不會因為兩個計數器互相超前而頻繁重新同步。
- 代價：5G-AKA 與 IMS AKA 會互相影響 SQN，取號必須原子（[ADR-0003](0003-atomic-sqn-allocation.md)）；回退到 PyHSS 時又會分成兩份。
- 驗證上的限制：實驗的 free-ran-ue 不檢查 SQN 新鮮度（`ue/security.go`），所以要用 USIM 模型的單元測試證明正確性（T13）。
- 對應需求：REQ-AUTH-01、REQ-AUTH-04、REQ-AUTH-05、REQ-AUTH-07；測試：T11、T13、T27
