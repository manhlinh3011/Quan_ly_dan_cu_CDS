import re
import json
import os
from typing import Tuple, List, Dict
import logging
from underthesea import word_tokenize
import unicodedata

class FeedbackClassifier:
    def __init__(self):
        self._load_config()
        self._load_rules()
        self._setup_logging()
        self._load_tfidf_model()
        self._load_severity_model()
        
    def _load_severity_model(self):
        """Load severity classifier model"""
        import pickle
        try:
            with open('models/severity_vectorizer.pkl', 'rb') as f:
                self.severity_vectorizer = pickle.load(f)
            with open('models/severity_classifier.pkl', 'rb') as f:
                self.severity_classifier = pickle.load(f)
        except Exception as e:
            logging.error(f"Error loading severity model: {str(e)}")
            self.severity_vectorizer = None
            self.severity_classifier = None
    def _load_tfidf_model(self):
        """Load TF-IDF + Logistic Regression model"""
        import pickle
        try:
            with open('models/vectorizer.pkl', 'rb') as f:
                self.tfidf_vectorizer = pickle.load(f)
            with open('models/classifier.pkl', 'rb') as f:
                self.tfidf_classifier = pickle.load(f)
        except Exception as e:
            logging.error(f"Error loading TF-IDF model: {str(e)}")
            self.tfidf_vectorizer = None
            self.tfidf_classifier = None
    def _apply_tfidf_classification(self, title: str, description: str) -> Tuple[str, float, List[str]]:
        """Apply TF-IDF + Logistic Regression classification"""
        if not self.tfidf_vectorizer or not self.tfidf_classifier:
            return None
        try:
            text = f"{title} {description}"
            text = self._preprocess_text(text)
            X = self.tfidf_vectorizer.transform([text])
            probs = self.tfidf_classifier.predict_proba(X)[0]
            pred_label = self.tfidf_classifier.classes_[probs.argmax()]
            confidence = probs.max()
            # Extract top terms
            important_terms = []
            try:
                feature_names = self.tfidf_vectorizer.get_feature_names_out()
                top_indices = X.toarray()[0].argsort()[-3:][::-1]
                important_terms = [feature_names[i] for i in top_indices if X.toarray()[0][i] > 0]
            except:
                pass
            return pred_label, confidence, important_terms
        except Exception as e:
            logging.error(f"TF-IDF classification error: {str(e)}")
            return None

    def _load_config(self):
        """Load classifier configuration"""
        self.config = {
            'use_word_tokenize': True
        }

    def _initialize_model(self):
        """Initialize model - deprecated, kept for compatibility"""
        pass

    def _load_rules(self):
        """Load classification rules and keywords"""
        self.rules = {
            'khieu_nai': {
                'strong_patterns': [
                    'khiếu nại', 'tố cáo', 'khiếu kiện', 'tố giác', 'khiếu tố',
                    'yêu cầu giải quyết', 'yêu cầu xem xét', 'yêu cầu xử lý',
                    'không đồng ý', 'không chấp nhận', 'không thỏa đáng',
                    'vi phạm', 'trái quy định', 'thiệt hại', 'sai phạm'
                ],
                'keywords': [
                    'bồi thường', 'xử lý trách nhiệm', 'kỷ luật', 'truy cứu',
                    'quyết định', 'không hợp lý', 'không công bằng', 'không đúng',
                    'sai quy trình', 'trái luật', 'không đúng quy định', 'khiếu',
                    'đền bù', 'bất cập', 'sai sót', 'oan sai'
                ]
            },
            'phan_anh': {
                'strong_patterns': [
                    'phản ánh', 'kiến nghị', 'góp ý', 'đề xuất', 'báo cáo',
                    'thông báo tình trạng', 'tình hình', 'hiện trạng'
                ],
                'keywords': [
                    'hư hỏng', 'xuống cấp', 'ô nhiễm', 'mất trật tự',
                    'mất vệ sinh', 'ùn tắc', 'ngập nước', 'thiếu nước',
                    'mất điện', 'không an toàn', 'gây nguy hiểm'
                ]
            }
        }

    def _setup_logging(self):
        """Setup logging for classification results"""
        logging.basicConfig(
            filename='logs/feedback_classification.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def _preprocess_text(self, text: str) -> str:
        """Preprocess input text"""
        # Convert to lowercase and normalize spaces
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep Vietnamese diacritics
        text = re.sub(r'[^\w\s\u0080-\u024F]', ' ', text)
        
        # Word tokenization for Vietnamese
        if self.config['use_word_tokenize']:
            try:
                tokens = word_tokenize(text)
                text = ' '.join(tokens)
            except:
                pass
                
        return text

    def _apply_ml_classification(self, title: str, description: str) -> Tuple[str, float, List[str]]:
        """Deprecated ML classification method - kept for compatibility"""
        return None

    @staticmethod
    def strip_accents(s: str) -> str:
        try:
            return ''.join(
                c for c in unicodedata.normalize('NFD', s)
                if unicodedata.category(c) != 'Mn'
            )
        except Exception:
            return s

    def _apply_rule_classification(self, title: str, description: str) -> Tuple[str, float, List[str]]:
        """Apply rule-based classification with enhanced keyword weighting"""
        # Cho tiêu đề trọng số cao hơn
        text = f"{title} {title} {description}".lower()
        text = self._preprocess_text(text)
        text_noacc = self.strip_accents(text)
        
        scores = {'khieu_nai': 0, 'phan_anh': 0}
        matched_terms = []

        # Nếu có từ khóa mạnh về khiếu nại trong tiêu đề, ưu tiên cao (hỗ trợ không dấu)
        title_lower = title.lower()
        title_noacc = self.strip_accents(title_lower)
        for pattern in self.rules['khieu_nai']['strong_patterns']:
            p_noacc = self.strip_accents(pattern)
            if pattern in title_lower or p_noacc in title_noacc:
                scores['khieu_nai'] += 5  # Tăng trọng số cho từ khóa trong tiêu đề
                matched_terms.append(f"{pattern} (tiêu đề)")

        # Check for strong patterns first (hỗ trợ không dấu)
        for label in ['khieu_nai', 'phan_anh']:
            for pattern in self.rules[label]['strong_patterns']:
                p_noacc = self.strip_accents(pattern)
                if pattern in text or p_noacc in text_noacc:
                    weight = 4 if label == 'khieu_nai' else 3  # Ưu tiên từ khóa khiếu nại
                    scores[label] += weight
                    if pattern not in [term.split(' (')[0] for term in matched_terms]:
                        matched_terms.append(pattern)

        # Then check for regular keywords (hỗ trợ không dấu)
        for label in ['khieu_nai', 'phan_anh']:
            for keyword in self.rules[label]['keywords']:
                k_noacc = self.strip_accents(keyword)
                if keyword in text or k_noacc in text_noacc:
                    weight = 2 if label == 'khieu_nai' else 1  # Ưu tiên từ khóa khiếu nại
                    scores[label] += weight
                    if keyword not in [term.split(' (')[0] for term in matched_terms]:
                        matched_terms.append(keyword)

        # Calculate confidence based on score difference
        total_score = sum(scores.values())
        if total_score == 0:
            # Nếu không có từ khóa nào match, mặc định là phản ánh với độ tin cậy thấp
            return 'phan_anh', 0.6, []

        # Determine winner
        if scores['khieu_nai'] > scores['phan_anh']:
            label = 'khieu_nai'
            margin = scores['khieu_nai'] - scores['phan_anh']
        else:
            label = 'phan_anh'
            margin = scores['phan_anh'] - scores['khieu_nai']

        # Calculate confidence
        confidence = min(0.95, 0.6 + (margin / total_score) * 0.35)

        return label, confidence, matched_terms[:3]

    def _extract_important_terms(self, text: str, label: str) -> List[str]:
        """Extract terms that influenced the classification"""
        important_terms = []
        
        # Check against our rules for the predicted label
        for pattern in self.rules[label]['strong_patterns']:
            if pattern in text:
                important_terms.append(pattern)
                
        for keyword in self.rules[label]['keywords']:
            if keyword in text and keyword not in important_terms:
                important_terms.append(keyword)
                
        return important_terms[:3]

    def _classify_severity(self, title: str, description: str) -> Tuple[str, float]:
        """Phân loại mức độ nghiêm trọng của phản ánh/khiếu nại sử dụng OpenAI API hoặc fallback về quy tắc"""
        # Thử phân tích bằng OpenAI API trước
        from services.openai_service import OpenAIService
        openai_service = OpenAIService()
        
        api_result = openai_service.analyze_feedback(title, description)
        if api_result:
            return api_result['severity'], api_result['confidence']
            
        # Nếu API thất bại, fallback về phân tích quy tắc
        text = f"{title} {description}".lower()
        text_noacc = self.strip_accents(text)
        
        # Các từ khóa và mẫu câu chỉ mức độ nghiêm trọng cao
        high_patterns = [
            # An toàn tính mạng / cháy nổ
            'cháy', 'cháy nhà', 'cháy nổ', 'hỏa hoạn', 'bốc cháy', 'nổ',
            'chập điện', 'điện giật', 'rò rỉ gas', 'rò rỉ khí gas', 'nổ bình gas',
            'nổ nồi hơi', 'nổ đường ống', 'cháy rừng', 'cháy chợ', 'cháy kho',
            'khói dày đặc', 'khói mù mịt', 'cần cứu hỏa', 'xe cứu hỏa',

            # Tai nạn nghiêm trọng
            'gây chết người', 'tử vong', 'tai nạn nghiêm trọng', 'nguy hiểm đến tính mạng',
            'đe dọa tính mạng', 'thương tích nặng', 'nhập viện', 'cấp cứu',

            # Thảm họa / thiên tai
            'sập nhà', 'sập cầu', 'sạt lở', 'lũ quét', 'ngập lụt nghiêm trọng',
            'bão lớn', 'động đất', 'lốc xoáy', 'giông lốc',

            # Ô nhiễm/hóa chất nghiêm trọng
            'ô nhiễm nghiêm trọng', 'độc hại', 'nguy hại', 'phát tán độc hại',
            'gây bệnh', 'dịch bệnh', 'nhiễm độc', 'rò rỉ hóa chất', 'tràn hóa chất',

            # An ninh trật tự nghiêm trọng
            'ma túy', 'vũ khí', 'gây rối nghiêm trọng', 'băng nhóm', 'tội phạm',
            'đe dọa', 'hành hung', 'bạo lực', 'trấn lột', 'cướp', 'cướp giật',
            'đánh nhau', 'ẩu đả', 'xô xát', 'đâm chém', 'đánh hội đồng',

            # Tham nhũng, tiêu cực lớn
            'tham nhũng', 'tiêu cực', 'trục lợi', 'biển thủ',

            # Khẩn cấp / ảnh hưởng rộng
            'khẩn cấp', 'cần giải quyết ngay', 'nhiều người', 'cả khu vực', 'toàn xã',
            'cộng đồng', 'ảnh hưởng nghiêm trọng', 'thiệt hại lớn'
        ]

        # Các từ khóa và mẫu câu chỉ mức độ trung bình
        medium_patterns = [
            # Cơ sở hạ tầng
            'hư hỏng', 'xuống cấp', 'sửa chữa', 'nâng cấp', 'ổ gà', 'nứt', 'lún', 'trơn trượt',
            'ngập nước', 'cống tắc', 'đèn hỏng',

            # Vệ sinh môi trường
            'rác thải', 'vệ sinh', 'mùi hôi', 'nước thải', 'đốt rác', 'khói',

            # Trật tự đô thị
            'lấn chiếm', 'xây dựng sai phép', 'họp chợ tự phát', 'đỗ xe sai quy định', 'buôn bán lấn chiếm',

            # Dịch vụ công
            'chậm trễ', 'thái độ không tốt', 'sai quy trình', 'thu phí sai', 'hồ sơ ách tắc',

            # Tiện ích
            'mất điện', 'mất nước', 'đường sá', 'internet chập chờn', 'thiếu đèn', 'đèn đường'
        ]
        
        # Đếm số lượng pattern match (hỗ trợ không dấu)
        def count_matches(patterns: List[str]) -> int:
            c = 0
            for p in patterns:
                p_noacc = self.strip_accents(p)
                if p in text or p_noacc in text_noacc:
                    c += 1
            return c
        
        high_matches = count_matches(high_patterns)
        medium_matches = count_matches(medium_patterns)
        
        # Logic phân loại
        if high_matches > 0:
            # Có dấu hiệu nghiêm trọng
            # Chuẩn hóa: một từ khóa nghiêm trọng đủ để gán "Cao" với tin cậy ≥ 85%
            confidence = min(0.95, 0.85 + 0.03 * max(high_matches - 1, 0))
            return 'high', confidence
        elif medium_matches > 0:
            # Có dấu hiệu mức độ trung bình
            confidence = min(0.85, 0.70 + 0.05 * medium_matches)
            return 'medium', confidence
        else:
            # Không tìm thấy dấu hiệu đặc biệt
            return 'low', 0.65
            
    def classify(self, title: str, description: str) -> Dict:
        """Main classification method combining rules and TF-IDF"""
        # Log input
        logging.info(f"Classifying feedback - Title: {title}")

        # Try rule-based first vì có độ chính xác cao hơn
        rule_result = self._apply_rule_classification(title, description)
        if rule_result and rule_result[1] >= 0.7:
            label, confidence, terms = rule_result
            method = "rules"
        else:
            # Fallback to TF-IDF if rules không đủ tin cậy
            tfidf_result = self._apply_tfidf_classification(title, description)
            if tfidf_result and tfidf_result[1] >= 0.75:  # Tăng ngưỡng tin cậy cho TF-IDF
                label, confidence, terms = tfidf_result
                method = "tfidf"
            else:
                # Nếu cả hai phương pháp đều không đủ tin cậy, dùng kết quả từ rules
                label, confidence, terms = rule_result
                method = "rules"

        # Phân loại mức độ nghiêm trọng
        severity, severity_confidence = self._classify_severity(title, description)

        # Log result
        result = {
            'label': label,
            'confidence': confidence,
            'important_terms': terms,
            'method': method,
            'severity': severity,
            'severity_confidence': severity_confidence
        }
        logging.info(f"Classification result: {json.dumps(result)}")

        return result