import os
import google.generativeai as genai
from dotenv import load_dotenv

# 載入你的金鑰
load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

print("🔍 正在查詢你的專屬 AI 模型清單...")
print("-" * 30)

try:
    # 列出所有你可以用的模型
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ 支援的模型名稱： {m.name}")
except Exception as e:
    print(f"❌ 查詢失敗，請檢查金鑰是否正確：{e}")