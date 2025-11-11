import pandas as pd
import random

phan_anh_templates = [
    ("Phản ánh về {issue}", "{desc}"),
    ("Góp ý về {issue}", "{desc}"),
    ("Kiến nghị xử lý {issue}", "{desc}"),
    ("Báo cáo tình trạng {issue}", "{desc}"),
]
phan_anh_issues = [
    "đường hỏng", "rác thải", "mất điện", "nước sinh hoạt", "vệ sinh môi trường", "cây xanh nguy hiểm", "tiếng ồn", "an ninh trật tự", "ngập nước", "thiếu nước", "mất trật tự", "ô nhiễm"
]
phan_anh_descs = [
    "Khu vực thường xuyên bị {issue} gây khó khăn cho sinh hoạt.",
    "{issue} không được xử lý kịp thời gây ảnh hưởng cộng đồng.",
    "Người dân phản ánh về tình trạng {issue} kéo dài.",
    "Đề nghị cơ quan chức năng kiểm tra và xử lý {issue}."
]

khieu_nai_templates = [
    ("Khiếu nại về {issue}", "{desc}"),
    ("Tố cáo việc {issue}", "{desc}"),
    ("Yêu cầu giải quyết {issue}", "{desc}"),
    ("Không đồng ý với {issue}", "{desc}"),
]
khieu_nai_issues = [
    "cấp giấy chứng nhận", "kết quả xét duyệt", "thu phí không đúng", "thái độ phục vụ", "bồi thường", "xây dựng sai phép", "lấn chiếm đất", "giải quyết hồ sơ chậm", "quyết định không hợp lý", "xử lý trách nhiệm", "kỷ luật cán bộ"
]
khieu_nai_descs = [
    "Đã nộp hồ sơ nhưng chưa được giải quyết về {issue}.",
    "Không đồng ý với cách xử lý {issue} của cơ quan chức năng.",
    "Đề nghị xem xét lại quyết định liên quan đến {issue}.",
    "Yêu cầu làm rõ trách nhiệm về {issue}."
]

def generate_samples(n=50):
    rows = []
    for _ in range(n):
        # Phản ánh
        t = random.choice(phan_anh_templates)
        issue = random.choice(phan_anh_issues)
        desc = random.choice(phan_anh_descs).format(issue=issue)
        rows.append({
            'title': t[0].format(issue=issue),
            'description': t[1].format(desc=desc, issue=issue),
            'label': 'phan_anh'
        })
        # Khiếu nại
        t = random.choice(khieu_nai_templates)
        issue = random.choice(khieu_nai_issues)
        desc = random.choice(khieu_nai_descs).format(issue=issue)
        rows.append({
            'title': t[0].format(issue=issue),
            'description': t[1].format(desc=desc, issue=issue),
            'label': 'khieu_nai'
        })
    return pd.DataFrame(rows)

if __name__ == "__main__":
    df = generate_samples(100)
    # Đọc dữ liệu cũ
    try:
        old = pd.read_csv('data/feedback_training/feedback_data.csv')
        df = pd.concat([old, df], ignore_index=True)
    except Exception:
        pass
    df.to_csv('data/feedback_training/feedback_data.csv', index=False)
    print(f"Đã bổ sung {len(df)} mẫu vào data/feedback_training/feedback_data.csv")
