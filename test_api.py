from services.openai_service import OpenAIService

def test_api():
    service = OpenAIService()
    
    # Test cases
    test_cases = [
        {
            "title": "Phản ánh tình trạng bạo lực học đường",
            "content": "Tại trường THCS XYZ đang xảy ra tình trạng học sinh bị bạo lực, đe dọa và bắt nạt nghiêm trọng, ảnh hưởng đến sức khỏe tinh thần và thể chất của nhiều em."
        },
        {
            "title": "Rác thải tồn đọng tại khu chợ",
            "content": "Khu vực chợ ABC có tình trạng rác thải không được thu gom kịp thời, gây mùi hôi và mất vệ sinh."
        }
    ]
    
    print("Test kết nối OpenAI API:")
    print("-" * 50)
    
    for case in test_cases:
        print(f"\nTiêu đề: {case['title']}")
        print(f"Nội dung: {case['content']}")
        
        result = service.analyze_feedback(case['title'], case['content'])
        
        if result:
            print("\nKết quả phân tích:")
            print(f"- Mức độ nghiêm trọng: {result['severity']}")
            print(f"- Độ tin cậy: {result['confidence']:.2%}")
            print(f"- Lý do: {result['reason']}")
        else:
            print("\nLỗi: Không thể kết nối OpenAI API. Vui lòng kiểm tra:")
            print("1. File config/api_config.json đã được tạo")
            print("2. API key đã được cấu hình đúng")
            break
            
        print("-" * 50)

if __name__ == '__main__':
    test_api()