# VoNR 端到端完整性與 3GPP 對照

> 狀態：2026-10-22 盤點；同日補上 W3b、W5c 的規格後更新；依據 `specs/3gpp-r17/` 的原文與三組規格（[rx-n5](../rx-n5/README.md)、[hss-udm](../hss-udm/README.md)、[smf-n1n2](../smf-n1n2/README.md)）
> 用途：回答兩個問題。(1) 照目前的計畫與規格做完，Kamailio 接上 free5GC 的 VoNR 是否完整？(2) 每一項與 3GPP 規格的關係是符合、部分符合、刻意偏離，還是不做？

## 先看這裡

**結論：補上 W3b（rx-n5 v0.4）與 W5c（smf-n1n2 v0.2）的規格之後，照規格做完，VoNR 通話的生命週期（註冊、建立、QoS 到 RAN／UE、掛斷、斷線或資源失效時結束通話）在本專案範圍內是完整的。** 剩下的是選擇性功能與刻意不做的項目。第一版盤點時的缺口與處理如下：

| 類別 | 缺口 | 為什麼重要 | 建議 |
|---|---|---|---|
| ~~必要但沒規格~~ **已補** | QoS flow／PDU session 遺失時，P-CSCF 要結束通話（TS 23.228 附錄 Y.2.4、TS 29.513 B.4.2） | 規格用「shall」：UE 斷線後，IMS 端的通話會一直掛著 | rx-n5 §8A（W3b）＋smf-n1n2 §8A（W5c） |
| **必要但排序錯** | AMF 宣告 IMS VoPS（W2）排在 Phase 0，比 W5 早 | TS 23.501 §5.16.3.2：要有支援語音的 5G QoS flow，才可以宣告 | **W2 改成在 W5 的 G3 之後才打開**（本文已改計畫） |
| ~~選擇性，計畫中有但沒規格~~ **已補** | re-INVITE（W3d＋W5b）、註冊時（W3c）、HSS 主動通知（W8b）、QoS notification control（W5d）、抓包測試（W1）、W2／W7 檢查清單 | 規格都已寫好；其中 W3c 的 `n5` 模式與 W5d 的端到端需要先修 free5gc PCF／SMF（rx-n5 附錄 E、smf-n1n2 附錄 D） | 見 §5 的待選清單 |
| 不在計畫內 | Gm 的 IPsec（TS 33.203）、緊急通話、SMS over IP、EPS fallback、P-CSCF restoration、T-ADS、計費、合法監聽、漫遊 | 完整商用 VoNR 才需要 | 寫進「宣稱範圍與限制」，不做 |

標示說明：

| 狀態 | 意思 |
|---|---|
| ✅ 符合 | 依規格做（或計畫做完後會符合），引用的條款已讀過原文 |
| 🟡 部分 | 主要行為符合，部分分支不做或候選值未核對 |
| 🔶 偏離 | 刻意用不同的方式達成；理由見 ADR |
| ❌ 不符 | 現況或計畫與規格衝突，需要修 |
| ⬜ 不做 | 刻意排除，寫在非目標 |
| ❓ 未涵蓋 | 必要但目前沒有任何規格涵蓋 |

## 1. 端到端完整性

依 VoNR 的生命週期，把每一步對到「誰做、哪份規格、現況、計畫做完後」。

### 1.1 開機到可以打電話

| # | 步驟 | 3GPP | 負責 | 現況 | 計畫做完後 |
|---|---|---|---|---|---|
| 1 | 5G 註冊、5G-AKA | TS 23.502 §4.2.2 | AMF／AUSF／UDM | ✅ | ✅（SQN 改原子取號，hss-udm REQ-AUTH-03） |
| 2 | 告訴 UE 支援 IMS 語音 | TS 23.501 §5.16.3.2 | AMF（W2） | ❌ `imsVoPS: 0` | ✅ 但**必須在 W5 完成後才打開**（§2.1） |
| 3 | `ims` DNN 的 PDU session、預設 QoS 5QI 5 | TS 23.228 Y.2.1 | SMF、UDR | ✅ | ✅ |
| 4 | P-CSCF discovery | TS 23.228 Y.1.1、TS 23.502 §4.3.2 | SMF（PCO） | ✅ 僅 IPv4 | ✅ 僅 IPv4 |
| 5 | UPF 到 P-CSCF 之間不做 NAT | TS 23.228 Y.5 | UPF | ✅ | ✅ |

