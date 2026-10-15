# 3GPP IMS 相關標準整理

> 整理日期：2026-10-14
> ✓ 表示 `specs/3gpp-r17/` 裡有 Rel-17 原文；條款編號取自這些原文的目錄。沒有打 ✓ 的規格只列用途，名稱與範圍以 3GPP 網站為準。
> 「本專案」欄依目前的設計原則（Kamailio 負責 IMS、5GC 不處理 SIP、只做 IMS↔5GC 的 policy 交換）標出優先度。

## 1. 先看懂 3GPP 的編號

| 系列 | 內容 | 例 |
|---|---|---|
| 22 | 服務需求（stage 1） | TS 22.228 |
| 23 | 架構與流程（stage 2） | TS 23.228 |
| 24 | UE 與網路之間的協定（stage 3） | TS 24.229 |
| 26 | 媒體、codec | TS 26.114 |
| 29 | 網路節點之間的介面（stage 3） | TS 29.228、29.514 |
| 32 | 計費、網管 | TS 32.260 |
| 33 | 安全 | TS 33.203 |
| 35 | 演算法 | TS 35.206 |

檔名 `23228-h30` 的 `h` 是 Release 17，後面兩碼是版本（`h30` = 17.3.0；字母 a–z 代表 10 以後）。

## 2. 一張圖看 IMS 規格的位置

```
          服務需求 22.228
                │
     架構 23.228（IMS 本體）── 23.218（呼叫模型、iFC）── 23.003（識別碼）
       │            │                       │
   接取網路      SIP 信令                 介面
  23.501/502/503  24.229（核心）     Diameter：29.228/229（Cx）、29.328/329（Sh）、29.214（Rx）
  23.228 附錄 Y   24.173（MMTel）    SBA：29.514（N5）、29.562（Nhss_ims）、29.513（policy 流程）
  24.229 附錄 U   24.6xx（補充服務）
       │            │                       │
   安全 33.203    媒體 26.114            互通 29.163／29.165、緊急 23.167、連續性 23.237
```

## 3. 依主題整理

### A. 架構與需求

| 規格 | 內容 | 重點條款 | 本專案 |
|---|---|---|---|
| TS 22.228 | IMS 服務需求（stage 1） | — | 背景 |
| ✓ TS 23.228 | **IMS 架構（stage 2）**，最重要的入門規格 | 4 概念（4.3 命名定址、4.6 各 CSCF 角色、4.8 安全）；5.2 註冊；5.4–5.10 session 建立到釋放；附錄 Y：用 5GS 接 IMS；附錄 AA：IMS 的 SBA | **必讀** |
| TS 23.218 | IM 呼叫模型：S-CSCF 依 iFC 把請求交給 AS | — | 背景（本專案沒有 AS） |
| ✓ TS 23.003 | 識別碼：IMPI／IMPU 從 IMSI 推導、IMS 網域格式 | 13 章 | 背景 |
| TS 23.002 | 3GPP 整體網路架構 | — | 背景 |

### B. 用 5GS 接 IMS（與本專案最相關）

| 規格 | 內容 | 重點條款 | 本專案 |
|---|---|---|---|
| ✓ TS 23.228 附錄 Y | 5GS 作為 IMS 的接取網路 | Y.1.1 P-CSCF discovery；Y.2 QoS（信令 QoS、媒體與 QoS flow 的關係、經 PCF 預留資源） | **必讀** |
| ✓ TS 23.501 | 5G 系統架構：IMS 支援、P-CSCF discovery、5QI 表 | — | 查 5QI、IMS voice 指示 |
| ✓ TS 23.502 | 5G 流程：PDU session 建立與修改 | 4.3.2、4.3.3（含 network-requested modification） | SMF 要補 N1N2 時的依據 |
| ✓ TS 23.503 | 5G policy 架構 | **附錄 C：PCF 支援以 Rx 介接的 IMS AF** | **必讀**（Adapter 的依據） |
| ✓ TS 24.229 附錄 U | 用 5GS 接 IMS 時 UE／P-CSCF 的行為 | — | 參考 |
| ✓ TS 24.501 | 5G NAS（Registration Accept 的 IMS VoPS 指示、ePCO） | — | AMF `imsVoPS` |
| ✓ TS 24.008 | PCO 格式（P-CSCF 位址的 container） | — | SMF PCO |

