import json
import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from models import Feedback, Announcement, DocumentType, DocumentRequest
from forms import FeedbackForm, DocumentRequestForm
from utils import save_uploaded_file, resize_image, send_email
from app import db

citizen_bp = Blueprint('citizen', __name__)

@citizen_bp.route('/dashboard')
@login_required
def dashboard():
    # Get user's feedbacks
    user_feedbacks = Feedback.query.filter_by(user_id=current_user.id).order_by(
        Feedback.created_at.desc()
    ).limit(10).all()
    
    # Get recent announcements
    recent_announcements = Announcement.query.filter_by(is_published=True).order_by(
        Announcement.publish_date.desc()
    ).limit(5).all()
    
    # Statistics
    total_feedbacks = Feedback.query.filter_by(user_id=current_user.id).count()
    resolved_feedbacks = Feedback.query.filter_by(
        user_id=current_user.id,
        status='resolved'
    ).count()
    pending_feedbacks = Feedback.query.filter_by(
        user_id=current_user.id,
        status='pending'
    ).count()
    
    return render_template('citizen/dashboard.html',
                         user_feedbacks=user_feedbacks,
                         recent_announcements=recent_announcements,
                         total_feedbacks=total_feedbacks,
                         resolved_feedbacks=resolved_feedbacks,
                         pending_feedbacks=pending_feedbacks)

@citizen_bp.route('/feedback', methods=['GET', 'POST'])
@login_required
def submit_feedback():
    form = FeedbackForm()
    
    if form.validate_on_submit():
        # Handle multiple file uploads
        attachments = []
        files = request.files.getlist('attachments')
        for f in files:
            if f and f.filename:
                filename = save_uploaded_file(f, 'feedback')
                if filename:
                    attachments.append(filename)
                    # Resize image if it's an image file
                    file_ext = filename.split('.')[-1].lower()
                    if file_ext in ['jpg', 'jpeg', 'png', 'gif']:
                        full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                        resize_image(full_path)
        
        # Phân loại tự động bằng AI
        from services.feedback_classifier import FeedbackClassifier
        classifier = FeedbackClassifier()
        result = classifier.classify(form.title.data, form.description.data)
        
        feedback = Feedback(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            location=form.location.data,
            attachments=json.dumps(attachments) if attachments else None,
            user_id=current_user.id,
            kind=result['label'],
            severity=result['severity'],
            severity_confidence=result['severity_confidence']
        )
        
        db.session.add(feedback)
        db.session.commit()

        # Notify admins via email (if configured)
        try:
            emails_cfg = current_app.config.get('ADMIN_NOTIFY_EMAILS', '')
            if emails_cfg:
                recipients = [e.strip() for e in emails_cfg.split(',') if e.strip()]
            else:
                # Fallback: all active admin emails
                from models import User
                recipients = [u.email for u in User.query.filter_by(role='admin', is_active=True).all() if u.email]
            if recipients:
                subject = 'Phản ánh mới từ người dân'
                body = f'{current_user.full_name} đã gửi phản ánh: {feedback.title}\nĐịa điểm: {feedback.location or "(không cung cấp)"}'
                send_email(subject, recipients, body_text=body)
        except Exception:
            pass
        
        flash('Gửi phản ánh thành công! Chúng tôi sẽ xem xét và phản hồi trong thời gian sớm nhất.', 'success')
        return redirect(url_for('citizen.dashboard'))
    
    return render_template('citizen/feedback.html', form=form)



@citizen_bp.route('/feedback/history')
@login_required
def feedback_history():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    category = request.args.get('category', '')
    
    # Base query
    feedbacks_query = Feedback.query.filter_by(user_id=current_user.id)
    
    # Apply filters
    if status:
        feedbacks_query = feedbacks_query.filter(Feedback.status == status)
    
    if category:
        feedbacks_query = feedbacks_query.filter(Feedback.category == category)
    
    # Order by creation date, newest first
    feedbacks_query = feedbacks_query.order_by(Feedback.created_at.desc())
    
    # Pagination
    feedbacks = feedbacks_query.paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('citizen/feedback_history.html',
                         feedbacks=feedbacks,
                         status=status,
                         category=category)

@citizen_bp.route('/feedback/<int:id>')
@login_required
def feedback_detail(id):
    feedback = Feedback.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    attachments = []
    if feedback.attachments:
        try:
            attachments = json.loads(feedback.attachments)
        except Exception:
            attachments = []
    return render_template('citizen/feedback_detail.html', feedback=feedback, attachments=attachments)

