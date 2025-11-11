import json
from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, make_response, current_app, abort
from flask_login import login_required, current_user
from functools import wraps
from models import User, Household, Resident, TemporaryResidence, Feedback, Announcement, BenefitCategory, Beneficiary, BenefitPayment, DocumentType, DocumentRequest
from forms import HouseholdForm, ResidentForm, TemporaryResidenceForm, AnnouncementForm, BenefitCategoryForm, BeneficiaryForm, DocumentTypeForm, AdminUserForm
from utils import save_uploaded_file, export_residents_to_csv, export_residents_to_xml, get_age_from_birth_date, send_email
from utils import chatbot_answer, admin_required, viewer_allowed, admin_or_self
from app import db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@viewer_allowed
def dashboard():
    # Statistics
    total_households = Household.query.count()
    total_residents = Resident.query.count()
    pending_feedbacks = Feedback.query.filter_by(status='pending').count()
    published_announcements = Announcement.query.filter_by(is_published=True).count()
    
    # Recent feedbacks
    recent_feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).limit(5).all()
    
    # Demographics by hamlet (count residents including head of household)
    households = Household.query.all()
    residents = Resident.query.all()
    # Build map household_id -> {count, has_head}
    hh_residents_count = {}
    hh_has_head = {}
    for r in residents:
        hh_residents_count[r.household_id] = hh_residents_count.get(r.household_id, 0) + 1
        if r.relationship == 'Chủ hộ':
            hh_has_head[r.household_id] = True
    # Aggregate per hamlet
    stats_map = {}
    for h in households:
        if h.hamlet not in stats_map:
            stats_map[h.hamlet] = { 'hamlet': h.hamlet, 'households': 0, 'residents': 0 }
        s = stats_map[h.hamlet]
        s['households'] += 1
        count = hh_residents_count.get(h.id, 0)
        # If no resident marked as head, add the head_of_household as a person
        if not hh_has_head.get(h.id, False):
            count += 1
        s['residents'] += count
    hamlets_stats = list(stats_map.values())
    
    # Total people = residents + households that do not have a resident flagged as 'Chủ hộ'
    households_without_head = 0
    for h in households:
        if not hh_has_head.get(h.id, False):
            households_without_head += 1
    total_people = len(residents) + households_without_head
    
    # Temporary residence counts (active in-date)
    active_temp_residents = TemporaryResidence.query.filter(TemporaryResidence.is_active.is_(True)).count()

    return render_template('admin/dashboard.html',
                         total_households=total_households,
                         total_residents=total_residents,
                         pending_feedbacks=pending_feedbacks,
                         published_announcements=published_announcements,
                         recent_feedbacks=recent_feedbacks,
                         hamlets_stats=hamlets_stats,
                         active_temp_residents=active_temp_residents,
                         total_people=total_people)

@admin_bp.route('/population')
@login_required
@viewer_allowed
def population():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    hamlet = request.args.get('hamlet', '')
    age_group = request.args.get('age_group', '')
    
    # Base query
    households_query = Household.query
    
    # Apply filters
    if search:
        households_query = households_query.filter(
            db.or_(
                Household.household_code.contains(search),
                Household.head_of_household.contains(search),
                Household.address.contains(search)
            )
        )
    
    if hamlet:
        households_query = households_query.filter(Household.hamlet == hamlet)
    
    # Pagination
    households = households_query.paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get all hamlets for filter
    hamlets = db.session.query(Household.hamlet).distinct().all()
    hamlets = [h[0] for h in hamlets]
    # Active temporary residence count (for quick stats on population page)
    temporary_residents = TemporaryResidence.query.filter(TemporaryResidence.is_active.is_(True)).count()
    # Children under 18 (based on birth_date)
    from datetime import date
    current_year = date.today().year
    children_count = 0
    for r in Resident.query.all():
        if getattr(r, 'birth_date', None):
            age = current_year - r.birth_date.year
            if age < 18:
                children_count += 1

    return render_template('admin/population.html',
                         households=households,
                         hamlets=hamlets,
                         search=search,
                         hamlet=hamlet,
                         age_group=age_group,
                         total_households=Household.query.count(),
                         total_residents=Resident.query.count(),
                         temporary_residents=temporary_residents,
                         children_count=children_count)

