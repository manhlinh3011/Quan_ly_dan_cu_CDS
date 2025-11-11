import os
import openai
import json
from typing import Dict, Optional
import logging

class OpenAIService:
    def __init__(self):
        # Đọc API key từ file cấu hình
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'api_config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.api_key = config.get('openai', {}).get('api_key')
        except Exception as e:
            logging.error(f"Không thể đọc file cấu hình API: {str(e)}")
            self.api_key = None
            
        # Cập nhật API key mới
        if not self.api_key:
            logging.warning("OpenAI API key chưa được cấu hình trong config/api_config.json")
            self.api_key = None
            
        openai.api_key = self.api_key
        
    def analyze_feedback(self, title: str, content: str) -> Optional[Dict]:
        """Phân tích phản ánh/khiếu nại sử dụng OpenAI API"""
        if not self.api_key:
            return None
            
        try:
            # Tạo prompt để phân tích
            system_prompt = """Bạn là một chuyên gia phân tích phản ánh, khiếu nại của người dân. 
Nhiệm vụ của bạn là phân tích mức độ nghiêm trọng của vấn đề dựa trên các tiêu chí:

1. Mức độ nghiêm trọng (severity):
- HIGH: Ảnh hưởng đến tính mạng, sức khỏe; vi phạm pháp luật nghiêm trọng; tham nhũng; 
        ô nhiễm nghiêm trọng; ảnh hưởng đến nhiều người; cần giải quyết khẩn cấp
- MEDIUM: Cơ sở hạ tầng hư hỏng; vệ sinh môi trường; trật tự đô thị; 
          dịch vụ công chậm trễ; tiện ích gián đoạn
- LOW: Vấn đề nhỏ, cá nhân, không gấp

2. Lý do phân loại: Giải thích ngắn gọn lý do phân loại mức độ nghiêm trọng

Trả về kết quả theo định dạng JSON:
{
    "severity": "HIGH/MEDIUM/LOW",
    "confidence": 0.7-0.95,
    "reason": "Lý do phân loại..."
}"""

            user_prompt = f"""Tiêu đề: {title}
Nội dung: {content}

Hãy phân tích mức độ nghiêm trọng của phản ánh/khiếu nại trên."""

            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Chuẩn hóa kết quả
            result['severity'] = result['severity'].lower()
            result['confidence'] = float(result['confidence'])
            
            logging.info(f"OpenAI API response: {json.dumps(result, ensure_ascii=False)}")
            
            return result
            
        except Exception as e:
            logging.error(f"OpenAI API error: {str(e)}")
            return None