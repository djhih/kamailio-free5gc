# 總覽：現況、計畫與對照

> 2026-10-22 由原本的 `docs/current/` 與 `docs/plan/` 合併而成。各元件的詳細規格在 `docs/rx-n5/`、`docs/smf-n1n2/`、`docs/hss-udm/`、`docs/e2e-harness/`。

## 先看哪份

| 文件 | 回答什麼問題 | 給誰看 |
|---|---|---|
| [free5gc-kamailio-integration.md](free5gc-kamailio-integration.md) | 現在的部署怎麼對接？測試實際驗證了什麼？缺什麼？ | 第一次接觸的人 |
| [vonr-ims-nf-plan.md](vonr-ims-nf-plan.md) | 要做哪些工作（W1～W8）？順序、門檻、風險、待決定？ | 所有人 |
| [vonr-3gpp-conformance.md](vonr-3gpp-conformance.md) | 做完之後完不完整？每一項跟 3GPP 的關係？ | 指導者、評審 |
| [w2-w7-checklists.md](w2-w7-checklists.md) | W2、W7 要逐項確認什麼？部署和查證的版本差多少？ | 實作者 |
| [vonr-ims-dev-process.md](vonr-ims-dev-process.md) | 照 free5gc 慣例怎麼開發、怎麼分 repo、怎麼測？ | 實作者 |

**以哪份為準：** 現況以 [free5gc-kamailio-integration.md](free5gc-kamailio-integration.md) 為準；工作項、時程與待決定以 [vonr-ims-nf-plan.md](vonr-ims-nf-plan.md) 為準；元件的行為以各規格組的 interface-spec 為準。互相衝突時視為文件錯誤，要修正。

## 工作項與規格組

| 工作項 | 規格 |
|---|---|
| W1 抓包版測試 | [../e2e-harness/](../e2e-harness/README.md) |
| W2 imsVoPS、W7 版本查證 | [w2-w7-checklists.md](w2-w7-checklists.md) |
| W3 Rx／N5 Adapter、W4 Kamailio 設定 | [../rx-n5/](../rx-n5/README.md) |
| W5 SMF 通知 RAN／UE、W6 free-ran-ue 回應器 | [../smf-n1n2/](../smf-n1n2/README.md) |
| W8 HSS 併入 UDM | [../hss-udm/](../hss-udm/README.md) |
