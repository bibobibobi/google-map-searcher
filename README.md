#  AI 社群美食導航員 (AI-Powered Restaurant Navigator Line Bot)

## 專案簡介 (Introduction)
這是一個基於 Python 與 Flask 開發的 LINE Bot 應用程式。
旨在解決社群媒體（Instagram, Threads）上美食貼文資訊碎片化、缺乏明確地址的痛點。透過整合社群平台 API 與 Google Gemini AI 模型，系統能自動從貼文的非結構化文字與圖片 OCR 辨識內容中，精準萃取實體店面資訊，並直接生成 Google Maps 導航連結。

## 核心功能 (Features)
* **多平台網址解析**：支援自動識別並解析 Instagram (Posts/Reels) 與 Threads 的貼文網址。
* **跨平台 API 整合**：透過 RapidAPI 介接第三方爬蟲服務，獲取貼文詳細資料，並能挖出隱藏在圖片無障礙標籤 (Accessibility Captions) 中的地標資訊。
* **LLM 智慧資料萃取**：導入 Google Gemini 2.5 Flash 模型，將散落的碎化資訊（如：城市、店名片段、留言補充）進行 NLP 分析，精準重組出完整的地標名稱。
* **即時地圖導航**：自動生成經過 URL Encoding 的安全 Google Maps 搜尋連結，解決通訊軟體斷開特殊字元網址的問題。

## 技術棧 (Tech Stack)
* **後端開發**: Python 3, Flask
* **平台串接**: LINE Messaging API
* **AI 與資料處理**: Google Generative AI (Gemini SDK), JSON Parsing, 正規表達式 (Regex), RESTful API Integration