### C. SIP／SDP 信令

| 規格 | 內容 | 重點條款 | 本專案 |
|---|---|---|---|
| ✓ TS 24.229 | **IMS 的 SIP／SDP 行為（stage 3）**，各節點該做什麼 | 5.1 UE、**5.2 P-CSCF**、5.3 I-CSCF、5.4 S-CSCF、5.7 AS、5.8 MRFC、5.10 IBCF、5.11 E-CSCF；6 SDP；**附錄 A：引用的 IETF RFC 清單** | 對照 Kamailio 行為 |
| TS 24.173 | MMTel：IMS 語音／視訊電話服務 | — | 背景 |
| TS 24.604～24.654 | 補充服務（轉接、保留、來電顯示、會議…） | — | 不需要（沒有 TAS） |
| TS 24.628 | 補充服務共用的基本流程 | — | 不需要 |
| TS 24.341 | SMS over IP | — | 不需要 |
| TS 24.623 | 用 XCAP（Ut 介面）設定補充服務 | — | 不需要 |

### D. Diameter 介面（Kamailio 與 PyHSS 使用中）

| 規格 | 介面 | 內容 | 本專案 |
|---|---|---|---|
| ✓ TS 29.228 | Cx／Dx | UAR／MAR／SAR／LIR 的流程、user profile 內容 | 現況：PyHSS ↔ I/S-CSCF；計畫 W8：UDM ↔ I/S-CSCF |
| ✓ TS 29.229 | Cx／Dx | Diameter 協定細節（AVP） | 同上；W8 寫字典時查 |
| TS 29.328／29.329 | Sh | AS 存取 HSS | 不需要 |
| ✓ TS 29.214 | **Rx** | P-CSCF（AF）向 PCRF／PCF 要 QoS：AAR／STR／RAR／ASR | **必讀**（Kamailio `ims_qos`） |
| TS 29.212 | Gx | 4G 的 PCRF ↔ PGW | 背景 |

### E. 5G 服務化介面（SBA）

| 規格 | 介面 | 內容 | 本專案 |
|---|---|---|---|
| ✓ TS 29.514 | **N5** | Npcf_PolicyAuthorization：app session、媒體元件、事件 | **必讀** |
| ✓ TS 29.513 | — | Policy 訊令流程；**7.3.2 PCF 與 Rx AF 互通**；**附錄 B：IMS 各情境要交換的資訊**（B.2 建立、B.3 修改、B.4 結束、B.5–B.8 註冊時） | **必讀** |
| ✓ TS 29.562 | N70／N71 | HSS 給 IMS 的服務（Nhss_ImsUECM／SDM／UEAU） | 不做（Kamailio 只支援 Cx） |
| ✓ TS 29.510 | — | NRF：註冊、discovery、token | Adapter 註冊用 |
| ✓ TS 29.505／29.519 | — | UDR 的用戶與 policy 資料 | W8（Rel-17 沒有 IMS 用戶資料，要非標準擴充） |
| ✓ TS 29.571 | — | SBI 共用資料型別 | 寫 Adapter 時查 |

### F. 安全

| 規格 | 內容 | 重點條款 | 本專案 |
|---|---|---|---|
| ✓ TS 33.203 | IMS 存取安全：IMS AKA、UE ↔ P-CSCF 的 IPsec | 4 架構、6 機制、7 SA 建立、8 ISIM | 背景（本專案沒有 IPsec） |
| ✓ TS 33.102 | 3G AKA：SQN、AUTS 重新同步 | — | 背景 |
| ✓ TS 35.206／35.208 | Milenage 演算法與測試資料 | — | 背景 |
| TS 33.210 | 網路節點之間的 IP 安全（NDS/IP） | — | 不需要 |
| TS 33.328 | IMS 媒體加密 | — | 不需要 |

### G. 媒體

| 規格 | 內容 | 本專案 |
|---|---|---|
| TS 26.114 | MTSI：IMS 電話的媒體處理（codec、RTP、jitter buffer） | 背景 |
| TS 26.441／26.445 | EVS codec | 不需要 |
| TS 26.071／26.171 | AMR／AMR-WB codec | 不需要 |

