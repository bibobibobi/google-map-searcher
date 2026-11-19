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

社群貼文中的店家資訊不一定具有固定格式，可能散落在描述文字或其他上下文中。

透過 Google Gemini 分析取得的貼文文字，要求模型以 JSON 格式回傳店家名稱及地址，讓後續程式能以結構化資料處理辨識結果。

### 3. 自動產生地圖搜尋連結

將 AI 擷取出的店家名稱與地址進行 URL 編碼，再組合成 Google Maps 搜尋網址，降低使用者從社群內容切換到地圖搜尋的操作成本。

### 4. LINE Webhook 整合

使用 Flask 建立 LINE Webhook 接收端點，處理使用者傳入的訊息及貼文連結，依照來源平台執行對應的資料擷取與 AI 分析流程，最後將結果回傳至 LINE。

## 環境設定

本專案需要以下 API 金鑰：

| 環境變數 | 用途 |
|---|---|
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Bot 存取權杖 |
| `LINE_CHANNEL_SECRET` | LINE Webhook 驗證 |
| `GEMINI_API_KEY` | Google Gemini API |
| `RAPIDAPI_KEY` | RapidAPI 存取金鑰 |

請建立 `.env` 檔案並填入自己的 API 金鑰：

```env
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret
GEMINI_API_KEY=your_gemini_api_key
RAPIDAPI_KEY=your_rapidapi_key
```

## 本機執行

### 環境需求

- Python 3
- LINE Messaging API Channel
- Google Gemini API Key
- RapidAPI Key

### 安裝依賴套件

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

安裝套件：

```bash
pip install -r requirements.txt
```

設定 `.env` 後，啟動 Flask：

```bash
python app.py
```

接著需設定 LINE Webhook URL 指向可公開存取的服務端點，才能接收 LINE 訊息。

## 專案開發方式

本專案由我負責產品構想、功能規劃、流程拆解及 API 整合，並運用 AI 協助逐步實作與調整。

開發過程中，我將原本需要使用者手動搜尋的流程拆解為貼文解析、資料擷取、AI 資訊辨識及地圖連結產生等階段，完成一個結合第三方 API 與生成式 AI 的自動化工具。
