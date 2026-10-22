# 現況：free5gc × Kamailio 怎麼對接

> 對象：`kamailio-free5gc/`（free5gc 映像 `v4.2.3`、Kamailio 6.1.x、PyHSS、free-ran-ue v2.5.0）
> 更新：2026-10-22。內容依專案設定檔、腳本與 free5gc 原始碼整理。這份只描述**現在的部署**；要改成什麼樣子見 [vonr-ims-nf-plan.md](vonr-ims-nf-plan.md)

## 版本

| 元件 | 部署 | 備註 |
|---|---|---|
| free5gc NF | `free5gc/*:v4.2.3` 映像（只有 tag，沒有 digest） | v4.2.3 釘的 NF 版本：AMF、SMF、PCF、UDM、NRF、AUSF v1.4.5，UDR v1.4.4，UPF v1.2.12 |
| Kamailio | `debian:trixie-slim`＋apt `kamailio61` | **沒有鎖小版本**；lab README 寫 6.1.4，實際取決於 build 時間（[w2-w7-checklists.md](w2-w7-checklists.md) W7-A） |
| PyHSS | `latest@sha256:da53ca70…` | README 寫 2.0.0，與 digest 是否一致未查證 |
| free-ran-ue | v2.5.0＋`ran/pcscf-discovery.patch` | — |
| gtp5g | 0.10.2 | — |

本專案讀原始碼查證時用的是本機較新的版本（主 repo v4.3.0），與部署的差距見 [w2-w7-checklists.md](w2-w7-checklists.md)。

## 總覽：五個對接點

5GC 與 IMS 之間沒有任何 SIP 介面。兩邊的接觸只有下面五處：①③⑤ 是網路介面（N6、PCO、N5），②④ 是設定與開戶時的對齊。

| # | 對接點 | 5GC 側 | IMS 側 | 主要設定 |
|---|---|---|---|---|
| ① | 使用者面（N6） | UPF | P-CSCF | `docker-compose.yaml`、`config/upf-n6.sh` |
| ② | `ims` DNN 與預設 QoS | UDR 訂閱、SMF | — | `scripts/subscriber-template.json`、`config/smfcfg.yaml` |
| ③ | P-CSCF discovery | SMF（PCO） | P-CSCF 位址 | `config/smfcfg.yaml`、`ran/pcscf-discovery.patch` |
| ④ | 用戶身分與金鑰 | UDR | PyHSS | `scripts/lib-keys.sh`、`02-`／`04-add-*-subscribers.sh` |
| ⑤ | Policy／QoS | PCF → SMF → UPF | P-CSCF＋AF shim | `pcscf/kamailio.cfg`、`af/main.go` |

## ① 使用者面：UPF 是唯一的橋

- 兩個 Docker 網段：`corenet` 10.100.200.0/24（5GC、gNB；host bridge `br-poc-core`）、`dnnet` 10.100.100.0/24（CSCF、PyHSS、AF；host bridge `br-poc-dn`）
- UPF 同時接兩邊：N3／N4 在 corenet，N6 在 dnnet。UE 要到 IMS 只能經 UPF
- SIP 和 RTP 對 5GC 來說只是 user plane 的 IP 封包：UE → gNB →（GTP-U）→ UPF → N6 → P-CSCF
- **往 dnnet 不做 NAT**（`upf-n6.sh`）：Kamailio 看到的是 UE 的真實 IP（符合 TS 23.228 附錄 Y.5）。否則兩支 UE 會變成同一個位址，PCF 也無法用 UE IP 綁定 session
- RTP 在 UPF 內直接轉給另一支 UE，不經過 CSCF，也不經過 `br-poc-dn`
- free-ran-ue 的 GTP-U 不看 QFI：不管 RAN 知不知道語音 QoS flow，RTP 都會通

## ② `ims` DNN 與預設 QoS

| 項目 | 值 |
|---|---|
| UE 使用的 DNN | `ims`（free-ran-ue 一個 UE 只能有一個 PDU session） |
| 位址池 | 10.62.0.0/16 |
| 預設 QoS | 5QI 5（IMS 信令）、ARP 1、AMBR 10 Mbps |
| 對照：`internet` | 5QI 9、ARP 8 |

SIP 信令一開始就走 5QI 5 的預設 QoS flow（靜態設定，不是註冊時由 P-CSCF 動態要求）；語音的 5QI 1 由 ⑤ 在通話時加上。

