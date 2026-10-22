# HSS 併入 UDM：用一支手機走一遍

> 性質：說明（informative）。行為以 [interface-spec.md](interface-spec.md) 為準；這份文件和規格衝突時，以規格為準。

## 1. 一句話

原本由 PyHSS 回答 Kamailio「這個人是誰、該由哪台 S-CSCF 服務、給我認證向量」的工作，改由 free5gc 的 UDM 回答；答案用的資料和 5G 註冊用的是同一份。

## 2. 改之前與改之後

```
改之前   I-CSCF、S-CSCF ──Cx──▶ PyHSS（自己一份 K、OPc、SQN）
         AUSF ──────────Nudm──▶ UDM ──Nudr──▶ UDR（另一份 K、OPc、SQN）

改之後   I-CSCF、S-CSCF ──Cx──▶ UDM（HSS 子系統）──┐
         AUSF ──────────Nudm──▶ UDM ──────────────┴──▶ UDR（一份 K、OPc、SQN＋IMS 資料）
```

Kamailio 看不出差別：它連的還是 `hss.ims.mnc093.mcc208.3gppnetwork.org` 的 3868，講的還是 Cx。

## 3. 一支手機從開機到掛斷

主角：UE1，IMSI `208930000000001`。

- IMPI：`208930000000001@ims.mnc093.mcc208.3gppnetwork.org`
- IMPU：`sip:208930000000001@ims.mnc093.mcc208.3gppnetwork.org`

UDR 裡一開始的 SQN 是 `000000000020`。下表右邊兩欄是每一步之後 UDR 裡的值。

| # | 發生什麼 | Cx 訊息 | UDR 的 SQN | UE1 的註冊紀錄 |
|---|---|---|---|---|
| 1 | UE1 開機，做 5G-AKA | 無（Nudm_UEAU） | `…21`（取走 `…20`） | 沒有紀錄（＝NR0） |
| 2 | UE1 送 REGISTER 給 P-CSCF，轉到 I-CSCF | I-CSCF → UDM：UAR | 不變 | 不變 |
| 3 | UDM 查身分索引找到 SUPI；沒有任何已存 S-CSCF | UDM → I-CSCF：UAA，帶 Server-Capabilities（mandatory 0），Experimental-Result 2001 FIRST_REGISTRATION，**沒有 Server-Name** | 不變 | 不變 |
| 4 | I-CSCF 從自己的 `s_cscf` 表挑出 capability 0 的 S-CSCF，轉送 REGISTER | — | — | — |
| 5 | S-CSCF 要認證向量 | S-CSCF → UDM：MAR（Digest-AKAv1-MD5，Server-Name＝S-CSCF） | `…22`（取走 `…21`） | NR1：已存 S-CSCF、authPending |
| 6 | UDM 用取到的 SQN 跑 Milenage | UDM → S-CSCF：MAA（RAND‖AUTN、XRES、CK、IK） | 不變 | 不變 |
| 7 | S-CSCF 回 401，UE1 算出 response 再送 REGISTER；I-CSCF 再問一次 | UAR → UAA：已存 S-CSCF＋Experimental-Result 2002 | 不變 | 不變 |
| 8 | S-CSCF 驗證成功，通知 HSS | SAR REGISTRATION → SAA：User-Data（XML profile），Result-Code 2001 | 不變 | REG，authPending 清掉 |
| 9 | UE2 打給 UE1，I-CSCF 要找 UE1 的 S-CSCF | LIR → LIA：已存 S-CSCF，Result-Code 2001 | 不變 | 不變 |
| 10 | UE1 掛斷電話 | 無（掛斷不經過 HSS） | 不變 | 不變 |
| 11 | UE1 解除註冊（Expires: 0） | UAR（DE_REGISTRATION）→ UAA；SAR USER_DEREGISTRATION → SAA 2001 | 不變 | NR0，已存 S-CSCF 清掉 |

要注意的幾點：

- **第 1 步與第 5 步取的是同一個 SQN 計數器。** 這是 TS 33.203 §8.2 對 USIM 做 IMS 存取的要求（[ADR-0002](adr/0002-shared-auth-data-and-sqn.md)）。
- **第 3 步不回 Server-Name**，S-CSCF 由 I-CSCF 自己挑（[ADR-0006](adr/0006-uaa-capabilities-on-first-registration.md)）。PyHSS 在這一步會直接回 Server-Name。
- **第 5 步的 MAR 不會讓 UE1 變成「已註冊」**，只會記下「哪台 S-CSCF 正在認證它」。所以第 7 步 I-CSCF 再問時，才知道要送回同一台。
- **第 10 步跟 HSS 無關。** 通話資源由 P-CSCF 與 Rx／N5 Adapter 處理（[../rx-n5/](../rx-n5/README.md)）。

