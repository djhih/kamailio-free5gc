# ADR-0006：第一階段不支援 AAR 更新（PATCH）

- 狀態：提案
- 日期：2026-10-22
- 相關：計畫 [vonr-ims-nf-plan.md](../../overview/vonr-ims-nf-plan.md) §7 第 1、2 項（原本的「re-INVITE 對策」已由 [ADR-0009](0009-patch-or-replace-on-aar-update.md) 提出）

## 背景

re-INVITE 時 Kamailio 會在同一個 Session-Id 上送新的 AAR。free5gc PCF（v1.4.5 原始碼）的 PATCH 有兩個限制（細節見 [ims-af-thesis-comparison.md](../../background/ims-af-thesis-comparison.md) 2.2）：

1. 只到當初 POST 的 `medComponents` 找要替換的舊規則；同一元件第二次 PATCH 改了 flow，舊 PCC rule 不會被刪，之後 Delete 也刪不到。
2. PATCH 沒帶 `evSubsc` 時，PCF 會清掉既有的事件訂閱。

對策有三：照樣 PATCH（接受舊規則殘留）、Delete 後重建（短暫沒有語音規則）、修 PCF（違反原則）。還沒決定。

## 決定

第一階段收到更新一律拒絕，保持原有 app session 不變。不 PATCH，也不改成 Delete＋Create。對策留到 W3b 決定，屆時新增一張 ADR 取代本決定。

## 後果

- 第一階段不會產生 PATCH 造成的殘留規則。
- 通話中改 codec 或改 port 時，Kamailio 會收到失敗；那通電話繼續用原本的規則。實驗用的 SIPp 情境不做 re-INVITE，影響可以接受。
- Adapter 必須能正確區分「重送」與「更新」，不能把更新當重送回成功（REQ-AAR-12、13）。
- 測試：T05。
