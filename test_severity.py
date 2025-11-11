from services.feedback_classifier import FeedbackClassifier

# Khởi tạo classifier
classifier = FeedbackClassifier()

# Test các trường hợp với mức độ khác nhau
test_cases = [
    # Mức độ cao
    {
        "title": "Tai nạn nghiêm trọng do ổ gà",
        "description": "Đoạn đường có nhiều ổ gà sâu gây tai nạn nghiêm trọng, đã có người bị thương nặng phải nhập viện"
    },
    {
        "title": "Tình trạng ma túy trong khu dân cư",
        "description": "Có nhóm đối tượng tụ tập sử dụng và buôn bán ma túy, gây hoang mang cho cả khu vực"
    },
    # Mức độ trung bình
    {
        "title": "Rác thải tập kết không đúng nơi quy định",
        "description": "Khu vực chợ có tình trạng vứt rác bừa bãi, gây mất vệ sinh"
    },
    {
        "title": "Đường xuống cấp cần sửa chữa",
        "description": "Mặt đường bị xuống cấp, nhiều ổ gà gây khó khăn cho việc đi lại"
    },
    # Mức độ thấp
    {
        "title": "Cần lắp thêm đèn đường",
        "description": "Đề xuất lắp thêm đèn chiếu sáng tại ngõ 123 để thuận tiện đi lại"
    },
    {
        "title": "Đề nghị cắt tỉa cây xanh",
        "description": "Cành cây trước nhà hơi rậm rạp, mong được cắt tỉa gọn gàng"
    }
]

print("Test kết quả phân loại mức độ nghiêm trọng:\n")
for case in test_cases:
    print(f"Input:")
    print(f"- Tiêu đề: {case['title']}")
    print(f"- Nội dung: {case['description']}")
    
    result = classifier.classify(case['title'], case['description'])
    
    print("\nKết quả phân loại:")
    print(f"- Loại: {result['label']}")
    print(f"- Mức độ: {result['severity']}")
    print(f"- Độ tin cậy (phân loại): {result['confidence']:.2%}")
    print(f"- Độ tin cậy (mức độ): {result['severity_confidence']:.2%}")
    print("\n" + "-"*50 + "\n")