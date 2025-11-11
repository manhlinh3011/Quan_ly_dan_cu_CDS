import os
import uuid
import json
import qrcode
import pandas as pd
from io import BytesIO
from flask import current_app, url_for
from werkzeug.utils import secure_filename
from PIL import Image

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_uploaded_file(file, subfolder=''):
    """Save uploaded file and return the filename"""
    if file and file.filename:
        # Generate unique filename
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
        
        # Create subfolder if specified
        if subfolder:
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
            os.makedirs(upload_path, exist_ok=True)
            filepath = os.path.join(upload_path, unique_filename)
        else:
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save file
        file.save(filepath)
        
        # Return relative path for storage in database
        if subfolder:
            return f"{subfolder}/{unique_filename}"
        return unique_filename
    return None

def resize_image(image_path, max_size=(800, 600)):
    """Resize image to reduce file size"""
    try:
        with Image.open(image_path) as img:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            img.save(image_path, optimize=True, quality=85)
    except Exception as e:
        current_app.logger.error(f"Error resizing image {image_path}: {e}")

# Constants for dropdowns and forms
FEEDBACK_PRIORITIES = [
    ('low', 'Thấp'),
    ('medium', 'Trung bình'), 
    ('high', 'Cao')
]

ANNOUNCEMENT_PRIORITIES = [
    ('low', 'Thấp'),
    ('medium', 'Trung bình'),
    ('high', 'Cao')
]