@admin_bp.route('/household/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_household():
    form = HouseholdForm()
    if form.validate_on_submit():
        # Check if household code already exists
        existing = Household.query.filter_by(household_code=form.household_code.data).first()
        if existing:
            flash('Mã hộ gia đình đã tồn tại.', 'error')
            return render_template('admin/add_household.html', form=form)
        
        household = Household(
            household_code=form.household_code.data,
            address=form.address.data,
            hamlet=form.hamlet.data,
            head_of_household=form.head_of_household.data,
            phone=form.phone.data,
            head_id_number=form.head_id_number.data,
            head_birth_date=form.head_birth_date.data,
            head_occupation=form.head_occupation.data,
            head_gender=form.head_gender.data
        )
        # Lưu tọa độ vào Household (không tạo nhân khẩu Chủ hộ)
        lat_str = request.form.get('current_lat')
        lng_str = request.form.get('current_lng')
        def to_float(s):
            try:
                return float(s) if s is not None and s != '' else None
            except Exception:
                return None
        household.location_lat = to_float(lat_str)
        household.location_lng = to_float(lng_str)

        db.session.add(household)
        db.session.commit()

        flash('Thêm hộ gia đình thành công!', 'success')
        return redirect(url_for('admin.population'))
    
    return render_template('admin/add_household.html', form=form)

@admin_bp.route('/household/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_household(id):
    household = Household.query.get_or_404(id)
    form = HouseholdForm(obj=household)
    
    if form.validate_on_submit():
        form.populate_obj(household)
        # Cập nhật tọa độ cho Household từ form
        lat_str = request.form.get('current_lat')
        lng_str = request.form.get('current_lng')
        def to_float(s):
            try:
                return float(s) if s is not None and s != '' else None
            except Exception:
                return None
        household.location_lat = to_float(lat_str)
        household.location_lng = to_float(lng_str)
        household.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Đã cập nhật thông tin hộ khẩu thành công.', 'success')
        return redirect(url_for('admin.population'))
    
    return render_template('admin/edit_household.html', form=form, household=household)

@admin_bp.route('/household/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_household(id):
    household = Household.query.get_or_404(id)
    
    # Delete all residents in the household
    Resident.query.filter_by(household_id=id).delete()
    
    # Delete household
    db.session.delete(household)
    
    try:
        db.session.commit()
        return jsonify({"message": "Đã xóa hộ khẩu thành công"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Có lỗi xảy ra khi xóa hộ khẩu"}), 500
    
    if form.validate_on_submit():
        # Check if household code already exists (excluding current)
        existing = Household.query.filter(
            Household.household_code == form.household_code.data,
            Household.id != id
        ).first()
        if existing:
            flash('Mã hộ gia đình đã tồn tại.', 'error')
            return render_template('admin/edit_household.html', form=form, household=household)
        
        household.household_code = form.household_code.data
        household.address = form.address.data
        household.hamlet = form.hamlet.data
        household.head_of_household = form.head_of_household.data
        household.phone = form.phone.data
        household.head_id_number = form.head_id_number.data
        household.head_birth_date = form.head_birth_date.data
        household.head_occupation = form.head_occupation.data
        household.head_gender = form.head_gender.data
        household.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Cập nhật hộ gia đình thành công!', 'success')
        return redirect(url_for('admin.population'))
    
    return render_template('admin/edit_household.html', form=form, household=household)

@admin_bp.route('/household/<int:id>/residents')
@login_required
@viewer_allowed
def household_residents(id):
    household = Household.query.get_or_404(id)
    residents = Resident.query.filter_by(household_id=id).all()
    from datetime import date
    current_year = date.today().year
    children_count = len([r for r in residents if r.birth_date and (current_year - r.birth_date.year) < 18])
    elderly_count = len([r for r in residents if r.birth_date and (current_year - r.birth_date.year) > 60])
    return render_template('admin/household_residents.html', household=household, residents=residents, current_year=current_year, children_count=children_count, elderly_count=elderly_count)

@admin_bp.route('/resident/add/<int:household_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def add_resident(household_id):
    household = Household.query.get_or_404(household_id)
    form = ResidentForm()
    
    if form.validate_on_submit():
        # Chuẩn hóa CMND/CCCD: bỏ khoảng trắng và trả None nếu rỗng
        id_number = (form.id_number.data or '').strip() or None
        
        # Check if ID number already exists
        if id_number:
            existing = Resident.query.filter_by(id_number=id_number).first()
            if existing:
                flash('Số CMND/CCCD đã tồn tại.', 'error')
                return render_template('admin/add_resident.html', form=form, household=household)
        
        resident = Resident(
            full_name=form.full_name.data,
            birth_date=form.birth_date.data,
            gender=form.gender.data,
            id_number=id_number,
            relationship=form.relationship.data,
            occupation=form.occupation.data,
            phone=form.phone.data,
            notes=form.notes.data,
            current_lat=form.current_lat.data,
            current_lng=form.current_lng.data,
            household_id=household_id
        )
        
        db.session.add(resident)
        db.session.commit()
        
        flash('Thêm nhân khẩu thành công!', 'success')
        return redirect(url_for('admin.household_residents', id=household_id))
    
    return render_template('admin/add_resident.html', form=form, household=household)

@admin_bp.route('/resident/<int:id>')
@login_required
@viewer_allowed
def view_resident(id):
    resident = Resident.query.get_or_404(id)
    household = Household.query.get_or_404(resident.household_id)
    from datetime import date
    current_year = date.today().year
    return render_template('admin/resident_detail.html', resident=resident, household=household, current_year=current_year)

@admin_bp.route('/resident/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_resident(id):
    resident = Resident.query.get_or_404(id)
    household_id = resident.household_id
    # Xóa các bản ghi liên quan để tránh lỗi khóa ngoại
    try:
        TemporaryResidence.query.filter_by(resident_id=id).delete(synchronize_session=False)
    except Exception:
        pass
    try:
        Beneficiary.query.filter_by(resident_id=id).delete(synchronize_session=False)
    except Exception:
        pass
    db.session.delete(resident)
    db.session.commit()
    flash('Đã xóa nhân khẩu.', 'success')
    return redirect(url_for('admin.household_residents', id=household_id))

@admin_bp.route('/resident/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_resident(id):
    resident = Resident.query.get_or_404(id)
    household = Household.query.get_or_404(resident.household_id)
    form = ResidentForm(obj=resident)
    if form.validate_on_submit():
        # Chuẩn hóa CMND/CCCD: bỏ khoảng trắng và trả None nếu rỗng
        id_number = (form.id_number.data or '').strip() or None
        if id_number:
            existing = Resident.query.filter(
                Resident.id_number == id_number,
                Resident.id != id
            ).first()
            if existing:
                flash('Số CMND/CCCD đã tồn tại.', 'error')
                return render_template('admin/edit_resident.html', form=form, resident=resident, household=household)

        resident.full_name = form.full_name.data
        resident.birth_date = form.birth_date.data
        resident.gender = form.gender.data
        resident.id_number = id_number
        resident.relationship = form.relationship.data
        resident.occupation = form.occupation.data
        resident.phone = form.phone.data
        resident.notes = form.notes.data
        resident.current_lat = form.current_lat.data
        resident.current_lng = form.current_lng.data
        resident.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Cập nhật nhân khẩu thành công!', 'success')
        return redirect(url_for('admin.household_residents', id=resident.household_id))

    return render_template('admin/edit_resident.html', form=form, resident=resident, household=household)

@admin_bp.route('/resident/<int:resident_id>/temporary', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_temporary_residence(resident_id):
    resident = Resident.query.get_or_404(resident_id)
    form = TemporaryResidenceForm()
    if form.validate_on_submit():
        tr = TemporaryResidence(
            type=form.type.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            destination=form.destination.data,
            reason=form.reason.data,
            contact_info=form.contact_info.data,
            lat=form.lat.data,
            lng=form.lng.data,
            resident_id=0 if form.is_for_head.data else resident_id,
            head_household_id=resident.household_id if form.is_for_head.data else None,
            is_for_head=form.is_for_head.data
        )
        db.session.add(tr)
        db.session.commit()
        # Sync resident current location if this record applies to the resident and is active
        if not tr.is_for_head and tr.is_active and tr.resident_id:
            res = Resident.query.get(tr.resident_id)
            if res:
                res.current_lat = tr.lat
                res.current_lng = tr.lng
                db.session.commit()
        flash('Đã lưu thông tin tạm trú/tạm vắng.', 'success')
        return redirect(url_for('admin.manage_temporary_residence', resident_id=resident_id))

    records = TemporaryResidence.query.filter_by(resident_id=resident_id).order_by(TemporaryResidence.start_date.desc()).all()
    return render_template('admin/temporary_residence.html', resident=resident, form=form, records=records)

@admin_bp.route('/household/<int:household_id>/temporary', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_head_temporary(household_id):
    household = Household.query.get_or_404(household_id)
    form = TemporaryResidenceForm()
    if request.method == 'GET':
        form.is_for_head.data = True
    if form.validate_on_submit():
        tr = TemporaryResidence(
            type=form.type.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            destination=form.destination.data,
            reason=form.reason.data,
            contact_info=form.contact_info.data,
            lat=form.lat.data,
            lng=form.lng.data,
            resident_id=0,
            head_household_id=household_id,
            is_for_head=True
        )
        db.session.add(tr)
        db.session.commit()
        # Sync household map location if this record is active and has coordinates
        if tr.is_for_head and tr.is_active and tr.head_household_id:
            hh = Household.query.get(tr.head_household_id)
            if hh:
                hh.location_lat = tr.lat
                hh.location_lng = tr.lng
                db.session.commit()
        flash('Đã lưu thông tin tạm trú/tạm vắng cho Chủ hộ.', 'success')
        return redirect(url_for('admin.manage_head_temporary', household_id=household_id))

    records = TemporaryResidence.query.filter_by(head_household_id=household_id).order_by(TemporaryResidence.start_date.desc()).all()
    return render_template('admin/temporary_residence_head.html', household=household, form=form, records=records)

@admin_bp.route('/temporary/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_temporary_residence(id):
    record = TemporaryResidence.query.get_or_404(id)
    resident = None
    household = None
    if record.is_for_head:
        household = Household.query.get_or_404(record.head_household_id)
    else:
        resident = Resident.query.get_or_404(record.resident_id)
    form = TemporaryResidenceForm(obj=record)
    if form.validate_on_submit():
        record.type = form.type.data
        record.start_date = form.start_date.data
        record.end_date = form.end_date.data
        record.destination = form.destination.data
        record.reason = form.reason.data
        record.contact_info = form.contact_info.data
        record.lat = form.lat.data
        record.lng = form.lng.data
        record.updated_at = datetime.utcnow()
        db.session.commit()
        # Sync resident current location if applicable
        if not record.is_for_head and record.is_active and record.resident_id:
            res = Resident.query.get(record.resident_id)
            if res:
                res.current_lat = record.lat
                res.current_lng = record.lng
                db.session.commit()
        # Sync household location if this is a head record
        if record.is_for_head and record.is_active and record.head_household_id:
            hh = Household.query.get(record.head_household_id)
            if hh:
                hh.location_lat = record.lat
                hh.location_lng = record.lng
                db.session.commit()
        flash('Đã cập nhật bản ghi tạm trú/tạm vắng.', 'success')
        if record.is_for_head:
            return redirect(url_for('admin.manage_head_temporary', household_id=record.head_household_id))
        else:
            return redirect(url_for('admin.manage_temporary_residence', resident_id=record.resident_id))
    return render_template('admin/edit_temporary_residence.html', form=form, resident=resident, household=household, record=record)

@admin_bp.route('/temporary/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_temporary_residence(id):
    record = TemporaryResidence.query.get_or_404(id)
    resident_id = record.resident_id
    db.session.delete(record)
    db.session.commit()
    # Clear resident location if this active record was the source of sync
    if resident_id:
        res = Resident.query.get(resident_id)
        if res:
            res.current_lat = None
            res.current_lng = None
            db.session.commit()
    # Clear household location if this was a head record
    if record.is_for_head and record.head_household_id:
        hh = Household.query.get(record.head_household_id)
        if hh:
            hh.location_lat = None
            hh.location_lng = None
            db.session.commit()
    flash('Đã xóa bản ghi tạm trú/tạm vắng.', 'success')
    return redirect(url_for('admin.manage_temporary_residence', resident_id=resident_id))

@admin_bp.route('/temporary-management')
@login_required
@viewer_allowed
def temporary_overview():
    page = request.args.get('page', 1, type=int)
    tmp_type = request.args.get('type', '')
    status = request.args.get('status', '')  # active/inactive
    hamlet = request.args.get('hamlet', '')
    search = request.args.get('search', '')

    query = db.session.query(TemporaryResidence, Resident, Household) 
    query = query.outerjoin(Resident, TemporaryResidence.resident_id == Resident.id)
    query = query.outerjoin(Household, db.or_(Resident.household_id == Household.id, TemporaryResidence.head_household_id == Household.id))

    if tmp_type:
        query = query.filter(TemporaryResidence.type == tmp_type)
    if status == 'active':
        query = query.filter(TemporaryResidence.is_active.is_(True))
    elif status == 'inactive':
        query = query.filter(TemporaryResidence.is_active.is_(False))
    if hamlet:
        query = query.filter(Household.hamlet == hamlet)
    if search:
        query = query.filter(db.or_(Resident.full_name.contains(search), Household.household_code.contains(search)))

    query = query.order_by(TemporaryResidence.start_date.desc())

    per_page = 20
    total = query.count()
    items = query.limit(per_page).offset((page-1)*per_page).all()

    hamlets = [h[0] for h in db.session.query(Household.hamlet).distinct().all()]

    return render_template('admin/temporary_overview.html',
                           items=items,
                           page=page,
                           per_page=per_page,
                           total=total,
                           tmp_type=tmp_type,
                           status=status,
                           hamlet=hamlet,
                           hamlets=hamlets,
                           search=search)

# Benefits management
@admin_bp.route('/benefits')
@login_required
@viewer_allowed
def benefits():
    categories = BenefitCategory.query.order_by(BenefitCategory.name).all()
    target_type = request.args.get('target_type', '')
    status = request.args.get('status', '')  # active/inactive
    category_id = request.args.get('category_id', type=int)
    hamlet = request.args.get('hamlet', '')
    q = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)

    query = db.session.query(Beneficiary, BenefitCategory, Household, Resident) 
    query = query.join(BenefitCategory, Beneficiary.category_id == BenefitCategory.id)
    query = query.outerjoin(Household, Beneficiary.household_id == Household.id)
    query = query.outerjoin(Resident, Beneficiary.resident_id == Resident.id)

    if target_type:
        query = query.filter(Beneficiary.target_type == target_type)
    if status == 'active':
        query = query.filter(Beneficiary.is_active.is_(True))
    elif status == 'inactive':
        query = query.filter(Beneficiary.is_active.is_(False))
    if category_id:
        query = query.filter(Beneficiary.category_id == category_id)
    if hamlet:
        # áp dụng cho hộ trực tiếp hoặc hộ của nhân khẩu
        query = query.filter(db.or_(Household.hamlet == hamlet, Resident.household.has(Household.hamlet == hamlet)))
    if q:
        query = query.filter(
            db.or_(
                Household.household_code.contains(q),
                Household.head_of_household.contains(q),
                Resident.full_name.contains(q)
            )
        )

    query = query.order_by(Beneficiary.created_at.desc())

    # Export CSV
    if request.args.get('export') == 'csv':
        from io import StringIO
        import csv
        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(['Đối tượng', 'Mã hộ', 'Họ tên', 'Danh mục', 'Bắt đầu', 'Kết thúc', 'Thôn/Xóm', 'Trạng thái'])
        for b, c, h, r in query.all():
            household_code = (h.household_code if h else (r.household.household_code if r and r.household else ''))
            fullname = (r.full_name if r else (h.head_of_household if h else ''))
            hamlet_name = (h.hamlet if h else (r.household.hamlet if r and r.household else ''))
            writer.writerow([
                'Hộ' if b.target_type == 'household' else 'Nhân khẩu',
                household_code,
                fullname,
                c.name,
                b.start_date.isoformat() if b.start_date else '',
                b.end_date.isoformat() if b.end_date else '',
                hamlet_name,
                'Đang hiệu lực' if b.is_active else 'Ngừng'
            ])
        response = make_response(si.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = 'attachment; filename=doi_tuong_chinh_sach.csv'
        return response

    per_page = 20
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    # Payments removed: no schedules/overdue logic needed
    # danh sách thôn/xóm
    hamlets = [h[0] for h in db.session.query(Household.hamlet).distinct().all()]

    return render_template('admin/benefits.html',
                           categories=categories,
                           items=items,
                           target_type=target_type,
                           status=status,
                           category_id=category_id,
                           hamlet=hamlet,
                           hamlets=hamlets,
                           q=q,
                           page=page,
                           per_page=per_page)

@admin_bp.route('/benefits/category/<int:category_id>')
@login_required
@viewer_allowed
def benefits_by_category(category_id):
    c = BenefitCategory.query.get_or_404(category_id)
    target_type = request.args.get('target_type', '')
    status = request.args.get('status', '')
    hamlet = request.args.get('hamlet', '')
    q = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)

    query = db.session.query(Beneficiary, Household, Resident)
    query = query.filter(Beneficiary.category_id == category_id)
    query = query.outerjoin(Household, Beneficiary.household_id == Household.id)
    query = query.outerjoin(Resident, Beneficiary.resident_id == Resident.id)
    if target_type:
        query = query.filter(Beneficiary.target_type == target_type)
    if status == 'active':
        query = query.filter(Beneficiary.is_active.is_(True))
    elif status == 'inactive':
        query = query.filter(Beneficiary.is_active.is_(False))
    if hamlet:
        query = query.filter(db.or_(Household.hamlet == hamlet, Resident.household.has(Household.hamlet == hamlet)))
    if q:
        query = query.filter(db.or_(Household.household_code.contains(q), Household.head_of_household.contains(q), Resident.full_name.contains(q)))

    per_page = 20
    items = query.order_by(Beneficiary.created_at.desc()).limit(per_page).offset((page-1)*per_page).all()
    hamlets = [h[0] for h in db.session.query(Household.hamlet).distinct().all()]

    return render_template('admin/benefits_category.html',
                           category=c,
                           items=items,
                           target_type=target_type,
                           status=status,
                           hamlet=hamlet,
                           hamlets=hamlets,
                           q=q,
                           page=page,
                           per_page=per_page)

@admin_bp.route('/benefits/beneficiary/<int:id>/toggle-paid', methods=['POST'])
@login_required
@admin_required
def toggle_beneficiary_paid(id):
    b = Beneficiary.query.get_or_404(id)
    b.is_paid = not getattr(b, 'is_paid', False)
    db.session.commit()
    flash('Đã cập nhật trạng thái chi trả.', 'success')
    return redirect(url_for('admin.benefits'))

# Remove quick-add payment: schedules no longer used

@admin_bp.route('/benefits/category/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_benefit_category(id):
    cat = BenefitCategory.query.get_or_404(id)
    form = BenefitCategoryForm(obj=cat)
    if form.validate_on_submit():
        cat.code = form.code.data
        cat.name = form.name.data
        cat.target_type = form.target_type.data
        cat.support_amount = form.support_amount.data
        db.session.commit()
        flash('Đã cập nhật danh mục.', 'success')
        return redirect(url_for('admin.benefits'))
    return render_template('admin/benefit_category_form.html', form=form)

@admin_bp.route('/benefits/category/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_benefit_category(id):
    cat = BenefitCategory.query.get_or_404(id)
    db.session.delete(cat)
    db.session.commit()
    flash('Đã xóa danh mục.', 'success')
    return redirect(url_for('admin.benefits'))

@admin_bp.route('/benefits/beneficiary/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_beneficiary(id):
    b = Beneficiary.query.get_or_404(id)
    form = BeneficiaryForm(obj=b)
    form.category_id.choices = [(c.id, c.name) for c in BenefitCategory.query.order_by(BenefitCategory.name).all()]
    form.household_id.choices = [(h.id, f"{h.household_code} - {h.head_of_household}") for h in Household.query.order_by(Household.household_code).all()]
    form.resident_id.choices = [(0, '— Không chọn —')] + [(r.id, f"{r.full_name} ({r.household.household_code})") for r in Resident.query.order_by(Resident.full_name).all()]
    if form.validate_on_submit():
        b.target_type = form.target_type.data
        b.household_id = form.household_id.data if form.target_type.data == 'household' else None
        b.resident_id = (None if form.target_type.data == 'household' else (None if form.resident_id.data == 0 else form.resident_id.data))
        b.category_id = form.category_id.data
        b.start_date = form.start_date.data
        b.end_date = form.end_date.data
        b.is_active = form.is_active.data
        b.support_amount = form.support_amount.data
        b.notes = form.notes.data
        db.session.commit()
        flash('Đã cập nhật đối tượng.', 'success')
        return redirect(url_for('admin.benefits'))
    return render_template('admin/beneficiary_form.html', form=form)

@admin_bp.route('/benefits/beneficiary/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_beneficiary(id):
    b = Beneficiary.query.get_or_404(id)
    # Remove related payment rows to satisfy NOT NULL FK on benefit_payment.beneficiary_id
    try:
        BenefitPayment.query.filter_by(beneficiary_id=id).delete(synchronize_session=False)
    except Exception:
        pass
    db.session.delete(b)
    db.session.commit()
    flash('Đã xóa đối tượng.', 'success')
    return redirect(url_for('admin.benefits'))

@admin_bp.route('/benefits/category/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_benefit_category():
    form = BenefitCategoryForm()
    if form.validate_on_submit():
        cat = BenefitCategory(code=form.code.data, name=form.name.data, target_type=form.target_type.data, support_amount=form.support_amount.data)
        db.session.add(cat)
        db.session.commit()
        flash('Đã thêm danh mục.', 'success')
        return redirect(url_for('admin.benefits'))
    return render_template('admin/benefit_category_form.html', form=form)

@admin_bp.route('/benefits/beneficiary/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_beneficiary():
    form = BeneficiaryForm()
    # Populate select choices
    form.category_id.choices = [(c.id, c.name) for c in BenefitCategory.query.order_by(BenefitCategory.name).all()]
    form.household_id.choices = [(h.id, f"{h.household_code} - {h.head_of_household}") for h in Household.query.order_by(Household.household_code).all()]
    # Default target_type to household on first load
    if not form.target_type.data:
        form.target_type.data = 'household'
    # If target is household, keep resident select as a placeholder
    if form.target_type.data == 'household':
        form.resident_id.choices = [(0, '— Không chọn —')]
    else:
        # limit residents by selected household if provided
        try:
            selected_household_id = int(request.form.get('household_id') or 0)
        except Exception:
            selected_household_id = 0
        if selected_household_id:
            form.resident_id.choices = [(r.id, f"{r.full_name} ({r.household.household_code})") for r in Resident.query.filter_by(household_id=selected_household_id).order_by(Resident.full_name).all()]
        else:
            form.resident_id.choices = [(0, '— Không chọn —')]
    if form.validate_on_submit():
        b = Beneficiary(
            target_type=form.target_type.data,
            household_id=form.household_id.data if form.target_type.data == 'household' else None,
            resident_id=form.resident_id.data if form.target_type.data == 'resident' else None,
            category_id=form.category_id.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            is_active=form.is_active.data,
            support_amount=form.support_amount.data,
            notes=form.notes.data
        )
        db.session.add(b)
        db.session.commit()
        flash('Đã thêm đối tượng.', 'success')
        return redirect(url_for('admin.benefits'))
    return render_template('admin/beneficiary_form.html', form=form)

@admin_bp.route('/api/household/<int:household_id>/residents')
@login_required
@admin_required
def api_household_residents(household_id):
    residents = Resident.query.filter_by(household_id=household_id).order_by(Resident.full_name).all()
    data = [{
        'id': r.id,
        'full_name': r.full_name,
        'household_code': r.household.household_code if r.household else ''
    } for r in residents]
    return jsonify(data)

## Schedules removed

@admin_bp.route('/export/residents')
@login_required
@admin_required
def export_residents():
    format_type = request.args.get('format', 'csv')
    hamlet = request.args.get('hamlet', '')
    
    # Base query
    residents_query = Resident.query.join(Household)
    
    if hamlet:
        residents_query = residents_query.filter(Household.hamlet == hamlet)
    
    residents = residents_query.all()
    
    if format_type == 'xml':
        data = export_residents_to_xml(residents)
        response = make_response(data)
        response.headers['Content-Type'] = 'application/xml'
        response.headers['Content-Disposition'] = 'attachment; filename=danh_sach_dan_cu.xml'
    else:
        data = export_residents_to_csv(residents)
        response = make_response(data)
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = 'attachment; filename=danh_sach_dan_cu.csv'
    
    return response

@admin_bp.route('/feedback-management')
@login_required
@viewer_allowed
def feedback_management():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    category = request.args.get('category', '')
    kind = request.args.get('kind', '')
    
    # Base query
    feedbacks_query = Feedback.query
    
    # Apply filters
    if status:
        feedbacks_query = feedbacks_query.filter(Feedback.status == status)
    
    if category:
        feedbacks_query = feedbacks_query.filter(Feedback.category == category)
    if kind:
        feedbacks_query = feedbacks_query.filter(Feedback.kind == kind)
        
    severity = request.args.get('severity', '')
    if severity == 'high':
        # Chỉ lấy 'Cao' với độ tin cậy >= 85%
        feedbacks_query = feedbacks_query.filter(
            Feedback.severity == 'high',
            Feedback.severity_confidence >= 0.85
        )
    elif severity == 'medium':
        # Lấy 'Trung bình' + các trường hợp 'Cao' nhưng độ tin cậy < 85%
        feedbacks_query = feedbacks_query.filter(
            db.or_(
                Feedback.severity == 'medium',
                db.and_(Feedback.severity == 'high', Feedback.severity_confidence < 0.85)
            )
        )
    elif severity == 'low':
        feedbacks_query = feedbacks_query.filter(Feedback.severity == 'low')
    
    # Sắp xếp theo thời gian: mới nhất hiển thị trên cùng
    feedbacks_query = feedbacks_query.order_by(
        Feedback.created_at.desc()
    )
    
    # Pagination
    feedbacks = feedbacks_query.paginate(
        page=page, per_page=20, error_out=False
    )
    # Parse attachments for display
    attachments_map = {}
    for f in feedbacks.items:
        try:
            attachments_map[f.id] = json.loads(f.attachments) if f.attachments else []
        except Exception:
            attachments_map[f.id] = []

    # AI classify info (for display: confidence + reasons)
    classify_info_map = {}
    for f in feedbacks.items:
        try:
            label, conf, reasons = _classify_feedback_text(f.title or '', f.description or '')
            classify_info_map[f.id] = {
                'label': label,
                'confidence': conf,
                'reasons': reasons,
            }
        except Exception:
            classify_info_map[f.id] = {'label': f.kind or 'phan_anh', 'confidence': 0.6, 'reasons': []}

    return render_template('admin/feedback_management.html',
                         feedbacks=feedbacks,
                         status=status,
                         category=category,
                         kind=kind,
                         attachments_map=attachments_map,
                         classify_info_map=classify_info_map)

@admin_bp.route('/feedback/<int:id>/classify', methods=['POST'])
@login_required
@admin_required
def classify_feedback(id):
    """Phân loại phản ánh sử dụng AI."""
    fb = Feedback.query.get_or_404(id)
    from services.feedback_classifier import FeedbackClassifier
    classifier = FeedbackClassifier()
    result = classifier.classify(fb.title or '', fb.description or '')
    
    fb.kind = result['label']
    fb.severity = result['severity']
    fb.severity_confidence = result['severity_confidence']
    
    db.session.commit()
    severity_confidence = int(result["severity_confidence"]*100)
    severity_level = "Cao" if result["severity"] == "high" else "Trung bình" if result["severity"] == "medium" else "Thấp"
    
    # Xác định loại thông báo dựa trên mức độ nghiêm trọng và độ tin cậy
    message_type = 'success'
    if result["severity"] == "high" and severity_confidence >= 85:
        message_type = 'danger'
    elif result["severity"] == "medium" or (result["severity"] == "high" and severity_confidence < 85):
        message_type = 'warning'
    
    flash(
        f'Đã phân loại: {"Phản ánh" if result["label"] == "phan_anh" else "Khiếu nại"} '
        f'(tin cậy {int(result["confidence"]*100)}%) - '
        f'Mức độ: {severity_level} '
        f'(tin cậy {severity_confidence}%)', 
        message_type
    )
    return redirect(url_for('admin.feedback_management'))

@admin_bp.route('/feedback/classify-all')
@login_required
@admin_required
def classify_all_feedbacks():
    import logging
    from services.feedback_classifier import FeedbackClassifier
    classifier = FeedbackClassifier()
    
    count = 0
    updated_kind = 0
    updated_severity = 0
    
    for fb in Feedback.query.all():
        result = classifier.classify(fb.title or '', fb.description or '')
        
        # Cập nhật phân loại phản ánh/khiếu nại
        if result['confidence'] >= 0.7 and (fb.kind != result['label']):
            old_kind = fb.kind
            fb.kind = result['label']
            updated_kind += 1
            logging.info(f"Cập nhật phân loại ID {fb.id}: {old_kind} -> {result['label']} (tin cậy: {result['confidence']:.0%})")
        
        # Cập nhật mức độ nghiêm trọng (không hạ bậc)
        severity_confidence = result['severity_confidence']
        actual_severity = result['severity']
        
        if fb.severity != actual_severity or (fb.severity_confidence != severity_confidence):
            old_severity = fb.severity
            fb.severity = actual_severity
            fb.severity_confidence = severity_confidence
            updated_severity += 1
            logging.info(f"Cập nhật mức độ ID {fb.id}: {old_severity} -> {actual_severity} (tin cậy: {severity_confidence:.0%})")
        
        count += 1
    
    db.session.commit()
    
    if updated_kind > 0 or updated_severity > 0:
        flash(f'AI đã kiểm tra {count} mục: cập nhật {updated_kind} phân loại và {updated_severity} mức độ nghiêm trọng.', 'success')
    else:
        flash(f'AI đã kiểm tra {count} mục. Các phân loại hiện tại đều đã chính xác.', 'info')
    
    return redirect(url_for('admin.feedback_management'))

def _classify_feedback_text(title: str, description: str):
    """Phân loại phản ánh/khiếu nại sử dụng FeedbackClassifier."""
    from services.feedback_classifier import FeedbackClassifier
    
    try:
        classifier = FeedbackClassifier()
        result = classifier.classify(title, description)
        
        return (
            result['label'],
            result['confidence'],
            result['important_terms']
        )
    except Exception as e:
        # Log error
        import logging
        logging.error(f"Classification error: {str(e)}")
        
        # Return safe default
        return 'phan_anh', 0.6, []

    # Weighted heuristic: title keywords x2, description x1; more coverage -> higher confidence
    complaint_keywords = [
        'khiếu nại','khieu nai','tố cáo','to cao','không đồng ý','khong dong y',
        'đề nghị giải quyết','de nghi giai quyet','yêu cầu xử lý','yeu cau xu ly',
        'quyết định','quyet dinh','bồi thường','boi thuong','kỷ luật','ky luat'
    ]
    report_keywords = [
        'phản ánh','phan anh','phản hồi','phan hoi','phản ánh hiện trường','hien truong',
        'ổ gà','o ga','rác thải','rac thai','mất điện','mat dien','an ninh','còi kéo','coi keo'
    ]
    reasons = []
    score_complaint = 0
    score_report = 0
    t = (title or '').lower()
    d = (description or '').lower()
    for k in complaint_keywords:
        if k in t:
            score_complaint += 2
            reasons.append(k)
        if k in d:
            score_complaint += 1
            if k not in reasons:
                reasons.append(k)
    for k in report_keywords:
        if k in t:
            score_report += 2
        if k in d:
            score_report += 1
    if score_complaint > score_report:
        # confidence from normalized margin
        margin = max(1, score_complaint - score_report)
        conf = min(0.95, 0.6 + 0.08 * min(5, margin))
        return 'khieu_nai', conf, reasons[:3]
    else:
        margin = max(1, score_report - score_complaint)
        conf = min(0.95, 0.6 + 0.08 * min(5, margin))
        return 'phan_anh', conf, reasons[:3]

@admin_bp.route('/feedback/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_feedback(id):
    fb = Feedback.query.get_or_404(id)
    # Optionally remove files from storage
    try:
        if fb.attachments:
            files = json.loads(fb.attachments)
            import os
            base = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            for f in files:
                path = os.path.join(base, f)
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass
    except Exception:
        pass
    db.session.delete(fb)
    db.session.commit()
    flash('Đã xoá phản ánh/khiếu nại.', 'success')
    return redirect(url_for('admin.feedback_management'))

@admin_bp.route('/feedback/<int:id>/update', methods=['POST'])
@login_required
@admin_required
def update_feedback(id):
    feedback = Feedback.query.get_or_404(id)
    
    status = request.form.get('status')
    admin_response = request.form.get('admin_response')
    
    if status:
        feedback.status = status
        if status == 'resolved':
            feedback.resolved_at = datetime.utcnow()
    
    if admin_response:
        feedback.admin_response = admin_response
    
    feedback.updated_at = datetime.utcnow()
    db.session.commit()
    
    flash('Cập nhật phản ánh thành công!', 'success')
    # Notify user via email if available (rich content)
    try:
        user = User.query.get(feedback.user_id)
        if user and user.email:
            subject = 'Cập nhật phản ánh của bạn'
            # Friendly status mapping
            status_map = {
                'pending': 'Chờ xử lý',
                'in_progress': 'Đang xử lý',
                'resolved': 'Đã giải quyết',
                'rejected': 'Từ chối',
            }
            status_vn = status_map.get(feedback.status, feedback.status)
            # Build view link for user
            try:
                detail_url = url_for('citizen.feedback_detail', id=feedback.id, _external=True)
            except Exception:
                detail_url = url_for('citizen.feedback_detail', id=feedback.id)
            # Plain text fallback
            body_text = (
                f'Xin chào {user.full_name},\n\n'
                f'Phản ánh: {feedback.title}\n'
                f'Trạng thái: {status_vn}\n'
                f'Phản hồi từ cán bộ: {feedback.admin_response or "—"}\n'
                f'Địa điểm: {feedback.location or "(không cung cấp)"}\n'
                f'Ngày cập nhật: {feedback.updated_at.strftime("%d/%m/%Y %H:%M") if feedback.updated_at else "—"}\n\n'
                f'Xem chi tiết: {detail_url}\n'
            )
            # HTML content
            body_html = (
                f'<div style="font-family:Segoe UI,Arial,sans-serif;font-size:14px">'
                f'<h3 style="margin:0 0 8px">Cập nhật phản ánh của bạn</h3>'
                f'<p><strong>Tiêu đề:</strong> {feedback.title}</p>'
                f'<p><strong>Trạng thái:</strong> {status_vn}</p>'
                f'<p><strong>Phản hồi từ cán bộ:</strong><br>{(feedback.admin_response or "—")}</p>'
                f'{f"<p><strong>Địa điểm:</strong> {feedback.location}</p>" if feedback.location else ""}'
                f'{f"<p><strong>Cập nhật lúc:</strong> {feedback.updated_at.strftime('%d/%m/%Y %H:%M')}</p>" if feedback.updated_at else ""}'
                f'<p style="margin-top:12px"><a href="{detail_url}" style="display:inline-block;background:#0d6efd;color:#fff;padding:8px 12px;border-radius:4px;text-decoration:none">Xem chi tiết</a></p>'
                f'</div>'
            )
            send_email(subject, [user.email], body_text=body_text, body_html=body_html)
    except Exception:
        pass
    return redirect(url_for('admin.feedback_management'))

@admin_bp.route('/bulletin-management')
@login_required
@viewer_allowed
def bulletin_management():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    
    # Base query
    announcements_query = Announcement.query
    
    # Apply filters
    if category:
        announcements_query = announcements_query.filter(Announcement.category == category)
    
    # Order by creation date, newest first
    announcements_query = announcements_query.order_by(Announcement.created_at.desc())
    
    # Pagination
    announcements = announcements_query.paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/bulletin_management.html',
                         announcements=announcements,
                         category=category)

@admin_bp.route('/ai/chat', methods=['POST'])
@login_required
@admin_required
def ai_chat():
    data = request.get_json(silent=True) or {}
    message = data.get('message', '')
    domain = data.get('domain', 'auto')
    result = chatbot_answer(message, domain)
    return jsonify(result)

@admin_bp.route('/announcement/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_announcement():
    form = AnnouncementForm()
    
    if form.validate_on_submit():
        # Handle file upload
        attachments = []
        if form.attachments.data:
            filename = save_uploaded_file(form.attachments.data, 'announcements')
            if filename:
                attachments.append(filename)
        
        announcement = Announcement(
            title=form.title.data,
            content=form.content.data,
            category=form.category.data,
            priority=form.priority.data,
            is_published=form.is_published.data,
            publish_date=form.publish_date.data or datetime.utcnow(),
            attachments=json.dumps(attachments) if attachments else None,
            created_by=current_user.id
        )
        
        db.session.add(announcement)
        db.session.commit()
        
        flash('Thêm thông báo thành công!', 'success')
        # Notify all active citizen users by email with detail link
        try:
            recipients = [u.email for u in User.query.filter_by(role='citizen', is_active=True).all() if u.email]
            if recipients:
                subject = 'Thông báo mới từ UBND xã'
                # Build detail link
                try:
                    detail_url = url_for('bulletin.detail', id=announcement.id, _external=True)
                except Exception:
                    detail_url = url_for('bulletin.detail', id=announcement.id)
                # Map category/priority
                cat_map = {
                    'general': 'Chung',
                    'policy': 'Chính sách',
                    'event': 'Sự kiện',
                }
                pri_map = {
                    'low': 'Thấp',
                    'normal': 'Bình thường',
                    'high': 'Cao',
                }
                cat_vn = cat_map.get(announcement.category, announcement.category or 'Chung')
                pri_vn = pri_map.get(announcement.priority, announcement.priority or 'Bình thường')
                # Plain text
                body_text = (
                    f'Thông báo mới: {announcement.title}\n'
                    f'Phân loại: {cat_vn}\n'
                    f'Độ ưu tiên: {pri_vn}\n\n'
                    f'Xem chi tiết: {detail_url}\n'
                )
                # HTML
                body_html = (
                    f'<div style="font-family:Segoe UI,Arial,sans-serif;font-size:14px">'
                    f'<h3 style="margin:0 0 8px">{announcement.title}</h3>'
                    f'<p><strong>Phân loại:</strong> {cat_vn} &nbsp;—&nbsp; <strong>Ưu tiên:</strong> {pri_vn}</p>'
                    f'<p style="margin-top:12px"><a href="{detail_url}" style="display:inline-block;background:#0d6efd;color:#fff;padding:8px 12px;border-radius:4px;text-decoration:none">Xem chi tiết thông báo</a></p>'
                    f'</div>'
                )
                send_email(subject, recipients, body_text=body_text, body_html=body_html)
        except Exception:
            pass
        return redirect(url_for('admin.bulletin_management'))
    
    return render_template('admin/add_announcement.html', form=form)

@admin_bp.route('/announcement/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_announcement(id):
    announcement = Announcement.query.get_or_404(id)
    form = AnnouncementForm(obj=announcement)
    if form.validate_on_submit():
        announcement.title = form.title.data
        announcement.content = form.content.data
        announcement.category = form.category.data
        announcement.priority = form.priority.data
        announcement.is_published = form.is_published.data
        announcement.publish_date = form.publish_date.data or announcement.publish_date
        # Không thay đổi attachments ở form sửa đơn giản
        db.session.commit()
        flash('Đã cập nhật thông báo!', 'success')
        return redirect(url_for('admin.bulletin_management'))
    return render_template('admin/add_announcement.html', form=form, edit_mode=True)

@admin_bp.route('/announcement/<int:id>/toggle-publish')
@login_required
@admin_required
def toggle_announcement_publish(id):
    announcement = Announcement.query.get_or_404(id)
    announcement.is_published = not announcement.is_published
    if announcement.is_published and not announcement.publish_date:
        announcement.publish_date = datetime.utcnow()
    
    db.session.commit()
    
    status = 'xuất bản' if announcement.is_published else 'ẩn'
    flash(f'Đã {status} thông báo thành công!', 'success')
    return redirect(url_for('admin.bulletin_management'))

@admin_bp.route('/documents/types', methods=['GET', 'POST'])
@login_required
@admin_required
def document_types():
    form = DocumentTypeForm()
    if form.validate_on_submit():
        # check unique code
        if DocumentType.query.filter_by(code=form.code.data).first():
            flash('Mã loại giấy tờ đã tồn tại.', 'error')
        else:
            dt = DocumentType(
                code=form.code.data,
                name=form.name.data,
                description=form.description.data,
                required_fields=form.required_fields.data,
                fee=form.fee.data,
                processing_time_days=form.processing_time_days.data
            )
            db.session.add(dt)
            db.session.commit()
            flash('Đã thêm loại giấy tờ.', 'success')
            return redirect(url_for('admin.document_types'))
    # Sắp xếp theo ID tăng dần để cột # đúng thứ tự
    items = DocumentType.query.order_by(DocumentType.id.asc()).all()
    return render_template('admin/document_types.html', form=form, items=items)

@admin_bp.route('/documents/types/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_document_type(id):
    dt = DocumentType.query.get_or_404(id)
    db.session.delete(dt)
    db.session.commit()
    flash('Đã xoá loại giấy tờ.', 'success')
    return redirect(url_for('admin.document_types'))

@admin_bp.route('/documents/types/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_document_type(id):
    dt = DocumentType.query.get_or_404(id)
    form = DocumentTypeForm(obj=dt)
    if form.validate_on_submit():
        # keep code unique but allow same record
        existing = DocumentType.query.filter(DocumentType.code == form.code.data, DocumentType.id != id).first()
        if existing:
            flash('Mã loại giấy tờ đã tồn tại.', 'error')
        else:
            dt.code = form.code.data
            dt.name = form.name.data
            dt.description = form.description.data
            dt.required_fields = form.required_fields.data
            dt.fee = form.fee.data
            dt.processing_time_days = form.processing_time_days.data
            db.session.commit()
            flash('Đã cập nhật loại giấy tờ.', 'success')
            return redirect(url_for('admin.document_types'))
    return render_template('admin/document_type_form.html', form=form, edit_mode=True)

@admin_bp.route('/documents/requests')
@login_required
@viewer_allowed
def document_requests_admin():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    type_id = request.args.get('type_id', type=int)

    query = db.session.query(DocumentRequest, User, DocumentType) \
        .join(User, DocumentRequest.user_id == User.id) \
        .join(DocumentType, DocumentRequest.type_id == DocumentType.id)

    if status:
        query = query.filter(DocumentRequest.status == status)
    if type_id:
        query = query.filter(DocumentRequest.type_id == type_id)

    query = query.order_by(DocumentRequest.submitted_at.desc())

    per_page = 20
    total = query.count()
    items = query.limit(per_page).offset((page-1)*per_page).all()

    types = DocumentType.query.order_by(DocumentType.name).all()
    return render_template('admin/document_requests.html', items=items, page=page, per_page=per_page, total=total, status=status, types=types, type_id=type_id)

@admin_bp.route('/documents/requests/<int:id>', methods=['GET', 'POST'])
@login_required
@viewer_allowed
def document_request_admin_detail(id):
    dr = DocumentRequest.query.get_or_404(id)
    if request.method == 'POST':
        if current_user.role != 'admin':
            abort(403)
        new_status = request.form.get('status')
        admin_comment = request.form.get('admin_comment')
        expected_pickup_date = request.form.get('expected_pickup_date')
        if new_status:
            dr.status = new_status
        if admin_comment is not None:
            dr.admin_comment = admin_comment
        if expected_pickup_date:
            try:
                from datetime import datetime as dt
                dr.expected_pickup_date = dt.strptime(expected_pickup_date, '%Y-%m-%d').date()
            except Exception:
                pass
        db.session.commit()
        flash('Đã cập nhật yêu cầu.', 'success')
        # Notify requester by email with detailed info
        try:
            req_user = User.query.get(dr.user_id)
            doc_type = DocumentType.query.get(dr.type_id)
            if req_user and req_user.email:
                subject = 'Cập nhật yêu cầu giấy tờ'
                status_map = {
                    'pending': 'Chờ duyệt',
                    'in_review': 'Đang duyệt',
                    'approved': 'Đã duyệt',
                    'rejected': 'Từ chối',
                    'completed': 'Hoàn tất',
                }
                status_vn = status_map.get(dr.status, dr.status)
                # Build link
                try:
                    detail_url = url_for('citizen.document_request_detail', id=dr.id, _external=True)
                except Exception:
                    detail_url = url_for('citizen.document_request_detail', id=dr.id)
                # Plain text
                body_text = (
                    f'Xin chào {req_user.full_name},\n\n'
                    f'Yêu cầu giấy tờ #{dr.id}\n'
                    f'Loại: {(doc_type.name if doc_type else "—")}\n'
                    f'Trạng thái: {status_vn}\n'
                    f'Ghi chú cán bộ: {dr.admin_comment or "—"}\n'
                    f'Ngày hẹn trả dự kiến: {dr.expected_pickup_date.strftime("%d/%m/%Y") if dr.expected_pickup_date else "—"}\n\n'
                    f'Xem chi tiết: {detail_url}\n'
                )
                # HTML
                pickup_html = dr.expected_pickup_date.strftime('%d/%m/%Y') if dr.expected_pickup_date else '—'
                body_html = (
                    f'<div style="font-family:Segoe UI,Arial,sans-serif;font-size:14px">'
                    f'<h3 style="margin:0 0 8px">Cập nhật yêu cầu giấy tờ</h3>'
                    f'<p><strong>Mã yêu cầu:</strong> #{dr.id}</p>'
                    f'<p><strong>Loại giấy tờ:</strong> {(doc_type.name if doc_type else "—")}</p>'
                    f'<p><strong>Trạng thái:</strong> {status_vn}</p>'
                    f'<p><strong>Ghi chú cán bộ:</strong><br>{(dr.admin_comment or "—")}</p>'
                    f'<p><strong>Ngày hẹn trả dự kiến:</strong> {pickup_html}</p>'
                    f'<p style="margin-top:12px"><a href="{detail_url}" style="display:inline-block;background:#0d6efd;color:#fff;padding:8px 12px;border-radius:4px;text-decoration:none">Xem chi tiết</a></p>'
                    f'</div>'
                )
                send_email(subject, [req_user.email], body_text=body_text, body_html=body_html)
        except Exception:
            pass
        return redirect(url_for('admin.document_request_admin_detail', id=id))

    user = User.query.get(dr.user_id)
    doc_type = DocumentType.query.get(dr.type_id)
    attachments = []
    if dr.attachments:
        try:
            attachments = json.loads(dr.attachments)
        except Exception:
            attachments = []
    return render_template('admin/document_request_detail.html', dr=dr, user=user, doc_type=doc_type, attachments=attachments)

@admin_bp.route('/documents/requests/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_document_request(id):
    dr = DocumentRequest.query.get_or_404(id)
    db.session.delete(dr)
    db.session.commit()
    flash('Đã xoá yêu cầu.', 'success')
    return redirect(url_for('admin.document_requests_admin'))

@admin_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_admin_user():
    form = AdminUserForm()
    if form.validate_on_submit():
        # unique checks
        if User.query.filter_by(username=form.username.data).first():
            flash('Tên đăng nhập đã tồn tại, vui lòng chọn tên khác.', 'error')
            return render_template('admin/admin_user_form.html', form=form)
        if User.query.filter_by(email=form.email.data).first():
            flash('Email đã được sử dụng, vui lòng dùng email khác.', 'error')
            return render_template('admin/admin_user_form.html', form=form)

        from werkzeug.security import generate_password_hash
        role = form.role.data
        if role not in ['admin', 'viewer']:
            flash('Chỉ tạo tài khoản Admin hoặc Cán bộ xem.', 'error')
            return render_template('admin/admin_user_form.html', form=form)
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            phone=form.phone.data,
            role=role,
            is_active=True
        )
        user.password_hash = generate_password_hash(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Đã tạo tài khoản quản trị.', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/admin_user_form.html', form=form)

@admin_bp.route('/users')
@login_required
@viewer_allowed
def admin_users():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')
    query = User.query.filter(User.role.in_(['admin', 'viewer']))
    if q:
        query = query.filter(User.username.contains(q) | User.full_name.contains(q) | User.email.contains(q))
    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/admin_users.html', users=users, q=q)

@admin_bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_admin_user(id):
    user = User.query.get_or_404(id)
    if user.role not in ['admin', 'viewer']:
        flash('Chỉ sửa tài khoản cán bộ.', 'error')
        return redirect(url_for('admin.admin_users'))
    form = AdminUserForm(obj=user)
    # Password optional on edit
    if request.method == 'GET':
        form.password.data = ''
    if form.validate_on_submit():
        # unique checks excluding current
        if User.query.filter(User.username == form.username.data, User.id != id).first():
            flash('Tên đăng nhập đã tồn tại, vui lòng chọn tên khác.', 'error')
            return render_template('admin/admin_user_form.html', form=form)
        if User.query.filter(User.email == form.email.data, User.id != id).first():
            flash('Email đã được sử dụng, vui lòng dùng email khác.', 'error')
            return render_template('admin/admin_user_form.html', form=form)
        user.username = form.username.data
        user.email = form.email.data
        user.full_name = form.full_name.data
        user.phone = form.phone.data
        # update role (only allow admin/viewer)
        if form.role.data in ['admin', 'viewer']:
            user.role = form.role.data
        if form.password.data:
            from werkzeug.security import generate_password_hash
            user.password_hash = generate_password_hash(form.password.data)
        db.session.commit()
        flash('Đã cập nhật tài khoản quản trị.', 'success')
        return redirect(url_for('admin.admin_users'))
    return render_template('admin/admin_user_form.html', form=form, edit_mode=True)

@admin_bp.route('/users/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_admin_user(id):
    user = User.query.get_or_404(id)
    if user.role != 'admin':
        flash('Chỉ xóa tài khoản admin.', 'error')
        return redirect(url_for('admin.admin_users'))
    # Prevent deleting yourself for safety
    if user.id == current_user.id:
        flash('Không thể xóa tài khoản của chính bạn.', 'error')
        return redirect(url_for('admin.admin_users'))
    db.session.delete(user)
    db.session.commit()
    flash('Đã xóa tài khoản quản trị.', 'success')
    return redirect(url_for('admin.admin_users'))

# Citizen users management
@admin_bp.route('/users/citizens')
@login_required
@viewer_allowed
def admin_citizens():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')
    query = User.query.filter_by(role='citizen')
    if q:
        query = query.filter(User.username.contains(q) | User.full_name.contains(q) | User.email.contains(q))
    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/citizen_users.html', users=users, q=q)

@admin_bp.route('/users/citizens/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_citizen_user(id):
    user = User.query.get_or_404(id)
    if user.role != 'citizen':
        flash('Chỉ sửa tài khoản người dùng.', 'error')
        return redirect(url_for('admin.admin_citizens'))
    form = AdminUserForm(obj=user)
    if request.method == 'GET':
        form.password.data = ''
    if form.validate_on_submit():
        if User.query.filter(User.username == form.username.data, User.id != id).first():
            flash('Tên đăng nhập đã tồn tại, vui lòng chọn tên khác.', 'error')
            return render_template('admin/citizen_user_form.html', form=form)
        if User.query.filter(User.email == form.email.data, User.id != id).first():
            flash('Email đã được sử dụng, vui lòng dùng email khác.', 'error')
            return render_template('admin/citizen_user_form.html', form=form)
        user.username = form.username.data
        user.email = form.email.data
        user.full_name = form.full_name.data
        user.phone = form.phone.data
        if form.password.data:
            from werkzeug.security import generate_password_hash
            user.password_hash = generate_password_hash(form.password.data)
        db.session.commit()
        flash('Đã cập nhật tài khoản người dùng.', 'success')
        return redirect(url_for('admin.admin_citizens'))
    return render_template('admin/citizen_user_form.html', form=form)

@admin_bp.route('/users/citizens/<int:id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_citizen_active(id):
    user = User.query.get_or_404(id)
    if user.role != 'citizen':
        flash('Chỉ thao tác với tài khoản người dùng.', 'error')
        return redirect(url_for('admin.admin_citizens'))
    user.is_active = not user.is_active
    db.session.commit()
    flash('Đã cập nhật trạng thái tài khoản.', 'success')
    return redirect(url_for('admin.admin_citizens'))

@admin_bp.route('/users/citizens/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_citizen_user(id):
    user = User.query.get_or_404(id)
    if user.role != 'citizen':
        flash('Chỉ xóa tài khoản người dùng.', 'error')
        return redirect(url_for('admin.admin_citizens'))
    db.session.delete(user)
    db.session.commit()
    flash('Đã xóa tài khoản người dùng.', 'success')
    return redirect(url_for('admin.admin_citizens'))
