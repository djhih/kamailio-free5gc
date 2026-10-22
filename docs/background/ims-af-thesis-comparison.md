# 碩論 IMS-AF 與本專案架構比較

> 狀態：分析完成；「app session 模型不採用碩論做法」是**建議，尚待決定**（2026-10-15）
> 對象：實驗室 2024 年碩論〈VoNR QoE Measurement and Prediction in 5G Mobile Networks〉第 3.1 節的 IMS-AF，對照本專案的現況（[../overview/free5gc-kamailio-integration.md](../overview/free5gc-kamailio-integration.md)）與計畫（[../rx-n5/design.md](../rx-n5/design.md)、[../overview/vonr-ims-nf-plan.md](../overview/vonr-ims-nf-plan.md)）
> 碩論資料放在本機的 `lab-ref/`，**不進 git**（見 `.gitignore`），原始來源是實驗室 NAS

## 先看這裡

**資料來源有三種，本文逐項標示：**

| 標示 | 意思 |
|---|---|
| 〔碩論〕 | 碩論內文、截圖或口試簡報裡寫的 |
| 〔查證〕 | 讀 free5gc PCF 原始碼確認的（`free5gc/NFs/pcf`，v1.4.5 與 2024-08 的 v1.2.5 行為相同） |
| 〔推論〕 | 根據上面兩者推出來的，沒有實測 |

**IMS-AF 的原始碼不在交接包裡**（`source_code.zip` 只有 QoE 模型的 notebook），本機也找不到。所以碩論的說法都無法對照程式碼驗證。

**三句話結論：**
1. 碩論的架構（Kamailio `ims_qos` 送 Rx → Go 寫的轉換器 → N5 打 PCF）跟我們的計畫相同，跟現在的 AF shim 不同。
2. 兩者主要差在 **app session 怎麼對應**。碩論是每支 UE 一個 app session，通話開始和結束都用 Update；我們是每個 Rx session 一個，通話開始用 POST、結束用 Delete。**在上游 free5gc PCF 上，碩論的釋放方式刪不掉語音規則**〔查證〕，所以建議不採用碩論的模型。
3. 碩論沒處理 5GC 往 IMS 的方向（terminate、事件），也沒有證據顯示 QoS flow 送到了 gNB／UE；這兩件事在我們的計畫裡是 W3b 跟 W5。

## 三種架構並列

```
碩論     Kamailio P-CSCF ──Rx(Diameter :4868)──▶ IMS-AF (Go) ──N5──▶ PCF ─▶ SMF ─▶ UPF
現況     Kamailio P-CSCF ──自訂 HTTP /call────▶ AF shim (Go) ──N5(h2c)──▶ PCF ─▶ SMF ─▶ UPF
計畫     Kamailio P-CSCF ──Rx(Diameter :3868)──▶ Rx/N5 Adapter ──N5──▶ PCF ─▶ SMF ─▶ UPF ─(W5 N1N2)─▶ gNB/UE
                                                        ◀── terminate／事件 (ASR／RAR, W3b) ──
```

## 1. IMS ↔ 5GC 的 policy 介面

| 項目 | 碩論 IMS-AF | 現況 AF shim | 計畫 Adapter |
|---|---|---|---|
| P-CSCF 送什麼 | 標準 Rx：`ims_qos` 送 AAR／STR〔碩論，有截圖〕 | 自訂 HTTP：`http_client` 在 200 OK 時 POST `/call`，內容是兩份 SDP | 標準 Rx（W4） |
| Kamailio 設定 | 接近 Kamailio IMS 範例設定（realm `ims.mnc001.mcc001…`，Destination-Realm `ims.smilecoms.com`）〔碩論截圖〕 | 自寫 `AF_*` 路由 | 載入 `cdp`／`ims_qos`，刪掉 `AF_*` |
| 轉換器 | Go + `fiorix/go-diameter/v4`〔碩論〕 | Go，只做 HTTP 轉 h2c | Go + `go-diameter`，free5gc NF 骨架，`free5gc/openapi` PolAuth client |
| Diameter port | 4868〔碩論〕 | — | 3868 |
| NRF 註冊／token | 碩論沒寫 | 註冊為 AF，NF instance ID 固定 | 註冊為 AF（設計 §9 第 5 步） |
| PCF 位址 | 碩論沒寫 | 寫死 | W3a 寫死，W3c 改由 BSF 查 |

## 2. App session 的對應方式（最大的差異）

### 2.1 兩種模型逐步比較

以一支 UE 為例（主叫、被叫各有自己的 PDU session，各走一次）。

**碩論模型（每支 UE 一個 app session）**〔碩論〕

