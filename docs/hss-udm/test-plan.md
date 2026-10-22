# HSS 併入 UDM 測試計畫（W8a＋W8b）

| 項目 | 內容 |
|---|---|
| 版本／狀態 | v0.3／審查中（2026-10-22：新增 T35–T44，W8b） |
| 驗證對象 | [interface-spec.md](interface-spec.md) 的 REQ-* |
| 門檻 | G0–G4，見 [../overview/vonr-ims-nf-plan.md](../overview/vonr-ims-nf-plan.md) W8 |

## 1. 測試案例

**層級**：U＝單元（`statemachine.go`、mapper、共用認證向量函式；UDR 用可注入延遲、失敗與版本衝突的 stub）；I＝整合（真的 UDM、UDR、MongoDB，Cx 對端用 go-diameter 寫的小 client）；E＝端到端（Kamailio＋free-ran-ue＋SIPp）。並行相關的 U／I 測試必須開 Go race detector。

| ID | 情境 | 層級 | 必須觀察到的結果 |
|---|---|---|---|
| T01 | 用 D03 在 PyHSS 部署錄下的 UAR、MAR、SAR、LIR 解碼 | U | 四種請求都能解碼；每個 M-bit 為 1 的 AVP 都在字典裡 |
| T02 | CER／DWR／DPR；未在白名單的 peer；對端宣告多個 Cx vendor | I | CEA 以 Vendor-Specific-Application-Id 宣告 16777216／10415；DWR、DPR 正常；非白名單 peer 被拒（RC 3010 候選）；宣告 4491、13019、0 的 peer 仍能連上 |
| T03 | 未知 AVP：M-bit 0 與 1 | U | M-bit 0 忽略並照常回答；M-bit 1 回 RC 5001＋Failed-AVP |
| T04 | 身分錯誤：未知 IMPI、未知 IMPU、IMPI 與 IMPU 不相屬、Tel URI、host 大小寫不同的 IMPU | U | 依序回 Exp 5001、5001、5002、5001；host 大小寫不同仍能找到同一個 SUPI |
| T05 | UAR REGISTRATION：NR0、NR1、REG、UNREG 各一次 | U | NR0 回 Server-Capabilities（Mandatory-Capability 0）＋Exp 2001，**沒有** Server-Name；其他三種回已存 S-CSCF＋Exp 2002，**沒有** capabilities |
| T06 | UAR DE_REGISTRATION：NR0、NR1、REG、UNREG | U | NR0 回 Exp 5003 且不帶 Server-Name；其他回已存 S-CSCF＋RC 2001 |
| T07 | UAR：REGISTRATION_AND_CAPABILITIES、BarringIndication＝1、Visited-Network 不在允許清單、emergency 旗標 | U | 依序回 capabilities＋RC 2001（無 Server-Name）、RC 5003（AUTHORIZATION_REJECTED）、Exp 5004、RC 5012 |
| T08 | 每個 T05–T07 案例前後各取一次 UDR 快照 | U | UAR 前後的註冊紀錄完全相同 |
| T09 | MAR 一般請求，SIP-Number-Auth-Items＝1、3，`maxAuthItems`＝1 | U、I | 回 1 組向量；SIP-Authenticate 32 bytes；XRES、CK、IK 長度正確；已存 S-CSCF 與 authPending 依 §9.2 寫入；回答之前 UDR 寫入已完成 |
| T10 | MAR：SIP Digest、NASS-Bundled、Unknown 認證方式；缺 Server-Name | U | 前三者回 Exp 5006；缺 Server-Name 回 RC 5005（MISSING_AVP） |
| T11 | MAR 重新同步：合法 AUTS 且 Server-Name 相同；Server-Name 不同；MAC-S 錯誤 | U | 第一種的 SQN 變成 SQN_MS＋33，新向量通過 T13 的 USIM 模型驗證；第二、三種回 RC 5012，SQN 不變 |
| T12 | Milenage 對照 TS 35.208 測試資料 | U | 所有測試組的 RES、CK、IK、AK、MAC-A 相符 |
| T13 | USIM 模型（依 TS 33.102 C.2.2 的 array 機制，IND 5 bits）：隨機交錯 1000 次 5G-AKA 與 IMS AKA；另外把一組向量重送兩次 | U | 交錯的每一組都被 USIM 模型接受；重送的第二次被拒（同一 SQN 不會被接受兩次） |
| T14 | 同一個 SUPI 上，50 個 goroutine 混合發 5G-AKA 與 MAR，對真的 UDR＋MongoDB | I | 發出的 SQN 全部不同；UDR 最後的 SQN＝初始值＋成功取號的次數；race detector 乾淨 |
| T15 | 5G-AKA 經 AUSF → UDM 的路徑 | I | SQN 經 sqn-allocations 取號（抓包或 UDR log 可見）；舊的 PATCH `/sequenceNumber` 不再出現 |
| T16 | SAR REGISTRATION、RE_REGISTRATION；已存另一台 S-CSCF 時的 REGISTRATION | U | 依 §9.2 轉成 REG、清 authPending、帶 User-Data、RC 2001；另一台的情況回 Exp 5005 且帶已存 S-CSCF |
| T17 | SAR UNREGISTERED_USER：NR0、REG（同一台）、REG（另一台） | U | 前兩者轉成 UNREG 並帶 User-Data；第三者回 Exp 5005＋已存 S-CSCF |
| T18 | SAR：類型 4、5、8、11；6、7；9、10；0（同一台與另一台）；12、13、14、99；多個 Public-Identity 配 REGISTRATION；只有 User-Name 的 TIMEOUT_DEREGISTRATION；兩者都沒有 | U | 依 §9.2：4／5／8／11 轉 NR0 並回 RC 2001；6／7 轉 NR0 並回 Exp 2004；9／10 清 authPending、NR1 清 S-CSCF；0 同一台帶 User-Data、另一台 RC 5012；12–14 與 99 回 Exp 5007；多身分回 RC 5009；只有 User-Name 能找到 IMPU；兩者都沒有回 RC 5005 |
| T19 | LIR：REG、UNREG、NR1、NR0，各配 `unregisteredServices` true／false 與 Originating-Request | U | 依 §9.2：REG／UNREG 回已存 S-CSCF＋RC 2001；NR1＋unregistered service 回已存 S-CSCF；NR0＋unregistered service 回 capabilities＋Exp 2003；其他 NR 回 Exp 5003；LIR 前後狀態相同；User-Authorization-Type 不影響結果 |
| T20 | §9.2 轉移表逐列的表格驅動測試 | U | 每一列至少一個案例；動作、答案代碼、下一狀態都相符 |
| T21 | User-Data：一般、BarringIndication＝1 | U | 用 `xmllint --schema scscf/CxDataType_Rel7.xsd` 驗證通過；沒有 `InitialFilterCriteria`、沒有 Charging-Information |
| T22 | 每個指令配 UDR 失敗、逾時（超過 `udrTimeout`）、412 用完重試 | U | 都回 RC 5012；不帶向量、User-Data、Server-Name；註冊紀錄沒有改變 |
| T23 | 兩台 S-CSCF 對同一個 IMPU 同時送 SAR REGISTRATION | I | 恰好一個 RC 2001，另一個 Exp 5005；UDR 的 S-CSCF 是成功那一台 |
| T24 | MAR 之後、SAR 之前重啟 UDM | I | 重啟後 SAR REGISTRATION 成功；UAR 在重啟前後對同一 IMPU 的答案相同 |
| T25 | UDR 擴充 API：PUT（合法、IMPU 非 canonical、IMPU 已屬於別的 SUPI）、GET 身分索引、PUT 註冊紀錄 If-Match 錯誤、刪除 subscription、刪除單一註冊紀錄 | I | 依序 201／200、被正規化或拒絕、409、索引正確、412、註冊紀錄與索引一併刪除且之後 LIR 回 Exp 5001、單一註冊紀錄可刪 |
| T26 | 5G 回歸：free-ran-ue 註冊並建立 PDU session，`cx.enable` false 與 true 各一次 | E | 兩次都成功；`cx.enable` false 時 UDM 沒有開 3868 |
| T27 | 端到端：移除 PyHSS 後跑 `03-call-test.sh` | E | 註冊與通話成功；pcap 中 UAA、MAA、SAA、LIA 的 Origin-Host 是 UDM；UAA（第一次）沒有 Server-Name；UDR 只有一個 SQN，且 5G-AKA 與 IMS AKA 之後都比原值大 |
| T28 | 回退：照 G4 的程序切回 PyHSS | E | 回退後 `03-call-test.sh` 通過；切換期間 PyHSS 與 UDM 沒有同時取得 `hss.ims…` 別名 |
| T29 | 跑完 T27 之後搜尋 UDM、UDR 的 log；OAuth 關閉時的啟動 log | I | 找不到 K、OP、OPc、CK、IK、XRES、AUTS 與完整 IMPI／IMPU／SUPI；有「實驗 profile：SBI 未授權」 |
| T30 | 指標與 readiness；UDR 停止 | I | REQ-OBS-02 的指標存在且數值與測試動作一致；UDR 停止時 readiness 為否、Cx 指令都回 RC 5012、peer 連線仍在 |
| T31 | 設定檢查：`allowedPeers` 空、`udrTimeout` 5s、`maxAuthItems` 0、`bindAddr` 0.0.0.0 | U | 前三者拒絕啟動；最後一個輸出警告；啟動 log 有設定且不含秘密值 |
| T32 | 開戶：改寫後的 `04-add-ims-subscribers.sh` 跑兩次 | I | UDR 有正確的 ims-subscription 與索引；第二次執行結果相同（可重複執行） |
| T33 | peer 斷線再連上 | I | 記錄事件；所有註冊紀錄不變 |
| T34 | 程式審查：HSS 子系統的 import 與鎖 | — | 不 import SIP 套件；沒有跨請求、跨 UDR 呼叫持有的全域鎖 |
| T35 | W8b：註冊後檢查紀錄 | U | `scscfDiameterHost` 是 S-CSCF 的 Origin-Host（不是 Server-Name）；`sarImpi` 正確 |
| T36 | W8b：RTR 與 PPR 的內容（stub S-CSCF） | U、I | Destination-Host／Realm、User-Name 取自紀錄；Auth-Session-State 1；新的 Session-Id；沒有 Associated-Identities；NEW_SERVER_ASSIGNED 帶 Public-Identity；PPR 只帶 User-Data 且能通過 XSD |
| T37 | W8b：RTR PERMANENT_TERMINATION、SERVER_CHANGE、NEW_SERVER_ASSIGNED 的狀態更新 | U | 前兩者收到成功 RTA 才變 NR0；RTA 前 LIR 仍回原 S-CSCF；NEW_SERVER_ASSIGNED 不改狀態 |
| T38 | W8b：RTA 逾時與錯誤；觸發來源為刪除開戶與管理操作 | U | 依 `cx.w8b.retry` 重送；用完後刪除開戶照樣刪除並告警；管理操作狀態不變並回錯誤 |
| T39 | W8b：REG 時另一台 S-CSCF 的 MAR | U | 對原 S-CSCF 送 RTR NEW_SERVER_ASSIGNED；兩者 Diameter 位址相同時不送 |
| T40 | W8b：PPA 成功、5008、5009、5001、逾時 | U | 依 REQ-PPR-04：5008／5009 改送 RTR SERVER_CHANGE；5001 變 NR0；逾時重送後告警 |
| T41 | W8b：修改開戶資料（BarringIndication、IMPU） | U、I | 前者送 PPR；後者改送 RTR SERVER_CHANGE；NR0 的用戶都不送 |
| T42 | W8b：`cx.w8b.enable` false | U | 不送 RTR、PPR；刪除開戶依 W8a 行為 |
| T43 | W8b 端到端：UE1 註冊後經擴充 API 刪除 UE1 | E | 抓包看到 RTR／RTA；之後 UE2 打給 UE1 時 LIA 回 Exp 5001 或 5003；UE 端不會收到 NOTIFY（實驗限制） |
| T44 | W8b 連線方式（D15）與 Kamailio 反應（D16） | I | 記錄 RTR／PPR 走的連線與 S-CSCF 的回應；結論寫回 interface-spec 附錄 B |

