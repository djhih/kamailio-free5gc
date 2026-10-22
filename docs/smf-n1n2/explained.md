# SMF 通知 gNB 與 UE：用一通電話走一遍

> 性質：說明（informative）。行為以 [interface-spec.md](interface-spec.md) 為準；這份文件和規格衝突時，以規格為準。

## 1. 一句話

PCF 為一通電話加上或拿掉語音 QoS 規則時，SMF 除了改 UPF，也要告訴 gNB（N2）和手機（N1），讓三邊對「這個 PDU session 有哪些 QoS flow」看法一致。

## 2. 現在少了什麼

```
現在   PCF ──policy 更新──▶ SMF ──PFCP──▶ UPF          （gNB、UE 什麼都不知道）
之後   PCF ──policy 更新──▶ SMF ──PFCP──▶ UPF
                             └──N1N2──▶ AMF ──NGAP──▶ gNB ──NAS──▶ UE
```

PDU session 建立時，SMF 已經用同樣的方式告訴 gNB 與 UE 有一個預設 QoS flow（5QI 5，QFI 1）。這次要補的是之後「多一個、少一個」的通知。

## 3. 一通電話

UE1 打給 UE2。下面只看 UE1 那一側；UE2 那一側一模一樣，各自一個程序。

| # | 發生什麼 | 訊息 | UE1 的 QoS flow |
|---|---|---|---|
| 1 | UE2 回 200 OK，P-CSCF 經 Adapter 要資源 | Rx AAR → N5 Create | QFI 1（預設） |
| 2 | PCF 新增 PCC rule（5QI 1），通知 SMF | SmPolicyUpdateNotify | — |
| 3 | SMF 套用 PCC rule，配 QFI 2，更新 UPF；回 PCF 204 | PFCP | QFI 2：TO_ADD |
| 4 | SMF 組 N1（create QoS rule、create flow description 5QI 1，PTI＝0）與 N2（AddOrModify QFI 2），一次交給 AMF | N1N2MessageTransfer | QFI 2：ADDING，T3591 開始 |
| 5 | AMF 把 N2 和 NAS 一起送給 gNB；gNB 把 NAS 轉給 UE1 | NGAP Modify Request、NAS Command | — |
| 6 | gNB 回 QFI 2 成功 | Modify Response → UpdateSMContext | — |
| 7 | UE1 回 Complete | NAS → UpdateSMContext | QFI 2：SYNCED，T3591 停 |
| 8 | 通話中 | RTP 走 QFI 2 | — |
| 9 | BYE，Adapter 刪 app session；PCF 通知 SMF 刪 PCC rule | N5 Delete → SmPolicyUpdateNotify | — |
| 10 | SMF 發現 QFI 2 沒有 PCC rule 參照了（PCF 的通知沒說要刪 QoS，SMF 自己推導） | PFCP | QFI 2：TO_DELETE |
| 11 | SMF 送刪除（delete QoS rule、delete flow description；N2 ToRelease QFI 2） | N1N2 | DELETING |
| 12 | gNB 回 Response、UE1 回 Complete | — | QFI 2 移除，QFI 才釋放 |

## 4. 現在的 free-ran-ue 在哪裡卡住

第 5 步：gNB 收到 Modify Request 時，dispatcher 沒有這個 case，只記一行「Unknown NGAP PDU」。UE1 也不認得 Modification Command。所以第 6、7 步永遠不會發生，SMF 會在 T3591 逾時 5 次後中止。這就是要 patch free-ran-ue 的原因（[ADR-0005](adr/0005-patch-free-ran-ue-responder.md)）。

就算沒有 patch，第 8 步的 RTP 仍然通：free-ran-ue 的 GTP-U 根本不看 QFI。所以「通話打得通」不代表這個功能做對了，要看 N1、N2 的內容和程序有沒有完成。

## 5. 出狀況的時候

### 5.1 通話太短：刪除比新增先結束

第 9 步發生時，第 4～7 步還沒走完。SMF 先把 UPF 規則刪掉，但不立刻送第二個 N1N2，而是把「刪 QFI 2」排隊；等新增程序結束，再送刪除。QFI 2 在刪除完成前不會配給別人（[ADR-0003](adr/0003-one-procedure-per-session.md)）。

### 5.2 UE 不回

T3591 每 16 秒逾時一次，前 4 次重送同一個 Command，第 5 次放棄。UPF 規則不回退，QFI 2 標成 TO_SYNC，下一次有任何 policy 更新時一起補送（[ADR-0004](adr/0004-keep-upf-rules-on-abort.md)）。

### 5.3 gNB 拒絕 QFI 2

gNB 在 Modify Response 的失敗清單放 QFI 2。UE 那邊已經收到 create QoS rule 了，所以 SMF 要再發一個程序，把 QoS rule 從 UE 刪掉（TS 23.502 §4.3.3.2 步驟 7）。

W5c 再多做一步：SMF 向 PCF 回報這條 PCC rule 已經 INACTIVE，PCF 通知 Adapter「資源失效」，Adapter 判斷整通電話的語音都沒了，送 ASR 給 Kamailio 結束通話（rx-n5 W3b）。gNB 在通話中主動釋放 QFI 2（PDU Session Resource Notify）時也是同一條鏈。這樣使用者不會對著一條沒有語音資源的線講話（TS 23.228 附錄 Y.2.4）。

### 5.4 UE 這時候要求釋放 PDU session

SMF 放棄修改，直接走釋放（TS 24.501 §6.3.2.5 c）。

## 6. 不做的事

- 不改既有 QoS flow 的參數（re-INVITE 改 codec）：W5b。
- 不在 UE 閒置時延後補送：W5b。
- 不保證真實 gNB、手機的行為：patch 過的 free-ran-ue 只是回應器。

## 7. 名詞對照

| 名詞 | 白話 |
|---|---|
| QFI | QoS flow 的編號，PDU session 內唯一 |
| QoS rule | 給 UE 的「哪些封包走哪個 QFI」規則（N1） |
| QoS flow description | 給 UE 的「這個 QFI 是什麼等級」（5QI、頻寬）（N1） |
| N2 SM information | 給 gNB 的 QoS flow 清單（新增或釋放） |
| PTI | 5GSM 程序的交易編號；網路自己發起時填「未指派」 |
| T3591 | SMF 等 UE 回 Complete 的計時器 |
