# 驗證紀錄

日期：2026-10-22。此份公開紀錄只列出實際已知的結果；原 Stage 1.1 歷史報告不代表這次新增 API 已驗收。

| 檢查 | 指令 | 結果 |
|---|---|---|
| Python 語法 | python -m compileall -q app alembic scripts tests | PASS，exit 0 |
| 單元測試 | python -m pytest tests/unit -q -p no:cacheprovider | PASS，13 passed，exit 0 |
| 測試收集 | python -m pytest --collect-only -q -p no:cacheprovider | 34 tests collected，exit 0；收集不等於執行通過 |
| PostgreSQL 整合／並發 | python scripts/check_project.py | PASS，34 passed，exit 0；由使用者終端執行，代理讀取實際保存的日誌確認 |
| 新版容器啟動／HTTP demo | README Quick Start + python scripts/demo.py | NOT VERIFIED |
| GitHub Actions | push / pull_request | NOT VERIFIED；尚未建立 remote |

單元測試執行環境：本機 Python 3.11。已觀察到 Starlette 對 HTTPX TestClient 的棄用警告，並非失敗；目前沿用鎖定依賴，後續升級需一起驗證。

DB 測試使用真實 PostgreSQL；TestClient 並發規模為 20 次不同使用者請求及 10 次同使用者操作，沒有 throughput、p95 或 p99 數據。沒有執行原企畫書全部階段，不宣稱高負載或 production ready。

本次 PostgreSQL 17.11 隔離容器實測：34 passed，沒有失敗；migration downgrade/upgrade 與 metadata 對照檢查、報名／取消 rollback、4 項並發案例均包含於其中。Docker build 及測試容器清理退出碼皆為 0。原始日誌保留本機 docs/evidence/portfolio-tests.local.json（不提交，避免機器資訊混入公開版本）。
