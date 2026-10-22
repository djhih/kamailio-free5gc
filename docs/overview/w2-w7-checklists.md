# W2 與 W7 檢查清單

> 狀態：2026-10-22
> 這兩項工作沒有新程式，不另立規格組；用檢查清單驗收，每一項都對到抓包檢查或原始碼比對。

## W2：AMF 宣告支援 IMS 語音

| # | 項目 | 依據 | 驗收 |
|---|---|---|---|
| W2-1 | `config/amfcfg.yaml` 的 `configuration.nasIE.networkFeatureSupport5GS.imsVoPS` 由 0 改成 1（同一段已有 `enable: true`、`length: 1`） | lab 設定檔 L66–70 | 設定 diff |
| W2-2 | **W5 的 G3 通過之後才改。** TS 23.501 V17.15.0 §5.16.3.2：要有支援語音的 5G QoS flow，AMF 才可以宣告 IMS VoPS | [vonr-3gpp-conformance.md](vonr-3gpp-conformance.md) §2.1 | 計畫時程 |
| W2-3 | Registration Accept 的 5GS network feature support 中 IMS VoPS 3GPP＝1 | 部署的 AMF v1.4.5：`build.go` `BuildRegistrationAccept` 用 `SetIMSVoPS3GPP`；查證的 v1.4.6 用新的 nas API。部署用 NEA0，tshark 可直接解 | [e2e-harness](../e2e-harness/interface-spec.md) CHK-W2-01 |
| W2-4 | 已知限制：AMF 在 Nudm_UECM 註冊時把 `ImsVoPs` 寫死成 `HOMOGENEOUS_NON_SUPPORT`（`internal/sbi/consumer/udm_service.go`，兩個版本都是），W2 改不到 | TS 23.501 §5.16.3.3 要求依實際情況送 | 列為限制；要修需另立工作項（改 AMF），W8 之後的 T-ADS 才會用到 |
| W2-5 | free-ran-ue 是否解析這個 IE | 未查證 | 只驗證 AMF 送出的值 |

## W7：部署版本與查證版本一致

### 版本現況（2026-10-22 盤點）

| 元件 | 部署 | 查證用的原始碼 | 差距 |
|---|---|---|---|
| free5gc NF 映像 | `free5gc/*:v4.2.3`，只有 tag、沒有 digest | 本機 `NFs/*`（free5gc 主 repo 在 v4.3.0） | v4.2.3 釘的版本：AMF v1.4.5（本機 HEAD 多 51 個 commit）、SMF v1.4.5（多 48）、PCF v1.4.5（多 16）、UDM v1.4.5（多 16）、UDR v1.4.4（多 15）、UPF v1.2.12（多 21）、NRF v1.4.5（多 17）、AUSF v1.4.5（多 8） |
| Kamailio | `debian:trixie-slim`＋apt `kamailio61`，**沒有鎖小版本** | GitHub master（rx-n5 附錄 B） | 「6.1.4」只是 lab README 的說法，實際版本取決於 build 時間 |
| free-ran-ue | v2.5.0＋`pcscf-discovery.patch` | 本機 v2.5.0-26 | 26 個 commit |
| PyHSS | `latest@sha256:da53ca70…` | 沒有原始碼 | README 說 2.0.0，與 digest 是否一致未查證 |
| gtp5g | 0.10.2 | — | 一致 |

### 檢查項目

每一項都要在**部署版本**上得到結論：用 `git diff <v4.2.3 釘的版本>..HEAD -- <檔案>` 比對相關函式，並在部署環境抓包佐證。

| # | 項目 | 用到的文件 | 比對的位置 | 佐證 |
|---|---|---|---|---|
| W7-1 | SMF 收到 policy 更新時不送 N1N2 | smf-n1n2 前提 | `notifier.go` `HandleSMPolicyUpdateNotify` | T26（smf-n1n2 G0） |
| W7-2 | Modification Command builder 沒有 QoS IE、PTI 用 `smContext.Pti`；N2 builder 沒有釋放清單 | smf-n1n2 §2 | `gsm_build.go`、`ngap_build.go` | 原始碼 |
| W7-3 | PCF 刪除通知不帶 QosDecs；SMF 只在 QosDecs 為 nil 時釋放 QFI | smf-n1n2 ADR-0002 | `pcf/internal/context/ue.go` `RemovePccRule`；`sm_context_policy.go` | T26 |
| W7-4 | PCF 的 PATCH 限制（重複 PATCH、Flow-Status、`evSubsc`） | rx-n5 ADR-0009、碩論比較 2.2 | `policyauthorization.go` `HandleModAppSessionContext`、`removeMediaComp`、`getFlowInfos` | rx-n5 T47、T48 |
| W7-5 | PCF 送 terminate 後即刪除 app session；全部失效只送事件；QOS_NOTIF 不帶 `qncReports` | rx-n5 ADR-0007、0008；smf-n1n2 ADR-0010 | `smpolicy.go` | rx-n5 T35、T40 |
| W7-6 | PCF 的 CONTROL→5QI 9、fNum 0 的子元件會產生空的 PCC rule | rx-n5 ADR-0010、附錄 E | `pcc_rule.go`、`policyauthorization.go` | 原始碼 |
| W7-7 | AMF 在 Service Request 後丟掉 `PDU_RES_MOD_REQ` | smf-n1n2 ADR-0009 | `amf/internal/gmm/handler.go` `HandleServiceRequest` | 原始碼 |
| W7-8 | UDM 的 SQN 讀出、加 1、整份寫回（非原子） | hss-udm ADR-0003 | `generate_auth_data.go`；UDR `PatchDataToDBAndNotify` | hss-udm T14 |
| W7-9 | AMF 有 `imsVoPS` 設定並編進 Registration Accept | W2 | `build.go` | CHK-W2-01 |
| W7-10 | `ims_qos` 預設送 IMPU；上行 Flow-Description 寫成 `from <UE> to <對方>`；收到 ASR 會結束 dialog | rx-n5 附錄 B、D03、D05、D10 | Kamailio 6.1.x（實際 build 的版本） | rx-n5 G1 抓包 |
| W7-11 | Kamailio 的 Cx 用法（I-CSCF 吃只有 capabilities 的 UAA、S-CSCF 處理 RTR／PPR） | hss-udm D04、D16 | 同上 | hss-udm G1 |

### 需要先處理的事

| # | 項目 | 為什麼 |
|---|---|---|
| W7-A | Kamailio 的 apt 安裝鎖定小版本（例如 `kamailio=6.1.4*`），或至少把實際版本記入 manifest | 不鎖版本時，同一份 cfg 在不同時間 build 會得到不同行為 |
| W7-B | free5gc 映像記錄 image id 或 digest | tag 會被覆蓋；label 看不出 NF 版本 |
| W7-C | 決定 fork 的基礎版本（rx-n5 D01、hss-udm D01、smf-n1n2 D01 是同一個問題） | W5、W8 的三個 fork 要一致 |
