from flask import Blueprint, render_template, request, make_response, url_for, jsonify
from utils import generate_qr_code, chatbot_answer
from models import Announcement
from utils import generate_qr_code
from app import db

bulletin_bp = Blueprint('bulletin', __name__)

@bulletin_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    
    # Base query for published announcements
    announcements_query = Announcement.query.filter_by(is_published=True)
    
    # Apply category filter
    if category:
        announcements_query = announcements_query.filter(Announcement.category == category)
    
    # Order by priority and publish date
    announcements_query = announcements_query.order_by(
        Announcement.priority.desc(),
        Announcement.publish_date.desc()
    )
    
    # Pagination
    announcements = announcements_query.paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('bulletin/index.html',
                         announcements=announcements,
                         category=category)

@bulletin_bp.route('/<int:id>')
def detail(id):
    announcement = Announcement.query.filter_by(id=id, is_published=True).first_or_404()
    
    # Increment view count
    announcement.view_count += 1
    db.session.commit()
    
    return render_template('bulletin/detail.html', announcement=announcement)

@bulletin_bp.route('/qr-code')
def generate_qr():
    """Generate QR code for bulletin board access"""
    bulletin_url = url_for('bulletin.index', _external=True)
    
    # Generate QR code
    qr_image = generate_qr_code(bulletin_url)
    
    # Return as PNG image
    response = make_response(qr_image.getvalue())
    response.headers['Content-Type'] = 'image/png'
    response.headers['Content-Disposition'] = 'inline; filename=bulletin_qr.png'
    
    return response

@bulletin_bp.route('/ai/chat', methods=['POST'])
def public_ai_chat():
    data = request.get_json(silent=True) or {}
    message = data.get('message', '')
    # Only allow public domains
    domain = data.get('domain', 'auto')
    if domain not in ('auto', 'xa_info', 'thu_tuc'):
        domain = 'auto'
    result = chatbot_answer(message, domain)
    return jsonify(result)
