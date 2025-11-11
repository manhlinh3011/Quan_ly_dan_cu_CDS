from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SelectField, IntegerField, DateField, BooleanField, PasswordField, FloatField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange, ValidationError
from wtforms.widgets import TextArea
class BenefitCategoryForm(FlaskForm):
    code = StringField('Mã danh mục', validators=[DataRequired(message='Vui lòng nhập Mã danh mục.'), Length(max=50)])
    name = StringField('Tên danh mục', validators=[DataRequired(message='Vui lòng nhập Tên danh mục.'), Length(max=120)])
    target_type = SelectField('Áp dụng cho', choices=[('household', 'Hộ gia đình'), ('resident', 'Nhân khẩu')], validators=[DataRequired()])
    support_amount = IntegerField('Mức hỗ trợ mặc định (VND)', validators=[Optional(), NumberRange(min=0, message='Số tiền không âm')])

class BeneficiaryForm(FlaskForm):
    target_type = SelectField('Đối tượng', choices=[('household', 'Hộ gia đình'), ('resident', 'Nhân khẩu')], validators=[DataRequired(message='Vui lòng chọn Đối tượng.')])
    household_id = SelectField('Hộ gia đình', choices=[], coerce=int, validators=[Optional()])
    resident_id = SelectField('Nhân khẩu', choices=[], coerce=int, validators=[Optional()])
    category_id = SelectField('Danh mục', choices=[], coerce=int, validators=[DataRequired(message='Vui lòng chọn Danh mục.')])
    start_date = DateField('Ngày bắt đầu', validators=[DataRequired(message='Vui lòng nhập Ngày bắt đầu.')])
    end_date = DateField('Ngày kết thúc', validators=[Optional()])
    is_active = BooleanField('Đang hiệu lực')
    support_amount = IntegerField('Mức hỗ trợ (VND)', validators=[Optional(), NumberRange(min=0, message='Số tiền không âm')])
    notes = StringField('Ghi chú', validators=[Optional(), Length(max=255)])

    def validate(self, extra_validators=None):
        is_valid = super().validate(extra_validators=extra_validators)
        # Ràng buộc Ngày kết thúc bắt buộc và phải sau/ngang Ngày bắt đầu
        if not self.end_date.data:
            self.end_date.errors.append('Vui lòng nhập Ngày kết thúc.')
            return False
        if self.start_date.data and self.end_date.data < self.start_date.data:
            self.end_date.errors.append('Ngày kết thúc phải sau hoặc bằng Ngày bắt đầu.')
            return False
        return is_valid

class BenefitPaymentForm(FlaskForm):
    beneficiary_id = SelectField('Đối tượng', choices=[], coerce=int, validators=[DataRequired()])
    period = StringField('Kỳ chi trả (YYYY-MM)', validators=[DataRequired(), Length(max=7)])
    amount = IntegerField('Số tiền (VND)', validators=[DataRequired()])
    due_date = DateField('Ngày đến hạn', validators=[DataRequired()])
    status = SelectField('Trạng thái', choices=[('pending', 'Chờ chi'), ('paid', 'Đã chi'), ('overdue', 'Quá hạn')], validators=[DataRequired()])
    paid_at = DateField('Ngày chi', validators=[Optional()])
    method = StringField('Phương thức', validators=[Optional(), Length(max=50)])
    reference = StringField('Mã chứng từ', validators=[Optional(), Length(max=120)])

class LoginForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[DataRequired(message='Vui lòng nhập Tên đăng nhập.'), Length(min=3, max=64)])
    password = PasswordField('Mật khẩu', validators=[DataRequired(message='Vui lòng nhập Mật khẩu.')])

class RegisterForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[DataRequired(message='Vui lòng nhập Tên đăng nhập.'), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(message='Vui lòng nhập Email.'), Email()])
    full_name = StringField('Họ tên', validators=[DataRequired(message='Vui lòng nhập Họ tên.'), Length(max=120)])
    phone = StringField('Số điện thoại', validators=[Optional(), Length(max=20)])
    password = PasswordField('Mật khẩu', validators=[DataRequired(message='Vui lòng nhập Mật khẩu.'), Length(min=6)])