@citizen_bp.route('/documents', methods=['GET'])
@login_required
def document_requests_list():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')

    query = DocumentRequest.query.filter_by(user_id=current_user.id)
    if status:
        query = query.filter(DocumentRequest.status == status)
    query = query.order_by(DocumentRequest.submitted_at.desc())

    items = query.paginate(page=page, per_page=10, error_out=False)
    return render_template('citizen/document_requests.html', items=items, status=status)

@citizen_bp.route('/documents/new', methods=['GET', 'POST'])
@login_required
def document_request_new():
    form = DocumentRequestForm()
    form.type_id.choices = [(t.id, t.name) for t in DocumentType.query.order_by(DocumentType.name).all()]

    if form.validate_on_submit():
        attachments = []
        f = form.attachments.data
        if f and getattr(f, 'filename', None):
            filename = save_uploaded_file(f, 'documents')
            if filename:
                attachments.append(filename)
        dr = DocumentRequest(
            user_id=current_user.id,
            type_id=form.type_id.data,
            applicant_full_name=form.applicant_full_name.data,
            applicant_phone=form.applicant_phone.data,
            applicant_id_number=form.applicant_id_number.data,
            notes=form.notes.data,
            attachments=json.dumps(attachments) if attachments else None
        )
        db.session.add(dr)
        db.session.commit()

        # Notify admins via email (if configured)
        try:
            emails_cfg = current_app.config.get('ADMIN_NOTIFY_EMAILS', '')
            if emails_cfg:
                recipients = [e.strip() for e in emails_cfg.split(',') if e.strip()]
            else:
                from models import User
                recipients = [u.email for u in User.query.filter_by(role='admin', is_active=True).all() if u.email]
            if recipients:
                subject = 'Yêu cầu giấy tờ mới'
                body = f'Người dùng {current_user.full_name} đã gửi yêu cầu giấy tờ (ID #{dr.id}).'
                send_email(subject, recipients, body_text=body)
        except Exception:
            pass
        flash('Đã gửi yêu cầu đăng ký giấy tờ.', 'success')
        return redirect(url_for('citizen.document_requests_list'))

    return render_template('citizen/document_request_form.html', form=form)

@citizen_bp.route('/documents/<int:id>', methods=['GET'])
@login_required
def document_request_detail(id):
    dr = DocumentRequest.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    atts = []
    if dr.attachments:
        try:
            atts = json.loads(dr.attachments)
        except Exception:
            atts = []
    return render_template('citizen/document_request_detail.html', dr=dr, attachments=atts)

@citizen_bp.route('/documents/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def document_request_edit(id):
    dr = DocumentRequest.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    if dr.status != 'pending':
        flash('Chỉ được sửa yêu cầu khi đang ở trạng thái Chờ duyệt.', 'error')
        return redirect(url_for('citizen.document_request_detail', id=id))

    form = DocumentRequestForm(obj=dr)
    form.type_id.choices = [(t.id, t.name) for t in DocumentType.query.order_by(DocumentType.name).all()]

    if form.validate_on_submit():
        # allow to re-upload single file (replace attachments)
        attachments = []
        f = form.attachments.data
        if f and getattr(f, 'filename', None):
            filename = save_uploaded_file(f, 'documents')
            if filename:
                attachments.append(filename)
        dr.type_id = form.type_id.data
        dr.applicant_full_name = form.applicant_full_name.data
        dr.applicant_phone = form.applicant_phone.data
        dr.applicant_id_number = form.applicant_id_number.data
        dr.notes = form.notes.data
        if attachments:
            dr.attachments = json.dumps(attachments)
        db.session.commit()
        flash('Đã cập nhật yêu cầu.', 'success')
        return redirect(url_for('citizen.document_request_detail', id=id))

    return render_template('citizen/document_request_form.html', form=form)

@citizen_bp.route('/documents/<int:id>/delete', methods=['POST'])
@login_required
def document_request_delete(id):
    dr = DocumentRequest.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    if dr.status != 'pending':
        flash('Chỉ được xoá yêu cầu khi đang ở trạng thái Chờ duyệt.', 'error')
        return redirect(url_for('citizen.document_request_detail', id=id))
    db.session.delete(dr)
    db.session.commit()
    flash('Đã xoá yêu cầu.', 'success')
    return redirect(url_for('citizen.document_requests_list'))
