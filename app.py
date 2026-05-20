import os
import re
import requests
import urllib.parse
import google.generativeai as genai
import json
from flask import Flask, request, abort
from linebot.exceptions import InvalidSignatureError
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# 初始化 LINE Bot 與 Gemini
configuration = Configuration(access_token=os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
api_client = ApiClient(configuration)
line_bot_api = MessagingApi(api_client)
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# ==========================================
# 🧠 AI 大腦：綜合情報分析儀
# ==========================================
def extract_location_with_ai(text_content):
    if not text_content or text_content.strip() == "":
        return None
        
    model = genai.GenerativeModel('gemini-3.1-flash-lite') 
    
    prompt = """
    你現在是一個專業的地圖資料萃取器。這篇貼文可能介紹了單一或多間不同的餐廳與景點。
    請找出所有被提及的實體店面或地標，並「嚴格」以 JSON 陣列 (JSON Array) 的格式回傳。
    
    規則：
    1. 每個地點必須包含 "name" (店名) 和 "address" (地址/區域) 兩個欄位。
    2. 如果沒有詳細地址，"address" 請填入城市或商圈 (例如：東京表參道)。
    3. 絕對不要加上 ```json 等 Markdown 標記，也不要任何問候語，只要純 JSON 文字！
    4. 如果完全沒有實體地點，請回傳空陣列 []。
    """
    
    try:
        response = model.generate_content(prompt + text_content)
        ai_result = response.text.strip().replace("```json", "").replace("```", "").strip()
        return ai_result
    except Exception as e:
        print(f"AI 判讀失敗：{e}")
        return None

# ==========================================
# 🗺️ 工具函式：產生 Google Maps 搜尋連結
# ==========================================
def generate_google_maps_link(name, address):
    # 使用標準 URL 編碼，這裡確保是純淨的網址
    search_keyword = f"{name} {address}".strip()
    encoded_keyword = urllib.parse.quote(search_keyword)
    return f"https://www.google.com/maps/search/?api=1&query={encoded_keyword}"

# ==========================================
# 📱 平台處理員 1：Instagram
# ==========================================
def handle_instagram(user_text):
    match = re.search(r'/(?:p|reel|reels)/([^/?#&]+)', user_text)
    if not match:
        return "IG 網址格式錯誤，找不到代碼。"
        
    clean_url = user_text.split('?')[0] 
    api_url = "https://instagram-looter2.p.rapidapi.com/post" 
    querystring = {"url": clean_url} 
    headers = {
        "x-rapidapi-key": os.getenv('RAPIDAPI_KEY'),
        "x-rapidapi-host": "instagram-looter2.p.rapidapi.com", 
        "Content-Type": "application/json"
    }
    
    try:
        # 加上 timeout 保護
        response = requests.get(api_url, headers=headers, params=querystring, timeout=10)
        json_data = response.json()
        caption = json_data.get("edge_media_to_caption", {}).get("edges", [{}])[0].get("node", {}).get("text", "")
        extracted_place = extract_location_with_ai(caption)
        
        if extracted_place and extracted_place != "[]":
            places = json.loads(extracted_place)
            reply_text = "🤖 AI 為您找到以下地點：\n\n"
            for p in places:
                maps_url = generate_google_maps_link(p.get("name"), p.get("address"))
                reply_text += f"🍽️ {p.get('name')}\n📍 {p.get('address')}\n🗺️ 導航：\n{maps_url}\n\n"
            return reply_text
        return "🤖 貼文好像沒有提到具體實體店面。"
    except Exception as e:
        print(f"IG Debug Error: {e}")
        return "IG 處理錯誤，請確認網址或 API 狀態。"

# ==========================================
# 📱 平台處理員 2：Threads
# ==========================================
def handle_threads(user_text):
    match = re.search(r'/post/([^/?#&]+)', user_text)
    if not match:
        return "Threads 網址格式錯誤。"
    
    api_url = "https://threadsscraper.p.rapidapi.com/thread-comments"
    querystring = {"thread_code": match.group(1), "map_replies": "0"}
    headers = {
        "x-rapidapi-key": os.getenv('RAPIDAPI_KEY'),
        "x-rapidapi-host": "threadsscraper.p.rapidapi.com"
    }
    
    try:
        response = requests.get(api_url, headers=headers, params=querystring, timeout=10)
        items = response.json().get('data', [])
        if not items: return "無法抓取貼文。"
        
        main_text = items[0].get('caption', {}).get('text', '')
        extracted_place = extract_location_with_ai(main_text)
        
        if extracted_place and extracted_place != "[]":
            places = json.loads(extracted_place)
            reply_text = "🤖 AI 為您找到以下地點：\n\n"
            for p in places:
                maps_url = generate_google_maps_link(p.get("name"), p.get("address"))
                reply_text += f"🍽️ {p.get('name')}\n🗺️ 導航：\n{maps_url}\n\n"
            return reply_text
        return "🤖 沒有找到實體地點。"
    except Exception as e:
        print(f"Threads Debug Error: {e}")
        return "Threads 處理錯誤。"

# ==========================================
# 📱 平台處理員 3：Facebook
# ==========================================
def handle_facebook(user_text):
    match = re.search(r'(https?://[^\s]+(?:facebook\.com|fb\.com|fb\.watch)[^\s]+)', user_text)
    if not match: return "無效的 FB 網址。"
    
    api_url = "https://facebook-scraper-api4.p.rapidapi.com/get_facebook_post_details" 
    querystring = {"link": match.group(1)} 
    headers = {
        "x-rapidapi-key": os.getenv('RAPIDAPI_KEY'),
        "x-rapidapi-host": "facebook-scraper-api4.p.rapidapi.com"
    }
    
    try:
        response = requests.get(api_url, headers=headers, params=querystring, timeout=10)
        data_list = response.json()
        
        # 加入簡單的防錯機制，避免 data_list 抓空導致 [0] 報錯
        if not data_list or len(data_list) == 0:
            return "FB 爬蟲找不到這篇貼文資料。"
            
        fb_text = data_list[0].get('values', {}).get('text', '')
        
        extracted_place = extract_location_with_ai(fb_text)
        if extracted_place and extracted_place != "[]":
            places = json.loads(extracted_place)
            reply_text = "🤖 AI 找到以下地點：\n\n"
            for p in places:
                maps_url = generate_google_maps_link(p.get("name"), p.get("address"))
                reply_text += f"🍽️ {p.get('name')}\n🗺️ 導航：\n{maps_url}\n\n"
            return reply_text
        return "🤖 沒有找到實體地點。"
    except Exception as e:
        print(f"FB Debug Error: {e}")
        return "FB 處理錯誤。"

# ==========================================
# 🌐 LINE Webhook & Router
# ==========================================
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try: handler.handle(body, signature)
    except InvalidSignatureError: abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_text = event.message.text
    if "instagram.com" in user_text: reply = handle_instagram(user_text)
    elif "threads.net" in user_text or "threads.com" in user_text: reply = handle_threads(user_text)
    elif "facebook.com" in user_text or "fb.com" in user_text: reply = handle_facebook(user_text)
    else: return

    line_bot_api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[TextMessage(text=reply)]))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)