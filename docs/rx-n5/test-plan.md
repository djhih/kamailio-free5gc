# Rx／N5 Adapter 測試計畫（第一階段）

| 項目 | 內容 |
|---|---|
| 版本／狀態 | v0.6／審查中（2026-10-22：v0.6 新增 T53–T62，W3c、W5d、BSF；v0.5 新增 T46–T52，W3d；v0.4 新增 T35–T45，W3b；v0.3 新增 T30–T34，W4） |
| 驗證對象 | [interface-spec.md](interface-spec.md) 的 REQ-* |
| 門檻 | G0–G4，見 [../overview/vonr-ims-nf-plan.md](../overview/vonr-ims-nf-plan.md) W3a |

## 1. 測試案例

**層級**：U＝單元（mapper、狀態機，PCF 用可注入延遲與故障的 stub）；I＝整合（真的 PCF、假的 Diameter client）；E＝端到端（Kamailio＋兩支 UE）。並行相關的 U／I 測試必須開 Go race detector。

| ID | 情境 | 層級 | 必須觀察到的結果 |
|---|---|---|---|
| T01 | 合法 AUDIO AAR | U、I | 一個 app session；保存完整 URI；AAA 成功；N5 body 符合 §5.2 |
| T02 | 缺 Session-Id／Framed-IP、IPv4 不合法、編號重複、頻寬溢位、DNN 不允許 | U | 明確拒絕；PCF Create 呼叫次數為 0 |
| T03 | 不支援的 Media-Type（含 CONTROL）、不支援的 Specific-Action | U、I | 不回成功；不建立資源；Specific-Action 處理符合 REQ-AAR-08 的結論 |
| T04 | Create 進行中與完成後各重送一次 AAR | U | Create 只呼叫一次；兩次重送拿到同一答案 |
| T05 | ACTIVE 上送內容不同的 AAR | U、I | 被拒絕；原 app session 不變；沒有 PATCH、Delete、第二次 Create |
| T06 | 正常 STR | I、E | 抓包看到 `POST …/delete`（不是 HTTP DELETE）；app session 與專屬規則消失；同 UE 其他資源不受影響 |
| T07 | 重複 STR、未知 Session-Id 的 STR、CLOSED 後同 Session-Id 的新 AAR | U | 重複 STR 回 tombstone 答案；未知 session 依 REQ-STR-04；新 AAR 被拒；沒有誤刪 |
| T08 | PCF 回 403／500／400 | U、I | 依 §10.1 回覆；不回成功；session 轉 CLOSED |
| T09 | PCF 已建立但回覆遺失（stub 建立後不回）；之後再送 AAR | U | `CREATE_UNKNOWN`；告警；後續 AAR 回失敗且不再 Create |
| T10 | PCF 成功但本地保存失敗 | U | 補償刪除；補償失敗時留下 DELETE_PENDING；AAA 不回成功 |
| T11 | Delete 逾時、可重試錯誤、不可重試錯誤 | U | DELETE_PENDING；URI 保留；重試次數與間隔符合 §11；耗盡後告警 |
| T12 | AAR 與 STR 並行；STR 比 Create 回應先到 | U | `pendingTermination` 不遺失；Create 成功後立刻刪除；沒有孤兒資源 |
| T13 | 同一 UE 有兩個 Rx session，刪其中一個 | U、I | 另一個 app session 與規則不受影響 |
| T14 | Adapter 在 CREATING、ACTIVE、DELETING 各重啟一次 | I | 重啟後依 REQ-ST-04 恢復；ACTIVE 的 session 仍能被 STR 正常刪除 |
| T15 | URL 處理：非根 apiPrefix、FQDN／IP、相對 Location、指向非允許主機的 Location | U | 前三者正確解析並保存；最後一個當回覆不完整，且沒有對該主機發請求 |
| T16 | Flow 方向 | E | 對照 Rx、N5、N7、UPF PDR 與實際 UE 位址／port，上下行方向正確 |
| T17 | callback：terminate、未知 callbackKey、重複通知 | I | 路徑可達；回 204／404；可追蹤；session 狀態不變；沒有 ASR 被記錄成已送 |
| T18 | 兩支 UE 端到端通話 | E | IMS 註冊、INVITE／200／ACK／BYE、AAR／AAA、STR／STA 與雙向 RTP 在抓包中可互相對應 |
| T19 | Diameter peer：CER／DWR、未在白名單的 peer | I | CEA 宣告 16777236／10415；DWR 正常；非白名單 peer 被拒 |
| T20 | 未知 AVP：M-bit 0 與 1；用 D03 錄下的 Kamailio AAR | U | M-bit 0 忽略並成功；M-bit 1 回錯誤＋Failed-AVP；真實 AAR 能解碼 |
| T21 | peer 斷線再連上 | I | 記錄事件；既有 session 狀態不變 |
| T22 | Delete 回 404：資源不存在、路徑錯誤 | U | 前者 CLOSED；後者當錯誤處理（DELETE_PENDING） |
| T23 | mapper 表格驅動 | U | 每列 §5.2 對應都有測試；Flow-Description 原樣複製（或依 D05 結論改寫） |
| T24 | 設定檢查：allowedPeers 空、advertisedBase 為 0.0.0.0、serviceBase 無法解析 | U | 拒絕啟動或警告，依 REQ-CFG-01、REQ-CB-05 |
| T25 | log 遮蔽與實驗 profile | I | 跑完 T18 後搜尋 log，沒有 K／OP／OPc／token／完整 SUPI；OAuth 關閉時有實驗 profile 記錄 |
| T26 | 指標與健康檢查 | I | REQ-OBS-02 的指標存在且數值和測試動作一致；PCF 停掉時「可處理新請求」變成否 |
| T27 | 優雅關閉 | I | 進行中的 Create／Delete 留下可恢復紀錄；重啟後接續 |
| T28 | NRF 註冊 | I | NRF 查得到這個 AF |
| T29 | shim 切換與回退 | E | 切換後只有 Adapter 建立 app session；執行回退程序後 shim 路徑的 `03-call-test.sh` 通過 |
| T30 | P-CSCF 映像與設定靜態檢查 | U | 映像內有 `cdp`、`cdp_avp`、`ims_qos` 模組檔；`kamailio -c` 通過；cfg 不含 `http_client` 與 `AF_*` route；`terminate_dialog_on_rx_failure` 有明確值；有 P-CSCF 的 cdp 設定檔且只列 Adapter |
| T31 | P-CSCF 與 Adapter 的 Diameter 連線 | I | 抓包看到 P-CSCF 對 Adapter 送 CER，宣告 16777236／10415；沒有對 HSS 的連線 |
| T32 | 一通電話的 Rx 訊息數量與時機 | E | 200 OK 之後恰好兩個 AAR（一個 orig、一個 term），各自 AAA；BYE 之後恰好兩個 STR；IMS 註冊期間沒有任何 AAR |
| T33 | Adapter 回 AAR 失敗（例如 PCF 停掉） | E | 依 REQ-KAM-06（D09 的結論）處理；D09 關閉前：通話建立、P-CSCF log 有錯誤 |
| T34 | cfg diff 審查 | — | diff 只涵蓋模組、cdp、`ims_qos` modparam、onreply 的 `Rx_AAR` 與移除的 `AF_*` |
| T35 | W3b：ACTIVE 時收到 terminate（`PDU_SESSION_TERMINATION`），PCF stub 已刪除 app session | U、I | 先回 204；之後 Delete 收到 404＋`APPLICATION_SESSION_CONTEXT_NOT_FOUND` 並視為已清理；送出 ASR（Abort-Cause 0）；ASA 後收到 STR 回 STA 成功；session CLOSED |
| T36 | W3b：ASA 逾時與錯誤；ASR 後一直沒有 STR | U | 依 `w3b.asr.retry` 重送同一 Session-Id 的 ASR，用完告警；`strWait` 到期轉 CLOSED；之後到達的 STR 依 tombstone 回 STA 成功；沒有新的 Create |
| T37 | W3b：terminate 分別在 CREATING、DELETING、DELETE_PENDING、CREATE_UNKNOWN、CLOSED 到達；重複 terminate | U | 依 §9.2：CREATING 的 AAR 最後回失敗且沒有 ASR；DELETING／DELETE_PENDING 只回 204；CREATE_UNKNOWN 回 204 並送 ASR；CLOSED 有 tombstone 回 204、無則 404；重複通知冪等 |
| T38 | W3b：termCause 對 Abort-Cause | U | 依 §10.3 逐列對應 |
| T39 | W3b：AAR 訂閱 2／4／9 的組合 | U | 含任一者時 Create 帶 `evSubsc`（FAILED_RESOURCES_ALLOCATION、events 路徑）；只有其他值時不帶；`subscribedActions` 已保存 |
| T40 | W3b：FAILED_RESOURCES_ALLOCATION 全部失效（無 `flows`、`flows` 涵蓋所有 flow）與部分失效 | U | 全部失效：Delete 成功後送 ASR（Abort-Cause 0）；部分失效：送 RAR，Flows 正確，Specific-Action 依訂閱為 9、4 或不送；app session 不變 |
| T41 | W3b：RAA 逾時；peer 斷線時要送 ASR／RAR | U、I | RAR 依 `w3b.rar.retry` 重送後告警，session 狀態不變；peer 斷線時排隊，`peerWait` 內連上就送出，逾時告警 |
| T42 | W3b：其他事件（SUCCESSFUL_RESOURCES_ALLOCATION、ACCESS_TYPE_CHANGE）；未知 callbackKey 的事件 | U | 前者回 204、只記錄、沒有 RAR；後者 404 |
| T43 | W3b 端到端：通話中用 free-ran-ue 釋放 UE2 的 PDU session | E | 抓包看到 SMF → PCF 的 SM policy 刪除、PCF → Adapter 的 terminate、Adapter → P-CSCF 的 ASR／ASA、兩支 UE 都收到 BYE、之後兩段 STR／STA；UPF 規則清除 |
| T44 | W3b 端到端：free-ran-ue 的故障注入讓 gNB 拒絕語音 QFI（smf-n1n2 W5c） | E | SMF 送 ruleReports、PCF 送 FAILED_RESOURCES_ALLOCATION、Adapter 送 ASR、通話結束 |
| T45 | 設定：`w3b.enable` false 時的 terminate；`tombstoneTTL` ≤ `strWait` | U | 前者依 REQ-CB-03（只記錄、不送 ASR）；後者拒絕啟動 |
| T46 | W3d：分類（只改頻寬、只改 codec、改 port、改 Flow-Status、加減 media component） | U | 前兩者歸「只改頻寬或 codec」，其餘歸「其他」 |
| T47 | W3d：只改頻寬 → PATCH（PCF stub 與真 PCF） | U、I | PATCH body 只含改變的元件且帶 `evSubsc`；真 PCF 上同一條 PCC rule 的 MBR 改變、沒有新規則；AAA 成功 |
| T48 | W3d：改 port 兩次（真 PCF） | I | 每次都是 Delete 再 Create；PCF 與 UPF 上沒有舊規則殘留；`resourceUri` 換成新的 |
| T49 | W3d：PATCH 失敗；Delete 失敗；Delete 成功但 Create 失敗；Create 逾時 | U | 依 REQ-UPD-05：`resourceUncertain`＋告警／原 session 不變／NO_RESOURCE／CREATE_UNKNOWN；AAA 都不回成功 |
| T50 | W3d：更新的重送；更新進行中收到 STR、terminate | U | 重送只得到同一答案、沒有第二次 PATCH 或 Delete／Create；STR、terminate 等目前操作結束後才處理 |
| T51 | W3d 端到端：SIPp 在通話中送 re-INVITE（改 port）與 hold／resume | E | 抓包看到同一 Session-Id 的 AAR、Delete、Create；UPF 規則換成新的；SMF 依序刪除舊 QFI、新增新 QFI（smf-n1n2 W5b） |
| T52 | W3d 設定：`w3d.enable` false | U | AAR 更新依 REQ-AAR-13 拒絕 |
| T53 | W3c：辨識信令 session（MCN 0＋AF_SIGNALLING；Media-Type CONTROL） | U | 兩者都歸 SIGNALLING；一般 AUDIO 歸 MEDIA |
| T54 | W3c `off`、`local` 模式下的註冊時 AAR | U、I | `off` 回失敗（REQ-AAR-04）；`local` 回 AAA 成功、PCF 沒有收到任何請求；STR 回 STA 成功 |
| T55 | W3c `local`：同 UE 通話中被 terminate | U | 媒體 session 走 ASR；同 UE 的信令 session 也收到 ASR |
| T56 | W3c `n5` 未宣告前提 | U | 拒絕啟動 |
| T57 | W3c `n5`（PCF stub 模擬附錄 E 修好的行為）：Create 內容、Specific-Action 對應、`evsNotif` 轉 AAA、後續 AAR 的非一次性 Specific-Action、terminate 與 FAILED_RESOURCES_ALLOCATION | U | Create 只有 MCN 0 的 AF_SIGNALLING 子元件；事件依 REQ-REG-05；D13 未關閉時 AAA 不帶 IP-CAN-Type 等 AVP；後續的非一次性 Specific-Action 被忽略；terminate 走 ASR；FAILED_RESOURCES_ALLOCATION 送 RAR（4 或 2）且不送 ASR |
| T58 | W3c 端到端（`local`）：SIPp 註冊、打電話、掛斷 | E | 註冊時看到 `Rx_AAR_Register` 的 AAR 與 AAA 成功；PCF 上沒有多出的 PCC rule；語音規則照常建立與刪除 |
| T59 | W5d：AAR 訂閱 2／3 時 Create 的 `evSubsc` | U | `w5d.enable` true 時含 QOS_NOTIF；false 時不含 |
| T60 | W5d：QOS_NOTIF 帶 `qncReports`（NOT_GUARANTEED、GUARANTEED、有無 `flows`）與不帶 `qncReports` | U | 前者依 REQ-QOS-02 送 RAR(2)／RAR(3)，Flows 正確；後者只記錄 |
| T61 | BSF：查到、204、BSF 無回應 | U、I | 查到時用 `pcfIpEndPoints` 組位址並記在 session；204 回 AAA 失敗、不改用預設 PCF；之後同一 session 都用同一個 PCF |
| T62 | BSF 端到端（free5gc BSF） | I | PCF 建 SM policy 後，Adapter 以 UE IP 查到同一個 PCF |

