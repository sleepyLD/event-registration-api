# Event Registration API

使用 **FastAPI + PostgreSQL** 建立的小型限額活動報名 API。展示基本 REST API、資料驗證、Migration、交易與自動化測試。

這是範圍有限的後端練習／面試展示專案，使用 AI 協助開發。不包含前端、登入、付款或正式營運所需的授權機制。

## 功能

- 建立測試使用者、建立及查詢活動。
- 報名、取消、取消後重新報名，保留取消歷史。
- 額滿及重複報名回傳 409；不存在資源回傳 404；非法輸入回傳 422。
- PostgreSQL row lock + transaction 保護名額，partial unique index 防止重複有效報名。
- Alembic 管理三張資料表；Docker Compose 提供本機啟動與隔離測試。

## 快速啟動

需要 Python 3.11+（只用來產生本機設定、執行 demo）及已啟動的 Docker Desktop。以下指令都在 clone 後的 repository 根目錄執行。

~~~powershell
python scripts/init_env.py
docker compose up --build -d
docker compose exec -T api alembic upgrade head
~~~

開啟 [Swagger UI](http://localhost:8000/docs)，或 [健康檢查](http://localhost:8000/health)。

~~~powershell
python scripts/demo.py
~~~

Demo 會建立兩位使用者與容量 1 的活動，展示「報名成功 → 第二人額滿 → 取消 → 第二人成功」。資料會保留，重跑會新增另一組資料。

~~~powershell
docker compose ps
docker compose logs --tail=100 api
docker compose stop
docker compose up -d
~~~

第一次與程式變更後使用 up --build -d；日常重啟可用 up -d。Migration 須明確執行，不由每個 API worker 自動建表。stop 保留資料，請勿為重啟而刪除 volume。

init_env.py 產生隨機密碼到 .env，已存在則保留；.env 不提交 Git，也不進入 Docker build context。已有 DB volume 時，直接更改 .env 不會同步修改資料庫密碼。API 僅綁定 127.0.0.1:8000，資料庫不發布 host port。

## API

| Method | Endpoint | 用途 |
|---|---|---|
| GET | /health | 檢查 DB 連線；正常 200，失敗 503 |
| POST | /users | 建立使用者 |
| POST | /events | 建立活動 |
| GET | /events | 活動列表 |
| GET | /events/{event_id} | 活動明細與剩餘名額 |
| POST | /events/{event_id}/registrations | 使用 user_id 報名 |
| GET | /events/{event_id}/registrations | 有效報名名單 |
| DELETE | /events/{event_id}/registrations/{user_id} | 取消報名 |

完整欄位與錯誤格式見 [API 合約](docs/specification.md)；執行中的 Swagger 可直接試操作。

## 測試

~~~powershell
python scripts/check_project.py
~~~

會建置測試 image，使用另一個 Compose project、另一個 PostgreSQL server 與獨立網路，結束後停止測試容器。測試 DB 使用 tmpfs，不清理或寫入開發 DB。資料清理 fixture 只允許指定 test database / role。

測試包含輸入驗證、循序報名與重報、資料庫 CHECK / FK / partial unique、Migration 升降版、交易回滾，以及 20 個請求競爭名額、重複報名／取消、混合操作。並發測試以多執行緒 TestClient 呼叫 ASGI app，使用真實 PostgreSQL 交易；不等同於外部 HTTP 高負載測試。

測試狀態及確切數量以 [驗證紀錄](docs/verification.md) 為準。GitHub Actions 設定會在 push / PR 執行同一組測試；尚未上傳前不宣稱雲端 CI 通過。

## 設計重點

~~~text
HTTP → FastAPI / Pydantic → registration service → SQLAlchemy → PostgreSQL
~~~

每次報名或取消先以 SELECT ... FOR UPDATE 鎖定活動，再於同一 transaction 內變更報名紀錄與剩餘名額。所有操作遵守相同鎖定順序；失敗時整筆 rollback。同活動的名額修改會依序進行，設計簡單但高競爭時會等待鎖。

交易完成後應滿足：0 ≤ remaining_slots ≤ capacity、active_count + remaining_slots = capacity，且同人同活動最多一筆 active。CHECK 保護單列數值；partial unique 保護重複有效報名；跨表計數一致性仍依賴交易，不能只靠 CHECK。

## 範圍與限制

- user_id 是測試身分，沒有認證或授權；不應直接部署為公開營運系統。
- 沒有前端、分頁、Redis、背景佇列、付款或效能數據；尚未完成原企畫書的完整 benchmark / baseline。
- 本機小規模並發測試通過也不能代表任意負載、網路故障與正式環境下的保證。
- image 使用可更新的 Python 3.11 / PostgreSQL 17 標籤；Python 套件版本已鎖定。
- 單一 PostgreSQL、同步 SQLAlchemy；不涉及跨服務一致性。

面試前閱讀 [複習筆記](docs/interview-notes.md)；上傳步驟見 [GitHub 發布](docs/publishing.md)。
