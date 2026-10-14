# 3GPP Rel-17 規格（2026-10-06 下載）

來源：`https://www.3gpp.org/ftp/Specs/archive/`，每份取 Rel-17（版本號 `h`）的最新版。`zip/` 是原始壓縮檔。

| 規格 | 檔案 | 版本 | 內容 | 用在 |
|---|---|---|---|---|
| TS 23.228 | 23228-h30.docx | 17.3.0 | IMS 架構；附錄 AA：IMS 的 SBA（N5、N70、N71、Nhss_ims） | 背景 |
| TS 24.229 | 24229-hj0.doc | 17.19.0 | IMS 的 SIP 行為（P/I/S-CSCF 各自要做的事） | 背景 |
| TS 23.501 | 23501-hf0.docx | 17.15.0 | 5G 系統架構、5QI 表 | 背景（5QI） |
| TS 23.502 | 23502-hf0.docx | 17.15.0 | 5G 流程 | W5（SMF：4.3.3 PDU session 修改） |
| TS 23.503 | 23503-hb0.docx | 17.11.0 | Policy 與計費架構 | 核心：附錄 C 定義 PCF 支援 Rx |
| TS 23.003 | 23003-hb0.docx | 17.11.0 | 識別碼（IMPI／IMPU 從 IMSI 推導、IMS 網域） | 目前用不到 |
| TS 24.008 | 24008-h90.docx | 17.9.0 | PCO 格式（P-CSCF 位址 container） | 背景（PCO） |
| TS 24.501 | 24501-hi1.docx | 17.18.1 | 5G NAS、ePCO | W2（imsVoPS）、背景（ePCO） |
| TS 29.514 | 29514-hg0.doc | 17.16.0 | N5：Npcf_PolicyAuthorization | 核心 |
| TS 29.513 | 29513-he0.docx | 17.14.0 | Policy 訊令流程、Rx／N5 與 QoS 參數對應 | 核心：7.3.2、附錄 B |
| TS 29.214 | 29214-h60.docx | 17.6.0 | Rx（Kamailio `ims_qos` 用的介面） | 核心 |
| TS 29.228 | 29228-h10.docx | 17.1.0 | Cx 訊令流程與資料（含 user profile） | 目前用不到 |
| TS 29.229 | 29229-h30.docx | 17.3.0 | Cx Diameter 協定細節 | 目前用不到 |
| TS 29.562 | 29562-ha0.docx | 17.10.0 | HSS 給 IMS 的 SBI 服務（Nhss_ims*） | 目前用不到 |
| TS 29.510 | 29510-hg0.docx | 17.16.0 | NRF（註冊、discovery、token） | W3（Adapter 向 NRF 註冊） |
| TS 29.505 | 29505-hd0.docx | 17.13.0 | UDR 用戶資料 | 目前用不到 |
| TS 29.519 | 29519-hh0.doc | 17.17.0 | UDR 的 policy／application 資料 | 目前用不到 |
| TS 29.571 | 29571-hd0.docx | 17.13.0 | SBI 共用資料型別 | 核心 |
| TS 33.203 | 33203-h10.doc | 17.1.0 | IMS 存取安全（IMS AKA、IPsec） | 目前用不到 |
| TS 33.102 | 33102-h00.doc | 17.0.0 | 3G 安全（AKA、SQN、AUTS 重新同步） | 目前用不到 |
| TS 35.206 | 35206-h00.doc | 17.0.0 | Milenage 演算法 | 目前用不到 |
| TS 35.208 | 35208-h00.doc | 17.0.0 | Milenage 測試資料 | 目前用不到 |

OpenAPI 定義（壓縮檔附帶）：`TS29514_Npcf_PolicyAuthorization.yaml`、`TS29562_Nhss_ims{UECM,SDM,UEAU}.yaml`、`TS29510_Nnrf_*.yaml`、`TS29505_Subscription_Data.yaml`、`TS29519_*.yaml`、`TS29571_CommonData.yaml`；Cx 的 user profile schema 是 `CxData_Type_Rel17.xsd`。

版本欄是由檔名推得（`h`＝17，後兩碼依 3GPP 的 0–9、a–z 編碼）。

IMS 相關規格的完整整理（含沒下載的規格、條款索引、對照本專案）：`../../docs/background/3gpp-ims-standards.md`。