## 2. 需求追溯

| 需求 | 測試 | 檢驗方式 |
|---|---|---|
| REQ-GEN-01 | T01、T18、T19 | 測試＋抓包 |
| REQ-GEN-02 | — | 程式審查（不 import SIP／SDP 套件；不設定 5QI） |
| REQ-GEN-03 | T03、T05、T08、T09 | 測試 |
| REQ-GEN-04 | T01、T10 | 測試 |
| REQ-PEER-01～04 | T19 | 測試 |
| REQ-PEER-05 | T20 | 測試 |
| REQ-PEER-06 | T21 | 測試 |
| REQ-AAR-01、02、05、06、07、09 | T02 | 測試 |
| REQ-AAR-03 | T02（無法綁定）、T23（推導規則） | 測試 |
| REQ-AAR-04、08 | T03、T54 | 測試 |
| REQ-AAR-10 | T23、T16 | 測試＋抓包 |
| REQ-AAR-11、12 | T04、T12 | 測試 |
| REQ-AAR-13 | T05、T52 | 測試 |
| REQ-AAR-14 | T09 | 測試 |
| REQ-STR-01、02 | T06、T11、T13 | 測試 |
| REQ-STR-03 | T22 | 測試 |
| REQ-STR-04 | T07 | 測試 |
| REQ-STR-05 | T12 | 測試 |
| REQ-STR-06 | T06、T11 | 測試 |
| REQ-N5-01 | — | 程式審查＋manifest |
| REQ-N5-02 | T01、T09、T15 | 測試 |
| REQ-N5-03、06 | T15 | 測試 |
| REQ-N5-04 | T06 | 抓包 |
| REQ-N5-05 | T05 | 抓包 |
| REQ-N5-07 | T09 | 測試 |
| REQ-N5-08 | T28 | 測試 |
| REQ-CB-01、03、04 | T17、T45 | 測試 |
| REQ-CB-02 | T17 | 測試＋程式審查 |
| REQ-CB-05 | T24 | 測試 |
| REQ-ST-01、02 | T04、T12（race detector） | 測試 |
| REQ-ST-03、04 | T14 | 測試 |
| REQ-ST-05 | — | 程式審查 |
| REQ-CFG-01 | T24 | 測試 |
| REQ-CFG-02 | T11 | 測試 |
| REQ-SEC-01、02 | T25 | 測試 |
| REQ-OBS-01～03 | T26 | 測試 |
| REQ-OPS-01 | T27 | 測試 |
| REQ-OPS-02 | T29 | 測試 |
| REQ-KAM-01、02、04、08 | T30 | 測試 |
| REQ-KAM-03 | T30、T31 | 測試＋抓包 |
| REQ-KAM-05、07 | T32 | 抓包 |
| REQ-KAM-06 | T33 | 測試 |
| REQ-KAM-09 | T34 | 程式審查（cfg diff） |
| REQ-EVT-01、02 | T39 | 測試 |
| REQ-EVT-03、04 | T42 | 測試 |
| REQ-ASR-01～03 | T35、T38、T43 | 測試＋抓包 |
| REQ-ASR-04、05 | T36 | 測試 |
| REQ-ASR-06 | T37 | 測試 |
| REQ-RAR-01～03 | T40、T44 | 測試＋抓包 |
| REQ-RAR-04、05 | T41 | 測試 |
| REQ-CFG-03 | T45 | 測試 |
| REQ-UPD-01 | T46 | 測試 |
| REQ-UPD-02、03 | T47 | 測試 |
| REQ-UPD-04 | T48、T51 | 測試＋抓包 |
| REQ-UPD-05 | T49 | 測試 |
| REQ-UPD-06、07 | T50 | 測試 |
| REQ-KAM-10 | T51 | 抓包 |
| REQ-KAM-11 | T58 | 抓包 |
| REQ-REG-01 | T53 | 測試 |
| REQ-REG-02、03 | T54 | 測試 |
| REQ-REG-04～09 | T56、T57 | 測試 |
| REQ-REG-10 | T55 | 測試 |
| REQ-QOS-01 | T59 | 測試 |
| REQ-QOS-02、03 | T60 | 測試 |
| REQ-BSF-01～03 | T61 | 測試 |
| REQ-BSF-04 | T61、T62 | 測試 |

