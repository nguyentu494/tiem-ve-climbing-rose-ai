import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

class Gemini:
    def __init__(self):
        self.model = "gemini-2.5-flash-lite-preview-06-17"
        self.model_provider = "google_genai"
    def llm(self):
        return init_chat_model(
            model=self.model,
            model_provider=self.model_provider,
            temperature=0.3,            
        )
    

# def test_connection():
#     chat = Gemini().llm()
#     response = chat.invoke("Xin chào, bạn có hoạt động không?")
#     print("✅ Kết nối thành công! Phản hồi từ model:")
#     print(response.content)

# if __name__ == "__main__":
#     test_connection()

    