## 2. 需求追溯

| 需求 | 測試 | 檢驗方式 |
|---|---|---|
| REQ-GEN-01 | T02、T27 | 測試＋抓包 |
| REQ-GEN-02 | T26 | 測試 |
| REQ-GEN-03 | T05、T34 | 測試＋程式審查（不 import SIP 套件；UAA 不自選 S-CSCF） |
| REQ-GEN-04 | T07、T10、T18、T42 | 測試 |
| REQ-GEN-05 | T09、T22 | 測試 |
| REQ-GEN-06 | T07、T18、T20 | 測試（逐案檢查答案放在 Result-Code 或 Experimental-Result） |
| REQ-PEER-01～03 | T02 | 測試 |
| REQ-PEER-04 | T26、T31 | 測試 |
| REQ-PEER-05 | T01、T03 | 測試 |
| REQ-PEER-06 | T27 | 抓包 |
| REQ-PEER-07 | T33 | 測試 |
| REQ-ID-01、04 | T04 | 測試 |
| REQ-ID-02 | T04、T25 | 測試 |
| REQ-ID-03 | T25 | 測試 |
| REQ-UAR-01、02 | T04 | 測試 |
| REQ-UAR-03、04、07、08 | T07 | 測試 |
| REQ-UAR-05 | T05、T27 | 測試＋抓包 |
| REQ-UAR-06 | T06 | 測試 |
| REQ-UAR-09 | T08 | 測試 |
| REQ-UAR-10 | T22 | 測試 |
| REQ-MAR-01 | T04 | 測試 |
| REQ-MAR-02、07 | T10 | 測試 |
| REQ-MAR-03、04 | T09 | 測試 |
| REQ-MAR-05、06 | T11 | 測試 |
| REQ-SAR-01 | T04 | 測試 |
| REQ-SAR-02、05～09 | T18 | 測試 |
| REQ-SAR-03 | T16、T23 | 測試 |
| REQ-SAR-04 | T17 | 測試 |
| REQ-SAR-10 | T22 | 測試 |
| REQ-LIR-01～04 | T19 | 測試 |
| REQ-LIR-05 | T19、T22 | 測試 |
| REQ-AUTH-01 | T27 | 測試（UDR 只有一份認證資料）＋程式審查 |
| REQ-AUTH-02 | T13、T14 | 測試 |
| REQ-AUTH-03 | T15 | 測試 |
| REQ-AUTH-04 | T13、T14 | 測試 |
| REQ-AUTH-05 | T11 | 測試 |
| REQ-AUTH-06 | T12 | 測試 |
| REQ-AUTH-07 | T09 | 測試（AMF 與 UDR 一致）；D14 結論後補案例 |
| REQ-AUTH-08 | T13 | 測試 |
| REQ-AUTH-09 | T22 | 測試（取號後寫入失敗，SQN 不回退） |
| REQ-UD-01、02、04 | T21 | 測試 |
| REQ-UD-03 | T16、T17、T18 | 測試 |
| REQ-ST-01、02 | T23 | 測試 |
| REQ-ST-03 | T24 | 測試 |
| REQ-ST-04 | T14、T34 | 測試＋程式審查 |
| REQ-CFG-01～03 | T31 | 測試 |
| REQ-DATA-01 | T15、T25 | 測試＋程式審查（標準 Nudr 路由未被修改） |
| REQ-DATA-02、03、04、06 | T25 | 測試 |
| REQ-DATA-05 | T14 | 測試 |
| REQ-SEC-01、02 | T29 | 測試 |
| REQ-SEC-03 | T31 | 測試＋程式審查 |
| REQ-OBS-01 | T29 | 測試（log 欄位齊全） |
| REQ-OBS-02 | T30 | 測試 |
| REQ-OPS-01 | T30 | 測試 |
| REQ-OPS-02、04 | T28 | 測試 |
| REQ-OPS-03 | T25 | 測試 |
| REQ-OPS-05 | T32 | 測試＋程式審查（腳本只呼叫擴充 API） |
| REQ-CLI-01 | T36、T44 | 測試 |
| REQ-CLI-02、03 | T35、T36 | 測試 |
| REQ-CLI-04 | T36 | 測試 |
| REQ-CLI-05 | T41 | 測試 |
| REQ-RTR-01 | T43 | 測試＋抓包 |
| REQ-RTR-02、04 | T36 | 測試 |
| REQ-RTR-03 | T39 | 測試 |
| REQ-RTR-05 | T37 | 測試 |
| REQ-RTR-06、07 | T38 | 測試 |
| REQ-PPR-01～03 | T36、T41 | 測試 |
| REQ-PPR-04 | T40 | 測試 |

