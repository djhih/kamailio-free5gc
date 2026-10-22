# ADR-0009：AAR 更新時，只改頻寬或 codec 用 PATCH，其他變更先 Delete 再 Create

- 狀態：提案
- 日期：2026-10-22
- 取代：[ADR-0006](0006-no-aar-update-in-phase1.md) 在 W3d（`w3d.enable` 為 true）時的效力；W3a 仍依 ADR-0006
- 相關：smf-n1n2 的 W5b

## 背景

讀 free5gc PCF v1.4.5 原始碼（`internal/sbi/processor/policyauthorization.go`）得到的行為：

1. PATCH 時先用 `removeMediaComp()` 刪舊規則，但只到當初 POST 的 `medComponents` 找；PATCH 加入的元件不會寫回。所以同一個元件第二次以後的 PATCH 找不到舊規則。
2. 接著 `handleMediaSubComponent()` 用 Flow-Description 比對既有 PCC rule（`GetPccRuleByFlowInfos`）：**找得到就沿用並只更新 QoS**，找不到才建新規則。
3. Flow-Status 只影響新建規則的 packet filter 方向（`getFlowInfos` 的 `PacketFilterUsage`）；沿用既有規則時不會更新。
4. PATCH 沒帶 `evSubsc` 會清掉事件訂閱。

由 2：flow 沒變、只改頻寬時，不論第幾次 PATCH 都會找到同一條規則並更新 QoS，是安全的。由 1、3：flow 或 Flow-Status 改了，第二次以後的 PATCH 會留下舊規則，或方向設定不生效。

另外，同一支 UE 兩個 app session 的 flow 相同時，PCF 會讓它們共用同一條 PCC rule；刪掉其中一個會連帶刪掉共用的規則。所以不能先 Create 新的再 Delete 舊的。

## 決定

- 只改頻寬或 codec：PATCH，且一律帶 `evSubsc`。
- flow、Flow-Status 或 media component 有任何改變：先 Delete 舊的 app session，成功後再 Create 新的（break-before-make）。

## 後果

- 好處：不改 PCF 也不會留下孤兒規則；hold／resume（Flow-Status 改變）能正確生效。
- 代價：break-before-make 期間 UPF 短暫沒有語音規則；SMF 會看到「刪 QFI、再加新 QFI」兩次 policy 更新，等於兩個網路發起修改程序（smf-n1n2 ADR-0003 會依序處理）。Create 失敗時 Rx session 會處在沒有資源的狀態（NO_RESOURCE）。
- 保留的出路：PCF 若修好第 1、3 點，可以改成一律 PATCH，只要改 REQ-UPD-01 的分類。
- 對應需求：REQ-UPD-01～07、REQ-KAM-10；測試：T46～T52