| 步驟 | Kamailio → 轉換器 | 轉換器 → PCF | 轉換器裡的狀態 |
|---|---|---|---|
| ① IMS 註冊 | AAR（Session-Id `…;7`，Media-Type=CONTROL） | `POST /app-sessions`，建立 app session A | Subscription-Id → A |
| ② 通話建立 | AAR（**另一個** Session-Id `…;12`，AUDIO） | 用 Subscription-Id 找到 A → `PATCH A`，加入語音元件 | `…;12` → (A, UpdateData) |
| ③ 通話釋放 | STR（`…;12`） | 把子元件的 FStatus 改成 REMOVED → `PATCH A` | 刪掉 `…;12`，A 保留 |
| ④ 解除註冊 | STR（`…;7`） | 碩論沒寫 | — |

**我們的設計（每個 Rx session 一個 app session）**

| 步驟 | Kamailio → 轉換器 | 轉換器 → PCF | 轉換器裡的狀態 |
|---|---|---|---|
| ① IMS 註冊 | （W3c 才做）AAR `…;7` | `POST`，建立 app session S | `…;7` → S |
| ② 通話建立 | AAR `…;12` | `POST`，建立 app session M | `…;12` → M |
| ③ 通話釋放 | STR `…;12` | `POST M/delete` | 刪掉 `…;12` |
| ④ 解除註冊 | STR `…;7` | `POST S/delete` | 刪掉 `…;7` |

現況的 AF shim 也是「每通電話一個 app session、結束時 Delete」，`03-call-test.sh` 驗證過這條路可行。

### 2.2 free5gc PCF 的實際行為〔查證〕

檔案：`free5gc/NFs/pcf/internal/sbi/processor/policyauthorization.go`、`internal/util/pcc_rule.go`。

| # | 行為 | 對碩論模型的影響 |
|---|---|---|
| a | PATCH 時，PCF 先用 `removeMediaComp()` 刪掉該元件的舊規則，但**只到當初 POST 的 `MedComponents` 裡找**；PATCH 加入的元件不會寫回那裡 | 步驟 ② 加的語音元件，步驟 ③ 找不到，所以刪不掉。PCF 接著用 flow 找到既有的語音 PCC rule，只重算頻寬，**5QI 1 規則留著** |
| b | REMOVED 的判斷看的是**元件**層級的 FStatus；碩論改的是**子元件**層級 | 這個判斷也沒有作用 |
| c | `MediaTypeTo5qiMap` 把 CONTROL 對應到 **5QI 9**（2022 年起沒變） | 碩論圖 3.10「註冊後建立 5QI 5 flow」不會發生 |
| d | PATCH 沒帶 `evSubsc` 時，PCF 會**清掉**既有的事件訂閱 | 步驟 ② 的 PATCH 會把註冊時的訂閱清掉 |
| e | Delete 會刪掉 `RelatedPccRuleIds` 裡的所有規則（包含 PATCH 加的），並通知 SMF | 我們的模型靠的是這條，行為正確 |

由 a、b、c 可知：**碩論描述的 QoS 結果跟上游 free5gc 對不上**。可能碩論也改了 PCF，也可能圖 3.10／3.15／3.19 是示意圖、不是實測〔推論〕。要有原始碼才能確定。

a、d 也會影響我們自己的 re-INVITE（PATCH）流程，見設計文件 §6.2。

### 2.3 其他差異

| 情境 | 碩論模型 | 我們的設計 |
|---|---|---|
| 同一支 UE 通話中又接第二通 | 兩通都寫進同一個 app session 的元件 1，第二通的記錄會蓋掉第一通的，第一通的規則變成孤兒〔推論，依查證 a〕 | 各自獨立，互不影響 |
| PDU session 斷線（PCF 送 terminate） | 只通知到每支 UE 的那一個 app session，分不出要結束哪一通 | 每通電話各自收到 → 對該通送 ASR |
| 還沒註冊，或註冊時的 AAR 失敗 | 無法建立通話 | 不影響通話 |
| Phase 1 要做的範圍 | 註冊 AAR + 通話 PATCH + 釋放 PATCH，可能還要改 PCF | 通話的 POST + Delete |
| 是否符合 TS 29.513 附錄 B | 否：兩個 Rx session 併成一個 app session | 是：一個 Rx session 對一個 app session |

另外，碩論第 3.1.1.3 節的開頭寫「呼叫 `Npcf_PolicyAuthorization_Delete`」，實作描述卻是 `Update`，前後不一致〔碩論〕。

**建議：維持我們設計的模型。** 若要改採碩論模型，要先拿到 IMS-AF 原始碼，確認他們有沒有改 PCF。

## 3. AVP 對應

| 項目 | 碩論 IMS-AF | 計畫 Adapter |
|---|---|---|
| Framed-IP-Address → `ueIpv4` | 有（截圖標示） | 有 |
| Subscription-Id → `supi` | 截圖標示了對應，但 IMPU 怎麼轉成 SUPI 沒寫 | §4.2：IMPU 的 user part 是 15 位數字就轉成 `imsi-…`，可以設定 |
| AF-Application-Identifier → `afAppId` | 有（`"IMS Services"`） | 有，沒帶時用設定值 |
| Media-Component-Description → `medComponents` | 有 | 有，§5.2 逐欄對應 |
| Specific-Action → `evSubsc` | AAR 裡帶了 1、2、3、4、6、12，碩論沒說怎麼處理 | §5.3 對應表，其中 2、3、4 待確認 |
| Flow-Description 上行寫法 | 截圖裡 Media-Sub-Component 是收合的，看不到 | 待確認（設計 §10.2） |
| 錯誤對應 | 「依不同錯誤加上對應的錯誤訊息」，沒有列表 | §5.4 對應表 |
| 不認識的 AVP | 截圖看得到 ETSI Reservation-Priority，碩論沒提 | 設計 §10.1 待確認 |