## 4. 出狀況的時候

### 4.1 UE1 在第 6 步之後沒回應

S-CSCF 等 60 秒（`auth_vector_timeout`）後送 SAR AUTHENTICATION_TIMEOUT。UDM 清掉 authPending；因為 UE1 還沒註冊，已存 S-CSCF 也一起清掉，回到 NR0。不清的話，UE1 下次註冊會一直被導到同一台 S-CSCF。

### 4.2 UE1 的 SQN 和網路對不上

真的手機上，USIM 收到太舊的 SQN 時會回 AUTS。S-CSCF 再送一次 MAR，這次 SIP-Authorization 裡帶 RAND‖AUTS。UDM 確認 MAR 的 Server-Name 跟已存的相同後，用 AUTS 驗 MAC-S、取出 USIM 的 SQN，把 UDR 的 SQN 設成「USIM 的 SQN＋33」，再發新向量。這段計算跟 5G-AKA 的重新同步是同一個函式。

實驗用的 free-ran-ue 不檢查 SQN 新鮮度，所以這條路徑在端到端測試裡不會自然發生，要靠單元測試（[test-plan.md](test-plan.md) T11、T13）。

### 4.3 5G 註冊和 IMS 註冊同時發生

兩邊同時向 UDR 取號。現行 free5gc 是「讀出 SQN → 加 1 → 整份寫回」，兩邊可能拿到同一個 SQN。改用條件式取號後，後到的一方會發現 SQN 已經變了，重讀再取下一個（[ADR-0003](adr/0003-atomic-sqn-allocation.md)）。

### 4.4 UDR 掛掉

UDM 對每個 Cx 指令都回 Result-Code 5012（UNABLE_TO_COMPLY），不帶任何向量或 profile；Diameter 連線本身不斷。Kamailio 會讓這次 REGISTER 失敗，UE1 稍後重試。

### 4.5 UDM 重啟

註冊狀態都在 UDR，重啟後照常回答。例如 UE1 卡在第 5 步和第 8 步之間時 UDM 重啟，第 8 步的 SAR 仍然會成功。

## 5. UDR 裡多了什麼

| 資料 | 例子 | 誰寫 |
|---|---|---|
| IMS subscription | UE1 的 IMPI、IMPU、MSISDN `0900000001` | 開戶腳本（`04-`，改呼叫 UDR 擴充 API） |
| 身分索引 | `208930000000001@ims…` → `imsi-208930000000001`；`sip:208930000000001@ims…` → 同一個 SUPI | UDR 在寫 subscription 時自動維護 |
| 註冊紀錄 | UE1 的 IMPU：REG、S-CSCF `sip:scscf.ims…:6060`、版本號 | UDM（Cx） |
| 認證資料 | K、OPc、AMF `8000`、SQN | 開戶（`02-`）；SQN 由 UDM 取號 |

## 6. 不做的事

- 不支援 N70：Kamailio 不會講。
- 不主動踢人（RTR）或推 profile（PPR）：屬 W8b。
- 不支援 Tel URI、shared IMPU、wildcard、PSI、緊急註冊、漫遊：實驗用不到。
- 不幫 I-CSCF 挑 S-CSCF。

## 7. 名詞對照

| 名詞 | 白話 |
|---|---|
| UAR／UAA | I-CSCF 問：「這個人可以註冊嗎？誰在服務他？」 |
| MAR／MAA | S-CSCF 要：「給我認證這個人用的向量」 |
| SAR／SAA | S-CSCF 報告：「我現在負責他了（或不負責了）」，順便拿 profile |
| LIR／LIA | I-CSCF 問：「有人打給他，他在哪台 S-CSCF？」 |
| authPending | 「正在認證中」的旗標 |
| 取號 | 拿一個沒用過的 SQN |
| Result-Code vs Experimental-Result | 前者是 Diameter 共通的結果，後者是 Cx 專用的結果；同一個數字在兩邊意思不同 |
