# ADR-0003：身分無法安全綁定時拒絕，不退回只用 UE IP

- 狀態：提案
- 日期：2026-10-22
- 取代：v0.1 設計 §4.2 的「推不出 SUPI 就只用 `ueIpv4` 綁定」

## 背景

`ims_qos` 的 Subscription-Id 預設送 IMPU（SIP URI），不是 IMSI。free5gc PCF 只靠 UE IP 找 PDU session 時，搜尋迴圈找到後不會停，多 UE 時可能綁到錯的 session（`af/main.go` 已記錄）。「IMPU 的 user part 就是 IMSI」只在本專案的開戶腳本（`04-add-ims-subscribers.sh`）下成立。

## 決定

- SUPI 由明確的開戶 mapping 取得。
- IMPU 推導是可選功能，預設關閉；開啟時要求 user part 為 15 位數字且 realm 符合設定。
- 兩者都綁不出來時，拒絕 AAR，不呼叫 PCF。

## 後果

- 不會因為綁錯 UE 而把語音 QoS 裝到別人的 PDU session 上。
- 開戶資料不一致時通話會建立失敗，而不是「看起來成功但 QoS 給錯人」。錯誤會比較早、比較明顯。
- 要多維護一份 IMPU → SUPI mapping（W8 完成後可改由 UDM／UDR 提供）。
- 對應需求：REQ-AAR-03；測試：T02、T23。