## ③ P-CSCF discovery

1. UE 在 PDU Session Establishment Request 的 ePCO 裡要求 P-CSCF IPv4 位址（free-ran-ue 原本不送，靠 `pcscf-discovery.patch` 補上）
2. SMF 讀 `smfcfg.yaml` 中 `ims` DNN 的 `pcscf: 10.100.100.10`
3. 在 Accept 的 PCO（container 000Ch）回傳
4. UE 拿這個位址當 SIP outbound proxy

只支援 IPv4。

## ④ 用戶身分與金鑰

兩邊各有一份用戶資料，彼此沒有介面，一致性靠開戶腳本保證：

| | 5GC（UDR） | IMS（PyHSS） |
|---|---|---|
| 身分 | SUPI `imsi-208930000000001` | IMPI `208930000000001@ims.mnc093.mcc208.3gppnetwork.org`、IMPU `sip:…` |
| 開戶 | `02-add-subscribers.sh` | `04-add-ims-subscribers.sh` |
| 金鑰 | OPc | OPc |
| 認證 | 5G-AKA | IMS AKA |
| SQN | UDR 一個 | PyHSS 一個（**各自計數**，起始值都是 0x23） |

- 所有金鑰都由同一個 OP 推導（`lib-keys.sh`）：UDR、free-ran-ue、PyHSS 用 OPc，SIPp 用 OP
- 沒有 ISIM，IMPI 由 IMSI 推導（TS 23.003 §13.3；submodule 文件寫成 §13.4B，是引用錯誤）
- PyHSS 的 Cx：I-CSCF 用 UAR、LIR；S-CSCF 用 MAR、SAR。依 `pyhss.env` 的註解，第一次註冊時 UAA 會回 Server-Name（TS 29.228 §6.1.1.1 不允許；待抓包確認）

## ⑤ Policy／QoS：IMS 把媒體需求交給 5GC

```
P-CSCF ──HTTP POST /call──▶ AF shim ──h2c POST /app-sessions──▶ PCF ──N7──▶ SMF ──PFCP──▶ UPF
(200 OK 時，帶兩份 SDP)       (向 NRF 註冊為 AF)       (PCC rule、5QI 1)              (PDR + QER)
BYE ──/call/delete──▶ AF shim ──POST {appSessionUri}/delete──▶ PCF ──▶ SMF ──▶ UPF 移除規則
```

AF shim 送給 PCF 的 `AppSessionContext`：

| 類別 | 欄位 |
|---|---|
| session binding | `supi`、`ueIpv4`、`dnn` |
| 媒體 | `medType: AUDIO`（→ 5QI 1）、`fDescs`（`permit out／in 17 from <peer> to <ue>`）、`marBwUl／Dl`、`codecs` |
| 其他 | `afAppId: IMS-voice`、`notifUri: http://af:8090/notify`、`suppFeat: "0"` |

一通電話兩支 UE 各有自己的 PDU session，所以 P-CSCF 對主叫、被叫各預留一次。預留失敗時通話照常繼續（`pcscf/kamailio.cfg` 的 `AF_RESERVE`）。

### 對接時踩到的細節

| 細節 | 原因 |
|---|---|
| 一定要帶 `supi` | 沒帶時 PCF 的 session binding 會掃所有 UE 找 IP，迴圈不會在找到時停下，多 UE 時可能綁錯 |
| 不能用 `permit inout` | PCF 先比對 `permit in` 前綴，inout 會被當成只有上行 |
| 用 h2c 連 PCF | free5gc SBI 只講 HTTP/2 不加密；Kamailio 的 `http_client` 做不到，所以需要 shim |
| NRF 的 OAuth 關閉 | 開啟時 PCF → SMF 的 token scope 對不上，policy 更新送不到 SMF |
| AF 的 NF instance ID 固定 | 要和 free5gc 產生的 AF 憑證對上 |

## 測試實際驗證了什麼

讀 `scripts/03-call-test.sh`、`05-n5-qos-test.sh` 得到的實際判定（不是腳本註解的說法）：

