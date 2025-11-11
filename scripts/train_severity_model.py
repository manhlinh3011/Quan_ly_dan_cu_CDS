import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
import pickle
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/severity_training.log'),
        logging.StreamHandler()
    ]
)

def train_severity_model():
    """Huấn luyện mô hình phân loại mức độ nghiêm trọng"""
    # Load dữ liệu
    data_path = 'data/feedback_training/feedback_severity.csv'
    if not os.path.exists(data_path):
        logging.error(f"Không tìm thấy file dữ liệu tại {data_path}")
        return
        
    df = pd.read_csv(data_path)
    logging.info(f"Đã tải {len(df)} mẫu dữ liệu")

    # Kết hợp title và description để phân tích
    df['text'] = df['title'] + ' ' + df['description']
    
    # Chia dữ liệu train/test
    X_train, X_test, y_train, y_test = train_test_split(
        df['text'], 
        df['severity'],
        test_size=0.2,
        random_state=42
    )

    # Vectorize text bằng TF-IDF
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2)
    )
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    # Huấn luyện mô hình
    model = LogisticRegression(
        multi_class='multinomial',
        max_iter=1000
    )
    model.fit(X_train_tfidf, y_train)

    # Đánh giá mô hình
    y_pred = model.predict(X_test_tfidf)
    logging.info("\nKết quả đánh giá mô hình:")
    logging.info(classification_report(y_test, y_pred))

    # Lưu mô hình
    if not os.path.exists('models'):
        os.makedirs('models')
        
    with open('models/severity_vectorizer.pkl', 'wb') as f:
        pickle.dump(vectorizer, f)
    with open('models/severity_classifier.pkl', 'wb') as f:
        pickle.dump(model, f)
        
    logging.info("Đã lưu mô hình thành công")

if __name__ == '__main__':
    train_severity_model()