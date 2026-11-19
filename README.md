# AI-Powered Restaurant Navigator
# AI 社群美食導航員 — LINE Bot

**Turn restaurant recommendations shared on social media into searchable Google Maps locations through a LINE Bot.**  
透過 LINE Bot，將社群平台上的美食分享內容轉換成可直接搜尋的 Google Maps 地點資訊。

## Project Overview｜專案介紹

Restaurant recommendations are often shared through social media posts, but the actual restaurant name or address may be difficult to identify from the original content.

This project was built to simplify that process. Users can share a supported social media post link with the LINE Bot, which retrieves the post content, uses Google Gemini to identify potential restaurant information, and generates Google Maps search links.

社群平台上經常有值得收藏的美食分享，但貼文不一定會清楚標示店名或地址，使用者還需要自行搜尋與比對。

本專案希望簡化這個過程。使用者只要將支援的社群貼文連結傳送給 LINE Bot，系統便會取得貼文文字內容，透過 Google Gemini 分析可能的店家資訊，再產生 Google Maps 搜尋連結。

## How It Works｜系統運作流程

1. **Receive a Link｜接收連結**  
   The user sends a supported social media post URL to the LINE Bot.  
   使用者將社群貼文連結傳送給 LINE Bot。

2. **Retrieve Post Content｜取得貼文內容**  
   The backend identifies the platform and retrieves the post text through the corresponding scraping API.  
   後端判斷貼文來源，並透過對應的第三方 API 取得貼文文字。

3. **AI Information Extraction｜AI 資訊擷取**  
   Google Gemini analyzes the retrieved text and extracts potential restaurant names and addresses in structured JSON format.  
   Google Gemini 分析取得的文字，並以 JSON 格式整理可能的店名與地址。

4. **Generate Map Links｜產生地圖連結**  
   The system encodes the extracted location information into Google Maps search URLs and sends the results back through LINE.  
   系統將店家資訊轉換成 Google Maps 搜尋網址，再透過 LINE 回傳結果。

## Key Features｜核心功能

- **Multi-platform Post Handling｜多平台貼文處理**
  - Supports Instagram, Threads, and Facebook post links.
  - 支援 Instagram、Threads 與 Facebook 貼文連結。

- **AI-powered Location Extraction｜AI 地點資訊擷取**
  - Uses Google Gemini to identify potential restaurant names and addresses from unstructured post text.
  - 使用 Google Gemini 從非結構化貼文文字中辨識可能的店名與地址。

- **Automated Google Maps Links｜自動產生地圖搜尋連結**
  - Converts extracted restaurant information into URL-encoded Google Maps search links.
  - 將擷取到的店家資訊轉換為 Google Maps 搜尋連結，減少手動搜尋步驟。

- **LINE Messaging Integration｜LINE Bot 整合**
  - Provides an accessible interface through LINE Messaging API.
  - 透過 LINE Messaging API，讓使用者直接在 LINE 中操作。

## System Architecture｜系統架構

```text
User
  |
  | Social Media Post URL
  v
LINE Messaging API
  |
  v
Flask Webhook
  |
  +---- Identify Platform
  |       |
  |       +---- Instagram Scraper API
  |       +---- Threads Scraper API
  |       +---- Facebook Scraper API
  |
  v
Retrieve Post Text
  |
  v
Google Gemini
  |
  | Structured JSON
  v
Extract Restaurant Name & Address
  |
  v
Generate Google Maps Search URL
  |
  v
LINE Bot Reply
```

## Technical Stack｜技術架構

| Category | Technologies |
|---|---|
| Backend | Python, Flask |
| Messaging | LINE Messaging API, line-bot-sdk |
| AI | Google Gemini API |
| External APIs | RapidAPI scraping services |
| Data Processing | JSON, Regular Expressions |
| Configuration | python-dotenv |
| HTTP Requests | Requests |

## Implementation Highlights｜開發重點

- **Third-party API Integration｜第三方 API 整合**  
  Integrated different scraping services to retrieve post content from multiple social media platforms.  
  整合不同的第三方爬取服務，依照貼文來源取得對應的文字內容。

- **AI-assisted Data Extraction｜AI 輔助資訊擷取**  
  Designed prompts to convert unstructured post text into structured JSON containing restaurant names and addresses.  
  設計 AI 提示詞，將非結構化貼文文字整理成包含店名與地址的 JSON 資料。

- **Automated Processing Workflow｜自動化處理流程**  
  Connected LINE webhooks, external APIs, AI processing, and Google Maps URL generation into one workflow.  
  將 LINE Webhook、外部 API、AI 資訊分析與 Google Maps 連結產生整合成完整流程。

## Environment Variables｜環境變數

Create a `.env` file in the project root and configure the following values:

```env
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret
GEMINI_API_KEY=your_gemini_api_key
RAPIDAPI_KEY=your_rapidapi_key
```

請勿將 `.env` 或任何 API 金鑰提交至公開 Repository。

## Getting Started｜本機執行

### 1. Clone the repository

```bash
git clone https://github.com/bibobibobi/google-map-searcher.git
cd google-map-searcher
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

macOS / Linux:

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file and fill in the required credentials listed above.

### 5. Start the Flask application

```bash
python app.py
```

To receive LINE webhook events during local development, the Flask application must be reachable through a public HTTPS endpoint, and the endpoint must be configured in the LINE Developers Console.

本機測試 LINE Webhook 時，需要讓 Flask 服務透過公開 HTTPS 網址被 LINE 存取，並在 LINE Developers Console 設定對應的 Webhook URL。

## Notes｜注意事項

- The service depends on external scraping APIs and Google Gemini API availability.
- Retrieved restaurant information should be verified before visiting, as AI extraction may not always be accurate.
- 本服務依賴第三方社群資料 API 與 Google Gemini API；AI 擷取結果可能不完全正確，實際前往前仍應確認店家資訊。

## What I Learned｜專案收穫

This project provided hands-on experience in integrating messaging platforms, external APIs, and generative AI into an automated information-processing workflow. It also involved handling unstructured text and transforming AI-generated results into practical location search links.

透過這個專案，我實際練習了訊息平台整合、第三方 API 串接、生成式 AI 應用，以及將非結構化文字轉換為可使用資訊的自動化流程。
