# 面試前複習

## 如何定位

「我主要不是做後端，這個是我用 FastAPI 和 PostgreSQL、在 AI 協助下完成的小型練習。目的是熟悉 API、資料庫交易與基本測試，不是大型上線系統。」

不要把沒有親自理解的部分說成獨立設計。先重新跑 demo，再看下面幾段程式；被追問不熟悉的內容時，直接說明練習範圍。

## 一分鐘介紹

「這是一個限額活動報名 API。可以建立活動、報名與取消。我特別處理同時搶最後一個名額：在 PostgreSQL 交易中先鎖定活動，再修改名額與報名紀錄，失敗就一起回滾。另外用 partial unique index 限制同一人不能同時有兩筆有效報名。用 Docker 啟動環境，Alembic 管理資料表，pytest 測循序操作、資料約束與小規模並發。」

測試有沒有真的通過、規模多少，先看 verification.md；不要背不符合目前驗證狀態的數字。

## 對照程式看

| 檔案 | 要能解釋的內容 |
|---|---|
| app/main.py | 路由、輸入驗證、成功狀態碼、transaction begin / commit 邊界 |
| app/services/registrations.py | event row lock、額滿與重複報名判斷、取消釋放名額 |
| app/models/__init__.py | CHECK、FK、partial unique、取消歷史 |
| alembic/versions/0001_initial.py | 如何從空 DB 建立 schema，為何不用每次 create_all |
| tests/concurrency/test_registration.py | 同步發送、多獨立 session、檢查 DB 最終狀態 |
| tests/integration/test_database.py | 失敗後 rollback、migration roundtrip |
| compose.yaml / compose.test.yaml | 開發與測試隔離、volume 與 tmpfs |

## 常見追問

**為何不能先查剩一名，再直接報名？** 兩筆交易可能同時讀到 1，各自判斷可報，最後新增兩筆報名。單純程式 if 不會讓多交易互斥。

**FOR UPDATE 做什麼？** 對讀到的 event row 取得鎖，其他需要修改或鎖同一列的交易要等到本交易結束。之後再看有效報名與名額，依序決定能否寫入。普通 SELECT 仍可讀取已提交狀態。

**為何名額與報名要在同一交易？** 避免扣完名額但插入失敗造成名額遺失；取消也必須把改狀態與還名額一起提交。

**unique index 已經夠了嗎？** 不夠；只能阻擋同一人重複 active，不能阻擋不同人超收。反過來，只鎖名額也應保留 DB 層重複約束作為防線。

**取消後如何重報？** 舊紀錄改 cancelled，新增另一筆 active。partial unique 只限制 active，不會攔住取消歷史。

**代價是什麼？** 同一熱門活動的修改會排隊等待鎖；我選擇容易理解與驗證的方案，沒有做高負載 benchmark，所以不宣稱特定吞吐量。

**測試真的送外部 HTTP 嗎？** demo 透過本機 HTTP；pytest 並發使用 ASGI TestClient 加上真實 PostgreSQL，會測交易競爭，但沒有量測 Uvicorn／網路吞吐量。

**如果要正式上線？** 需要認證授權、部署與祕密管理、監控、流量限制、分頁、故障處理與更多壓力測試；目前未實作。

## 三個容易混淆的詞

- Image：程式及依賴打包的模板；container：image 執行中的實例。
- Compose：管理這個專案的 API 和 DB 如何一起啟動。
- Migration：有版本紀錄的 schema 變更；不是備份資料，也不是啟動容器。
