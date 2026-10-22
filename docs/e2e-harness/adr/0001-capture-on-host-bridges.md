# ADR-0001：在 host 的兩個 docker bridge 抓包，用 tshark 判定

- 狀態：提案
- 日期：2026-10-22

## 背景

- 現行 `03-call-test.sh` 的判定依賴 Kamailio 的 `xlog` 字串，W3、W4、W8 都會改到這些 log。
- `docker-compose.yaml` 把兩個網段的 bridge 命名為 `br-poc-core`（corenet）與 `br-poc-dn`（dnnet）。前者看得到 NGAP、N3 GTP-U（內層 SIP、RTP）、PFCP、SBI；後者看得到 N6 的 SIP、CSCF 之間的 SIP、Diameter、AF shim 的 HTTP。
- host 有 tshark 4.7.3、dumpcap；容器裡都沒有 tshark，free5gc 映像不一定有 tcpdump。
- NAS 是 NEA0、SBI 是 h2c，不需要解密。

## 決定

每次執行在 host 的兩個 bridge 各錄一份 pcapng，用固定的 decode-as 以 tshark 解碼，判定只依賴 pcap 與 UPF 規則快照。

## 後果

- 好處：不改任何容器；換元件不影響測試；所有介面的時間軸一致。
- 代價：UE↔UE 的 RTP 只能從 N3 看；h2c 要錄到連線開頭才解得出 header（D02）；需要抓包權限（D01）。
- 對應需求：REQ-CAP-01～04、REQ-DEC-01～04；測試：T01、T03、T13、T14
