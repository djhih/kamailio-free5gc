# IMS 情境動畫：小明打給小華

已使用本機 `/home/jjd/.local/bin/genoffice`（0.10.0）和
`/home/jjd/genoffice` 的 GenOffice 簡報引擎製作。
這次直接透過 CLI 操作，沒有變更全域 MCP 設定。

## 播放

- 最新整份簡報：`../../VoNR_over_IMS_kamailio_intro_animated_v2.pptx`。
- 最新三幕獨立版：`IMS_scenario_v2.pptx`。
- v2 將新增頁面的 39 條線路校正為水平／垂直，對齊 SIP 與 RTP 的兩端，補齊 HSS 垂直線，並放大、放慢第 8–9 頁的封包動畫。
- 完整版第 **8–10 頁** 是新動畫；原本第 8 頁起順延三頁。
- 在 GenOffice 或 PowerPoint 進入投影片播放模式，從第 8 頁開始。
  每次點擊／下一步顯示一個流程；第一幕 7 次、第二幕 6 次、第三幕 3 次。
  每段封包移動約 2–3.5 秒，等動畫停下後即可搭配對白講解。
- 動畫是可編輯的原生 PowerPoint 物件、路徑和時間軸，沒有巨集或外部媒體依賴。
  編輯畫面與靜態 PNG 會同時顯示全部物件；逐步顯示須使用投影片播放模式。
- 講者備註包含每一步的講稿、簡化範圍和資料來源。

## 內容

1. **先報到**：REGISTER、UAR/UAA、MAR/MAA、401 挑戰、Authorization、SAR/SAA、200 OK。
2. **撥號找人**：INVITE / SDP、LIR/LIA、Path 回程、180 響鈴、200 接聽、ACK。
3. **接通與掛斷**：P-CSCF 透過 AF shim / N5 要 QoS、RTP 經 UPF 雙向傳送、BYE / 200 OK 與 QoS 釋放。

「小明、小華」是講解角色。流程依本工作區的 PoC：主叫 P→I→S；兩個 P 是同一程序的兩個 leg；媒體在 UPF hairpin。
標準主叫 Service-Route、early media 等差異已寫在頁尾或講者備註。
5QI 1 為語音規則，信令仍維持 5QI 5；不代表整個 IMS session 被升級。

## 來源與製作檔

- 原簡報第 7、9、10、14–17、23–25 頁。
- `../../../kamailio-free5gc/{pcscf,icscf,scscf}/kamailio.cfg`。
- [Kamailio IMS P-CSCF registrar](https://www.kamailio.org/docs/modules/stable/modules/ims_registrar_pcscf.html)。
- [3GPP TS 23.228 / ETSI IMS 架構](https://www.etsi.org/deliver/etsi_ts/123200_123299/123228/18.05.00_60/ts_123228v180500p.pdf)。
- `style.md`、`outline.json`、`pages/*.json`：GenOffice 版面原始檔。
- `build_specs.py`：一次產生一頁 spec，交由 `genoffice slides check` 檢查。
- `animate.py`、`animation-ops.json`：從 GenOffice read-back ID 建立動畫。
- `integrate.mts`：用 GenOffice 引擎插入三頁，驗證動畫與原頁保存。
- `metadata/verification.json`：播放狀態、點擊數、路徑位移、掛斷收起 RTP、原檔 SHA-256 與 25 頁逐位元組比對結果。
- `v2-previews/`：新版 GenOffice 靜態排版預覽。
- `playback-previews/`：新版第 8–9 頁實際播放模式的初始、移動中、第一步完成及全頁完成截圖。

## 驗證範圍

三幕的 GenOffice 版面檢查通過；原生動畫在儲存、重新讀取、插入完整簡報後保持一致。
已用 GenOffice 播放狀態計算器驗證 16 組點擊、17 條移動路徑、封包進出場與 BYE 後收起 RTP。
v2 另在隔離設定的本機 GenOffice 中實際播放第 8 頁 7 步、第 9 頁 6 步，確認封包移動與逐步顯示可見。
25 張原投影片的 XML 及原始檔案皆未改動。
未在 Microsoft PowerPoint 桌面版逐步實播；字型使用本機 Noto Sans CJK TC，其他電腦可安裝此字型以保持相同排版。
