# 抓包版端到端測試的測試計畫（W1）

| 項目 | 內容 |
|---|---|
| 版本／狀態 | v0.1／審查中（2026-10-22） |
| 驗證對象 | [interface-spec.md](interface-spec.md) 的 REQ-* |
| 門檻 | 見 [../overview/vonr-ims-nf-plan.md](../overview/vonr-ims-nf-plan.md) W1 |

## 1. 測試案例

這組測試驗證的是**測試工具本身**。層級：U＝用預先錄好的 pcap 與快照跑檢查引擎；E＝在實驗環境實際執行情境。

| ID | 情境 | 層級 | 必須觀察到的結果 |
|---|---|---|---|
| T01 | 現有部署（PyHSS＋shim）跑 `run.sh call`，不加 `--with` | E | §8.1 的檢查全部 PASS，整體 PASS，退出碼 0；每個 PASS 都有證據指標 |
| T02 | 用 T01 的 pcap 製作負面樣本：刪掉 BYE、把 LIA 的結果改成失敗、只留一個方向的 RTP、刪掉 401 | U | 分別只有 CHK-SIP-01、CHK-CX-02、CHK-RTP-01、CHK-REG-02 為 FAIL；整體 FAIL，退出碼 1 |
| T03 | `br-poc-dn` 不存在或抓包啟動失敗 | E | 依賴 `br-poc-dn` 的檢查為 BLOCKED 並寫明原因；整體 INCOMPLETE，退出碼 2 |
| T04 | 找不到 gogtp5g-tunnel | E | CHK-UPF-* 為 BLOCKED；整體 INCOMPLETE，**不是** PASS |
| T05 | 某個步驟逾時（例如 UE2 不接聽） | E | 情境中止；pcap 與快照仍保存；依賴的檢查為 BLOCKED |
| T06 | 一支 UE 註冊失敗（錯誤的 K） | E | sipp 退出碼被記錄；CHK-REG-01 為 FAIL；整體 FAIL |
| T07 | 同一份 pcap 與快照重跑檢查引擎兩次 | U | 兩份 `checks.json` 相同 |
| T08 | 程式審查：判定程式不讀任何容器 log | — | 判定路徑沒有 `docker logs`、log 檔讀取或 grep log 字串 |
| T09 | `manifest.json` 內容 | E | REQ-EV-02 列的欄位全部存在且非空 |
| T10 | `03-call-test.sh`、`05-n5-qos-test.sh` 包裝 | E | 退出碼與 `run.sh` 相同 |
| T11 | `results/` 的版本控制與遮蔽工具 | — | `.gitignore` 涵蓋 `results/`；遮蔽工具處理後的 pcap 中找不到原始 IMSI |
| T12 | 現有部署加 `--with W3a,W4` | E | CHK-W3A-* 為 FAIL（現況還是 shim），證明檢查真的會被啟用與判定 |
| T13 | SBI 解碼：抓包在環境啟動前開始，與環境啟動後才開始 | E | 前者能解出 N5 的 HTTP/2 路徑；後者相關檢查為 BLOCKED 並註明 HPACK 原因（D02 的結論寫回 REQ-DEC-04） |
| T14 | 連跑兩次 | E | 第二次的 pcap 時間全部在第二次的執行時間窗內 |
| T15 | 新增一個檢查（例如 CHK-W2-01） | — | 只需新增檢查定義，不改情境腳本 |

## 2. 需求追溯

| 需求 | 測試 | 檢驗方式 |
|---|---|---|
| REQ-RUN-01 | T01、T12 | 測試 |
| REQ-RUN-02 | T01、T02、T03 | 測試 |
| REQ-RUN-03 | T10 | 測試 |
| REQ-RUN-04 | T01 | 測試 |
| REQ-RUN-05 | T05 | 測試 |
| REQ-RUN-06 | T06 | 測試 |
| REQ-CAP-01、02 | T14 | 測試 |
| REQ-CAP-03 | T03 | 測試 |
| REQ-CAP-04 | T08 | 程式審查（情境不修改容器） |
| REQ-DEC-01、02 | T01 | 測試 |
| REQ-DEC-03 | T07 | 測試 |
| REQ-DEC-04 | T13 | 測試 |
| REQ-UPF-01、02 | T01、T09 | 測試 |
| REQ-UPF-03 | T04 | 測試 |
| REQ-VER-01、02 | T02、T03、T04 | 測試 |
| REQ-VER-03 | T08 | 程式審查 |
| REQ-EV-01～03 | T01、T09 | 測試 |
| REQ-EV-04 | T11 | 測試＋審查 |
| REQ-CHK-01、02 | T15 | 程式審查 |
| REQ-CHK-03 | T01 | 測試 |

新增或修改需求時，必須同時更新這張表；沒有測試也沒有審查方式的需求不能進入實作。

## 3. 分層判定

測試工具本身沒有 L 層級；它產生其他規格組 L1～L3 的證據。W1 完成的定義是 T01～T15 通過。

## 4. 要保存的證據

T01、T02 的 pcap 與 `checks.json` 保存為檢查引擎的回歸樣本（遮蔽後）。

## 5. 版本 manifest

由工具自動產生（REQ-EV-02）。

## 6. 完成定義

T01～T15 通過；在現有部署上 §8.1 全部 PASS；舊的 log grep 判定已移除。