class HouseholdForm(FlaskForm):
    household_code = StringField('Mã hộ gia đình', validators=[DataRequired(message='Vui lòng nhập Mã hộ gia đình.'), Length(max=20)])
    address = StringField('Địa chỉ', validators=[DataRequired(message='Vui lòng nhập Địa chỉ.'), Length(max=200)])
    hamlet = SelectField('Thôn/Xóm', choices=[
        ('Thôn Mới', 'Thôn Mới'),
        ('Thôn Chang', 'Thôn Chang'),
        ('Thôn Trung', 'Thôn Trung'),
        ('Thôn Quyền', 'Thôn Quyền'),
        ('Thôn Then', 'Thôn Then'),
        ('Thôn Bản Tát', 'Thôn Bản Tát'),
        ('Thôn Kiêu', 'Thôn Kiêu'),
        ('Thôn Chì', 'Thôn Chì'),
        ('Thôn Tịnh', 'Thôn Tịnh'),
        
    ], validators=[DataRequired()])
    head_of_household = StringField('Chủ hộ', validators=[DataRequired(message='Vui lòng nhập Chủ hộ.'), Length(max=120)])
    phone = StringField('Số điện thoại', validators=[Optional(), Length(max=20)])
    # Thông tin bổ sung của chủ hộ
    head_id_number = StringField('CCCD/CMND', validators=[Optional(), Length(max=20)])
    head_birth_date = DateField('Ngày sinh', validators=[DataRequired(message='Vui lòng nhập Ngày sinh của Chủ hộ.')])
    head_occupation = StringField('Nghề nghiệp', validators=[Optional(), Length(max=100)])
    head_gender = SelectField('Giới tính', choices=[('Nam', 'Nam'), ('Nữ', 'Nữ')], validators=[Optional()])

    def validate_head_of_household(self, field):
        name = (field.data or '').strip()
        # Only letters and spaces are allowed (Unicode letters included)
        if any(not (ch.isalpha() or ch.isspace()) for ch in name):
            raise ValidationError('Chủ hộ chỉ được chứa chữ cái và khoảng trắng (không có số/ký tự đặc biệt).')

class ResidentForm(FlaskForm):
    full_name = StringField('Họ tên', validators=[DataRequired(message='Vui lòng nhập Họ tên.'), Length(max=120)])
    birth_date = DateField('Ngày sinh', validators=[DataRequired(message='Vui lòng nhập Ngày sinh.')])
    gender = SelectField('Giới tính', choices=[('Nam', 'Nam'), ('Nữ', 'Nữ')], validators=[DataRequired(message='Vui lòng chọn Giới tính.')])
    id_number = StringField('CMND/CCCD', validators=[Optional(), Length(max=20)], filters=[lambda x: x.strip() if x else None])
    relationship = SelectField('Quan hệ với chủ hộ', choices=[
        ('Chủ hộ', 'Chủ hộ'),
        ('Vợ/Chồng', 'Vợ/Chồng'),
        ('Con', 'Con'),
        ('Cha/Mẹ', 'Cha/Mẹ'),
        ('Anh/Chị/Em', 'Anh/Chị/Em'),
        ('Khác', 'Khác')
    ], validators=[DataRequired(message='Vui lòng chọn Quan hệ với chủ hộ.')])
    occupation = StringField('Nghề nghiệp', validators=[Optional(), Length(max=100)])
    phone = StringField('Số điện thoại', validators=[Optional(), Length(max=20)])
    notes = TextAreaField('Ghi chú', validators=[Optional()])
    current_lat = FloatField('Vĩ độ (lat)', validators=[Optional()])
    current_lng = FloatField('Kinh độ (lng)', validators=[Optional()])

