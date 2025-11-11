from services.feedback_classifier import FeedbackClassifier

# Khởi tạo classifier
classifier = FeedbackClassifier()

# Test một số trường hợp
test_cases = [
    {
        "title": "Phản ánh tình trạng ô nhiễm nghiêm trọng",
        "description": "Khu vực có mùi hôi thối, nhiều người dân bị ốm do ô nhiễm kéo dài"
    },
    {
        "title": "Khiếu nại thái độ phục vụ",
        "description": "Cán bộ thái độ không tốt khi tiếp nhận hồ sơ"
    },
    {
        "title": "Phản ánh về an ninh trật tự",
        "description": "Tình trạng đánh bạc và ma túy diễn ra công khai trong khu dân cư, gây hoang mang cho người dân"
    }
]

print("Test kết quả phân loại:\n")
for case in test_cases:
    print(f"Input:")
    print(f"- Tiêu đề: {case['title']}")
    print(f"- Nội dung: {case['description']}")
    
    result = classifier.classify(case['title'], case['description'])
    
    print("\nKết quả phân loại:")
    print(f"- Loại: {result['label']}")
    print(f"- Độ tin cậy: {result['confidence']:.2%}")
    print(f"- Từ khóa quan trọng: {', '.join(result['important_terms'])}")
    print(f"- Mức độ nghiêm trọng: {result['severity']}")
    print(f"- Độ tin cậy (mức độ): {result['severity_confidence']:.2%}")
    print("\n" + "-"*50 + "\n")