新增或修改需求時，必須同時更新這張表；沒有測試也沒有審查方式的需求不能進入 G2。

## 3. 分層判定

| 層級 | PASS 需要的證據 | 本階段 |
|---|---|---|
| L1 基本通話 | SIP 流程，以及能解析的雙向 RTP，對應到 N3 GTP-U 內層 flow | 必須 |
| L2 policy 生命週期 | Rx／N5 建立、釋放與 session 關聯一致（T01、T06、T18） | 必須 |
| L3 UPF 規則 | 通話前、中、後的專屬規則差異，含對應的 QER | 必須 |
| L2b 5GC 回報（W3b） | PDU session 釋放與資源失效時，ASR／RAR、BYE、STR 在抓包中可對應（T35、T40、T43、T44） | 必須（W3b） |
| L2c 通話中修改（W3d） | re-INVITE 前後的 AAR、N5 操作、UPF 規則可對應，沒有殘留規則（T48、T51） | 必須（W3d） |
| L2d IMS 註冊時（W3c） | 註冊時的 AAR／AAA 與依模式的 N5 行為可對應；語音規則不受影響（T57、T58） | 必須（W3c，`local` 模式） |
| L4 UE／RAN QoS | N1／N2 修改與成功回應、QFI 與 flow 的關聯 | W5 獨立工作，見 [../smf-n1n2/test-plan.md](../smf-n1n2/test-plan.md) L1–L3；未驗證要標示 |
| L5 傳輸品質 | 明確負載、瓶頸與路徑下的延遲、丟包、頻寬 | 後續工作 |