### 1.2 IMS 註冊

| # | 步驟 | 3GPP | 負責 | 現況 | 計畫做完後 |
|---|---|---|---|---|---|
| 6 | 身分由 USIM 推導（沒有 ISIM） | TS 23.228 Y.3.1、TS 23.003 §13.3 | 開戶 | ✅ | ✅ |
| 7 | UAR／UAA | TS 29.228 §6.1.1 | HSS（W8） | ❌ PyHSS 第一次註冊就回 Server-Name（待 G0 確認） | ✅ hss-udm ADR-0006 |
| 8 | MAR／MAA、IMS AKA | TS 29.228 §6.3、TS 33.203 | HSS（W8） | ❌ SQN 與 5G 分開 | ✅ 共用 SQN（hss-udm ADR-0002） |
| 9 | SAR／SAA、user profile | TS 29.228 §6.1.2 | HSS（W8） | ✅（PyHSS） | ✅ |
| 10 | Gm 的 IPsec 安全關聯 | TS 33.203 §6、§7 | P-CSCF、UE | ⬜ SIPp 與 P-CSCF 都沒用 | ⬜ 不做 |
| 11 | 註冊時的信令路徑狀態訂閱、信令 flow 提供 | TS 29.513 B.5、B.6（optional） | P-CSCF＋Adapter（W3c） | ⬜ | 🔶 rx-n5 §8B：預設 `local` 模式不呼叫 PCF；`n5` 模式照規格但需先修 PCF（照規格做會讓 SMF 的 policy 更新全部失敗、SIP 被搬到 5QI 9） |
| 12 | 註冊時訂閱 access type、PLMN 變更 | TS 29.513 B.7、B.8（optional） | 同上（W3c） | ⬜ | 🔶 `n5` 模式才有；free5gc SMF 不回報變更，只拿得到現值 |

### 1.3 通話

| # | 步驟 | 3GPP | 負責 | 現況 | 計畫做完後 |
|---|---|---|---|---|---|
| 13 | 從 SDP answer 提供 service information | TS 29.513 B.2.1、B.2.2 | P-CSCF（W4）＋Adapter（W3a） | 🔶 自訂 HTTP shim | ✅ Rx AAR → N5 Create |
| 14 | PCF → SMF → UPF 安裝語音規則 | TS 23.503、TS 23.502 §4.3.3.2 步驟 1b、2a | PCF、SMF | ✅ | ✅ |
| 15 | SMF 通知 RAN 與 UE 新的 QoS flow | TS 23.228 Y.2.3.1、TS 23.502 §4.3.3.2 步驟 3b～11 | SMF（W5） | ❌ 沒做 | ✅（在 patch 過的 free-ran-ue 上驗證） |
| 16 | 通話中修改（re-INVITE） | TS 29.513 B.3 | Adapter（W3d）、SMF（W5b） | ⬜ | 🔶 rx-n5 ADR-0009（只改頻寬用 PATCH，其他 Delete＋Create，因 free5gc PCF 的 PATCH 限制）；SMF `QFD_Mod`（smf-n1n2 §8B）；視訊不做 |
| 17 | 掛斷：BYE → STR → N5 Delete → 刪規則 | TS 29.513 B.4.1 | P-CSCF、Adapter（W3a） | ✅（shim） | ✅ |
| 18 | 掛斷後通知 RAN／UE 刪除 QoS flow | TS 23.502 §4.3.3.2 | SMF（W5） | ❌ 而且 QFI 可能不釋放 | ✅ smf-n1n2 ADR-0002 |

### 1.4 異常

