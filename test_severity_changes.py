from services.feedback_classifier import FeedbackClassifier

# Khởi tạo classifier
classifier = FeedbackClassifier()

# Test các trường hợp với mức độ khác nhau
test_cases = [
    # Mức độ cao với nhiều từ khóa (sẽ có độ tin cậy cao)
    {
        "title": "Tai nạn nghiêm trọng do ổ gà gây chết người",
        "description": "Đoạn đường có nhiều ổ gà sâu gây tai nạn nghiêm trọng, đã có người tử vong và nhiều người bị thương nặng phải nhập viện cấp cứu"
    },
    # Mức độ cao nhưng ít từ khóa (sẽ có độ tin cậy thấp hơn)
    {
        "title": "Tai nạn do ổ gà",
        "description": "Đoạn đường có ổ gà gây tai nạn, có người bị thương"
    },
    # Mức độ trung bình
    {
        "title": "Rác thải tập kết không đúng nơi quy định",
        "description": "Khu vực chợ có tình trạng vứt rác bừa bãi, gây mất vệ sinh"
    },
    # Mức độ thấp
    {
        "title": "Cần lắp thêm đèn đường",
        "description": "Đề xuất lắp thêm đèn chiếu sáng tại ngõ 123 để thuận tiện đi lại"
    }
]

print("Test kết quả phân loại mức độ nghiêm trọng sau khi điều chỉnh:\n")
for case in test_cases:
    print(f"Input:")
    print(f"- Tiêu đề: {case['title']}")
    print(f"- Nội dung: {case['description']}")
    
    result = classifier.classify(case['title'], case['description'])
    
    # Xác định màu hiển thị dựa trên mức độ và độ tin cậy
    severity_confidence = int(result['severity_confidence']*100)
    severity_level = "Cao" if result['severity'] == "high" else "Trung bình" if result['severity'] == "medium" else "Thấp"
    
    color = "Đỏ"
    if result['severity'] == "high" and severity_confidence >= 85:
        color = "Đỏ"
    elif result['severity'] == "medium" or (result['severity'] == "high" and severity_confidence < 85):
        color = "Vàng"
    else:
        color = "Xanh"
    
    print("\nKết quả phân loại:")
    print(f"- Loại: {result['label']}")
    print(f"- Mức độ: {severity_level}")
    print(f"- Độ tin cậy (phân loại): {result['confidence']:.2%}")
    print(f"- Độ tin cậy (mức độ): {result['severity_confidence']:.2%}")
    print(f"- Màu hiển thị: {color}")
    print("\n" + "-"*50 + "\n")