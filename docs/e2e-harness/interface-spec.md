# 抓包版端到端測試介面規格（W1）

| 項目 | 內容 |
|---|---|
| 版本／狀態 | v0.1／審查中（2026-10-22） |
| 適用範圍 | W1 的測試工具；各工作項的檢查清單見 §8 |
| 設計理由 | [design.md](design.md)、[adr/](adr/) |
| 驗證方式 | [test-plan.md](test-plan.md) §2 |

## 1. 範圍與用語

### 1.1 範圍

本規格定義測試工具的執行介面、抓包、解碼、UPF 規則快照、判定規則、證據輸出，以及各工作項要加入的檢查。對象環境是 `kamailio-free5gc` 的 docker compose 部署。

### 1.2 需求用語

本規格的需求用語比照 RFC 2119／RFC 8174，**只有粗體時**才有下列意思：

| 用語 | 對應 | 意思 |
|---|---|---|
| **必須** | MUST | 沒有例外 |
| **不得** | MUST NOT | 沒有例外 |
| **應** | SHOULD | 有正當理由時可以不做，但要在實作說明寫出理由 |
| **不應** | SHOULD NOT | 同上，反向 |
| **可** | MAY | 選擇性 |

需求編號格式 `REQ-<區域>-<序號>`，序號不重用。刪除的需求保留編號並標「（已刪除）」。

### 1.3 名詞

| 名詞 | 意思 |
|---|---|
| 情境 | 一組步驟與要跑的檢查，例如 `call` |
| 檢查 | 一個可判定的條件，有 ID（`CHK-…`）、適用工作項、對應需求 |
| 證據指標 | pcap 檔名＋frame number，或 UPF 規則 ID |
| run-id | 每次執行的唯一識別（時間戳＋短隨機值） |

## 2. 參考文件

| 文件 | 用到的部分 | 版本 | 核對狀態 |
|---|---|---|---|
| tshark／dumpcap | decode-as、`-T json`、欄位名稱 | 4.7.3（host） | 版本已確認；欄位名稱待 G1 |
| gtp5g | netlink 規則 | 0.10.2 | 已確認 |
| 各規格組的 REQ | 檢查對應的需求 | 見 §8 | — |

## 3. 執行介面

- **REQ-RUN-01** 入口**必須**是 `scripts/e2e/run.sh <scenario> [--with <工作項清單>]`；`--with` 決定要啟用哪些工作項的檢查（例如 `W3a,W4`）。
- **REQ-RUN-02** 退出碼：0＝PASS；1＝FAIL；2＝INCOMPLETE（有 SKIP 或 BLOCKED 的必須檢查）；3＝工具本身錯誤。
- **REQ-RUN-03** `03-call-test.sh`、`05-n5-qos-test.sh` **必須**保留為呼叫 `run.sh call`、`run.sh n5-qos` 的包裝，退出碼照傳。
- **REQ-RUN-04** 現行 03 的前置檢查（兩支 UE 有 PDU session 與 IP、從 PCO 取得 P-CSCF、UE 設定檔沒有寫死 P-CSCF）**必須**保留為檢查（CHK-PRE-*），失敗時後續檢查標 BLOCKED。
- **REQ-RUN-05** 每個步驟**必須**有逾時；逾時時中止情境，已錄的資料照常保存，依賴的檢查標 BLOCKED。
- **REQ-RUN-06** sipp 等工具的退出碼**必須**被檢查並記錄，**不得**被管線吞掉（現行 03 的註冊用 `| tail -3`）。

## 4. 抓包

- **REQ-CAP-01** **必須**在 host 的 `br-poc-core`、`br-poc-dn` 各錄一份 pcapng，在情境第一個步驟之前開始、最後一個步驟之後停止。
- **REQ-CAP-02** 每次執行**必須**重新錄；**不得**重用前次的 pcap 或從長時間錄製中切片。
- **REQ-CAP-03** 抓包啟動失敗或錄到 0 個封包時，依賴該 bridge 的檢查**必須**標 BLOCKED。
- **REQ-CAP-04** **不得**為了抓包修改任何容器（不安裝工具、不改 cfg）。

## 5. 解碼

- **REQ-DEC-01** 解碼**必須**使用固定的 decode-as 設定，至少：SBI 8000 與 AF shim 8090 為 HTTP/2；Diameter 3868；SIP 5060、4060、6060（UDP 與 TCP）。GTP-U 2152、PFCP 8805、NGAP（SCTP 38412）使用 tshark 預設。
- **REQ-DEC-02** SIP 在 `br-poc-core` 上**必須**從 GTP-U 內層解出，並能以內層 IP 分辨 UE。
- **REQ-DEC-03** 解碼結果**必須**只依賴 pcap 與 decode-as 設定；同一份 pcap 重跑**必須**得到相同結果。
- **REQ-DEC-04** 解不出某協定（例如 h2c 缺少連線開頭的 HPACK 狀態）時，依賴它的檢查**必須**標 BLOCKED，並在原因中說明。

