# ADR-0008：SMF 自行保存「最後同步給 RAN／UE 的內容」來偵測 QoS flow 修改

- 狀態：提案
- 日期：2026-10-22

## 背景

- free5gc SMF v1.4.6 的 `ApplyPccRules`：PCC rule 的 QoS data 改變時，用 `reflect.DeepEqual` 偵測，接著 `PreRemoveDataPath` 再 `CreatePccRuleDataPath`；後者呼叫 `AddQosFlow`，用新物件覆蓋 `AdditionalQosFlows[qfi]`，狀態是 `QoSFlowUnset`。
- `QoSFlowToBeModify` 只有宣告與判斷，從未被指派。
- QFI 由 QoS data ID 決定（`AssignQFI` 先查 `qosDataToQFI`），PCF 不換 ID 時 QFI 不變。

## 決定

SMF 為每個已同步的 QFI 保存最後同步的 5QI、ARP、GFBR、MFBR 與 QoS rule 的 packet filter。差異計算時，QFI 相同但內容不同的就是 TO_MODIFY，依 [interface-spec.md](../interface-spec.md) REQ-MOD-03 選 QoS rule 與 flow description 的操作碼。

## 後果

- 好處：不必改 `ApplyPccRules` 的重建方式；修改與新增分得清楚。
- 代價：多一份狀態，要在刪除、PDU session 釋放時一起清掉。
- 對應需求：REQ-MOD-01～06；測試：T33、T34
