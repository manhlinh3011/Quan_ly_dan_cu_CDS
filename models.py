from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), nullable=False, default='citizen')  # 'admin' or 'citizen'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    feedbacks = db.relationship('Feedback', backref='user', lazy=True)

class Household(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    household_code = db.Column(db.String(20), unique=True, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    hamlet = db.Column(db.String(50), nullable=False)  # Thôn/xóm
    head_of_household = db.Column(db.String(120), nullable=False)
    # Head of household additional info
    head_id_number = db.Column(db.String(20))  # CCCD/CMND
    head_birth_date = db.Column(db.Date)  # Ngày sinh
    head_occupation = db.Column(db.String(100))
    head_gender = db.Column(db.String(10))  # 'Nam' or 'Nữ'
    phone = db.Column(db.String(20))
    # Map location for household (saved at household level)
    location_lat = db.Column(db.Float)
    location_lng = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    residents = db.relationship('Resident', backref='household', lazy=True, cascade='all, delete-orphan')

class Resident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)  # 'Nam' or 'Nữ'
    id_number = db.Column(db.String(20), unique=True)  # CMND/CCCD
    relationship = db.Column(db.String(50), nullable=False)  # Quan hệ với chủ hộ
    occupation = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    notes = db.Column(db.Text)
    # Current map location (lat/lng) for display on resident management
    current_lat = db.Column(db.Float)
    current_lng = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key
    household_id = db.Column(db.Integer, db.ForeignKey('household.id'), nullable=False)
    
    # Relationships
    temporary_residences = db.relationship('TemporaryResidence', backref='resident', lazy=True)

class TemporaryResidence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  # 'tam_tru' or 'tam_vang'
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    destination = db.Column(db.String(200))  # Nơi đến (for tam_vang) or Nơi đi (for tam_tru)
    reason = db.Column(db.String(200))
    contact_info = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Map location of temporary stay (lat/lng)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    
    # Foreign key (either resident_id or head_household_id will be set)
    resident_id = db.Column(db.Integer, db.ForeignKey('resident.id'))
    head_household_id = db.Column(db.Integer, db.ForeignKey('household.id'))
    is_for_head = db.Column(db.Boolean, default=False)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # 'o_ga', 'rac_thai', 'mat_dien', 'an_ninh'
    # kind: phan_anh (phản ánh) / khieu_nai (khiếu nại) / None
    kind = db.Column(db.String(20))
    location = db.Column(db.String(200))
    priority = db.Column(db.String(20), default='medium')  # 'low', 'medium', 'high'
    severity = db.Column(db.String(20))  # 'low', 'medium', 'high' - phân loại bởi AI
    severity_confidence = db.Column(db.Float)  # Độ tin cậy của việc phân loại mức độ
    status = db.Column(db.String(20), default='pending')  # 'pending', 'in_progress', 'resolved', 'rejected'
    admin_response = db.Column(db.Text)
    attachments = db.Column(db.Text)  # JSON string of file paths
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    
    # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # 'tin_tuc', 'thong_bao', 'lich_hop', 'chinh_sach'
    priority = db.Column(db.String(20), default='normal')  # 'normal', 'important', 'urgent'
    is_published = db.Column(db.Boolean, default=False)
    publish_date = db.Column(db.DateTime)
    attachments = db.Column(db.Text)  # JSON string of file paths
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creator = db.relationship('User', backref='announcements')

# Social benefits tracking
class BenefitCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)  # ho_ngheo, can_ngheo, chinh_sach
    name = db.Column(db.String(120), nullable=False)
    target_type = db.Column(db.String(20), nullable=False, default='household')  # household/resident
    # Default support amount per beneficiary in this category (VND)
    support_amount = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Beneficiary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    target_type = db.Column(db.String(20), nullable=False)  # household/resident
    household_id = db.Column(db.Integer, db.ForeignKey('household.id'))
    resident_id = db.Column(db.Integer, db.ForeignKey('resident.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('benefit_category.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    # Simple tracking: whether support has been paid (no schedules)
    is_paid = db.Column(db.Boolean, default=False)
    # Override support amount for this beneficiary if different from category (VND)
    support_amount = db.Column(db.Integer)
    notes = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship('BenefitCategory')
    household = db.relationship('Household')
    resident = db.relationship('Resident')

class BenefitPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    beneficiary_id = db.Column(db.Integer, db.ForeignKey('beneficiary.id'), nullable=False)
    period = db.Column(db.String(7), nullable=False)  # YYYY-MM
    amount = db.Column(db.Integer, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending/paid/overdue
    paid_at = db.Column(db.Date)
    method = db.Column(db.String(50))
    reference = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    beneficiary = db.relationship('Beneficiary', backref='payments')

class DocumentType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    required_fields = db.Column(db.Text)  # JSON string mô tả các trường yêu cầu bổ sung
    fee = db.Column(db.Integer)  # phí dự kiến (VND)
    processing_time_days = db.Column(db.Integer)  # thời gian xử lý dự kiến (ngày)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DocumentRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('document_type.id'), nullable=False)

    applicant_full_name = db.Column(db.String(120), nullable=False)
    applicant_phone = db.Column(db.String(20))
    applicant_id_number = db.Column(db.String(20))
    notes = db.Column(db.Text)

    attachments = db.Column(db.Text)  # JSON list đường dẫn tệp

    status = db.Column(db.String(20), default='pending')  # pending/in_review/approved/rejected/completed
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Optional tracking fields
    admin_comment = db.Column(db.Text)
    expected_pickup_date = db.Column(db.Date)

    # Relationships
    user = db.relationship('User', backref='document_requests')
    doc_type = db.relationship('DocumentType')
