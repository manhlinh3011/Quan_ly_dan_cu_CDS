import os
import json
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy import inspect, text
from utils import format_vn_datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///commune_admin.db")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    # Email (SMTP) configuration via environment
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', '')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ('1','true','yes')
    app.config['MAIL_SENDER'] = os.environ.get('MAIL_SENDER', os.environ.get('MAIL_USERNAME', ''))
    # Comma-separated list of admin emails to notify on new submissions (optional)
    app.config['ADMIN_NOTIFY_EMAILS'] = os.environ.get('ADMIN_NOTIFY_EMAILS', '')
    # Fallback: load MAIL_* from config/mail_config.json if env vars are missing
    try:
        need_fallback = not (app.config.get('MAIL_SERVER') and app.config.get('MAIL_USERNAME') and app.config.get('MAIL_PASSWORD'))
        if need_fallback:
            cfg_path = os.path.join(os.path.dirname(__file__), 'config', 'mail_config.json')
            if os.path.exists(cfg_path):
                with open(cfg_path, 'r', encoding='utf-8') as f:
                    mail_cfg = json.load(f)
                app.config['MAIL_SERVER'] = app.config.get('MAIL_SERVER') or mail_cfg.get('MAIL_SERVER', '')
                app.config['MAIL_PORT'] = app.config.get('MAIL_PORT') or int(mail_cfg.get('MAIL_PORT', 587))
                app.config['MAIL_USERNAME'] = app.config.get('MAIL_USERNAME') or mail_cfg.get('MAIL_USERNAME', '')
                app.config['MAIL_PASSWORD'] = app.config.get('MAIL_PASSWORD') or mail_cfg.get('MAIL_PASSWORD', '')
                # normalize TLS flag
                tls_val = app.config.get('MAIL_USE_TLS')
                if tls_val in (None, ''):
                    tls_val = mail_cfg.get('MAIL_USE_TLS', True)
                if isinstance(tls_val, str):
                    app.config['MAIL_USE_TLS'] = tls_val.lower() in ('1','true','yes')
                else:
                    app.config['MAIL_USE_TLS'] = bool(tls_val)
                app.config['MAIL_SENDER'] = app.config.get('MAIL_SENDER') or mail_cfg.get('MAIL_SENDER', app.config.get('MAIL_USERNAME', ''))
                app.config['ADMIN_NOTIFY_EMAILS'] = app.config.get('ADMIN_NOTIFY_EMAILS') or mail_cfg.get('ADMIN_NOTIFY_EMAILS', '')
                logging.info('Loaded MAIL_* settings from config/mail_config.json fallback')
            else:
                logging.warning('mail_config.json not found; email will be disabled until MAIL_* is set')
    except Exception as e:
        logging.warning(f'Could not load mail_config.json: {e}')
    
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Vui lòng đăng nhập để truy cập trang này.'
    
    # Create upload directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    with app.app_context():
        # Import models
        from models import User, Household, Resident, Feedback, Announcement, Beneficiary, DocumentType, DocumentRequest
        
        # Create tables
        db.create_all()
        # Lightweight schema migration for SQLite
        try:
            insp = inspect(db.engine)
            # TemporaryResidence legacy columns
            cols = {c['name'] for c in insp.get_columns('temporary_residence')}
            alter_stmts = []
            if 'updated_at' not in cols:
                alter_stmts.append("ALTER TABLE temporary_residence ADD COLUMN updated_at DATETIME")
            if 'head_household_id' not in cols:
                alter_stmts.append("ALTER TABLE temporary_residence ADD COLUMN head_household_id INTEGER")
            if 'is_for_head' not in cols:
                alter_stmts.append("ALTER TABLE temporary_residence ADD COLUMN is_for_head BOOLEAN DEFAULT 0")
            # Map columns for TemporaryResidence
            if 'lat' not in cols:
                alter_stmts.append("ALTER TABLE temporary_residence ADD COLUMN lat FLOAT")
            if 'lng' not in cols:
                alter_stmts.append("ALTER TABLE temporary_residence ADD COLUMN lng FLOAT")
            # relax NOT NULL on resident_id for head records by creating column if missing constraint not adjustable easily
            # Ensure resident_id exists; if NULL constraint present, we can't drop in SQLite easily; we will set sentinel 0
            for stmt in alter_stmts:
                db.session.execute(text(stmt))
            if alter_stmts:
                db.session.commit()

            # Data cleanup: convert blank id_number to NULL to satisfy UNIQUE
            try:
                db.session.execute(text("UPDATE resident SET id_number = NULL WHERE id_number = ''"))
                db.session.commit()
            except Exception:
                db.session.rollback()

            # Resident map columns
            r_cols = {c['name'] for c in insp.get_columns('resident')}
            r_alter = []
            if 'current_lat' not in r_cols:
                r_alter.append("ALTER TABLE resident ADD COLUMN current_lat FLOAT")
            if 'current_lng' not in r_cols:
                r_alter.append("ALTER TABLE resident ADD COLUMN current_lng FLOAT")
            for stmt in r_alter:
                db.session.execute(text(stmt))
            if r_alter:
                db.session.commit()

            # Household map columns
            h_cols = {c['name'] for c in insp.get_columns('household')}
            h_alter = []
            if 'location_lat' not in h_cols:
                h_alter.append("ALTER TABLE household ADD COLUMN location_lat FLOAT")
            if 'location_lng' not in h_cols:
                h_alter.append("ALTER TABLE household ADD COLUMN location_lng FLOAT")
            for stmt in h_alter:
                db.session.execute(text(stmt))
            if h_alter:
                db.session.commit()

            # Patch beneficiaries: add is_paid if missing
            b_cols = {c['name'] for c in insp.get_columns('beneficiary')}
            if 'is_paid' not in b_cols:
                db.session.execute(text("ALTER TABLE beneficiary ADD COLUMN is_paid BOOLEAN DEFAULT 0"))
                db.session.commit()
            # Add kind column to feedback if missing
            f_cols = {c['name'] for c in insp.get_columns('feedback')}
            if 'kind' not in f_cols:
                db.session.execute(text("ALTER TABLE feedback ADD COLUMN kind VARCHAR(20)"))
                db.session.commit()

            # Benefits: add support_amount columns if missing
            bc_cols = {c['name'] for c in insp.get_columns('benefit_category')}
            if 'support_amount' not in bc_cols:
                db.session.execute(text("ALTER TABLE benefit_category ADD COLUMN support_amount INTEGER"))
                db.session.commit()

            bnf_cols = {c['name'] for c in insp.get_columns('beneficiary')}
            if 'support_amount' not in bnf_cols:
                db.session.execute(text("ALTER TABLE beneficiary ADD COLUMN support_amount INTEGER"))
                db.session.commit()
        except Exception as _:
            pass
        
        # Create default admin user if it doesn't exist
        try:
            admin_user = User.query.filter_by(username='admin').first()
        except Exception:
            admin_user = None
        if not admin_user:
            try:
                from werkzeug.security import generate_password_hash
                admin = User(
                    username='admin',
                    email='admin@ubnd.gov.vn',
                    full_name='Quản trị viên',
                    role='admin',
                    is_active=True
                )
                admin.password_hash = generate_password_hash('admin123')
                db.session.add(admin)
                db.session.commit()
                logging.info("Default admin user created: admin/admin123")
            except Exception:
                db.session.rollback()

        # Seed default DocumentType rows for commune services
        try:
            existing_codes = {t.code for t in db.session.query(DocumentType.code).all()}
            default_types = [
                {"code": "xac_nhan_cu_tru", "name": "Xác nhận cư trú", "description": "Xác nhận nơi cư trú hiện tại.", "required_fields": "[{\"key\":\"dia_chi_thuong_tru\",\"label\":\"Địa chỉ thường trú\"},{\"key\":\"dia_chi_tam_tru\",\"label\":\"Địa chỉ tạm trú\",\"optional\":true}]", "fee": 0, "processing_time_days": 1},
                {"code": "xac_nhan_tam_tru", "name": "Xác nhận tạm trú", "description": "Xác nhận thông tin tạm trú.", "required_fields": "[{\"key\":\"dia_chi_tam_tru\",\"label\":\"Địa chỉ tạm trú\"},{\"key\":\"thoi_gian_tu\",\"label\":\"Thời gian từ\"},{\"key\":\"thoi_gian_den\",\"label\":\"Thời gian đến\"}]", "fee": 0, "processing_time_days": 1},
                {"code": "xac_nhan_tam_vang", "name": "Xác nhận tạm vắng", "description": "Xác nhận thông tin tạm vắng.", "required_fields": "[{\"key\":\"noi_den\",\"label\":\"Nơi đến\"},{\"key\":\"thoi_gian_tu\",\"label\":\"Thời gian từ\"},{\"key\":\"thoi_gian_den\",\"label\":\"Thời gian đến\"},{\"key\":\"ly_do\",\"label\":\"Lý do\"}]", "fee": 0, "processing_time_days": 1},
                {"code": "xac_nhan_doc_than", "name": "Xác nhận tình trạng hôn nhân (độc thân)", "description": "Xác nhận độc thân phục vụ hồ sơ kết hôn, vay vốn...", "required_fields": "[{\"key\":\"ngay_sinh\",\"label\":\"Ngày sinh\"},{\"key\":\"noi_cu_tru\",\"label\":\"Nơi cư trú\"}]", "fee": 20000, "processing_time_days": 2},
                {"code": "xac_nhan_ho_ngheo", "name": "Xác nhận hộ nghèo", "description": "Xác nhận hộ thuộc diện nghèo.", "required_fields": "[{\"key\":\"ma_ho\",\"label\":\"Mã hộ\"},{\"key\":\"nam_xet_duyet\",\"label\":\"Năm xét duyệt\"}]", "fee": 0, "processing_time_days": 2},
                {"code": "xac_nhan_can_ngheo", "name": "Xác nhận hộ cận nghèo", "description": "Xác nhận hộ thuộc diện cận nghèo.", "required_fields": "[{\"key\":\"ma_ho\",\"label\":\"Mã hộ\"},{\"key\":\"nam_xet_duyet\",\"label\":\"Năm xét duyệt\"}]", "fee": 0, "processing_time_days": 2},
                {"code": "dang_ky_khai_sinh", "name": "Đăng ký khai sinh", "description": "Thủ tục đăng ký khai sinh.", "required_fields": "[{\"key\":\"ten_tre\",\"label\":\"Tên trẻ\"},{\"key\":\"ngay_sinh\",\"label\":\"Ngày sinh\"},{\"key\":\"noi_sinh\",\"label\":\"Nơi sinh\"},{\"key\":\"cha\",\"label\":\"Cha\"},{\"key\":\"me\",\"label\":\"Mẹ\"}]", "fee": 0, "processing_time_days": 3},
                {"code": "dang_ky_ket_hon", "name": "Đăng ký kết hôn", "description": "Thủ tục đăng ký kết hôn.", "required_fields": "[{\"key\":\"ten_vo\",\"label\":\"Họ tên vợ\"},{\"key\":\"ten_chong\",\"label\":\"Họ tên chồng\"},{\"key\":\"ngay_dang_ky\",\"label\":\"Ngày đăng ký\"}]", "fee": 0, "processing_time_days": 3},
                {"code": "dang_ky_khai_tu", "name": "Đăng ký khai tử", "description": "Thủ tục đăng ký khai tử.", "required_fields": "[{\"key\":\"nguoi_mat\",\"label\":\"Họ tên người mất\"},{\"key\":\"ngay_mat\",\"label\":\"Ngày mất\"},{\"key\":\"noi_mat\",\"label\":\"Nơi mất\"},{\"key\":\"ly_do\",\"label\":\"Lý do\"}]", "fee": 0, "processing_time_days": 3}
            ]
            created_any = False
            for t in default_types:
                if t["code"] not in existing_codes:
                    db.session.add(DocumentType(**t))
                    created_any = True
            if created_any:
                db.session.commit()
        except Exception as _:
            pass
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from blueprints.auth import auth_bp
    from blueprints.admin import admin_bp
    from blueprints.citizen import citizen_bp
    from blueprints.bulletin import bulletin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(citizen_bp, url_prefix='/citizen')
    app.register_blueprint(bulletin_bp, url_prefix='/bulletin')

    # Jinja filters
    app.jinja_env.filters['vn_datetime'] = format_vn_datetime
    from utils import get_document_status_display, get_document_status_badge, format_currency_vnd
    app.jinja_env.filters['doc_status'] = get_document_status_display
    app.jinja_env.filters['doc_status_badge'] = get_document_status_badge
    # Currency formatting (VND)
    app.jinja_env.filters['currency_vnd'] = format_currency_vnd

    # Static serving for uploaded files
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        from flask import send_from_directory
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    # Main routes
    @app.route('/')
    def index():
        from flask import render_template
        return render_template('index.html')
    
    return app

# Create the app instance only when running this file directly
if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5000)
