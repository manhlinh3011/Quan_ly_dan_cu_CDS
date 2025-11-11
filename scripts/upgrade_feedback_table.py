"""Script để thêm cột severity và severity_confidence vào bảng feedback"""
from app import db
from sqlalchemy import text

def upgrade():
    # Thêm cột severity
    # Thêm từng cột một vì SQLite không hỗ trợ thêm nhiều cột cùng lúc
    db.session.execute(text("ALTER TABLE feedback ADD COLUMN severity VARCHAR(20)"))
    db.session.execute(text("ALTER TABLE feedback ADD COLUMN severity_confidence FLOAT"))
    db.session.commit()
    
    print("Đã thêm cột severity và severity_confidence vào bảng feedback")
    
    # Phân loại lại tất cả feedback chưa có mức độ nghiêm trọng
    from models import Feedback
    from services.feedback_classifier import FeedbackClassifier
    
    classifier = FeedbackClassifier()
    count = 0
    for fb in Feedback.query.filter(Feedback.severity == None).all():
        result = classifier.classify(fb.title or '', fb.description or '')
        fb.severity = result['severity']
        fb.severity_confidence = result['severity_confidence']
        count += 1
        
    db.session.commit()
    print(f"Đã phân loại mức độ nghiêm trọng cho {count} phản ánh cũ")

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        upgrade()