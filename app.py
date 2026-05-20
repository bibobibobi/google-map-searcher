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
    2. 如果沒有詳細地址，"address" 請填入城市或商圈 (例如：東京表參道)，這對精準搜尋很重要。
    3. 絕對不要加上 ```json 等 Markdown 標記，也不要任何問候語，只要純 JSON 文字！
    4. 如果完全沒有實體地點，請回傳空陣列 []。

    範例格式：
    [
      {"name": "afternoon tea love and table", "address": "東京表參道"},
      {"name": "うどん 慎", "address": "東京新宿"}
    ]
    
    貼文綜合資訊如下：
    ---
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
    """
    輸入店名與地址，回傳編碼後的 Google Maps 搜尋連結
    """
    search_keyword = f"{name} {address}".strip()
    encoded_keyword = urllib.parse.quote(search_keyword)
    return f"[https://www.google.com/maps/search/?api=1&query=](https://www.google.com/maps/search/?api=1&query=){encoded_keyword}"


# ==========================================
# 處理Instagram
# ==========================================
def handle_instagram(user_text):
    match = re.search(r'/(?:p|reel|reels)/([^/?#&]+)', user_text)
    if not match:
        return "IG 網址格式錯誤，找不到代碼。"
        
    clean_url = user_text.split('?')[0] 
    api_url = "[https://instagram-looter2.p.rapidapi.com/post](https://instagram-looter2.p.rapidapi.com/post)" 
    querystring = {"url": clean_url} 
    
    headers = {
        "x-rapidapi-key": os.getenv('RAPIDAPI_KEY'),
        "x-rapidapi-host": "instagram-looter2.p.rapidapi.com", 
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(api_url, headers=headers, params=querystring)
        json_data = response.json()
        
        caption = ""
        if "edge_media_to_caption" in json_data:
            edges = json_data.get("edge_media_to_caption", {}).get("edges", [])
            if edges:
                caption = edges[0].get("node", {}).get("text", "")
        
        location_data = json_data.get("location", {})
        extracted_place = extract_location_with_ai(caption)
        
        # JSON 解析與網址生成
        if extracted_place and extracted_place != "[]":
            try:
                places = json.loads(extracted_place)
                reply_text = "🤖 AI 為您找到以下地點：\n\n"
                for p in places:
                    name, address = p.get("name", ""), p.get("address", "")
                    maps_url = generate_google_maps_link(name, address)
                    reply_text += f"🍽️ {name}\n📍 {address}\n🗺️ 導航：\n{maps_url}\n\n"
                return reply_text
            except json.JSONDecodeError:
                return "🤖 AI 回傳格式異常，無法產生連結。"
        elif location_data and location_data.get('name'):
            name = location_data['name']
            maps_url = generate_google_maps_link(name, "")
            return f"📍 從 IG 打卡地標找到：\n🍽️ {name}\n🗺️ 導航：\n{maps_url}"
        else:
            return "🤖 貼文好像沒有提到具體實體店面。"
            
    except Exception as e:
        print(f"IG API Error: {e}")
        return "IG 爬蟲發生錯誤，請檢查網路或 API 額度。"


# ==========================================
# 處理Threads
# ==========================================
def handle_threads(user_text):
    match = re.search(r'/post/([^/?#&]+)', user_text)
    if not match:
        return "Threads 網址格式錯誤，找不到代碼。"
        
    thread_code = match.group(1)
    api_url = "[https://threadsscraper.p.rapidapi.com/thread-comments](https://threadsscraper.p.rapidapi.com/thread-comments)"
    querystring = {"thread_code": thread_code, "map_replies": "0"}
    
    headers = {
        "x-rapidapi-key": os.getenv('RAPIDAPI_KEY'),
        "x-rapidapi-host": "threadsscraper.p.rapidapi.com",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(api_url, headers=headers, params=querystring)
        items = response.json().get('data', [])
        
        if not items:
            return "Threads 爬蟲找不到貼文資料或 API 失效。"
            
        main_post = items[0]
        main_text = main_post.get('caption', {}).get('text', '無主文')
        ocr_text = main_post.get('accessibility_caption', '')
        ocr_text = f"【圖片辨識】\n{ocr_text}\n\n" if ocr_text else ""
        
        comments_text = "".join([f"- {i.get('user', {}).get('username', '匿名')}: {i.get('caption', {}).get('text', '')}\n" for i in items[1:] if i.get('caption', {}).get('text', '')])
        
        combined_info = f"【主文】\n{main_text}\n\n{ocr_text}【留言區】\n{comments_text}"
        extracted_place = extract_location_with_ai(combined_info)
        
        if extracted_place and extracted_place != "[]":
            try:
                places = json.loads(extracted_place)
                reply_text = "🤖 AI 為您找到以下地點：\n\n"
                for p in places:
                    name, address = p.get("name", ""), p.get("address", "")
                    maps_url = generate_google_maps_link(name, address)
                    reply_text += f"🍽️ {name}\n📍 {address}\n🗺️ 導航：\n{maps_url}\n\n"
                return reply_text
            except json.JSONDecodeError:
                return "🤖 AI 回傳格式異常，無法產生連結。"
        else:
            return "🤖 貼文好像沒有提到具體實體店面。"
            
    except Exception as e:
        print(f"Threads API Error: {e}")
        return "Threads 爬蟲發生網路錯誤。"


# ==========================================
# 處理Facebook
# ==========================================
def handle_facebook(user_text):
    match = re.search(r'(https?://[^\s]+(?:facebook\.com|fb\.com|fb\.watch)[^\s]+)', user_text)
    if not match:
        return "雖然看起來像 FB，但找不到完整的有效網址喔。"
        
    fb_url = match.group(1)
    
    api_url = "https://facebook-scraper-api4.p.rapidapi.com/get_facebook_post_details" 
    querystring = {"link": fb_url} 
    
    headers = {
        "x-rapidapi-key": os.getenv('RAPIDAPI_KEY'),
        "x-rapidapi-host": "facebook-scraper-api4.p.rapidapi.com", 
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(api_url, headers=headers, params=querystring)
        # 注意：你的 API 回傳的是一個 List，所以要抓 [0]
        data_list = response.json()
        
        if not data_list or len(data_list) == 0:
            return "FB 爬蟲找不到這篇貼文資料。"
            
        post_data = data_list[0]
        # 根據你的 JSON，內容藏在 values -> text
        fb_text = post_data.get('values', {}).get('text', '')
        
        if not fb_text:
            return "這篇貼文沒有文字內容，AI 無法分析。"
            
        combined_info = f"【Facebook 貼文】\n{fb_text}"
        extracted_place = extract_location_with_ai(combined_info)
        
        # 解析 AI 結果
        if extracted_place and extracted_place != "[]":
            try:
                places = json.loads(extracted_place)
                reply_text = "🤖 AI 為您找到以下地點：\n\n"
                for p in places:
                    name, address = p.get("name", ""), p.get("address", "")
                    maps_url = generate_google_maps_link(name, address)
                    reply_text += f"🍽️ {name}\n📍 {address}\n🗺️ 導航：\n{maps_url}\n\n"
                return reply_text
            except json.JSONDecodeError:
                return "🤖 AI 回傳格式異常，無法產生連結。"
        else:
            return "🤖 這篇 FB 貼文好像沒有提到具體實體店面。"
            
    except Exception as e:
        print(f"FB API Error: {e}")
        return "Facebook 爬蟲發生網路錯誤，或 API 額度用盡。"


# ==========================================
# 🌐 LINE Webhook
# ==========================================
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


# ==========================================
# 🤖 處理使用者訊息 (總機 Router)
# ==========================================
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_text = event.message.text
    reply_text = ""

    print(f"📥 收到來自使用者的訊息：{user_text}")
    
    # 根據網址特徵，將工作分派給對應的平台處理員
    if "instagram.com" in user_text:
        reply_text = handle_instagram(user_text)
        
    elif "threads.net" in user_text or "threads.com" in user_text:
        reply_text = handle_threads(user_text)
        
    elif "facebook.com" in user_text or "fb.com" in user_text or "fb.watch" in user_text:
        reply_text = handle_facebook(user_text)
        
    else:
        # 如果不是三大平台，直接結束處理
        return

    # 📤 將最終結果回傳給 LINE 使用者
    if reply_text:
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)