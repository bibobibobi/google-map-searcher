# Google Map Searcher｜AI 社群美食導航員

一個結合 LINE Bot 與 Google Gemini 的 AI 美食搜尋工具，協助使用者從 Instagram、Threads 等社群貼文中擷取店家資訊，並快速轉換成 Google Maps 搜尋連結。

## 專案背景

在社群平台上，許多美食推薦資訊以貼文或留言形式呈現，使用者即使看到感興趣的店家，也可能需要自行搜尋店名、確認地址，再切換到地圖查找位置。

因此，我規劃並開發這個 LINE Bot，整合社群資料擷取服務與生成式 AI，將原本需要手動處理的搜尋流程自動化。

## 核心功能

- **LINE Bot 操作介面**：透過 LINE 傳送社群貼文連結，即可啟動資訊解析流程。
- **多平台貼文解析**：支援 Instagram、Threads 與 Facebook 貼文連結。
- **社群資料擷取**：透過 RapidAPI 串接不同平台的資料擷取服務，取得貼文文字內容。
- **AI 店家資訊辨識**：使用 Google Gemini 分析非結構化貼文內容，擷取可能的店家名稱與地址。
- **Google Maps 搜尋連結**：將辨識結果轉換為 Google Maps 搜尋網址，方便使用者查看店家位置。

## 系統流程

```text
使用者傳送社群貼文連結
          │
          ▼
       LINE Bot
          │
          ▼
    Flask Webhook
          │
          ▼
   判斷貼文來源平台
          │
          ▼
  RapidAPI 擷取貼文內容
          │
          ▼
  Google Gemini 分析文字
          │
          ▼
   擷取店家名稱與地址
          │
          ▼
   產生 Google Maps 連結
          │
          ▼
      回傳 LINE
```

## 技術架構

| 項目 | 使用技術 |
|---|---|
| 後端 | Python、Flask |
| Bot 平台 | LINE Messaging API |
| AI 模型 | Google Gemini |
| 外部 API | RapidAPI |
| HTTP 請求 | Requests |
| 資料格式 | JSON |
| 環境設定 | python-dotenv |

## 開發重點

### 1. 多平台 API 整合

不同社群平台具有不同的資料結構與 API 介面，因此針對 Instagram、Threads 及 Facebook 分別串接對應的 RapidAPI 服務，將不同來源的貼文內容整合至後續處理流程。

### 2. 使用生成式 AI 處理非結構化資料

社群貼文中的店家資訊不一定具有固定格式，可能散落在描述文字或其他上下文中。透過 Google Gemini 分析取得的貼文文字，要求模型以 JSON 格式回傳店家名稱及地址，讓後續程式能以結構化資料處理辨識結果。

### 3. 自動產生地圖搜尋連結

將 AI 擷取出的店家名稱與地址進行 URL 編碼，再組合成 Google Maps 搜尋網址，降低使用者從社群內容切換到地圖搜尋的操作成本。

### 4. LINE Webhook 整合

使用 Flask 建立 LINE Webhook 接收端點，處理使用者傳入的訊息及貼文連結，依照來源平台執行對應的資料擷取與 AI 分析流程，最後將結果回傳至 LINE。

## 環境設定

程式啟動時使用 `python-dotenv` 的 `load_dotenv()` 載入專案中的 `.env`；既有程序環境變數優先於 `.env` 中的值。請由範例建立自己的設定，並填入金鑰：

```bash
cp .env.example .env
```

| 環境變數 | 用途 |
|---|---|
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Bot 存取權杖 |
| `LINE_CHANNEL_SECRET` | LINE Webhook 驗證 |
| `GEMINI_API_KEY` | Google Gemini API |
| `RAPIDAPI_KEY` | RapidAPI 存取金鑰 |
| `APP_HOST` | Flask 監聽位址，預設 `127.0.0.1` |
| `APP_PORT` | Flask 監聽埠，預設 `5000` |

請勿提交 `.env`，也不要在 `.env.example` 填入真實金鑰。正式環境使用同機 Nginx 反向代理時，建議保留 `127.0.0.1:5000`，並避免對外開放 5000 埠。

## 本機執行

需要 Python 3、LINE Messaging API Channel、Google Gemini API Key 及 RapidAPI Key。

```bash
git clone https://github.com/bibobibobi/google-map-searcher.git
cd google-map-searcher
python -m venv venv
```

啟用虛擬環境：

```bash
# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

安裝套件並在設定 `.env` 後啟動：

```bash
pip install -r requirements.txt
python app.py
```

預設監聽 `http://127.0.0.1:5000`。例如在 macOS / Linux 暫時改用 5050 埠：

```bash
APP_HOST=127.0.0.1 APP_PORT=5050 python app.py
```

Windows PowerShell 可使用：

```powershell
$env:APP_HOST = '127.0.0.1'
$env:APP_PORT = '5050'
python app.py
```

LINE Webhook URL 需指向可公開存取的 `/callback` 端點，才能接收 LINE 訊息。

## Oracle Cloud 部署

正式環境為 Ubuntu 22.04，專案位於 `/home/ubuntu/google-map-searcher`，由 `linebot.service` 執行。Nginx 設定位於 `/etc/nginx/sites-available/linebot`，將 `/callback` 轉送至 `http://127.0.0.1:5000`。

1. 依既有發布流程更新專案檔案與依賴套件。
2. 將金鑰保留在私有 `.env`，或透過 systemd 的 `EnvironmentFile=` 提供；確認服務的 `APP_HOST=127.0.0.1`、`APP_PORT=5000` 與 Nginx 上游一致。
3. 確認 `/callback` 的 Nginx 上游設定為 `proxy_pass http://127.0.0.1:5000;`。
4. 在預定維護時段檢查設定、重啟服務並查看狀態：

   ```bash
   sudo nginx -t
   sudo systemctl restart linebot.service
   sudo systemctl status linebot.service
   sudo journalctl -u linebot.service -n 100 --no-pager
   ```

目前 `app.run()` 使用 Flask 開發伺服器；loopback 綁定與 Nginx 代理可降低直接暴露，但正式環境仍建議未來改用 Gunicorn 或 uWSGI，搭配 systemd 管理程序，並保留 Nginx 處理 TLS 與反向代理。

## 實際畫面

### 使用者分享貼文連結

<img src="https://github.com/user-attachments/assets/5fb1626c-41b0-4890-b9aa-d2b0a542943a" width="300">
<img src="https://github.com/user-attachments/assets/30f94d28-dda2-4ca1-981a-455fe8142481" width="300">

### LINE Bot 回傳 Google Maps 連結

<img src="https://github.com/user-attachments/assets/bc542c6c-6463-44f9-833b-4f2cf205ad4b" width="300">
<img src="https://github.com/user-attachments/assets/aa20fd14-e56a-4d97-ba20-6223692a2623" width="300">

## 專案開發方式

本專案由我負責產品構想、功能規劃、流程拆解及 API 整合，並運用 AI 協助逐步實作與調整。

開發過程中，我將原本需要使用者手動搜尋的流程拆解為貼文解析、資料擷取、AI 資訊辨識及地圖連結產生等階段，完成一個結合第三方 API 與生成式 AI 的自動化工具。
