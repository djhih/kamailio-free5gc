# VoNR NF 修改：開發流程與程式結構

> 狀態：草案（2026-10-06；2026-10-15 補上 W8；2026-10-22 對齊各規格組），配合 [vonr-ims-nf-plan.md](vonr-ims-nf-plan.md) 使用
> 參考：iThome 系列文〈5G 核心網路與雲原生開發之亂彈阿翔〉（free5GC 維護者撰寫）中的
> 〈Network Function 通用軟體架構〉、〈為 free5GC 導入 CI workflow〉、〈設計模式與重構〉，
> 並對照本機 free5gc v4.3.0 的實際程式碼（`~/free5gc/free5gc`）

系列文寫的是 free5GC v3.2.0，跟現在的 v4.3.0 已經不同。下面先整理 free5gc 實際怎麼開發，再定出本專案要照做的部分。

## 1. free5gc 是怎麼開發的

### 1.1 Repo 組織

- 主 repo `free5gc/free5gc` 只是組裝用：每個 NF 是獨立 repo，以 git submodule 掛在 `NFs/` 下。發佈新版本 = 更新 submodule 指向的 commit
- 共用程式拆成獨立 module：`github.com/free5gc/openapi`（SBI models 與 client）、`github.com/free5gc/util`（logger、metrics、version、milenage 等）
- 建置：主 repo 的 `Makefile` 對每個 NF 執行 `cd NFs/<nf>/cmd && go build`，並用 `-ldflags` 把版本、commit hash 寫進 `github.com/free5gc/util/version`
- 貢獻：修哪個 NF 就對哪個 NF 的 repo 發 PR；需要整合測試時，再到主 repo 發一個更新 submodule hash 的 PR

### 1.2 NF 的程式結構（v4.3.0，以 PCF 為例）

系列文把 NF 拆成 App、Protocol、Context、Logger、Sbi（producer／consumer）、Pkg、Util 七塊。v4.3.0 的實際配置如下：

```
<nf>/
├── cmd/main.go                 # urfave/cli 進入點：讀設定、建立 App、Start()
├── pkg/
│   ├── app/app.go              # App 介面：Start、Terminate、Context()、Config()、log 設定
│   ├── factory/                # config.go（設定的資料型別 + govalidator 驗證）、factory.go（讀 yaml）
│   └── service/init.go         # NewApp()：依序建立 context → consumer → processor → sbi.Server → metrics
└── internal/
    ├── context/                # NF 的狀態，單例，透過 GetSelf() 取得
    ├── logger/                 # 各子系統的 logger（MainLog、SBILog…）
    ├── util/                   # 轉換函式、router 授權檢查等
    └── sbi/
        ├── server.go           # gin router；每組服務一個 route group，各掛 OAuth 授權檢查
        ├── api_<service>.go    # HTTP handler：解析請求 → 呼叫 processor → 回應
        ├── processor/          # 業務邏輯；Processor 內嵌 App，經由它拿 Consumer
        └── consumer/           # 對其他 NF 的 client，每個目標服務一個檔案（nrf_service.go…），client 依 URI 快取
```

模組之間的依賴靠介面切開：processor 只依賴「有 `Consumer()` 的 App」，consumer 只依賴「有 `Config()`、`Context()` 的物件」。這正是系列文〈設計模式與重構〉案例二提到的作法：大套件拆成子套件後，用 interface 聚合，避免循環依賴。

### 1.3 CI

| 層級 | 位置 | 內容 |
|---|---|---|
| 每個 NF repo | `.github/workflows/commit-msg-check.yml` | commit 必須符合 Conventional Commits |
| | `golangci-lint.yml` | golangci-lint v2，設定在 `.golangci.yml`（啟用 lll、bodyclose、noctx、misspell 等；funlen 60 行） |
| | `go.yml` | `go build -v ./...`、`go test -v ./...` |
| 主 repo | `test.yml` | self-hosted runner（因為要載入 gtp5g 核心模組）：`make` 後用 `test_ci.sh` 跑 Go 寫的整合測試（TestRegistration 等），測試在 network namespace 裡跑，搭配 MongoDB |
| | `ci-test.yml` | 每日排程：拉 `free5gc/ci-test`，用 docker compose 跑整合測試與端到端測試 |

系列文提到的本機開發技巧：用 `act` 在本機跑 GitHub Actions，例如 `sudo act --privileged --container-cap-add CAP_SYS_ADMIN --container-cap-add NET_ADMIN pull_request`。前提是主機已經裝好 gtp5g。

### 1.4 系列文中的設計原則

- 熱路徑上避免共用一把 mutex：收訊息 → dispatcher → 固定大小的 worker pool；交易表這類共享狀態交給單一 goroutine 維護
- 單一套件過大（超過約 50 個函式或成員）就拆，例如 pfcp 拆成 server／handler／sender／message／tx，再用 interface 聚合
- NF 分 stateful／stateless；stateful 的狀態要能搬到外部儲存（3GPP 的 UDSF 就是為此而設）

## 2. 本專案的程式結構

照 1.2 的骨架。Rx（Diameter）放在系列文所說的「Protocol」那一層（相當於 AMF 的 NGAP），Rx ↔ N5 的對應獨立成純函式的 `internal/mapper/`。

完整的目錄與每個檔案的職責以 [../rx-n5/design.md](../rx-n5/design.md) §5.5為準，這裡不再重複，避免兩份不一致。