| # | 步驟 | 3GPP | 負責 | 現況 | 計畫做完後 |
|---|---|---|---|---|---|
| 19 | **PDU session 或 QoS flow 遺失 → PCF 通知 P-CSCF → 結束通話** | TS 23.228 Y.2.4、TS 29.513 B.4.2、TS 29.214 §4.4.6 | Adapter（W3b）、SMF（W5c） | ❌ shim 回 404 | ✅ rx-n5 §8A、smf-n1n2 §8A（Kamailio 對 ASR 的反應待 rx-n5 D10） |
| 20 | RAN 拒絕語音 QFI | TS 23.502 §4.3.3.2 步驟 7 | SMF（W5a、W5c） | ❌ | ✅ 從 UE 刪除（REQ-RSP-03）並回報 PCF（REQ-RPT-01） |
| 20b | RAN 在通話中主動釋放語音 QFI | TS 23.502 §4.3.3.2 步驟 1e | SMF（W5c） | ❌ SMF 不處理 `PDU_RES_NTY` | ✅ smf-n1n2 REQ-RPT-02、03 |
| 21 | UE 不回 Modification Command | TS 24.501 §6.3.2.5 a | SMF（W5） | ❌ T3591 只重送 3 次 | ✅ REQ-ST-04、REQ-CFG-02 |
| 22 | 認證逾時、失敗 | TS 29.228 §6.1.2.1 | HSS（W8） | 依 PyHSS | ✅ hss-udm REQ-SAR-07 |
| 23 | 營運端強制解除 IMS 註冊；profile 推送 | TS 29.228 §6.1.3、§6.2.2 | HSS（W8b） | ⬜ | ✅ hss-udm §8A（UE 端不會收到 NOTIFY：實驗的 P-CSCF 關閉 reg-event） |
| 23b | GFBR 無法保證時通知 | TS 23.501 §5.7.2.4、TS 29.514 §4.2.5.4 | SMF（W5d）、Adapter | ⬜ | 🟡 SMF 端 ✅（smf-n1n2 §8C）；PCF 轉給 AF 的通知缺 `qncReports`，端到端需修 PCF；Rx 端是近似對應（rx-n5 ADR-0011） |
| 23c | UE 閒置時的 QoS 同步 | TS 23.502 §4.3.3.2 步驟 1d | SMF（W5b） | ❌ | ✅ smf-n1n2 ADR-0009（free5gc AMF 在 Service Request 後會丟掉 PDU_RES_MOD_REQ，改為 UP 啟動後只送 N1） |
| 24 | P-CSCF restoration | TS 23.380、TS 29.513 B.9 | — | ⬜ | ⬜ 不做 |

### 1.5 其他 5GS 對 IMS 的支援（TS 23.501 §5.16.3.1 列出的功能）

| 功能 | 計畫 |
|---|---|
| IMS voice over PS 指示 | W2（§2.1 的排序修正） |
| P-CSCF 位址傳給 UE | ✅ 現況 |
| Paging policy differentiation | ⬜ 實驗 UE 不會 idle |
| IMS 緊急服務 | ⬜ |
| UE 發起的 domain selection、終端 domain selection（T-ADS） | ⬜（HSS 已在 UDM，之後可做） |
| P-CSCF restoration | ⬜ |
| NRF-based P-CSCF discovery、HSS discovery | ⬜ |
| AMF 給 UDM 的「Homogeneous Support of IMS Voice over PS Sessions」（§5.16.3.3） | ⬜ 未查 free5gc AMF 是否有送 |

## 2. 需要修正的地方

### 2.1 W2 的排序（本次已改計畫）

TS 23.501 V17.15.0 §5.16.3.2：AMF「may only indicate IMS voice over PS session supported over 3GPP access … if the network and the UE are able to support IMS voice over PS session in the current Registration Area **with a 5G QoS Flow that supports voice** as specified in clause 5.7」。在 W5 完成之前，語音 QoS flow 根本沒有送到 RAN，所以在 Phase 0 就打開 `imsVoPS` 不符合這一條。[vonr-ims-nf-plan.md](vonr-ims-nf-plan.md) W2 已改成「設定先準備好，W5 的 G3 通過後才打開」。