## 4. 5GC → IMS 方向、往 RAN 的方向

| 項目 | 碩論 IMS-AF | 現況 | 計畫 |
|---|---|---|---|
| PCF terminate → ASR | 碩論沒寫 | shim 回 404，通話會一直掛著 | W3b |
| PCF 事件 → RAR | 碩論沒寫 | 只記 log | W3b |
| re-INVITE → PATCH | 碩論沒寫 | 沒有 | W3b（受 2.2 a、d 限制，見設計 §6.2） |
| SMF 經 N1N2 通知 gNB／UE | 圖 3.10／3.15／3.19 是示意圖，沒有 N2 抓包 | 沒做（free5gc 的限制） | W5 + W6 |

free5gc SMF 收到 policy 更新時不會送 N1N2（讀 v4.3.0 原始碼確認，部署版本待 W7），所以碩論當時的 flow 應該也只到 SMF／UPF〔推論〕。

## 5. 環境與其他對接點

| 項目 | 碩論 | 本專案現況 |
|---|---|---|
| UE／RAN | UERANSIM + Jitsi，用 netns + `netns-exec` 讓 SIP 走 `uesimtun0` | free-ran-ue + SIPp |
| P-CSCF discovery | 碩論沒寫（應該是在 Jitsi 裡手動設定） | PCO（`pcscf-discovery.patch`） |
| DNN 與預設 QoS | 預設 flow 是 5QI 9（截圖 UE IP 10.61.0.1）；碩論說 5QI 5 由註冊時的 AAR 建立，但見 2.2 c | 專用的 `ims` DNN，預設就是 5QI 5 |
| HSS | 碩論沒寫 | PyHSS，跟 UDR 用同一個 OP 推導金鑰 |
| AMF `imsVoPS` | 碩論沒提 | 目前是 0，W2 改成 1 |
| 部署 | 實體 PC 上的 VM；UPF 跟 Kamailio 在同一台 VM | Docker compose，corenet／dnnet 兩個網段，N6 不做 NAT |
| 驗證 | Wireshark 截圖 + 主觀 QoE 實驗 | `03-call-test.sh`、`05-n5-qos-test.sh`（W1 會改成看抓包） |

## 6. 可以參考、不要沿用

**可以參考：**
1. **Rx 這一段的可行性**：截圖證實 Kamailio `ims_qos` 送出的 AAR／STR 有到 IMS-AF〔碩論〕。PCF 那一段的結果有 2.2 的疑慮，**不能當成整條路已經做通的證據**。
2. **AVP 樣本**：圖 3.9、3.13、3.14、3.18 有完整的 AAR／STR AVP 列表，可以拿來寫 `rx/types.go` 與 mapper 測試案例（設計 §9 第 2、3 步）。
3. **Kamailio 會帶的東西**：Specific-Action 一次帶好幾個、會有 ETSI Reservation-Priority、Subscription-Id 長度 88（跟 SIP URI 一致，符合「`ims_qos` 預設送 IMPU」）。
4. **Port**：碩論用 4868，沿用其 Kamailio 設定時要注意。

**不要沿用：**
1. 每支 UE 一個 app session、用 Subscription-Id 當 key、釋放用 Update（見第 2 節）。
2. **不要把碩論的 QoE 結果當成「5QI 1 有效」的證據。** VoNR 拓撲中 Kamailio 跟 UPF 在同一台 VM，被 `tc` 限速的 N6 只通往 iperf server（圖 4.25）；VoIP 的 SIP server 則在限速的 N6 另一端（圖 4.26）。加上 free5gc 的 QER 不真正限速、flow 沒送到 gNB，VoNR 的 MOS 較高，比較可能是路徑不同造成的〔推論〕。

## 7. 待確認

| 問題 | 怎麼確認 |
|---|---|
| IMS-AF 原始碼在哪 | 問交接文件上的承接人或指導教授，或查實驗室 NAS／GitLab |
| 碩論有沒有改 PCF（2.2 a、c） | 要看原始碼，或問人 |
| 碩論用的 free5gc、Kamailio 版本 | 碩論沒寫；看原始碼的 `go.mod` 或問人 |
| 碩論怎麼從 IMPU 推出 SUPI、有沒有處理 Specific-Action | 要看原始碼 |
| HackMD 交接筆記有沒有補充 | 打開 `lab-ref/交接hackmd.txt` 的連結 |
