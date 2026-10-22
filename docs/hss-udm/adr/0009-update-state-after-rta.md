# ADR-0009：PERMANENT_TERMINATION 與 SERVER_CHANGE 在收到 RTA 之後才更新註冊狀態

- 狀態：提案
- 日期：2026-10-22

## 背景

- TS 29.228 V17.1.0 §6.1.3 開頭說 HSS 把 Public Identity 改成 Not Registered 再通知 S-CSCF；但 §6.1.3.1 的詳細行為規定，PERMANENT_TERMINATION 的結果要依 RTA 的 Identity-with-Emergency-Registration 決定，SERVER_CHANGE 時 HSS 設為 Not Registered 並清除 S-CSCF 名稱。
- NEW_SERVER_ASSIGNED 時，新的 S-CSCF 已經由 MAR 存入，HSS 的狀態不需要再改。

## 決定

以 §6.1.3.1 為準：PERMANENT_TERMINATION、SERVER_CHANGE 收到成功的 RTA 才改狀態；NEW_SERVER_ASSIGNED 不改。

## 後果

- 好處：RTA 失敗時，HSS 與 S-CSCF 的狀態不會分歧。
- 代價：RTR 到 RTA 之間，UAR／LIR 仍會回原本的 S-CSCF。
- 對應需求：REQ-RTR-05；測試：T37
