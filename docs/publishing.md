# GitHub 發布

建議 repository 名稱：**event-registration-api**

建議 Description：

> 使用 FastAPI 與 PostgreSQL 建立的限額活動報名 API，包含交易控制、資料庫遷移與自動化測試。

英文可用：

> A small FastAPI and PostgreSQL API for capacity-limited event registration, with transactions, migrations, and automated tests.

Topics：python、fastapi、postgresql、sqlalchemy、docker、pytest。

## 建立及上傳

1. 在 GitHub 建立 public repository，使用上述名稱與簡介；保持空白，不要在網站額外產生 README 或 .gitignore。
2. 在本機專案根目錄執行以下步驟。YOUR_USERNAME 換成自己的 GitHub 帳號。

~~~powershell
git status
# 如果尚未設定 Git 提交身分，使用自己的姓名及 GitHub noreply email：
git config user.name "YOUR_NAME"
git config user.email "YOUR_GITHUB_NOREPLY_EMAIL"
git commit -m "Build event registration API portfolio demo"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/event-registration-api.git
git push -u origin main
~~~

上傳前先確認 verification.md 的測試狀態、git diff --cached --stat，以及 .env 未在 staged 清單。不要直接 git add -f 整個資料夾。

本專案沒有內建 GitHub token，也不代填作者身分。首次 push 可能需要在瀏覽器登入。若想讓其他人明確知道可否重用程式，再自行選擇授權；目前沒有宣告開源 license。

上傳後 Actions 頁面需實際跑綠，才可以說 GitHub CI 通過。public repository 不是自動公開部署 API。
