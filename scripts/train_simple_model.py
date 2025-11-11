import pandas as pd
import re
import unicodedata
from underthesea import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pickle
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/training.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def train_simple_model():
    # Tăng dữ liệu đơn giản
    def augment_text(text):
        # Hoán vị từ
        words = text.split()
        if len(words) > 4:
            import random
            random.shuffle(words)
            text_aug = ' '.join(words)
        else:
            text_aug = text
        # Thêm từ đồng nghĩa đơn giản cho một số từ phổ biến
        synonyms = {
            'phản ánh': ['góp ý', 'kiến nghị', 'báo cáo'],
            'khiếu nại': ['tố cáo', 'khiếu kiện', 'tố giác'],
            'rác': ['rác thải', 'chất thải'],
            'hỏng': ['hư', 'hư hỏng', 'xuống cấp'],
            'chậm': ['trễ', 'kéo dài'],
            'điện': ['mất điện', 'thiếu điện'],
            'nước': ['nước sạch', 'nước sinh hoạt']
        }
        for k, syns in synonyms.items():
            if k in text_aug:
                text_aug += ' ' + ' '.join(syns)
        return text_aug

    """Train a simple TF-IDF + Logistic Regression model"""
    # Load data
    data_path = 'data/feedback_training/feedback_data.csv'
    if not os.path.exists(data_path):
        logging.error(f"Không tìm thấy file dữ liệu tại {data_path}")
        return
        
    df = pd.read_csv(data_path)
    logging.info(f"Đã tải {len(df)} mẫu dữ liệu")
    
    # Chuẩn hóa dữ liệu đầu vào
    def normalize_text(text):
        text = str(text)
        text = unicodedata.normalize('NFC', text)
        text = text.lower()
        text = re.sub(r'[\W_]+', ' ', text)
        text = word_tokenize(text)
        text = ' '.join(text)
        # Loại bỏ stopwords tiếng Việt phổ biến
        stopwords = set(['và', 'là', 'của', 'cho', 'với', 'được', 'bị', 'nhưng', 'rằng', 'thì', 'mà', 'có', 'đã', 'này', 'ở', 'trong', 'khi', 'đến', 'từ', 'bằng', 'về', 'sau', 'trước', 'nên', 'hay', 'cũng', 'để', 'nữa', 'đó', 'nào', 'ra', 'vào', 'lúc', 'đi', 'lại', 'vẫn', 'thế', 'thôi', 'thật', 'chỉ', 'rất', 'rồi', 'vậy', 'vì', 'do', 'giữa', 'giúp', 'tại', 'trên', 'dưới', 'qua', 'theo', 'như', 'nhiều', 'ít', 'mỗi', 'mọi', 'cùng', 'đồng', 'các', 'những', 'ai', 'gì', 'sao', 'đâu', 'đây', 'đấy', 'đó', 'kia', 'kìa', 'hết', 'toàn', 'hơn', 'kém', 'đủ', 'chưa', 'đã', 'đang', 'sẽ', 'phải', 'cần', 'muốn', 'có', 'không', 'chẳng', 'chưa', 'chắc', 'được', 'bị', 'phải', 'thì', 'là', 'mà', 'nhưng', 'hoặc', 'và', 'hay', 'cũng', 'nên', 'vậy', 'vì', 'do', 'tại', 'bởi', 'như', 'để', 'với', 'của', 'cho', 'về', 'trong', 'trên', 'dưới', 'giữa', 'qua', 'theo', 'từ', 'đến', 'ra', 'vào', 'lúc', 'khi', 'sau', 'trước', 'này', 'kia', 'kìa', 'đây', 'đấy', 'đó', 'hết', 'toàn', 'hơn', 'kém', 'đủ', 'chưa', 'chắc', 'được', 'bị', 'phải', 'thì', 'là', 'mà', 'nhưng', 'hoặc', 'và', 'hay', 'cũng', 'nên', 'vậy', 'vì', 'do', 'tại', 'bởi', 'như', 'để', 'với', 'của', 'cho', 'về', 'trong', 'trên', 'dưới', 'giữa', 'qua', 'theo', 'từ', 'đến', 'ra', 'vào', 'lúc', 'khi', 'sau', 'trước', 'này', 'kia', 'kìa', 'đây', 'đấy', 'đó', 'hết', 'toàn', 'hơn', 'kém', 'đủ', 'chưa', 'chắc'])
        text = ' '.join([w for w in text.split() if w not in stopwords])
        return text

    df['text'] = (df['title'] + ' ' + df['description']).apply(normalize_text)
    # Tăng dữ liệu: mỗi mẫu gốc sẽ có thêm 1 bản tăng cường
    aug_rows = []
    for idx, row in df.iterrows():
        aug_text = augment_text(row['text'])
        if aug_text != row['text']:
            aug_rows.append({'text': aug_text, 'label': row['label']})
    if aug_rows:
        df = pd.concat([df, pd.DataFrame(aug_rows)], ignore_index=True)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        df['text'], df['label'], 
        test_size=0.2, 
        random_state=42,
        stratify=df['label']
    )
    
    # Create pipeline
    vectorizer = TfidfVectorizer(
        max_features=12000,           # Tăng số lượng đặc trưng
        ngram_range=(1, 4),           # Thêm ngram 4 để bắt cụm từ dài
        strip_accents=None,
        min_df=1,
        max_df=0.90,
        sublinear_tf=True
    )

    classifier = LogisticRegression(
        C=5.0,                        # Tăng regularization mạnh hơn
        class_weight='balanced',
        max_iter=1000,                 # Tăng số vòng lặp
        solver='lbfgs',
        random_state=42
    )
    
    # Train
    logging.info("Bắt đầu huấn luyện mô hình...")
    
    # Transform text to TF-IDF features
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)
    
    # Train classifier
    classifier.fit(X_train_tfidf, y_train)
    
    # Evaluate
    y_pred = classifier.predict(X_test_tfidf)
    logging.info("\nKết quả đánh giá mô hình:")
    logging.info("\n" + classification_report(y_test, y_pred))
    
    # Save model and vectorizer
    os.makedirs('models', exist_ok=True)
    with open('models/vectorizer.pkl', 'wb') as f:
        pickle.dump(vectorizer, f)
    with open('models/classifier.pkl', 'wb') as f:
        pickle.dump(classifier, f)
    
    logging.info("Đã lưu mô hình vào thư mục models/")
    
    # Test some predictions
    test_texts = [
        "Đường hư hỏng nặng cần sửa chữa",
        "Khiếu nại về việc cấp giấy chậm trễ",
        "Rác thải không được thu gom đúng giờ"
    ]
    
    X_test = vectorizer.transform(test_texts)
    predictions = classifier.predict(X_test)
    probabilities = classifier.predict_proba(X_test)
    
    logging.info("\nKiểm tra một số dự đoán:")
    for text, pred, prob in zip(test_texts, predictions, probabilities):
        confidence = max(prob)
        logging.info(f"\nText: {text}")
        logging.info(f"Dự đoán: {pred}")
        logging.info(f"Độ tin cậy: {confidence:.2f}")

if __name__ == '__main__':
    train_simple_model()