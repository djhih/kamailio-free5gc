# VoNR：Kamailio IMS × free5GC

研究如何讓 Kamailio IMS 依 3GPP 標準接上 free5GC，並規劃需要的 NF 修改。實驗環境是 [kamailio-free5gc](https://github.com/DBGR18/kamailio-free5gc)（git submodule）。

**設計原則：** 5GC 負責註冊、PDU session、QoS 與 policy；IMS（Kamailio）負責 SIP；AMF／SMF 不處理 SIP。要做的是讓兩邊正確交換媒體需求與 policy，並把 HSS 併入 free5gc UDM（對 Kamailio 仍是 Cx），讓 IMS 與 5G 共用一份用戶資料。

## 目前狀態

只有計畫與設計，尚未實作。從 [docs/plan/vonr-ims-nf-plan.md](docs/plan/vonr-ims-nf-plan.md) 開始看。

## 文件

| 文件 | 內容 |
|---|---|
| **計畫** | |
| [docs/plan/vonr-ims-nf-plan.md](docs/plan/vonr-ims-nf-plan.md) | 總計畫：8 個工作項（W1–W8）、時程、驗收方式 |
| [docs/plan/rx-n5-adapter-explained.md](docs/plan/rx-n5-adapter-explained.md) | Rx／N5 Adapter 要做什麼（用一通電話說明） |
| [docs/plan/rx-n5-adapter-design.md](docs/plan/rx-n5-adapter-design.md) | Adapter 怎麼寫：介面、程式結構、對應表、實作順序 |
| [docs/plan/hss-in-udm-design.md](docs/plan/hss-in-udm-design.md) | HSS 併入 UDM 怎麼寫：Cx、UDR 擴充、共用 SQN、實作順序 |
| [docs/plan/vonr-ims-dev-process.md](docs/plan/vonr-ims-dev-process.md) | 照 free5gc 慣例的開發流程與程式結構 |
| **現況** | |
| [docs/current/free5gc-kamailio-integration.md](docs/current/free5gc-kamailio-integration.md) | kamailio-free5gc 目前的五個對接點與缺口 |
| **背景** | |
| [docs/background/note.md](docs/background/note.md) | IMS、SIP、CSCF 入門筆記與 VoNR 架構圖解讀 |
| [docs/background/3gpp-ims-standards.md](docs/background/3gpp-ims-standards.md) | IMS 相關 3GPP 規格整理與閱讀順序 |
| [docs/background/ims-af-thesis-comparison.md](docs/background/ims-af-thesis-comparison.md) | 2024 年實驗室碩論的 IMS-AF 與本計畫的差異，含 free5gc PCF 的 PATCH 限制 |

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