### 2.2 W3b 沒有規格（已補）

TS 23.228 V17.3.0 Y.2.4.1：無線覆蓋遺失或 GFBR 無法維持時，「the 5GC may release the related GBR QoS flow and PCF and P-CSCF are notified appropriately」；P-CSCF 收到信令無法再傳給 UE 的通知時，「shall terminate any ongoing IMS session with that specific UE」。

第一版盤點時，這條鏈只有方向、沒有需求。現在補成兩段規格：

| 段 | 文件 | 內容 |
|---|---|---|
| SMF → PCF | smf-n1n2 §8A（W5c） | RAN 拒絕或釋放語音 QFI 時，以 ruleReports（INACTIVE）回報 PCF |
| PCF → Adapter → Kamailio | rx-n5 §8A（W3b） | terminate → 刪除 app session → ASR；FAILED_RESOURCES_ALLOCATION 全部失效 → ASR，部分失效 → RAR（4 或 9） |

補規格時另外發現兩件事：
- **free5gc PCF 在全部失效時只送事件、不送 terminate**，與 TS 29.514 §4.2.5.3 的 ALL_SDF_DEACTIVATION 不同。Adapter 自己判斷「全部失效」並送 ASR 來補（rx-n5 ADR-0008）。
- **Kamailio 只訂閱 Specific-Action 2、4，沒有 9**（依 2024 年碩論截圖，6.1.4 待確認）。所以部分失效時的 RAR 要用 4（TS 29.214 §5.3.13 Note 2a 允許）。

## 3. 逐條 3GPP 對照

「依據」欄指向做這件事的規格或 ADR。版本是 `specs/3gpp-r17/` 檔案內的版本。

### 3.1 架構（TS 23.228 V17.3.0、TS 23.501 V17.15.0、TS 23.503）

| 條款 | 規定（摘要） | 狀態 | 依據與說明 |
|---|---|---|---|
| 23.228 Y.0 | HSS 可以實作為 UDM 的一部分，但 IMS 功能維持獨立；對 CSCF 用 Cx 或 N70 | ✅ | hss-udm ADR-0001：UDM 內獨立的 `internal/cx`，對 Kamailio 用 Cx |
| 23.228 Y.0 | P-CSCF 與 PCF 之間用 N5 或 Rx | 🔶 | rx-n5 ADR-0001：Kamailio 用 Rx，由 Adapter 轉 N5；PCF 本身不支援 Rx。對外等於「支援 Rx 的 PCF」，但不能宣稱 free5gc PCF 支援 Rx |
| 23.228 Y.1.1 | P-CSCF discovery 在 PDU session 建立時進行 | 🟡 | 現況 PCO；只有 IPv4；不做 NRF-based discovery |
| 23.228 Y.2.1 | 至少一個 IMS 信令 QoS flow，用適當的 5QI | ✅ | `ims` DNN 預設 QoS 5QI 5（靜態設定，不是註冊時由 P-CSCF 動態要求） |
| 23.228 Y.2.2.1 | 同一個 media component 的 RTP／RTCP 在同一個 QoS flow | ✅ | PCF 一個 media component 產生一組 PCC rule；SMF 配同一個 QFI（G3 抓包確認） |
| 23.228 Y.2.3.1 | IMS 的 QoS flow 建立、修改、終止由網路依 SDP 發起 | 🟡 | 建立、終止：W3a＋W5a ✅；修改：W3d＋W5b ⬜ |
| 23.228 Y.2.4 | QoS flow 遺失要通知 P-CSCF，P-CSCF 結束通話 | ✅ | §2.2：rx-n5 W3b＋smf-n1n2 W5c |
| 23.228 Y.3.1 | 沒有 ISIM 時由 IMSI 推導 IMS 身分 | ✅ | 開戶規則；hss-udm 用明確索引（ADR-0005） |
| 23.228 Y.5 | UPF 與 P-CSCF 之間不應有 NAT | ✅ | `upf-n6.sh` 對 dnnet 不做 NAT |
| 23.228 附錄 AA | IMS 的 SBA（N70、N71） | ⬜ | hss-udm 非目標：Kamailio 不支援 |
| 23.501 §5.16.3.2 | 有語音 QoS flow 才宣告 IMS VoPS | ❌→✅ | §2.1，計畫已改排序 |
| 23.501 §5.7 | 5QI 1 是 GBR，要有 GFBR／MFBR | 🟡 | smf-n1n2 REQ-N2-02：PCF 沒給 GBR 時先不送（D04 待決定） |
| 29.513 Table 7.3.2-1 | Rx 沒帶 Minimum Requested Bandwidth 時，GBR 由營運商設定 | ❌（PCF） | free5gc PCF 只在有 MirBw 時填 GBR；不屬於本專案修改範圍，影響見 smf-n1n2 D04 |
| 23.503 附錄 C | PCF 支援 Rx 的情境 | 🔶 | 同 Y.0 的第二列 |

