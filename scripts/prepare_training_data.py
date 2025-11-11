import pandas as pd
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import Feedback, db

def prepare_training_data():
    """Lấy dữ liệu từ database và chuẩn bị cho training"""
    # Lấy tất cả feedback có nhãn
    feedbacks = Feedback.query.filter(
        Feedback.kind.in_(['phan_anh', 'khieu_nai'])
    ).all()
    
    # Chuyển đổi thành DataFrame
    data = []
    for fb in feedbacks:
        data.append({
            'title': fb.title or '',
            'description': fb.description or '',
            'label': fb.kind
        })
    
    df = pd.DataFrame(data)
    
    # Lưu dữ liệu
    output_path = 'data/feedback_training/feedback_data.csv'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    
    print(f"Đã lưu {len(data)} mẫu dữ liệu vào {output_path}")
    print(f"Phân bố nhãn:")
    print(df['label'].value_counts())
    
    return df

if __name__ == '__main__':
    # Import app context
    from app import create_app
    app = create_app()
    
    with app.app_context():
        prepare_training_data()