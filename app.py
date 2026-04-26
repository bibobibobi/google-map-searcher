import os
import re
import requests
import urllib.parse
import google.generativeai as genai
from flask import Flask, request, abort
from linebot.exceptions import InvalidSignatureError
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from dotenv import load_dotenv

def get_threads_content(url):
    """
    這是一個專屬工具：負責把 Threads 網址變成給 AI 看的純文字情報包
    """
    # 1. 用正則表達式抓出乾淨的 thread_code (尋找 post/ 後面的英數字)
    match = re.search(r'post/([a-zA-Z0-9_-]+)', url)
    if not match:
        return None # 如果網址格式不對，就回傳空值
    
    thread_code = match.group(1) # 成功拿到乾淨的 DXjRbZbjzJV
    
    # 2. 呼叫 RapidAPI
    api_url = "https://threadsscraper.p.rapidapi.com/thread-comments"
    querystring = {"thread_code": thread_code, "map_replies": "0"}
    headers = {
        "x-rapidapi-key": os.getenv('RAPIDAPI_KEY'),
        "x-rapidapi-host": "threadsscraper.p.rapidapi.com"
    }
    
    try:
        response = requests.get(api_url, headers=headers, params=querystring)
        json_data = response.json()
        
        # 3. 整理 JSON (這是我們上一回合討論的邏輯)
        items = json_data.get('data', [])
        if not items:
            return "這篇貼文沒有內容或抓取失敗"
            
        main_text = items[0].get('caption', {}).get('text', '無主文')
        full_content = f"【Threads 主文】\n{main_text}\n\n"
        
        # 加入圖片隱藏描述 (如果有)
        accessibility_caption = items[0].get('accessibility_caption')
        if accessibility_caption:
            full_content += f"【圖片隱藏描述】\n{accessibility_caption}\n\n"
            
        # 加入留言區
        full_content += "【留言區】\n"
        for item in items[1:]:
            author = item.get('user', {}).get('username', '匿名')
            comment_text = item.get('caption', {}).get('text', '')
            if comment_text:
                full_content += f"- 網友 {author} 說: {comment_text}\n"
                
        return full_content # 完美回傳整理好的文字！

    except Exception as e:
        print(f"Threads 爬蟲發生錯誤: {e}")
        return None

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
        
    model = genai.GenerativeModel('gemini-3.1-flash-lite-preview') #RPD500
    
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
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_text = event.message.text
    reply_text = ""
    target_name = None
    
    # ---------------------------
    # 路線 A：Instagram 處理邏輯 50/month
    # ---------------------------
    if "instagram.com" in user_text:
        match = re.search(r'/(?:p|reel|reels)/([^/?#&]+)', user_text)
        if match:
            clean_url = user_text.split('?')[0] 
            api_url = "https://instagram-looter2.p.rapidapi.com/post" 
            querystring = {"url": clean_url} 
            
            headers = {
                "x-rapidapi-key": os.getenv('RAPIDAPI_KEY'), # 共用 .env 裡的金鑰
                "x-rapidapi-host": "instagram-looter2.p.rapidapi.com", 
                "Content-Type": "application/json"
            }
            try:
                response = requests.get(api_url, headers=headers, params=querystring)
                json_data = response.json()

                # 👇 加入這行！把 IG 的真實 JSON 印出來
                print(f"🐛 IG API 回傳真相: {json_data}")
                
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
    # 路線 B：Threads 升級版處理邏輯 (支援留言與圖片 OCR) 100/month
    # ---------------------------
    elif "threads.net" in user_text or "threads.com" in user_text:
        match = re.search(r'/post/([^/?#&]+)', user_text)
        if match:
            thread_code = match.group(1) # 拿到乾淨的 DXjRbZbjzJV
            
            # 👇 換成全新的 thread-comments API
            api_url = "https://threadsscraper.p.rapidapi.com/thread-comments"
            querystring = {"thread_code": thread_code, "map_replies": "0"}
            
            headers = {
                "x-rapidapi-key": os.getenv('RAPIDAPI_KEY'), # 共用 .env 裡的金鑰
                "x-rapidapi-host": "threadsscraper.p.rapidapi.com",
                "Content-Type": "application/json"
            }
            
            try:
                response = requests.get(api_url, headers=headers, params=querystring)
                json_data = response.json()

                # 👇 加入這行！把 Threads 的真實 JSON 印出來
                print(f"🐛 Threads API 回傳真相: {json_data}")
                
                items = json_data.get('data', [])
                
                if not items:
                    reply_text = "Threads 爬蟲找不到這篇貼文的資料或 API 失效。"
                else:
                    # 1. 抓取主文 (陣列的第一筆)
                    main_post = items[0]
                    main_text = main_post.get('caption', {}).get('text', '無主文')
                    
                    # 2. 抓取圖片隱藏描述 (如果有)
                    ocr_text = main_post.get('accessibility_caption', '')
                    if ocr_text:
                        ocr_text = f"【圖片辨識文字】\n{ocr_text}\n\n"
                    else:
                        ocr_text = ""
                        
                    # 3. 抓取留言區 (陣列的第二筆開始)
                    comments_text = ""
                    for item in items[1:]:
                        author = item.get('user', {}).get('username', '匿名')
                        comment = item.get('caption', {}).get('text', '')
                        if comment:
                            comments_text += f"- {author} 說: {comment}\n"
                    
                    # 4. 綜合情報大拌炒
                    combined_info = f"【Threads 主文】\n{main_text}\n\n{ocr_text}【留言區】\n{comments_text}"
                    print(f"--- 傳給 AI 的綜合情報 ---\n{combined_info}\n-----------------------")
                    
                    # 5. 交給 AI 大腦
                    extracted_place = extract_location_with_ai(combined_info)
                    if extracted_place:
                        target_name = extracted_place
                        reply_text = f"🤖 AI 從 Threads (含留言區) 找到：\n{target_name}"
                        
            except Exception as e:
                reply_text = "Threads 爬蟲發生網路錯誤。"
                print(f"API Error: {e}")
        else:
            reply_text = "Threads 網址格式錯誤，找不到代碼。"

    else:
        # 如果不是 IG 也不是 Threads，直接結束處理
        return
            

    # ==========================================
    # 🗺️ 產生地圖連結並回傳 (共用邏輯)
    # ==========================================
    if target_name:
        safe_target_name = urllib.parse.quote(target_name)
        google_map_url = f"https://www.google.com/maps/search/?api=1&query={safe_target_name}"
        reply_text += f"\n\n🗺️ 點擊導航：\n{google_map_url}"
    elif reply_text == "":
        reply_text = "這篇貼文好像沒有寫地址喔！"

    line_bot_api.reply_message(
        ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
        )
    )

if __name__ == "__main__":
    app.run(port=5000)