### 3.2 Policy 與 QoS 程序（TS 23.502 V17.15.0、TS 29.513 V17.14.0）

| 條款 | 規定（摘要） | 狀態 | 依據與說明 |
|---|---|---|---|
| 29.513 B.2.1、B.2.2 | 從 SDP answer 取得資訊，Create app session；收到 PCF 確認後才把 SDP 傳給 UE | ✅ | W4 在 200 OK 時呼叫 `Rx_AAR`（rx-n5 REQ-KAM-05）；AAR 失敗時的 SIP 處理待 rx-n5 D09 |
| 29.513 B.2.1（optional） | 在 SDP offer 時先做授權檢查、要求 access network information | ⬜ | 不做 |
| 29.513 B.3 | 通話中修改 | ⬜ | rx-n5 ADR-0006：W3a 不支援 AAR 更新；W3d；free5gc PCF 的 PATCH 有限制（[碩論比較](../background/ims-af-thesis-comparison.md) 2.2） |
| 29.513 B.4.1 | BYE 或初始 INVITE 的 3xx～6xx 最終回應 → 結束 | ✅ | BYE → STR（`ims_qos`）；AAR 只在 200 OK 送，所以失敗的初始 INVITE 不會留下 app session |
| 29.513 B.4.2 | QoS flow 釋放或遺失 | ✅ | §2.2 |
| 29.513 B.5～B.8 | 註冊時的訂閱與信令 flow（optional） | ⬜ | W3c；free5gc PCF 把 CONTROL 對應到 5QI 9，所以價值在事件訂閱 |
| 29.513 B.9 | P-CSCF restoration | ⬜ | 不做 |
| 23.502 §4.3.3.2 1b、2a | PCF 觸發，SMF 先更新 UPF | ✅ | free5gc 現況 |
| 23.502 §4.3.3.2 3b～11 | SMF 經 N1N2 通知 RAN 與 UE，處理回應 | ❌→✅ | smf-n1n2 W5a |
| 23.502 §4.3.3.2 步驟 7 | RAN 拒絕 QFI 時，SMF 另發程序修正 UE | ❌→✅ | smf-n1n2 REQ-RSP-03 |
| 23.502 §4.3.3.2 步驟 1d、11 | QoS flow 刪除未同步時標記，之後補送 | ✅ | smf-n1n2 ADR-0004、ADR-0009；新增與修改的延後同步是延伸（REQ-SYNC-03） |
| 23.502 §4.3.3.2 步驟 1e、2 | RAN 釋放 QoS flow → SMF → 回報 PCF | ❌→✅ | smf-n1n2 §8A（W5c） |

### 3.3 Diameter 與 SBI 介面

