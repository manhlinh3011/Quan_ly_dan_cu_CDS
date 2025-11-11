from services.gemini_service import GeminiService

def test_gemini_api():
    print("Test kết nối Google Gemini API:")
    print("-" * 50)
    
    # Test case phản ánh nghiêm trọng
    title = "Phản ánh tình trạng bạo lực học đường"
    content = """Tại trường THCS XYZ đang xảy ra tình trạng học sinh bị bạo lực, đe dọa và bắt nạt nghiêm trọng, ảnh hưởng đến sức khỏe tinh thần và thể chất của nhiều em."""
    
    # Khởi tạo service
    service = GeminiService()
    
    # Gọi API phân tích
    result = service.analyze_feedback(title, content)
    
    if result:
        print(f"\nKết quả phân tích:")
        print(f"Mức độ nghiêm trọng: {result['severity'].upper()}")
        print(f"Độ tin cậy: {result['confidence']:.2f}")
        print(f"Lý do: {result['reason']}")
    else:
        print("\nLỗi: Không thể kết nối Google Gemini API. Vui lòng kiểm tra:")
        print("1. File config/api_config.json đã được tạo")
        print("2. API key đã được cấu hình đúng")

if __name__ == "__main__":
    test_gemini_api()