import os
import re
import requests
import urllib.parse
import google.generativeai as genai
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# 初始化 LINE Bot 與 Gemini
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# ==========================================
# 🧠 AI 大腦：綜合情報分析儀
# ==========================================
def extract_location_with_ai(text_content):
    if not text_content or text_content.strip() == "":
        return None
        
    model = genai.GenerativeModel('gemini-2.5-flash') # 使用你專屬的最新模型
    
    prompt = f"""
    你現在是一個精準的地圖資料萃取器。
    請從以下的社群貼文內容（包含內文與圖片辨識文字）中，尋找並萃取出「最完整、最精準的實體店面地址或地標名稱」。
    
    規則：
    1. 如果有地址跟店名，請把它們組合在一起（例如：台北市信義區信義路五段7號 台北101）。
    2. 如果只有店名與城市，也請組合在一起（例如：とくら 京都三条店）。
    3. 你的回答只能包含「地點資訊」本身，絕對「不要」加上任何其他的廢話、解釋、或是「好的」、「地址是」這種開場白。
    4. 如果這篇貼文裡面完全沒有提到任何實體地址或地標，請嚴格回傳「None」這四個英文字母。
    
    貼文綜合資訊如下：
    ---
    {text_content}
    """
    
    try:
        response = model.generate_content(prompt)
        ai_result = response.text.strip()
        
        if ai_result == "None" or not ai_result:
            return None
        return ai_result
    except Exception as e:
        print(f"AI 判讀失敗：{e}")
        return None

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
# 🤖 處理使用者訊息 (IG & Threads 路由)
# ==========================================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text
    reply_text = ""
    target_name = None
    
    # ---------------------------
    # 路線 A：Instagram 處理邏輯
    # ---------------------------
    if "instagram.com" in user_text:
        match = re.search(r'/(?:p|reel|reels)/([^/?#&]+)', user_text)
        if match:
            # 這裡我們不需要 shortcode，我們直接把使用者的整串網址傳給 API
            # 但保險起見，我們只取到 ? 前面的乾淨網址
            clean_url = user_text.split('?')[0] 
            
            # 👇 換成 instagram-looter2 的 API 網址
            api_url = "https://instagram-looter2.p.rapidapi.com/post" 
            
            # 👇 這家 API 要求的參數是 url
            querystring = {"url": clean_url} 
            
            headers = {
                "x-rapidapi-key": "f7ce5262dfmsh845803b7a42a4b9p1e0fdajsn97cd25aa76eb",
                # 👇 換成 instagram-looter2 的 Host
                "x-rapidapi-host": "instagram-looter2.p.rapidapi.com", 
                "Content-Type": "application/json"
            }
            try:
                # 發送請求
                response = requests.get(api_url, headers=headers, params=querystring)
                json_data = response.json()
                
                # 1. 精準抓取內文
                caption = ""
                if "edge_media_to_caption" in json_data:
                    edges = json_data.get("edge_media_to_caption", {}).get("edges", [])
                    if edges and len(edges) > 0:
                        caption = edges[0].get("node", {}).get("text", "")
                
                # 2. 精準抓取官方地標
                location_data = json_data.get("location", {})
                
                # 3. 交給 AI 判讀
                extracted_place = extract_location_with_ai(caption)
                if extracted_place:
                    target_name = extracted_place
                    reply_text = f"🤖 AI 從 IG 內文找到地址：\n{target_name}"
                elif location_data and location_data.get('name'):
                    target_name = location_data['name']
                    reply_text = f"📍 從 IG 打卡地標找到：\n{target_name}"
                    
            except Exception as e:
                reply_text = "IG 爬蟲發生錯誤，請檢查網路或 API 額度。"
                print(f"API Error: {e}")
        else:
            reply_text = "IG 網址格式錯誤，找不到代碼。"

    # ---------------------------
    # 路線 B：Threads 處理邏輯
    # ---------------------------
    elif "threads.net" in user_text or "threads.com" in user_text:
        match = re.search(r'/post/([^/?#&]+)', user_text)
        if match:
            web_id = match.group(1)
            api_url = "https://threads-by-meta-threads-an-instagram-app-detailed.p.rapidapi.com/get_post_with_web_id"
            querystring = {"web_id": web_id}
            headers = {
                "x-rapidapi-key": "f7ce5262dfmsh845803b7a42a4b9p1e0fdajsn97cd25aa76eb",
                "x-rapidapi-host": "threads-by-meta-threads-an-instagram-app-detailed.p.rapidapi.com",
                "Content-Type": "application/json"
            }
            try:
                response = requests.get(api_url, headers=headers, params=querystring)
                json_data = response.json()
                
                # 防呆機制：檢查 API 是否回傳錯誤
                if "error" in json_data or "errors" in json_data:
                     reply_text = "Threads 爬蟲發生錯誤，API 可能失效。"
                     print("API Error:", json_data)
                else:
                    post_info = json_data.get('post', {})
                    
                    # 1. 抓取主要文字內文
                    caption_text = post_info.get('caption', {}).get('text', '')
                    
                    # 2. 抓取圖片的無障礙說明 (隱藏在 carousel_media 或 image_versions2 裡)
                    ocr_text = ""
                    if 'carousel_media' in post_info and post_info['carousel_media']:
                        for item in post_info['carousel_media']:
                            if item.get('accessibility_caption'):
                                ocr_text += item['accessibility_caption'] + " "
                    elif 'accessibility_caption' in post_info and post_info['accessibility_caption']:
                         ocr_text = post_info['accessibility_caption']
                    
                    # 3. 綜合情報大拌炒
                    combined_info = f"內文：{caption_text}\n圖片辨識文字：{ocr_text}"
                    print(f"--- 傳給 AI 的綜合情報 ---\n{combined_info}\n-----------------------") # 方便你在終端機看抓到了什麼
                    
                    # 4. 交給 AI 大腦
                    extracted_place = extract_location_with_ai(combined_info)
                    if extracted_place:
                        target_name = extracted_place
                        reply_text = f"🤖 AI 從 Threads 綜合情報找到：\n{target_name}"
            except Exception as e:
                reply_text = "Threads 爬蟲發生網路錯誤。"
                print(e)
        else:
            reply_text = "Threads 網址格式錯誤，找不到代碼。"
            

    # ==========================================
    # 🗺️ 產生地圖連結並回傳 (共用邏輯)
    # ==========================================
    if target_name:
        safe_target_name = urllib.parse.quote(target_name)
        google_map_url = f"https://www.google.com/maps/search/?api=1&query={safe_target_name}"
        reply_text += f"\n\n🗺️ 點擊導航：\n{google_map_url}"
    elif reply_text == "":
        reply_text = "這篇貼文好像沒有寫地址喔！🥲"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    app.run(port=5000)