| 條款 | 規定（摘要） | 狀態 | 依據與說明 |
|---|---|---|---|
| TS 29.214（Rx） | AAR／AAA、STR／STA；ASR、RAR | 🟡 | rx-n5：AAR、STR、ASR、RAR 都有規格（W3a、W3b）；錯誤碼與對應關係為候選，待 rx-n5 D02、D11 |
| TS 29.214 §4.4.6.1 | IP-CAN session 終止 → 每個 Rx session 送 ASR，AF 回 ASA 後送 STR | ✅ | rx-n5 REQ-ASR-01～05 |
| TS 29.214 §4.4.6.2 | 部分 SDF 失效 → RAR；全部失效 → ASR | ✅ | rx-n5 REQ-RAR-01～03、ADR-0008 |
| TS 29.514（N5） | Create、Delete（`POST …/delete`）、PATCH、Notify | 🟡 | Create、Delete ✅；PATCH ⬜（W3d）；terminate 與事件 callback ✅（W3a 可接收、W3b 處理） |
| TS 29.514 §4.2.5.3 | terminate：回 204 後呼叫 Delete | ✅ | rx-n5 REQ-ASR-01、ADR-0007（free5gc PCF 已自行刪除，Delete 回 404 視為已清理） |
| TS 29.228 §6.1.1.1（UAR） | 第一次註冊不得回 S-CSCF 名稱 | ❌→✅ | hss-udm ADR-0006；現況 PyHSS 疑似違反（待 G0 抓包） |
| TS 29.228 §6.1.2.1（SAR） | 各種 Server-Assignment-Type 的狀態轉移 | 🟡 | hss-udm §6.3、§9.2：支援的類型 ✅；restoration、多 IMPI、wildcard ⬜ |
| TS 29.228 §6.1.4.1（LIR） | 依註冊狀態回 S-CSCF 或 capabilities | ✅ | hss-udm §6.4 |
| TS 29.228 §6.3.1（MAR） | 存 S-CSCF、authentication pending、AUTS 重新同步 | ✅ | hss-udm §6.2 |
| TS 29.228 §6.1.3（RTR）、§6.2.2（PPR） | HSS 主動通知 | ✅ | hss-udm §8A（W8b）；RTA 失敗的處理規格沒規定，自訂於 ADR-0010 |
| TS 29.229 §6.2 | Experimental-Result 值 | ✅ | hss-udm §10.1；與 base Result-Code 分開（REQ-GEN-06） |
| RFC 6733 base Result-Code | — | 🟡 | 三組規格都列為候選值，各自的 D02 核對 |
| TS 29.505（UDR） | Nudr 資源 | 🔶 | hss-udm ADR-0004：IMS 資料用非標準擴充 `/nudr-ims-ext/v1` |

### 3.4 安全

| 條款 | 規定（摘要） | 狀態 | 依據與說明 |
|---|---|---|---|
| TS 33.203 §8.2 | USIM 做 IMS 存取時，key、演算法、SQN 檢查機制共用 | ❌→✅ | 現況 PyHSS 與 UDR 各一個 SQN；hss-udm ADR-0002 |
| TS 33.203 附錄 G | 建議不同 domain 用不同 IND 範圍 | ⬜ | hss-udm D07；目前每組向量 +1（TS 33.102 C.3.4 一般規則） |
| TS 33.203 §6、§7 | UE 與 P-CSCF 之間的 IPsec | ⬜ | 實驗不做；寫進各組的宣稱範圍 |
| TS 33.102 C.3.4 | IND 循環配置 | ✅ | free5gc UDM 現有行為 |
| — | 同一 SUPI 並行認證不得發出相同 SQN | ❌→✅ | hss-udm ADR-0003（現況非原子） |

### 3.5 NAS（TS 24.501 V17.18）

| 條款 | 規定（摘要） | 狀態 | 依據與說明 |
|---|---|---|---|
| §6.3.2.2 | 網路發起時 PTI 為「未指派」 | ❌→✅ | smf-n1n2 ADR-0006（現況 builder 用 UE 的 PTI） |
| §6.3.2.2 | QoS rule、flow description 變更要帶給 UE；新 GBR flow 要有 flow description | ❌→✅ | smf-n1n2 REQ-N1-02、03 |
| §6.3.2.2 | packet filter 數不得超過 UE 能力 | 🟡 | smf-n1n2 REQ-N1-05；上限來源待 D06 |
| §6.3.2.5 a | T3591 重送 4 次，第 5 次逾時中止 | ❌→✅ | 部署設定 3 次；smf-n1n2 REQ-CFG-02 |
| §6.3.2.5 c、d | 與 UE 發起的釋放、修改相撞 | ✅ | smf-n1n2 REQ-ST-05 |