def generate_qr_code(url, size=10, border=4):
    """Generate QR code for given URL"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to BytesIO
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return img_buffer

def export_residents_to_csv(residents):
    """Export residents data to CSV"""
    data = []
    for resident in residents:
        data.append({
            'Họ tên': resident.full_name,
            'Ngày sinh': resident.birth_date.strftime('%d/%m/%Y') if getattr(resident, 'birth_date', None) else '',
            'Giới tính': resident.gender,
            'CMND/CCCD': resident.id_number or '',
            'Quan hệ': resident.relationship,
            'Nghề nghiệp': resident.occupation or '',
            'Số điện thoại': getattr(resident, 'phone', '') or '',
            'Mã hộ': resident.household.household_code,
            'Địa chỉ': resident.household.address,
            'Thôn/Xóm': resident.household.hamlet,
            'Chủ hộ': resident.household.head_of_household
        })
    
    df = pd.DataFrame(data)
    return df.to_csv(index=False, encoding='utf-8-sig')

def export_residents_to_xml(residents):
    """Export residents data to XML"""
    data = []
    for resident in residents:
        data.append({
            'ho_ten': resident.full_name,
            'ngay_sinh': resident.birth_date.strftime('%Y-%m-%d') if getattr(resident, 'birth_date', None) else '',
            'gioi_tinh': resident.gender,
            'cmnd_cccd': resident.id_number or '',
            'quan_he': resident.relationship,
            'nghe_nghiep': resident.occupation or '',
            'so_dien_thoai': getattr(resident, 'phone', '') or '',
            'ma_ho': resident.household.household_code,
            'dia_chi': resident.household.address,
            'thon_xom': resident.household.hamlet,
            'chu_ho': resident.household.head_of_household
        })
    
    df = pd.DataFrame(data)
    # Use built-in etree parser to avoid lxml dependency
    return df.to_xml(index=False, encoding='utf-8', parser='etree')

def get_age_from_birth_date(birth_date):
    """Calculate age from birth date"""
    if not birth_date:
        return None
    from datetime import date
    today = date.today()
    years = today.year - birth_date.year
    has_had_birthday = (today.month, today.day) >= (birth_date.month, birth_date.day)
    return years if has_had_birthday else years - 1

def format_vietnamese_date(date_obj):
    """Format date in Vietnamese style"""
    if not date_obj:
        return ''
    
    months = [
        '', 'tháng 1', 'tháng 2', 'tháng 3', 'tháng 4', 'tháng 5', 'tháng 6',
        'tháng 7', 'tháng 8', 'tháng 9', 'tháng 10', 'tháng 11', 'tháng 12'
    ]
    
    return f"ngày {date_obj.day} {months[date_obj.month]} năm {date_obj.year}"

def get_category_display_name(category):
    """Get display name for categories"""
    categories = {
        'o_ga': 'Ổ gà đường xá',
        'rac_thai': 'Rác thải môi trường',
        'mat_dien': 'Mất điện',
        'an_ninh': 'An ninh trật tự',
        'khac': 'Khác',
        'tin_tuc': 'Tin tức',
        'thong_bao': 'Thông báo',
        'lich_hop': 'Lịch họp',
        'chinh_sach': 'Chính sách mới'
    }
    return categories.get(category, category)

def get_status_display_name(status):
    """Get display name for status"""
    statuses = {
        'pending': 'Chờ xử lý',
        'in_progress': 'Đang xử lý',
        'resolved': 'Đã giải quyết',
        'rejected': 'Từ chối'
    }
    return statuses.get(status, status)

def get_priority_display_name(priority):
    """Get display name for priority"""
    priorities = {
        'low': 'Thấp',
        'medium': 'Trung bình',
        'high': 'Cao',
        'normal': 'Bình thường',
        'important': 'Quan trọng',
        'urgent': 'Khẩn cấp'
    }
    return priorities.get(priority, priority)

def format_vn_datetime(dt, fmt='%d/%m/%Y %H:%M'):
    """Format datetime/date to Asia/Ho_Chi_Minh timezone for display.

    - Accepts both datetime and date objects
    - Treats naive datetime as UTC, then converts to Asia/Ho_Chi_Minh
    - For date objects, converts to datetime at 00:00 UTC before converting
    """
    if not dt:
        return ''

    from datetime import datetime as _DT, date as _D, timezone, timedelta

    # If a pure date is provided, convert to datetime at midnight
    if isinstance(dt, _D) and not isinstance(dt, _DT):
        dt = _DT(dt.year, dt.month, dt.day)

    try:
        from zoneinfo import ZoneInfo
        zoneinfo_available = True
    except Exception:
        zoneinfo_available = False

    # Ensure timezone-aware (assume UTC for naive datetimes)
    if getattr(dt, 'tzinfo', None) is None:
        dt = dt.replace(tzinfo=timezone.utc)

    # Convert to Vietnam timezone
    if zoneinfo_available:
        try:
            dt = dt.astimezone(ZoneInfo('Asia/Ho_Chi_Minh'))
        except Exception:
            dt = dt.astimezone(timezone(timedelta(hours=7)))
    else:
        dt = dt.astimezone(timezone(timedelta(hours=7)))

    return dt.strftime(fmt)

def format_currency_vnd(amount):
    """Format integer/float amount to Vietnamese currency string.

    - Returns '-' for falsy/None amounts
    - Uses dot as thousands separator and appends 'đ'
    """
    try:
        if amount is None:
            return '-'
        # Accept strings; attempt to cast
        if isinstance(amount, str) and amount.strip() != '':
            amount = float(amount)
        # Ensure number
        num = float(amount)
        # Format without decimals
        s = f"{num:,.0f}"
        # Convert comma to dot for Vietnamese style
        s = s.replace(',', '.')
        return f"{s} đ"
    except Exception:
        return '-'  # Fallback gracefully

def get_document_status_display(status):
    mapping = {
        'pending': 'Chờ duyệt',
        'in_review': 'Đang duyệt',
        'approved': 'Đã duyệt',
        'rejected': 'Từ chối',
        'completed': 'Hoàn tất',
    }
    return mapping.get(status, status)

def get_document_status_badge(status):
    mapping = {
        'pending': 'warning',
        'in_review': 'info',
        'approved': 'primary',
        'rejected': 'danger',
        'completed': 'success',
    }
    return mapping.get(status, 'secondary')

def send_email(subject, recipients, body_text=None, body_html=None):
    """Send email via SMTP using app config. Silently no-op if not configured.

    Config keys used:
    - MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, MAIL_USE_TLS, MAIL_SENDER
    """
    try:
        cfg = current_app.config
        username = cfg.get('MAIL_USERNAME')
        password = cfg.get('MAIL_PASSWORD')
        server = cfg.get('MAIL_SERVER')
        port = int(cfg.get('MAIL_PORT', 587))
        use_tls = bool(cfg.get('MAIL_USE_TLS', True))
        sender = cfg.get('MAIL_SENDER', username)

        if not (server and username and password and recipients):
            # Not configured; warn and skip sending
            try:
                current_app.logger.warning('Email not sent: SMTP not configured or recipients empty.')
            except Exception:
                pass
            return False

        from email.message import EmailMessage
        import smtplib

        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = ', '.join(recipients)
        if body_html:
            msg.set_content(body_text or '')
            msg.add_alternative(body_html, subtype='html')
        else:
            msg.set_content(body_text or '')

        with smtplib.SMTP(server, port) as smtp:
            if use_tls:
                smtp.starttls()
            smtp.login(username, password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        try:
            current_app.logger.error(f"Email send failed: {e}")
        except Exception:
            pass
        return False

# --- Simple RAG over local markdown files for chatbot ---
import re as _re

def _read_text_file(path: str) -> str:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return ''

def _split_paragraphs(text: str):
    paras = [p.strip() for p in _re.split(r'\n\s*\n', text) if p.strip()]
    return paras[:]

def _simple_similarity(a: str, b: str) -> float:
    a = a.lower()
    b = b.lower()
    aw = set(_re.findall(r'[a-z0-9à-ỹ]+', a))
    bw = set(_re.findall(r'[a-z0-9à-ỹ]+', b))
    if not aw or not bw:
        return 0.0
    inter = len(aw & bw)
    union = len(aw | bw)
    return inter / union

def chatbot_answer(message: str, domain: str = 'auto'):
    base = os.path.dirname(__file__) or '.'
    paths = []
    if domain in ('auto', 'xa_info'):
        paths.append(os.path.join(base, 'Gioi_thieu_xa_info.md'))
    if domain in ('auto', 'thu_tuc'):
        paths.append(os.path.join(base, 'Thu_tuc_giay_to.md'))
    candidates = []
    for p in paths:
        content = _read_text_file(p)
        for para in _split_paragraphs(content):
            score = _simple_similarity(message, para)
            if score > 0:
                candidates.append((score, para, os.path.basename(p)))
    if not candidates:
        return {
            'answer': 'Xin lỗi, tôi chưa tìm thấy nội dung phù hợp. Vui lòng liên hệ Bộ phận một cửa (0123 456 789) để được hỗ trợ.',
            'sources': []
        }
    candidates.sort(reverse=True, key=lambda x: x[0])
    top = candidates[:2]
    answer = '\n\n'.join([c[1] for c in top])
    sources = [{'file': c[2], 'score': round(c[0], 3)} for c in top]
    return {'answer': answer, 'sources': sources}

# Permission decorators
from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Vui lòng đăng nhập để truy cập.', 'error')
            return redirect(url_for('auth.login'))
        if current_user.role != 'admin':
            flash('Bạn không có quyền truy cập chức năng này.', 'error')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def viewer_allowed(f):
    """Decorator to allow admin and viewer roles (read-only access)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Vui lòng đăng nhập để truy cập.', 'error')
            return redirect(url_for('auth.login'))
        if current_user.role not in ['admin', 'viewer']:
            flash('Bạn không có quyền truy cập chức năng này.', 'error')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def admin_or_self(f):
    """Decorator to allow admin or user accessing their own data"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Vui lòng đăng nhập để truy cập.', 'error')
            return redirect(url_for('auth.login'))
        
        # Admin can access everything
        if current_user.role == 'admin':
            return f(*args, **kwargs)
        
        # Check if user is accessing their own data
        user_id = kwargs.get('id') or kwargs.get('user_id')
        if user_id and int(user_id) == current_user.id:
            return f(*args, **kwargs)
        
        flash('Bạn không có quyền truy cập dữ liệu này.', 'error')
        abort(403)
    return decorated_function