新增或修改需求時，必須同時更新這張表；沒有測試也沒有審查方式的需求不能進入 G2。

## 3. 分層判定

| 層級 | PASS 需要的證據 | 本階段 |
|---|---|---|
| L1 Cx 協定 | 每個指令的答案代碼、欄位（Result-Code 或 Experimental-Result）與 AVP 符合 §6、§10（T01–T11、T16–T20） | 必須 |
| L2 IMS 註冊 | 經 UDM 完成 IMS 註冊，抓包可對應 UAR→MAR→401→UAR→SAR→200（T27） | 必須 |
| L3 通話與解除註冊 | LIR 正確導到被叫的 S-CSCF；解除註冊後狀態回 NR0（T27、T18） | 必須 |
| L4 SQN 正確性 | 單一計數器、並行不重複、USIM 模型接受交錯（T13、T14、T15） | 必須 |
| L5 真實 USIM／手機 | 實體 UE 的 5G-AKA 與 IMS AKA 交錯 | 後續（沒有設備；實驗 UE 不檢查 SQN 新鮮度） |
| L6 HSS 主動通知 | RTR、PPR 的抓包與之後的 LIR 結果（T43）；UE 端不驗證（P-CSCF 關閉 reg-event） | 必須（W8b） |

用 tshark 解析 Diameter、SIP，不用 log 字串判定。缺工具時輸出 SKIP 或 BLOCKED，不能算 PASS；L4 未驗證時，本階段整體不能算 PASS。