### 3.6 身分

| 條款 | 規定（摘要） | 狀態 | 依據與說明 |
|---|---|---|---|
| TS 23.003 §13.3 | 沒有 ISIM 時 IMPI 由 IMSI 推導 | ✅ | 開戶規則；`kamailio-free5gc` 文件把條款誤寫成 §13.4B |
| TS 23.003 §13.4 | IMPU 的 canonical form 與比較 | 🟡 | hss-udm REQ-ID-02；RFC 3261 §19.1.4 待核對 |

## 4. 沒有核對到的規格

下列規格與本對照有關，但本機沒有或沒讀，相關結論都只能算候選：

| 規格 | 影響 |
|---|---|
| TS 38.413（NGAP） | smf-n1n2 的 N2 IE、釋放 cause、PDU Session Resource Notify |
| TS 29.512 | smf-n1n2 的 ruleReports 語意（D10） |
| TS 29.502、TS 29.518 | smf-n1n2 的 UpdateSMContext、N1N2 cause |
| RFC 6733 | 三組規格的 base Result-Code |
| TS 24.229（P-CSCF 的 SIP 行為） | Kamailio 的行為，本專案不改，未逐條核對 |
| TS 23.632、TS 29.563 | UDM 與 HSS 分開部署時的互通；本設計是合併，未使用 |
| TS 33.401 | IMS AKA 向量的 AMF separation bit（hss-udm D14） |

## 5. 計畫外、尚未寫規格的待選項目

這些都是「完整商用 VoNR」才需要、但不在 W1～W8 的項目。若要納入，每一項都要先另立工作項再寫規格。

| 項目 | 3GPP | 涉及 | 備註 |
|---|---|---|---|
| Gm 的 IPsec（UE 與 P-CSCF 之間） | TS 33.203 §6、§7 | Kamailio `ims_ipsec_pcscf`、UE | SIPp 不支援；需要換 IMS client |
| IMS 緊急通話 | TS 23.167、TS 23.501 §5.16.4 | AMF、SMF、E-CSCF | 實驗沒有 E-CSCF |
| SMS over IP | TS 24.341、TS 29.513 B.11、B.12 | IP-SM-GW | — |
| EPS fallback | TS 23.502 §4.13.6.1、TS 23.501 §5.16.3.10 | AMF、RAN、EPC | 需要 4G 核網 |
| P-CSCF restoration | TS 23.380、TS 29.513 B.9 | SMF、PCF、HSS、P-CSCF | — |
| Terminating domain selection（T-ADS） | TS 23.501 §5.16.3.6 | HSS（已在 UDM）、AMF | AMF 送給 UDM 的 `ImsVoPs` 寫死，要先修（[w2-w7-checklists.md](w2-w7-checklists.md) W2-4） |
| NRF-based P-CSCF／HSS discovery | TS 23.501 §5.16.3.11、§5.16.3.12 | SMF、NRF | 目前用設定值 |
| PCO 的 IPv6 P-CSCF 位址 | TS 24.501 | SMF | 實驗只有 IPv4 |
| 計費（Rf／Ro、Nchf） | TS 32.260 | CSCF、CHF | — |
| 合法監聽 | TS 33.127 | 全部 | — |
| 漫遊 | TS 23.228 Y.9 | 全部 | — |
| 修 free5gc PCF 的 GBR 推導（Table 7.3.2-1）、QOS_NOTIF 內容、AF_SIGNALLING 處理 | TS 29.513、TS 29.514 | PCF | 會解除 smf-n1n2 D04、D13 與 rx-n5 W3c `n5` 模式的前提；違反計畫「不改 PCF」，需另行決定 |