## 6. UPF 規則快照

- **REQ-UPF-01** **必須**以固定版本的 gogtp5g-tunnel（D03）經 `nsenter` 進 UPF netns，讀 PDR、FAR、QER；版本記入 manifest。
- **REQ-UPF-02** `call` 情境**必須**在通話前、通話中（200 OK 之後）、掛斷後各取一次快照。
- **REQ-UPF-03** 工具不存在或讀取失敗時，依賴的檢查**必須**標 BLOCKED（現行 03 標 SKIP 且不影響 PASS，本條取代之）。

## 7. 判定與證據

- **REQ-VER-01** 每個檢查的結果**必須**是 PASS、FAIL、SKIP、BLOCKED 之一；PASS **必須**附證據指標，FAIL、SKIP、BLOCKED **必須**附原因。
- **REQ-VER-02** 整體結果：所有啟用的必須檢查都 PASS 才是 PASS；有任何 FAIL 是 FAIL；其他情況是 INCOMPLETE。SKIP、BLOCKED **不得**算作 PASS（[ADR-0002](adr/0002-skip-and-blocked-never-pass.md)）。
- **REQ-VER-03** 判定**不得**使用任何元件的 log 字串。log 只能當附件保存。
- **REQ-EV-01** 每次執行**必須**在 `results/<run-id>/` 保存：兩份 pcapng、UPF 快照、`checks.json`、`summary.txt`、`manifest.json`、各容器 log（附件）。
- **REQ-EV-02** `manifest.json` **必須**包含：本 repo 與 submodule 的 commit、每個容器的映像 id、Kamailio 版本（`kamailio -v`）、free-ran-ue 版本與 patch、gtp5g 版本、gogtp5g-tunnel 版本、tshark 版本、`--with` 的工作項。
- **REQ-EV-03** `checks.json` 每一項**必須**包含：檢查 ID、結果、對應的需求編號、證據指標或原因。
- **REQ-EV-04** `results/` **不得**進 git；分享 pcap 前**必須**遮蔽 IMSI 等身分。

## 8. 檢查清單

「工作項」欄表示 `--with` 包含該工作項時才啟用；「現況」表示不加 `--with` 也啟用（現有部署）。檢查條件裡的 Cx 指令碼、HTTP 路徑等，取自各規格組已核對的值。「對應需求」欄寫的是各規格組內的需求編號（省略前綴，例如「rx-n5 KAM-05」指 rx-n5 interface-spec 中編號 KAM-05 的需求）。

### 8.1 前置與基本通話（現況）

| ID | 條件 | 對應 |
|---|---|---|
| CHK-PRE-01 | 兩支 UE 都有 PDU session 與 IP | 現行 03 |
| CHK-PRE-02 | 兩支 UE 從 PCO 取得 P-CSCF 位址，且 UE 設定檔沒寫死 | 現行 03 |
| CHK-REG-01 | 每支 UE：GTP-U 內層有它送出的 REGISTER，與同一 Call-ID 的最終 `200 OK` | 現行 03（改為判定） |
| CHK-REG-02 | 每支 UE 的註冊流程中有 401（IMS AKA challenge） | 現行 03 |
| CHK-CX-01 | `br-poc-dn` 有 UAR／UAA、MAR／MAA、SAR／SAA（Cx 指令碼 300、303、301），各自結果為成功 | 現行 03（改為判定）；hss-udm 附錄 C |
| CHK-CX-02 | 通話時有 LIR／LIA（302），結果成功 | 現行 03 |
| CHK-SIP-01 | INVITE、180／200、ACK、BYE、200（BYE）都在 GTP-U 內層出現，方向正確 | 現行 03 |
| CHK-SIP-02 | SIP 經過 P-CSCF → I-CSCF → S-CSCF → P-CSCF（`br-poc-dn` 上的 SIP 路徑） | 現行 03 的三角色路徑（改為判定） |
| CHK-RTP-01 | GTP-U 內層有兩個方向的 RTP，port 與 SDP 協商的一致 | 現行 03（改為依 SDP 判定） |
| CHK-UPF-01 | 通話中快照有兩個方向的語音 PDR，參照的 QER 存在 | 現行 03、05 |
| CHK-UPF-02 | 掛斷後快照的 PDR 數等於通話前 | 現行 05 |
| CHK-AF-01 | （shim）`n5-qos` 情境：POST `/call` 回 200、`/call/delete` 之後規則消失 | 現行 05 |

