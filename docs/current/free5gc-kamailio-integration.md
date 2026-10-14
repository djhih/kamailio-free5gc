# free5gc × Kamailio 對接說明

> 對象：`kamailio-free5gc/`（free5gc 4.2.3、Kamailio 6.1.4、PyHSS 2.0.0、free-ran-ue 2.5.0）
> 內容依專案設定檔與程式碼整理；「缺口」一節另對照 free5gc v4.3.0 原始碼（2026-10-06）

## 總覽：五個對接點

5GC 與 IMS 之間沒有任何 SIP 介面。兩邊的接觸只有下面五處：

| # | 對接點 | 5GC 側 | IMS 側 | 主要設定 |
|---|---|---|---|---|
| ① | 使用者面（N6） | UPF | P-CSCF | `docker-compose.yaml`、`config/upf-n6.sh` |
| ② | `ims` DNN 與預設 QoS | UDR 訂閱、SMF | — | `scripts/subscriber-template.json`、`config/smfcfg.yaml` |
| ③ | P-CSCF discovery | SMF（PCO） | P-CSCF 位址 | `config/smfcfg.yaml`、`ran/pcscf-discovery.patch` |
| ④ | 用戶身分與金鑰 | UDR | PyHSS | `scripts/lib-keys.sh`、`02-`／`04-add-*-subscribers.sh` |
| ⑤ | Policy／QoS | PCF → SMF → UPF | P-CSCF + AF shim | `pcscf/kamailio.cfg`、`af/main.go` |

## ① 使用者面：UPF 是唯一的橋

- 兩個 Docker 網段：`corenet` 10.100.200.0/24（5GC、gNB）、`dnnet` 10.100.100.0/24（CSCF、PyHSS、AF）
- UPF 同時接兩邊：N3／N4 在 corenet，N6 在 dnnet。UE 要到 IMS 只能經 UPF
- SIP 和 RTP 對 5GC 來說只是 user plane 的 IP 封包：UE → gNB →（GTP-U）→ UPF → N6 → P-CSCF
- **往 dnnet 不做 NAT**（`upf-n6.sh`）：Kamailio 看到的是 UE 的真實 IP。否則兩支 UE 會變成同一個位址，SIP 需要 NAT 輔助，PCF 也無法用 UE IP 綁定 session
- RTP 在 UPF 內直接轉給另一支 UE，不經過 CSCF

## ② `ims` DNN 與預設 QoS

| 項目 | 值 |
|---|---|
| UE 使用的 DNN | `ims`（free-ran-ue 一個 UE 只能有一個 PDU session） |
| 位址池 | 10.62.0.0/16 |
| 預設 QoS | 5QI 5（IMS 信令）、ARP 1、AMBR 10 Mbps |
| 對照：`internet` | 5QI 9、ARP 8 |

SIP 信令一開始就走 5QI 5 的預設 QoS flow；語音的 5QI 1 由 ⑤ 在通話時加上。

## ③ P-CSCF discovery

1. UE 在 PDU Session Establishment Request 的 ePCO 裡要求 P-CSCF IPv4 位址（free-ran-ue 原本不送，靠 `pcscf-discovery.patch` 補上）
2. SMF 讀 `smfcfg.yaml` 中 `ims` DNN 的 `pcscf: 10.100.100.10`
3. 在 Accept 的 PCO（container 000Ch）回傳
4. UE 拿這個位址當 SIP outbound proxy

`03-call-test.sh` 會檢查 UE 設定檔裡沒有寫死 P-CSCF，確保位址真的是從網路學來的。

## ④ 用戶身分與金鑰

兩邊各有一份用戶資料，彼此沒有介面，一致性靠開戶腳本保證：

| | 5GC（UDR） | IMS（PyHSS） |
|---|---|---|
| 身分 | SUPI `imsi-208930000000001` | IMPI `208930000000001@ims.mnc093.mcc208.3gppnetwork.org`、IMPU `sip:…` |
| 開戶 | `02-add-subscribers.sh` | `04-add-ims-subscribers.sh` |
| 金鑰 | OPc | OPc |
| 認證 | 5G-AKA | IMS AKA |

- 所有金鑰都由同一個 OP 推導（`lib-keys.sh`）：UDR、free-ran-ue、PyHSS 用 OPc，SIPp 用 OP
- 兩種認證的 SQN 各自計數，起始值都設為 0x23

## ⑤ Policy／QoS：IMS 把媒體需求交給 5GC

```
P-CSCF ──HTTP POST /call──▶ AF shim ──h2c POST /app-sessions──▶ PCF ──N7──▶ SMF ──PFCP──▶ UPF
(200 OK 時，帶兩份 SDP)       (向 NRF 註冊為 AF)       (PCC rule、5QI 1)              (PDR + QER)
BYE ──/call/delete──▶ AF shim ──DELETE app session──▶ PCF ──▶ SMF ──▶ UPF 移除規則
```

AF shim 送給 PCF 的 `AppSessionContext`：

| 類別 | 欄位 |
|---|---|
| session binding | `supi`、`ueIpv4`、`dnn` |
| 媒體 | `medType: AUDIO`（→ 5QI 1）、`fDescs`（`permit out／in 17 from <peer> to <ue>`）、`marBwUl／Dl`、`codecs` |
| 其他 | `afAppId: IMS-voice`、`notifUri: http://af:8090/notify`、`suppFeat: "0"` |

一通電話兩支 UE 各有自己的 PDU session，所以 P-CSCF 對主叫、被叫各預留一次。

### 對接時踩到的細節

| 細節 | 原因 |
|---|---|
| 一定要帶 `supi` | 沒帶時 PCF 會掃所有 UE 找 IP，而那個迴圈不會在找到時停下，多 UE 時可能綁錯 |
| 不能用 `permit inout` | PCF 先比對 `permit in` 前綴，inout 會被當成只有上行 |
| 用 h2c 連 PCF | free5gc SBI 只講 HTTP/2 不加密；Kamailio 的 `http_client` 做不到，所以需要 shim |
| NRF 的 OAuth 關閉 | 開啟時 PCF → SMF 的 token scope 對不上，policy 更新送不到 SMF |
| AF 的 NF instance ID 固定 | 要和 free5gc 產生的 AF 憑證對上 |

## 驗證方式

| 測試 | 驗證什麼 |
|---|---|
| `03-call-test.sh` | 註冊、通話走完三個 CSCF；四種 Cx 指令都有用到；通話中 UPF 上有語音的 PDR／QER；SIP 和 RTP 確實在 GTP-U 裡 |
| `05-n5-qos-test.sh` | 不經 SIP，直接打 AF，確認 PCF → SMF → UPF 這條鏈 |

## 還沒打通的地方

| 缺口 | 影響 |
|---|---|
| SMF 收到 policy 更新後只改 UPF，沒經 AMF 送 N1N2 | gNB 與 UE 不知道語音的 QoS flow |
| PCF 的通知在 shim 只寫 log | PDU session 斷了，通話還掛著 |
| 註冊時沒有交換信令 flow、事件訂閱 | 與 TS 29.513 附錄 B.5–B.8 不符 |
| AMF `imsVoPS: 0` | 網路告訴 UE 不支援 IMS 語音；SIPp 不理會所以能通 |
| PCO 只支援 IPv4 P-CSCF | 無 IPv6 |
| QER 不真正限速 | free5gc 的已知限制，測試只驗證規則存在 |

改善方向見 [../plan/vonr-ims-nf-plan.md](../plan/vonr-ims-nf-plan.md)：以標準 Rx 的 Adapter 取代 shim，並補上 SMF 的 N1N2。