class TemporaryResidenceForm(FlaskForm):
    type = SelectField('Loại', choices=[
        ('tam_tru', 'Tạm trú'),
        ('tam_vang', 'Tạm vắng')
    ], validators=[DataRequired(message='Vui lòng chọn Loại.')])
    start_date = DateField('Ngày bắt đầu', validators=[DataRequired(message='Vui lòng nhập Ngày bắt đầu.')])
    end_date = DateField('Ngày kết thúc', validators=[Optional()])
    destination = StringField('Nơi đến/đi', validators=[Optional(), Length(max=200)])
    reason = StringField('Lý do', validators=[Optional(), Length(max=200)])
    contact_info = StringField('Thông tin liên hệ', validators=[Optional(), Length(max=200)])
    is_for_head = BooleanField('Áp dụng cho Chủ hộ')
    lat = FloatField('Vĩ độ (lat)', validators=[Optional()])
    lng = FloatField('Kinh độ (lng)', validators=[Optional()])

    def validate(self, extra_validators=None):
        valid = super().validate(extra_validators=extra_validators)
        # Ràng buộc chung cho cả Chủ hộ và Nhân khẩu
        required_errors = False
        # Ngày kết thúc bắt buộc và sau/ngang ngày bắt đầu
        if not self.end_date.data:
            self.end_date.errors.append('Vui lòng nhập Ngày kết thúc.')
            required_errors = True
        elif self.start_date.data and self.end_date.data < self.start_date.data:
            self.end_date.errors.append('Ngày kết thúc phải sau hoặc bằng Ngày bắt đầu.')
            required_errors = True
        # Ba trường văn bản bắt buộc
        if not (self.destination.data and self.destination.data.strip()):
            self.destination.errors.append('Vui lòng nhập Nơi đến/đi.')
            required_errors = True
        if not (self.reason.data and self.reason.data.strip()):
            self.reason.errors.append('Vui lòng nhập Lý do.')
            required_errors = True
        if not (self.contact_info.data and self.contact_info.data.strip()):
            self.contact_info.errors.append('Vui lòng nhập Thông tin liên hệ.')
            required_errors = True

        if required_errors:
            return False
        return valid

from utils import FEEDBACK_PRIORITIES, ANNOUNCEMENT_PRIORITIES


class FeedbackForm(FlaskForm):
    title = StringField('Tiêu đề', validators=[DataRequired(message='Vui lòng nhập Tiêu đề.'), Length(max=200)])
    description = TextAreaField('Mô tả chi tiết', validators=[DataRequired(message='Vui lòng nhập Mô tả chi tiết.')], widget=TextArea())
    category = SelectField('Loại phản ánh', choices=[
        ('o_ga', 'Ổ gà đường xá'),
        ('rac_thai', 'Rác thải môi trường'),
        ('mat_dien', 'Mất điện'),
        ('an_ninh', 'An ninh trật tự'),
        ('khac', 'Khác')
    ], validators=[DataRequired(message='Vui lòng chọn Loại phản ánh.')])
    priority = SelectField('Mức độ phản ánh', choices=FEEDBACK_PRIORITIES, default='medium', validators=[DataRequired(message='Vui lòng chọn Mức độ phản ánh.')])
    location = StringField('Địa điểm', validators=[DataRequired(message='Vui lòng nhập Địa điểm.'), Length(max=200)])
    attachments = FileField('Đính kèm ảnh/video', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'mp4', 'avi', 'mov'], 'Chỉ chấp nhận file ảnh và video!')
    ])

