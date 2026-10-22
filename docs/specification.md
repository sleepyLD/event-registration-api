# API / Data Contract

本專案為精簡展示版；完整原始階段規劃保留在本機，不代表所有階段已完成。

## 共通規則

- JSON；UTC ISO 8601 時間；列表依 id 升冪，無分頁。
- name / title 去除首尾空白且不可為空，嚴格字串。capacity 嚴格整數 1–10000，user_id 嚴格正整數，拒絕額外 body 欄位。
- path id 是可轉換的正整數；不合法時 422。
- 成功寫入於 transaction commit 後回應；取消 204 無 body。

## Endpoints

| Method | Path | Input | Success |
|---|---|---|---|
| GET | /health | — | 200 {status: ok, database: ok}；實際 SELECT 1 |
| POST | /users | {name} | 201 {id, name, created_at} |
| POST | /events | {title, capacity} | 201 Event |
| GET | /events | — | 200 Event[] |
| GET | /events/{event_id} | event_id | 200 Event |
| POST | /events/{event_id}/registrations | {user_id} | 201 Registration |
| GET | /events/{event_id}/registrations | event_id | 200 Registration[]（僅 active） |
| DELETE | /events/{event_id}/registrations/{user_id} | IDs | 204 |

Event = {id, title, capacity, remaining_slots, created_at}。
Registration = {id, event_id, user_id, status, created_at, cancelled_at}。
active 的 cancelled_at 為 null；取消後不回傳已取消記錄，但 DB 保留該記錄。

## Errors

頂層 JSON：{"code":"EVENT_FULL","message":"Event full"}。以 status/code 判斷，message 不是穩定介面。

| HTTP | Code | 條件 |
|---|---|---|
| 404 | EVENT_NOT_FOUND | 活動不存在 |
| 404 | USER_NOT_FOUND | 使用者不存在 |
| 404 | REGISTRATION_NOT_FOUND | 無有效報名可取消 |
| 409 | ALREADY_REGISTERED | 已有有效報名 |
| 409 | EVENT_FULL | 無名額 |
| 422 | VALIDATION_ERROR | 輸入錯誤；附 details: [{loc, type, message}] |
| 500 | INTERNAL_ERROR | 非預期錯誤，完整 rollback，不回傳連線字串 |
| 503 | DATABASE_UNAVAILABLE | 僅 /health 的 DB 探測失敗 |

報名檢查順序：輸入 → event（鎖列）→ user → 已報名 → 額滿。取消檢查順序：輸入 → event（鎖列）→ user → 有效報名。

## Schema / Transaction

- users：integer PK、非空 name、TIMESTAMPTZ created_at。
- events：integer PK、非空 title、capacity 1–10000、remaining_slots 0–capacity、created_at。
- registrations：integer PK、FK event/user（RESTRICT）、status active/cancelled、created_at、cancelled_at。CHECK status 與 cancelled_at 相符。
- Partial unique index：(event_id,user_id) WHERE status='active'。
- 建立活動 remaining_slots=capacity。每次報名或取消先鎖 event，名額與 registration 在同一交易變動。
- 取消將舊紀錄改為 cancelled 並還一個名額；重報新增紀錄。錯誤不能消耗或重複釋放名額。
- 最終條件：0 ≤ remaining_slots ≤ capacity；active_count + remaining_slots = capacity；同 pair 最多一筆 active。

詳細 schema 見 app/models/__init__.py 及 Alembic migration。功能驗證範圍見 verification.md。
