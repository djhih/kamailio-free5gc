# 簡報

| 簡報 | 內容 | 頁數 | 原始檔 |
|---|---|---|---|
| `VoNR_over_IMS_kamailio_intro.pptx` | VoNR／IMS 入門、kamailio-free5gc 的做法、NF 修改計畫 | 28 | `src/vonr-intro/`（第 12 頁另由 `src/vonr-architecture/` 產生） |
| `free5gc_kamailio_integration.pptx` | free5gc 與 Kamailio 的五個對接點 | 12 | `src/integration-deck/` |
| `VoNR_over_IMS_kamailio_intro_animated_v2.pptx` | 入門簡報加上三幕 IMS 情境動畫（第 8–10 頁） | — | `src/ims-scenario-animation/` |
| `VoNR_over_IMS_kamailio_intro_animated.pptx` | 上一版動畫 | — | 同上 |

## 注意

- **入門簡報的第 12 頁** 已由 `src/vonr-architecture/build_slide.py` 換成新的架構圖。從 `src/vonr-intro/` 整份重建會蓋掉它；重建後要再跑一次 `build_slide.py`。
- **兩份 `_animated` 簡報** 是 2026-10-06 以當時的入門簡報製作，沒有之後依 HackMD 加入的「各 NF 的修改範圍」與五階段計畫。
- `src/vonr-intro/`、`src/integration-deck/` 是 GenOffice 的頁面 spec（JSON）。GenOffice 只能寫入 `~/genoffice`、`~/Documents`，所以要先把資料夾複製到 `~/genoffice/` 再建置：

```bash
cp -r slides/src/integration-deck ~/genoffice/f5gc-kamailio-integration
cd ~/genoffice/f5gc-kamailio-integration
python3 build.py              # 產生 pages/*.json（build.py 內寫死了這個路徑）
genoffice create --type pptx --spec pages --outline outline.json --out deck.pptx --force
```

`src/vonr-intro/` 沒有 build.py，頁面直接手寫在 `pages/*.json`；`trim.py` 是精簡文字時用過的一次性腳本。