| 測試 | 影響 PASS／FAIL 的 | 只印出來、不影響判定的 |
|---|---|---|
| `03-call-test.sh` | sipp UAC 退出碼；GTP-U 封包數 > 0；pcscf log 裡的 BYE 計數；icscf log 裡的 LIR 計數；UPF 上找不到語音 PDR 時判 FAIL | 註冊結果（sipp 經 `tail -3`，退出碼沒檢查）；UAR／MAR／SAR 計數；三個 CSCF 的路徑；SIP 在 GTP-U 內的計數；RTP 的猜測。gtp5g 讀取工具不存在時 QoS 檢查是 SKIP，**仍可能 PASS** |
| `05-n5-qos-test.sh` | AF shim 回 200；每個方向剛好一條語音 PDR 且 QER 存在、GBR 不為 0；刪除後 PDR 數回到原值 | — |

判定依賴 Kamailio 的 `xlog` 字串，換元件或改 cfg 就會失效。改成抓包判定是 W1（[../e2e-harness/](../e2e-harness/README.md)）。

## 缺口

每一項的處理都在 [vonr-ims-nf-plan.md](vonr-ims-nf-plan.md)，條文對照在 [vonr-3gpp-conformance.md](vonr-3gpp-conformance.md)。

| 缺口 | 影響 | 證據 | 由誰處理 |
|---|---|---|---|
| IMS 到 5GC 用自訂 HTTP，不是 Rx／N5 | 證明不了標準對接；換元件就要重寫 | `pcscf/kamailio.cfg`、`af/main.go` | W3a、W4 |
| PCF 的 terminate 送到 `/notify/terminate`，shim 只接 `/notify`（404）；其他通知只寫 log | PDU session 斷了，通話還掛著（TS 23.228 Y.2.4） | `af/main.go` | W3b |
| SMF 收到 policy 更新只改 UPF，不送 N1N2 | gNB、UE 不知道語音 QoS flow | `smf` `HandleSMPolicyUpdateNotify` | W5a |
| 通話結束後 SMF 很可能不釋放語音 QoS flow 與 QFI（PCF 的刪除通知不帶 QosDecs） | QFI 洩漏；之後也無法通知 RAN／UE 刪除 | `pcf` `RemovePccRule`、`smf` `ApplyPccRules`（原始碼推論，待實測） | W5a（smf-n1n2 ADR-0002） |
| SMF 不處理 RAN 的 Notify，也不回報失敗的規則 | RAN 拒絕或釋放語音 QFI 時，IMS 不知道 | `smf` `pdu_session.go` | W5c |
| free-ran-ue 不處理 PDU Session Resource Modify 與 Modification Command | 就算 SMF 送了也沒有回應 | `gnb/ngapDispatcher.go`、`ue/ue.go` | W6 |
| AMF `imsVoPS: 0` | 網路告訴 UE 不支援 IMS 語音；SIPp 不理會所以能通 | `config/amfcfg.yaml` | W2（W5 完成後） |
| AMF 送給 UDM 的 `ImsVoPs` 寫死成不支援 | 之後做 T-ADS 時會錯 | `amf` `udm_service.go` | 計畫外（[w2-w7-checklists.md](w2-w7-checklists.md) W2-4） |
| IMS 與 5G 各有一個 SQN；兩份用戶資料靠腳本對齊 | 不符 TS 33.203 §8.2；資料可能不一致 | `lib-keys.sh`、PyHSS | W8a |
| 測試判定依賴 log 字串，QoS 檢查 SKIP 也會 PASS | 結果不可靠 | 上一節 | W1 |
| 註冊時沒有向 PCF 訂閱信令路徑、access type、PLMN | TS 29.513 B.5～B.8 是 optional，屬於「沒有做」不是「不符」 | — | W3c（預設 `local` 模式） |
| PCF 在 Rx 沒帶 Minimum Requested Bandwidth 時不給 GBR | 5QI 1 的 GBR flow 可能缺 GFBR（TS 29.513 Table 7.3.2-1 要求由營運商設定） | `pcf` `updateQosInMedSubComp` | 計畫外（smf-n1n2 D04） |
| PCO 只支援 IPv4 P-CSCF | 沒有 IPv6 | `smf` | 不在範圍 |
| QER 不真正限速 | 只能驗證規則存在 | free5gc 的已知限制 | 不在範圍 |
| Kamailio 沒有鎖版本；free5gc 映像沒有 digest | 不同時間 build 的行為可能不同 | `pcscf/Dockerfile` 等 | W7 |
