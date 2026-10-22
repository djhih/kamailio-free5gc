# ADR-0008：FAILED_RESOURCES_ALLOCATION 全部失效時送 ASR，部分失效時依訂閱送 RAR（4 或 9）

- 狀態：提案
- 日期：2026-10-22
- 相關：[ADR-0007](0007-delete-then-asr-on-terminate.md)；smf-n1n2 的 W5c

## 背景

- TS 29.214 V17.6.0 §4.4.6.2：部分 SDF 失效時，PCRF 送 RAR（Flows＋Specific-Action）；全部失效時送 ASR。§5.3.13 Note 2a：bearer 失效要報 INDICATION_OF_RELEASE_OF_BEARER(4) 還是 INDICATION_OF_FAILED_RESOURCES_ALLOCATION(9)，由實作決定。
- TS 29.514 V17.9.0 §4.2.5.5：部分失效用 FAILED_RESOURCES_ALLOCATION 事件；§4.2.5.3：全部失效用 terminate（ALL_SDF_DEACTIVATION）。
- free5gc PCF 收到 SMF 的失敗 ruleReports 時，刪掉那些 PCC rule，對訂閱的 AF 一律送 FAILED_RESOURCES_ALLOCATION 事件，**不會**改送 terminate（`smpolicy.go` 的 RuleReports 處理）。
- 2024 年碩論的截圖中，Kamailio 的 AAR 訂閱 1、2、3、4、6、12，沒有 9（6.1.4 待 D03）。

## 決定

Adapter 收到 FAILED_RESOURCES_ALLOCATION 時，自己判斷是否涵蓋本 session 所有 flow：全部失效就走 ADR-0007 的路徑（Delete＋ASR，Abort-Cause BEARER_RELEASED）；部分失效就送 RAR，Specific-Action 有訂閱 9 用 9，否則有訂閱 4 用 4，都沒有就只記錄。

## 後果

- 好處：對 Kamailio 呈現的是 TS 29.214 的行為，補上 free5gc PCF 少送的 terminate；Kamailio 只訂閱 4 時也收得到。
- 代價：Adapter 要知道 session 的完整 media component／flow 清單（W3a 已保存 `mediaComponents`）。
- 對應需求：REQ-EVT-01、REQ-RAR-01～05；測試：T39、T40、T41