### 8.2 各工作項的檢查

| ID | 工作項 | 條件 | 對應需求 |
|---|---|---|---|
| CHK-W2-01 | W2 | Registration Accept 的 5GS network feature support 中 IMS VoPS 3GPP＝1（NEA0 下可解） | [W2 檢查清單](../overview/w2-w7-checklists.md) |
| CHK-W3A-01 | W3a、W4 | 200 OK 之後兩個 AAR／AAA（成功），對應兩個 N5 `POST …/app-sessions` 201 | rx-n5 KAM-05、GEN-04 |
| CHK-W3A-02 | W3a、W4 | BYE 之後兩個 STR／STA，對應兩個 `POST …/delete` | rx-n5 STR-01 |
| CHK-W3A-03 | W3a、W4 | 沒有 P-CSCF → AF shim 的 HTTP 8090 | rx-n5 KAM-02 |
| CHK-W3B-01 | W3b | `release-pdu-session` 情境：terminate、ASR／ASA、兩支 UE 收到 BYE、STR／STA | rx-n5 ASR-01～03 |
| CHK-W3D-01 | W3d | `re-invite` 情境：同一 Session-Id 的更新 AAR，與對應的 PATCH 或 Delete＋Create | rx-n5 UPD-02、04 |
| CHK-W5-01 | W5a、W6 | 200 OK 之後每支 UE 一組 NGAP PDU Session Resource Modify Request／Response 與 NAS Modification Command（PTI＝0）／Complete | smf-n1n2 N1-01、XFER-01 |
| CHK-W5-02 | W5a、W6 | BYE 之後每支 UE 一組刪除（QosFlowToReleaseList、delete QoS rule） | smf-n1n2 N2-03 |
| CHK-W5-03 | W5c、W6 | 故障注入情境：SM policy update 帶 ruleReports（INACTIVE） | smf-n1n2 RPT-01 |
| CHK-W8-01 | W8a | Cx 答案的 Origin-Host 是 UDM；第一次註冊的 UAA 沒有 Server-Name、有 Server-Capabilities | hss-udm UAR-05 |
| CHK-W8-02 | W8a | 沒有任何 PyHSS 容器的流量 | hss-udm OPS-02 |
| CHK-W3C-01 | W3c | 註冊時有 `Rx_AAR_Register` 的 AAR 與成功的 AAA；`local` 模式下沒有對應的 N5 請求 | rx-n5 KAM-11、REG-03 |
| CHK-W5-04 | W5b、W6 | `bw-change` 情境：N1 帶 `QFD_Mod`、N2 AddOrModify 帶新參數，QFI 不變 | smf-n1n2 MOD-03、MOD-04 |
| CHK-W5-05 | W5d、W6 | 故障注入（e）：SM policy update 帶 `qncReports` | smf-n1n2 QNC-03 |
| CHK-W8-03 | W8b | `delete-subscriber` 情境：RTR／RTA，之後的 LIA 回未註冊 | hss-udm RTR-01 |

各規格組 test-plan 中標「抓包」的測試，**必須**能以本節的檢查或新增的檢查判定。

- **REQ-CHK-01** 每個檢查**必須**定義：ID、適用工作項、條件、對應需求、所需的 bridge 或快照。
- **REQ-CHK-02** 新增工作項的抓包驗收**必須**以新增檢查的方式加入，**不得**在情境腳本中寫一次性的判定。
- **REQ-CHK-03** §8.1 的檢查在**現有部署**上（不加 `--with`）**必須**全部 PASS，作為 W1 的完成條件。

---

## 附錄 A（參考）現行測試的檢查對照

| 現行 03／05 的檢查 | 方式 | 新的檢查 |
|---|---|---|
| UE IP、PCO、設定檔 | `docker exec cat`、grep 設定檔 | CHK-PRE-01、02（保留方式） |
| 註冊結果 | sipp 輸出 `tail -3`、grep log（只印出） | CHK-REG-01、02 |
| 三角色路徑 | grep Kamailio log（只印出） | CHK-SIP-02 |
| UAR／MAR／SAR | grep log 計數（只印出） | CHK-CX-01 |
| LIR | grep log 計數（**判定**） | CHK-CX-02 |
| QoS PDR | gtp5g 快照（SKIP 不算 FAIL） | CHK-UPF-01（BLOCKED 不算 PASS） |
| GTP-U 封包數 | `tcpdump -r` 計數（**判定**） | CHK-SIP-01、CHK-RTP-01 |
| BYE | grep pcscf log（**判定**） | CHK-SIP-01 |
| 05 的 PDR／QER 方向與 GBR | gtp5g 快照＋Python | CHK-UPF-01、CHK-AF-01 |