## 4. 要保存的證據

每次驗收保存：版本 manifest、測試命令與退出碼、帶時間的 log、pcap（Cx、SIP、NGAP／NAS）、驗收前後的 UDR 快照（`authenticationSubscription` 的 SQN、IMS 擴充的三個 collection）、逐案結果。

G0 的 PyHSS 基準 pcap 也要保存，作為 T01 的 fixture 與行為比較的依據。fixture 必須移除真實身分與金鑰（實驗用的是 3GPP 公開測試值，仍要註明來源）。

## 5. 版本 manifest（G0 填寫）

| 項目 | 必填 | 目前 |
|---|---|---|
| 本 repo 與 `kamailio-free5gc` submodule | URL、commit | 待填 |
| free5gc 與 UDM、UDR、AUSF、AMF | release、commit；UDM／UDR fork 的 commit | 部署 4.2.3；本機原始碼 UDM v1.4.6、UDR v1.4.4；待 D01 |
| Kamailio | 版本、映像 digest、`icscf.xml`、`scscf.xml`、`icscf/seed.sql` | 6.1.4，digest 待填 |
| PyHSS（G0 基準） | 映像 digest | `sha256:da53ca70…`（compose 中） |
| free-ran-ue、SIPp | 版本、patch、情境檔 commit | free-ran-ue v2.5.0＋`pcscf-discovery.patch`；SIPp 待填 |
| go-diameter | module 版本 | 待 D13（CHF 用 v3.0.2+incompatible） |
| MongoDB | 版本 | 待填 |
| xmllint、tshark | 版本 | 待填 |
| Go、OS、kernel、Docker、compose | 版本 | 待填 |
| 3GPP | 每份 TS 的版本與章節 | 見 [interface-spec.md](interface-spec.md) §2 |

只寫 main／master 不算填寫完成。

## 6. 完成定義

G0–G4 的證據齊全；必須的測試沒有未說明的 FAIL 或 SKIP；L1–L4 PASS；回退程序實測過一次。達成後只能使用 [design.md](design.md) §11 允許的說法：「W8a：free5gc UDM 以 Cx 取代 PyHSS 完成」。