以 `03-call-test.sh` 為起點，加上 Rx／N5 與資源前後對照。用 tshark 等工具解析 SIP／RTP／Diameter，不用 log 字串或封包長度猜測判定。缺工具時輸出 SKIP 或 BLOCKED；L3 未驗證時，本階段整體不能算 PASS。

## 4. 要保存的證據

每次驗收執行保存：版本 manifest、測試命令與退出碼、帶時間的 log、pcap、PCF 資源證據、UPF 規則快照、逐案結果。PCF 沒有列舉 app session 的管理 API，資源證據用可重現的測試探針或 UPF 規則快照取得，不假設不存在的 API。

測試 fixture 可以用抓包資料，但必須移除真實身分與敏感資料。

## 5. 版本 manifest（G0 填寫）

| 項目 | 必填 | 目前 |
|---|---|---|
| 本 repo 與 `kamailio-free5gc` submodule | URL、commit | 待填 |
| free5gc 與各 NF（PCF、SMF、AMF、UPF、NRF） | release、commit、gtp5g 版本 | 部署 4.2.3／查證 v4.3.0，待 W7 統一 |
| Kamailio | 版本、映像 digest、`ims_qos`／`cdp` 設定 | 6.1.4，digest 待填 |
| free-ran-ue、SIPp | 版本、patch、情境檔 commit | 待填 |
| `free5gc/openapi` | module 版本 | 待填 |
| Go、OS、kernel、Docker、compose | 版本 | 待填 |
| 3GPP | 每份 TS 的版本與章節 | 見 [interface-spec.md](interface-spec.md) §2 |

只寫 main／master 不算填寫完成。

## 6. 完成定義

G0–G4 的證據齊全；必須的測試沒有未說明的 FAIL 或 SKIP；資源釋放與隔離可以重現。達成後只能稱為「第一階段 Rx／N5 整合完成」（見 [design.md](design.md) §11）。
