# VoNR intro 第 12 頁：free5GC 接 IMS

已更新 `../../VoNR_over_IMS_kamailio_intro.pptx` 的第 12 頁。簡報共 28 頁，
只替換 `ppt/slides/slide12.xml`；其餘 27 頁及所有其他 ZIP parts 保持逐位元組一致。
圖中元件、文字、連線都是可編輯的原生 PowerPoint 物件。

## A. 找到的原始圖源

原圖就是 PPTX 內的原生圖形：
`VoNR_over_IMS_kamailio_intro.pptx!/ppt/slides/slide12.xml`。
原始內容留存為 [original-slide12.xml](original-slide12.xml)。
工作區未找到產生這一頁的獨立 Mermaid／Python／drawio 程式。
`kamailio-free5gc/docs/architecture.md` 有另一張 Mermaid 拓撲圖，
`ims-scenario-animation/` 則是三幕 IMS 動畫的產圖流程，都不是原第 12 頁的生成來源。
兩個 `_animated` 簡報的對應拓撲圖在第 15 頁；本次依要求更新 intro 主檔第 12 頁。

新版圖的 source of truth 是 [build_slide.py](build_slide.py)。
它生成本頁的 OOXML 與 layout manifest，再只替換主簡報中的對應頁。
PNG 是簡報渲染出的預覽，不是圖源。

## B. 修改與新增檔案

- 修改：`../../VoNR_over_IMS_kamailio_intro.pptx`。
- 新增圖源：`build_slide.py`；原圖備份：`original-slide12.xml`。
- 生成檔：`slide12.xml`、`layout.json`。
- 預覽：`preview/VoNR_over_IMS_kamailio_intro-12.png`。
- 驗證：`verification.json`、`layout-audit.json`、`semantic-audit.json`。
- 說明：本檔案。

重建與檢查（從工作區根目錄執行）：

```bash
python slides/src/vonr-architecture/build_slide.py
genoffice --json slides audit slides/VoNR_over_IMS_kamailio_intro.pptx --slide 11
genoffice render slides/VoNR_over_IMS_kamailio_intro.pptx --out slides/src/vonr-architecture/preview --page 12 --scale 2
```

Python 腳本需要 `lxml`；渲染／版面檢查使用本機 GenOffice。
字型使用 `Noto Sans CJK TC`。渲染預覽已檢查，未在 Microsoft PowerPoint 桌面版開啟。

## C. 新圖結構

- 左側 **UE / RAN**，中央 **5GC**，右側 **IMS**；分組是邏輯 domain，
  不把 Docker 的 `corenet`、`dnnet` 當成架構角色。
- **粗藍線**：UE → NR/Uu → gNB → N3/GTP-U → UPF → N6 → IMS Data Network。
  N6 箭頭止於 DN 容器邊界，另一段 DN 內 IP 連線通到 P-CSCF。
- **橘線**：Gm 是 UE → P-CSCF 的 SIP REGISTER／INVITE 邏輯流，
  明註實際封包由藍色 IP 路徑承載；Mw/SIP 接續到 I-CSCF、S-CSCF。
- **灰線**：I-CSCF、S-CSCF 各有 Cx/Diameter 連到同一個 HSS。
- **深色線**：AF → N5 → PCF → N7 → SMF → N4/PFCP → UPF。
- **棕色虛線與虛線框**：P-CSCF → Custom HTTP API → IMS-to-5GC AF Adapter，
  Adapter 明註 Custom、Implementation-specific、Non-3GPP。

箭頭表示請求／政策下發方向，省略回應；不是宣稱介面只能單向通訊。
RTP 在本 PoC 的 UPF hairpin，不經 CSCF，沒有把語音媒體畫到 SIP proxy。

## D. 3GPP 架構與命名

| Reference point | 架構端點 | 本圖的 service／protocol 層 |
|---|---|---|
| NR / Uu | UE ↔ NG-RAN | 本專案以模擬存取表示 |
| N3 | gNB ↔ UPF | GTP-U |
| N4 | SMF ↔ UPF | PFCP |
| N5 | AF ↔ PCF | Npcf_PolicyAuthorization；HTTP/2 SBI |
| N6 | UPF ↔ Data Network | User plane / IP connectivity |
| N7 | PCF ↔ SMF | Npcf_SMPolicyControl；HTTP/2 SBI |
| Gm | UE ↔ P-CSCF | SIP |
| Mw | CSCF ↔ CSCF | SIP |
| Cx | I-CSCF／S-CSCF ↔ HSS | Diameter |

標準定義 AF 功能及 N5 關係；**獨立的自訂 Adapter 程序和它與 P-CSCF 之間的 HTTP API**
是本專案的實作選擇。Non-3GPP 標記指這個自訂整合元件，並非 AF 功能本身不是標準概念。
N7 的下行箭頭是 PCF policy update 的因果方向；SMF 也會向 PCF 建立／更新 policy association。
UPF 的 forwarding／QoS enforcement 是標準角色，本圖的 PoC 註記只聲稱規則下發。

已對照工作區 Release 17 規格與官方版本：

