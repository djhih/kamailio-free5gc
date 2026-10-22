# ADR-0003：SQN 取號改成 UDR 端的原子操作，5G-AKA 路徑一起改

- 狀態：提案
- 日期：2026-10-22
- 取代：[archive/design-v0.1.md](../archive/design-v0.1.md) §9 第三點（「第一階段先記錄，必要時改成原子遞增」）
- 相關：[ADR-0002](0002-shared-auth-data-and-sqn.md)；D06

## 背景

- 現行 UDM 的 `GenerateAuthDataProcedure`：用 `QueryAuthSubsData` 讀出 SQN，在記憶體加 1，再用 JSON Patch `replace /sequenceNumber` 寫回（`udm/internal/sbi/processor/generate_auth_data.go`）。
- UDR 的 `PatchDataToDBAndNotify` 也是先讀整份文件、套用 patch、再整份更新（`udr/internal/database/mongodb/mongo_db_inplement.go`、free5gc util `RestfulAPIJSONPatch`），沒有以舊值為條件。
- 只有 5G-AKA 時，同一個 SUPI 很少同時認證；共用 SQN 之後，5G 註冊與 IMS 註冊可能同時發生。兩個請求讀到同一個 SQN，就會發出相同 SQN 的向量；真的 USIM 會把第二組當成重放而觸發重新同步。實驗的 free-ran-ue 不檢查 SQN 新鮮度，所以這種錯誤在端到端測試裡看不出來。
- JSON Patch 的 `test` 操作也救不了：UDR 是在讀出的副本上檢查，寫回時沒有條件。

## 決定

UDR 擴充新增 `sqn-allocations`（[interface-spec.md](../interface-spec.md) §12），以「目前 SQN 等於讀到的值」為條件，用單一資料庫條件式更新完成取號，衝突時在 UDR 內重試。UDM 的 5G-AKA 路徑與 IMS AKA 路徑都改用它。實作方式在 D06 關閉時定案。

## 後果

- 好處：不變量 I1（每組向量的 SQN 都不同）在並行下成立。
- 代價：動到 UDM 原本的 5G-AKA 流程，需要 5G 回歸測試（T26）；UDR 多一個非標準端點；取號後如果後續步驟失敗，SQN 會跳號（允許，REQ-AUTH-09）。
- 保留的出路：如果之後上游 UDR 提供原子遞增，可以換掉擴充端點，UDM 端只改 client。
- 對應需求：REQ-AUTH-02、REQ-AUTH-03、REQ-AUTH-09、REQ-DATA-05；測試：T14、T15、T26