class AnnouncementForm(FlaskForm):
    title = StringField('Tiêu đề', validators=[DataRequired(message='Vui lòng nhập Tiêu đề.'), Length(max=200)])
    content = TextAreaField('Nội dung', validators=[DataRequired(message='Vui lòng nhập Nội dung.')], widget=TextArea())
    category = SelectField('Loại thông báo', choices=[
        ('tin_tuc', 'Tin tức'),
        ('thong_bao', 'Thông báo'),
        ('lich_hop', 'Lịch họp'),
        ('chinh_sach', 'Chính sách mới')
    ], validators=[DataRequired(message='Vui lòng chọn Loại thông báo.')])
    priority = SelectField('Mức độ ưu tiên', choices=ANNOUNCEMENT_PRIORITIES, validators=[DataRequired(message='Vui lòng chọn Mức độ ưu tiên.')])
    is_published = BooleanField('Xuất bản ngay')
    publish_date = DateField('Ngày xuất bản', validators=[Optional()])
    attachments = FileField('Đính kèm file', validators=[
        FileAllowed(['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'], 'File không được hỗ trợ!')
    ])

# Admin create user form
class AdminUserForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[DataRequired(message='Vui lòng nhập Tên đăng nhập.'), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(message='Vui lòng nhập Email.'), Email()])
    full_name = StringField('Họ tên', validators=[DataRequired(message='Vui lòng nhập Họ tên.'), Length(max=120)])
    phone = StringField('Số điện thoại', validators=[Optional(), Length(max=20)])
    role = SelectField('Vai trò', choices=[
        ('admin', 'Quản trị viên (Toàn quyền)'),
        ('viewer', 'Cán bộ xem (Chỉ xem)'),
        ('citizen', 'Người dân')
    ], validators=[DataRequired(message='Vui lòng chọn Vai trò.')])
    password = PasswordField('Mật khẩu', validators=[DataRequired(message='Vui lòng nhập Mật khẩu.'), Length(min=6)])

class DocumentTypeForm(FlaskForm):
    code = StringField('Mã loại giấy tờ', validators=[DataRequired(message='Vui lòng nhập Mã loại giấy tờ.'), Length(max=50)])
    name = StringField('Tên loại giấy tờ', validators=[DataRequired(message='Vui lòng nhập Tên loại giấy tờ.'), Length(max=120)])
    description = TextAreaField('Mô tả', validators=[Optional()])
    required_fields = TextAreaField('Trường yêu cầu (JSON)', validators=[Optional()])
    fee = IntegerField('Lệ phí (VND)', validators=[Optional()])
    processing_time_days = IntegerField('Thời gian xử lý (ngày)', validators=[Optional()])

class DocumentRequestForm(FlaskForm):
    type_id = SelectField('Loại giấy tờ', coerce=int, validators=[DataRequired(message='Vui lòng chọn Loại giấy tờ.')])
    applicant_full_name = StringField('Họ tên người nộp', validators=[DataRequired(message='Vui lòng nhập Họ tên người nộp.'), Length(max=120)])
    applicant_phone = StringField('Số điện thoại', validators=[DataRequired(message='Vui lòng nhập Số điện thoại.'), Length(max=20)])
    applicant_id_number = StringField('CMND/CCCD', validators=[DataRequired(message='Vui lòng nhập CMND/CCCD.'), Length(max=20)])
    notes = TextAreaField('Ghi chú', validators=[DataRequired(message='Vui lòng nhập Ghi chú.'), Length(max=500, message='Ghi chú tối đa 500 ký tự.')])
    attachments = FileField('Đính kèm (ảnh/pdf)', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'pdf'], 'Chỉ chấp nhận ảnh hoặc PDF!')
    ])

    def validate_applicant_phone(self, field):
        if field.data and field.data.strip():
            import re
            digits = re.sub(r"\D", "", field.data)
            if not re.fullmatch(r"0\d{9,10}", digits):
                raise ValidationError('Số điện thoại không hợp lệ (bắt đầu bằng 0, 10-11 số).')

    def validate_applicant_id_number(self, field):
        if field.data and field.data.strip():
            import re
            digits = re.sub(r"\D", "", field.data)
            if not (len(digits) in (9, 12) and digits.isdigit()):
                raise ValidationError('CMND/CCCD không hợp lệ (9 hoặc 12 số).')
