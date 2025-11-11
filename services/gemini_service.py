import os
import json
import logging
from typing import Dict, Optional
import google.generativeai as genai

class GeminiService:
    def __init__(self):
        # Đọc API key từ file cấu hình
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'api_config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.api_key = config.get('google', {}).get('api_key')
        except Exception as e:
            logging.error(f"Không thể đọc file cấu hình API: {str(e)}")
            self.api_key = None
            
        if not self.api_key or self.api_key == "YOUR_GEMINI_API_KEY_HERE":
            logging.warning("Google Gemini API key chưa được cấu hình trong config/api_config.json")
            self.api_key = None
        else:
            genai.configure(api_key=self.api_key)
            
    def analyze_feedback(self, title: str, content: str) -> Optional[Dict]:
        """Phân tích phản ánh/khiếu nại sử dụng Google Gemini API"""
        if not self.api_key:
            return None
        try:
            # Tạo prompt để phân tích
            system_prompt = """Bạn là một chuyên gia phân tích phản ánh, khiếu nại của người dân. 
Nhiệm vụ của bạn là phân loại mức độ nghiêm trọng của vấn đề theo 3 mức:
- cao: Ảnh hưởng đến tính mạng, sức khỏe; vi phạm pháp luật nghiêm trọng; tham nhũng; ô nhiễm nghiêm trọng; ảnh hưởng đến nhiều người; cần giải quyết khẩn cấp
- bình thường: Cơ sở hạ tầng hư hỏng; vệ sinh môi trường; trật tự đô thị; dịch vụ công chậm trễ; tiện ích gián đoạn
- thấp: Vấn đề nhỏ, cá nhân, không gấp

2. Lý do phân loại: Giải thích ngắn gọn lý do phân loại mức độ

Trả về kết quả theo định dạng JSON:
{
    "severity": "cao/binh_thuong/thap",
    "confidence": 0.7-0.95,
    "reason": "Lý do phân loại..."
}"""

            user_prompt = f"""Tiêu đề: {title}
Nội dung: {content}

Hãy phân loại mức độ nghiêm trọng của phản ánh/khiếu nại trên."""

            # Khởi tạo model
            model = genai.GenerativeModel('models/gemini-2.5-pro')
            
            # Gọi API
            prompt = f"{system_prompt}\n\n{user_prompt}"
            response = model.generate_content(prompt)
            # Lấy kết quả trả về từ Gemini API
            if hasattr(response, 'text') and response.text:
                raw_output = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                raw_output = response.candidates[0].content.parts[0].text
            else:
                logging.error("Gemini API trả về kết quả rỗng hoặc không hợp lệ.")
                return None
            # Tìm phần JSON trong kết quả trả về
            raw_output = raw_output.strip()
            json_start = raw_output.find('{')
            json_end = raw_output.rfind('}')
            if json_start != -1 and json_end != -1:
                json_str = raw_output[json_start:json_end+1]
            else:
                logging.error(f"Không tìm thấy JSON hợp lệ trong output: {raw_output}")
                return None
            try:
                result = json.loads(json_str)
                # Chuẩn hóa lại nhãn mức độ
                confidence = float(result['confidence']) * 100 if result['confidence'] <= 1 else float(result['confidence'])
                if confidence < 70:
                    result['severity'] = 'thap'
                elif confidence < 90:
                    result['severity'] = 'binh_thuong'
                else:
                    result['severity'] = 'cao'
                result['confidence'] = confidence
                logging.info(f"Gemini API response: {json.dumps(result, ensure_ascii=False)}")
                return result
            except Exception as e:
                logging.error(f"Lỗi khi parse JSON từ Gemini API: {str(e)}. Output: {json_str}")
                return None
        except Exception as e:
            logging.error(f"Gemini API error: {str(e)}")
            return None

    @staticmethod
    def list_available_models():
        """Liệt kê các model khả dụng từ Gemini API"""
        import google.generativeai as genai
        import os, json
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'api_config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                api_key = config.get('google', {}).get('api_key')
            genai.configure(api_key=api_key)
            models = genai.list_models()
            print("Các model khả dụng từ Gemini API:")
            for m in models:
                print(f"- {m.name}")
        except Exception as e:
            print(f"Lỗi khi lấy danh sách model: {e}")