W5 是在 free5gc SMF 的 fork 裡加網路發起修改的程序狀態機（`internal/sbi/processor/nwmod.go`）與差異計算（`internal/context/qos_flow_diff.go`），目錄以 [../smf-n1n2/design.md](../smf-n1n2/design.md) §5.5 為準。

W8 不是新 NF，而是在 free5gc UDM 裡加一個 HSS 子系統：Cx（Diameter）放在 `internal/cx/`，跟 Nudm 的 `internal/sbi/` 平行，作法照 CHF 的 `ccs_diameter/`。目錄以 [../hss-udm/design.md](../hss-udm/design.md) §5.5 為準。注意 CHF 用的是 `github.com/fiorix/go-diameter v3.0.2+incompatible`，內建字典沒有 Cx（版本選擇見該文件 D13）。

SBI 的資料型別一律用 `github.com/free5gc/openapi/models`（`Pcf_PolAuth_*`）；N5 的 client 也已在 free5gc/openapi 裡。

## 3. 並行設計（套用 1.4）

| 元件 | 作法 |
|---|---|
| Rx 收包 | 接收 → dispatcher 依 Session-Id 雜湊分給固定數量的 worker；同一個 session 永遠由同一個 worker 處理，session 狀態不需要鎖 |
| N5 呼叫 | worker 把請求丟給 PCF client pool，結果回到原 worker 再回 AAA／STA；Rx 處理不被 PCF 卡住 |
| PCF 回呼 | HTTP handler 只依 appSessionId 找到 session，轉交給該 session 的 worker 送 RAR／ASR |
| 關機 | 照 free5gc 的 `context.WithCancel` + `sync.WaitGroup`：先停收包、等 worker 清空、再向 NRF 取消註冊 |

## 4. 開發流程

### 4.1 Repo 與分支

- Adapter 一個 repo；SMF 的修改（W5）fork `free5gc/smf`，是否發 PR 回上游待決定（smf-n1n2 D09）；HSS 併入 UDM（W8）fork `free5gc/udm` 與 `free5gc/udr`，只留在自己的 fork；free-ran-ue 的修改（W6）照 `ran/pcscf-discovery.patch` 做成 patch；測試工具（W1）放在 `kamailio-free5gc/scripts/e2e/`
- 三個 fork（SMF、UDM、UDR）要基於同一個 free5gc 版本（計畫第 7 節第 3 項、W7-C）
- `main` 永遠可以跑通端到端測試；每個功能開分支、發 PR、合併
- commit 照 Conventional Commits，例如 `feat(rx): handle STR`、`fix(processor): map Flow-Description direction`

### 4.2 每個 PR 的完成條件

1. `go build ./...`、`go test ./...` 通過
2. `golangci-lint run` 沒有新問題（`.golangci.yml` 照抄 free5gc NF 的設定）
3. 新的對應或事件有單元測試，並在 PR 說明寫出依據的條文（例如 TS 29.513 B.2.1）
4. 動到訊息流程的 PR：本機跑一次端到端測試，結果貼在 PR 說明

### 4.3 測試分層

| 層級 | 怎麼跑 | 對應 free5gc 的作法 |
|---|---|---|
| 單元 | `go test ./...`；Rx → N5 對應、事件對應、Cx 指令解碼都用表格驅動 | 各 NF repo 的 `go.yml` |
| 整合 | 小的 Rx client、Cx client（go-diameter）直接打 Adapter 與 UDM，加上真的 free5gc PCF／SMF／UPF／UDR | 主 repo 的 `test_ci.sh`、`ci-test` 的 IT compose |
| 端到端 | Kamailio + free5gc（W8 完成前是 Kamailio + PyHSS + free5gc），用抓包版測試工具（[../e2e-harness/](../e2e-harness/README.md)）判定 | `ci-test` 的 e2e compose |

### 4.4 CI

- repo 放 1.3 的三支 workflow（commit-msg、golangci-lint、go），用 GitHub 提供的 runner
- 端到端測試需要 gtp5g，只能用 self-hosted runner；先用 `act` 在本機跑

### 4.5 要讀的規格（`specs/3gpp-r17/`）

| 用途 | 規格 |
|---|---|
| 為什麼是 Rx 前端 | TS 23.503 附錄 C |
| IMS 與 PCF 要交換什麼 | TS 29.513 7.3.2、附錄 B |
| 兩端介面 | TS 29.214（Rx）、TS 29.514（N5）、TS 29.571（共用型別） |
| NRF | TS 29.510 |
| BSF（W3c） | TS 29.521（本機沒有；目前依 free5gc BSF 實作） |
| 5GC 回報（W3b） | TS 29.214 §4.4.6、TS 29.514 §4.2.5 |
| SMF 通知 RAN／UE（W5） | TS 23.502 §4.3.3.2、TS 24.501 §6.3.2、§9.11.4.12、§9.11.4.13；TS 38.413、29.502、29.518、29.512（本機沒有） |
| HSS 併入 UDM（W8） | TS 23.228 附錄 Y.0（部署方式）、TS 29.228／29.229（Cx）、TS 33.203（IMS AKA）、TS 23.003 §13（IMS 身分）、TS 29.505（UDR） |
| 背景 | TS 23.228、TS 24.229（IMS 怎麼用這些資訊）、TS 23.501（5QI） |