### H. 互通、緊急、連續性、計費

| 規格 | 內容 | 本專案 |
|---|---|---|
| TS 29.163 | IMS 與電路交換網路互通（MGCF） | 不需要 |
| TS 29.165 | IMS 業者之間的互連（NNI） | 不需要 |
| TS 29.162 | IMS 與一般 IP 網路互通 | 不需要 |
| TS 29.332／29.333／29.334 | MGCF–MGW、MRFC–MRFP、IMS-ALG–IMS-AGW 的控制介面 | 不需要 |
| TS 23.167 | IMS 緊急通話 | 之後 |
| TS 23.237／24.237 | IMS 服務連續性 | 不需要 |
| TS 23.216 | SRVCC（語音切到 CS） | 不需要 |
| TS 23.380 | IMS restoration（P-CSCF／S-CSCF 故障復原） | 之後 |
| TS 32.260 | IMS 計費 | 不需要 |

### I. 3GPP 以外但常一起用

| 來源 | 文件 | 內容 |
|---|---|---|
| GSMA | IR.92 | VoLTE 的 IMS profile（商用網路實際要支援哪些功能） |
| GSMA | NG.114 | 5G（VoNR）的 IMS profile |
| IETF | RFC 3261 | SIP |
| IETF | RFC 3264、RFC 8866 | SDP offer／answer、SDP |
| IETF | RFC 3550 | RTP／RTCP |
| IETF | RFC 3310 | HTTP Digest AKA（IMS AKA 在 SIP 裡的形式） |
| IETF | RFC 3327、RFC 3608 | Path、Service-Route |
| IETF | RFC 3325、RFC 7315 | P-Asserted-Identity、3GPP 的 P- header |
| IETF | RFC 3262、RFC 3312 | PRACK、preconditions |
| IETF | RFC 6733 | Diameter base |

完整的 RFC 清單在 TS 24.229 附錄 A。

## 4. 對照本專案

### 五個對接點 → 條款

| 對接點 | 規格與條款 |
|---|---|
| ① 使用者面（N6） | TS 23.228 4.12（NAT）；TS 23.501 |
| ② `ims` DNN 與預設 QoS | TS 23.228 Y.2.1（信令的 QoS）；TS 23.501 5QI 表 |
| ③ P-CSCF discovery | TS 23.228 Y.1.1；TS 24.008（PCO）；TS 24.501（ePCO） |
| ④ 用戶身分與金鑰 | TS 23.003 13 章；TS 29.228／29.229；TS 33.203 |
| ⑤ Policy／QoS | TS 23.228 Y.2.3；TS 23.503 附錄 C；TS 29.513 7.3.2、附錄 B；TS 29.214；TS 29.514 |
| 缺口：SMF 沒送 N1N2 | TS 23.502 4.3.3（network-requested PDU session modification） |
| 缺口：AMF imsVoPS | TS 24.501（5GS network feature support） |

### Kamailio 模組 → 規格

| 模組 | 對應規格 |
|---|---|
| `ims_registrar_pcscf`、`ims_usrloc_pcscf` | TS 24.229 5.2 |
| `ims_icscf` | TS 24.229 5.3、TS 29.228／29.229（UAR、LIR） |
| `ims_registrar_scscf`、`ims_usrloc_scscf` | TS 24.229 5.4、TS 29.228／29.229（SAR） |
| `ims_auth` | TS 33.203、RFC 3310、TS 29.228／29.229（MAR） |
| `ims_qos` | TS 29.214（Rx） |
| PyHSS | TS 29.228／29.229 |

## 5. 建議閱讀順序

1. **TS 23.228** 第 4 章與 5.2、5.4：先搞懂 IMS 的角色、註冊與通話
2. **TS 23.228 附錄 Y**：IMS 怎麼跑在 5GS 上
3. **TS 23.503 附錄 C** 與 **TS 29.513 附錄 B**：IMS 與 5GC 要交換什麼（Adapter 的需求來源）
4. **TS 29.214** 與 **TS 29.514**：Adapter 兩端的介面細節
5. 需要時再查 **TS 24.229** 對應節點的章節、**TS 23.502** 4.3.3