- [TS 23.501 §4.2.7：N3／N4／N5／N6／N7 的端點](https://www.etsi.org/deliver/etsi_ts/123500_123599/123501/17.15.00_60/ts_123501v171500p.pdf)
  （本機 `3gpp-r17/23501-hf0.docx`）。
- [TS 23.228：IMS 功能、Gm／Mw／Cx](https://www.etsi.org/deliver/etsi_ts/123200_123299/123228/17.03.00_60/ts_123228v170300p.pdf)
  （本機 `3gpp-r17/23228-h30.docx`，Cx 協定另見 `29228-h10.docx`／`29229-h30.docx`）。
- [TS 29.514：Npcf_PolicyAuthorization](https://www.etsi.org/deliver/etsi_ts/129500_129599/129514/17.16.00_60/ts_129514v171600p.pdf)
  （本機 `3gpp-r17/TS29514_Npcf_PolicyAuthorization.yaml`）。
- N7 的 `Npcf_SMPolicyControl` 名稱另核對本機 `3gpp-r17/23502-hf0.docx`
  與 `kamailio-free5gc/scripts/05-n5-qos-test.sh`。

## E. 實作核對

| 要確認的項目 | Repository 證據 | 圖上處理 |
|---|---|---|
| 三個 CSCF 是否用 Kamailio | `kamailio-free5gc/{pcscf,icscf,scscf}/Dockerfile`、各自 `kamailio.cfg`，以及 `docker-compose.yaml` 的 build 設定 | 分別標示 P/I/S-CSCF (Kamailio) |
| HSS 是否用 PyHSS | compose 的 `pyhss-hss`、`pyhss-api`、`pyhss-diameter` 與 `hss/pyhss.env` | HSS (PyHSS) |
| Adapter 在哪裡 | `kamailio-free5gc/af/main.go`、`af/Dockerfile`，compose 的 `af` service | 自訂 IMS-to-5GC AF Adapter |
| P-CSCF ↔ Adapter | `pcscf/kamailio.cfg` 的 `AF_URL`、`AF_RESERVE`、`AF_RELEASE` | Custom HTTP API；HTTP/1.1 JSON，POST `/call` 與 POST `/call/delete` |
| Adapter ↔ PCF | `af/main.go` 的 `http2.Transport`、`handleCall`、`handleCallDelete` | N5 / Npcf_PolicyAuthorization / HTTP/2 SBI (h2c) |
| 真的使用該 N5 service 嗎 | `af/main.go` 呼叫 `/npcf-policyauthorization/v1/app-sessions`；`config/pcfcfg.yaml` 宣告 `npcf-policyauthorization` | 已確認，不是僅依文件推定 |

建立時實際呼叫 `POST /npcf-policyauthorization/v1/app-sessions`；
釋放時呼叫 `POST {appSessionUri}/delete`，不是 HTTP DELETE。
PCF notification 使用 Adapter 的 `/notify`。API 路徑與程式模組名保留在此說明，
避免與投影片上的 reference point 混成同一層。

## F. 與原圖或理想架構的差異

1. 原頁把 UE、gNB 合成一個框；新版拆開，並註明 free-ran-ue 的 Uu 是邏輯示意，
   沒有暗示現有部署使用實體 NR 無線電。
2. 原圖 N6 視覺上接到 P-CSCF；實際是 UPF 接 `dnnet` 的 DN，P-CSCF 位於 DN 內。
3. `http_client` 是 Kamailio 模組名，真正的整合介面是自訂 HTTP API。
4. 專案目前尚未使用計畫中的 Rx／N5 Adapter。`ims-af-plan.md` 與 `vonr-ims-nf-plan.md`
   描述未來改造；本次沒有把規劃中的 Rx 畫成已存在的介面。
5. P→I→S 是目前 cfg 的 PoC 路由，不能視為所有 IMS 部署的通用主叫 INVITE 路徑；
   標準主叫通常依註冊所得 Service-Route 到 serving S-CSCF。本頁直接標示 PoC 路由範圍。
6. Repository 明示 QoS 測試只確認 PDR／QER 規則存在；端到端 GBR／限速並未驗證。
   整合說明也記錄 SMF policy update 後尚缺 gNB／UE 的 N1N2 更新，因此圖中不宣稱完整 VoNR QoS 已完成。
7. 部分既有文件把釋放操作簡寫為「DELETE app session」，但 `af/main.go` 實際是 POST `/delete`。

## G. 驗證與未確定事項

- 用實際 PPTX 生成 1920×1080 預覽，目視檢查文字、介面標籤、箭頭及 DN 邊界。
- GenOffice 第 12 頁版面檢查：0 errors、0 warnings；文字無 overlap／overflow／clipping。
- 封裝驗證：只改一個 slide XML，27 張其他投影片及其他 parts 均保留；ZIP 完整、XML 可解析、shape ID 唯一。
- N6 接 DN 邊界，UE／gNB 存在；AF→PCF→SMF→UPF 與 P-CSCF→Adapter 方向均已核對。
- 未對現行網路做 live 測試；本次核對的是 repository 實作與圖面，不新增運行結果主張。
- 本頁所用 reference point／service 名稱沒有尚待猜測的項目。
  是否達成實際端到端 QoS 保證仍不在本次驗證範圍，圖上已註明。
