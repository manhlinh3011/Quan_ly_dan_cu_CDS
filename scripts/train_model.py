import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import numpy as np
from datasets import Dataset
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/training.log'),
        logging.StreamHandler()
    ]
)

def compute_metrics(pred):
    """Tính toán các metrics đánh giá mô hình"""
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average='weighted'
    )
    acc = accuracy_score(labels, preds)
    
    return {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }

def train_model():
    """Huấn luyện mô hình phân loại phản ánh"""
    # Load dữ liệu
    data_path = 'data/feedback_training/feedback_data.csv'
    if not os.path.exists(data_path):
        logging.error(f"Không tìm thấy file dữ liệu tại {data_path}")
        return
        
    df = pd.read_csv(data_path)
    logging.info(f"Đã tải {len(df)} mẫu dữ liệu")
    
    # Chuẩn bị labels
    label2id = {'phan_anh': 0, 'khieu_nai': 1}
    id2label = {v: k for k, v in label2id.items()}
    df['label_id'] = df['label'].map(label2id)
    
    # Chia tập train/test
    train_df, test_df = train_test_split(
        df, test_size=0.2, random_state=42, stratify=df['label']
    )
    
    # Khởi tạo tokenizer và model
    model_name = 'vinai/phobert-base'
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=len(label2id),
        id2label=id2label,
        label2id=label2id
    )
    
    # Chuẩn bị dataset
    def tokenize_function(examples):
        # Kết hợp title và description, với title được nhân đôi để tăng trọng số
        texts = [
            f"{title} {title} {desc}" for title, desc in 
            zip(examples['title'], examples['description'])
        ]
        return tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512
        )
    
    # Chuyển đổi thành dataset format của HuggingFace
    train_dataset = Dataset.from_pandas(train_df)
    test_dataset = Dataset.from_pandas(test_df)
    
    # Tokenize datasets
    train_dataset = train_dataset.map(
        tokenize_function, batched=True, remove_columns=train_dataset.column_names
    )
    test_dataset = test_dataset.map(
        tokenize_function, batched=True, remove_columns=test_dataset.column_names
    )
    
    # Thiết lập training arguments
    training_args = TrainingArguments(
        output_dir="models/feedback_classifier",
        learning_rate=2e-5,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        num_train_epochs=3,
        weight_decay=0.01,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True
    )
    
    # Khởi tạo trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        compute_metrics=compute_metrics,
    )
    
    # Huấn luyện mô hình
    logging.info("Bắt đầu huấn luyện mô hình...")
    trainer.train()
    
    # Đánh giá mô hình
    metrics = trainer.evaluate()
    logging.info("Kết quả đánh giá mô hình:")
    for key, value in metrics.items():
        logging.info(f"{key}: {value}")
    
    # Lưu mô hình
    model_save_path = "models/feedback_classifier.pth"
    torch.save(model.state_dict(), model_save_path)
    logging.info(f"Đã lưu mô hình tại {model_save_path}")
    
    return metrics

if __name__ == '__main__':
    train_model()