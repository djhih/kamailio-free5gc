# VoNR：Kamailio IMS × free5GC

研究如何讓 Kamailio IMS 依 3GPP 標準接上 free5GC，並規劃需要的 NF 修改。實驗環境是 [kamailio-free5gc](https://github.com/DBGR18/kamailio-free5gc)（git submodule）。

**設計原則：** 5GC 負責註冊、PDU session、QoS 與 policy；IMS（Kamailio）負責 SIP；AMF／SMF 不處理 SIP。要做的是讓兩邊正確交換媒體需求與 policy，並把 HSS 併入 free5gc UDM（對 Kamailio 仍是 Cx），讓 IMS 與 5G 共用一份用戶資料。

## 目前狀態

只有計畫與規格，尚未實作。所有工作項（W1～W8）都已有規格；先看 [docs/overview/](docs/overview/README.md)。

## 文件

| 資料夾 | 內容 |
|---|---|
| [docs/overview/](docs/overview/README.md) | **總覽**：現況（五個對接點、測試實際驗證了什麼、缺口）、總計畫（W1～W8、時程、門檻、待決定）、3GPP 對照、W2／W7 檢查清單、開發流程 |
| [docs/e2e-harness/](docs/e2e-harness/README.md) | W1：抓包版端到端測試（檢查清單 CHK-*） |
| [docs/rx-n5/](docs/rx-n5/README.md) | W3、W4：Rx／N5 Adapter 與 Kamailio P-CSCF 設定 |
| [docs/smf-n1n2/](docs/smf-n1n2/README.md) | W5、W6：SMF 經 N1／N2 通知 gNB 與 UE；free-ran-ue 回應器 |
| [docs/hss-udm/](docs/hss-udm/README.md) | W8：HSS 併入 UDM |
| [docs/background/](docs/background/) | 背景：IMS 入門筆記（`note.md`）、3GPP 規格整理（`3gpp-ims-standards.md`）、2024 年碩論比較（`ims-af-thesis-comparison.md`） |

每個規格組（rx-n5、smf-n1n2、hss-udm、e2e-harness）都是同一個結構：README（索引）、explained（用例子走一遍，部分有）、design（為什麼、替代方案、風險）、interface-spec（編號需求）、test-plan（需求追溯）、adr/（決策）。

## 其他資料夾

| 資料夾 | 內容 |
|---|---|
| [slides/](slides/) | 簡報與產生簡報的原始檔（見 `slides/README.md`） |
| [specs/3gpp-r17/](specs/3gpp-r17/) | Rel-17 規格清單；規格本身不進 git，用 `download.sh` 下載 |
| [kamailio-free5gc/](kamailio-free5gc/) | 實驗環境（submodule） |
| `lab-ref/` | 實驗室前人資料（2024 年碩論交接包）。**不進 git**，只放在本機；原始來源是實驗室 NAS |

## 取得完整內容

```bash
git clone --recurse-submodules <this repo>
specs/3gpp-r17/download.sh     # 約 120 MB
```
