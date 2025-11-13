<h2 align="center"> 
     <a href="https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin"> 
     🎓 Faculty of Information Technology (DaiNam University) 
     </a> 
 </h2> 
 <h2 align="center"> 
    HỆ THỐNG QUẢN LÝ DÂN CƯ VÀ TƯƠNG TÁC CỘNG ĐỒNG UBND XÃXÃ
 </h2> 
 <div align="center"> 
     <p align="center"> 
         <img alt="AIoTLab Logo" width="170" src="https://github.com/user-attachments/assets/711a2cd8-7eb4-4dae-9d90-12c0a0a208a2" /> 
         <img alt="AIoTLab Logo" width="180" src="https://github.com/user-attachments/assets/dc2ef2b8-9a70-4cfa-9b4b-f6c2f25f1660" /> 
         <img alt="DaiNam University Logo" width="200" src="https://github.com/user-attachments/assets/77fe0fd1-2e55-4032-be3c-b1a705a1b574" /> 
     </p> 

 [![AIoTLab](https://img.shields.io/badge/AIoTLab-green?style=for-the-badge)](https://www.facebook.com/DNUAIoTLab) 
 [![Faculty of Information Technology](https://img.shields.io/badge/Faculty%20of%20Information%20Technology-blue?style=for-the-badge)](https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin) 
 [![DaiNam University](https://img.shields.io/badge/DaiNam%20University-orange?style=for-the-badge)](https://dainam.edu.vn) 
 
 </div> 
 
 --- 
 ## 1. Giới thiệu hệ thống 
 Hệ thống Quản lý Hành chính Xã là ứng dụng web hỗ trợ chính quyền xã/phường quản lý dân cư, hộ gia đình, tạm trú/tạm vắng, trợ cấp/phúc lợi, yêu cầu giấy tờ, thông báo/bản tin và phản hồi của người dân. Ứng dụng phân quyền rõ ràng (quản trị viên, người xem, công dân), có chức năng xuất dữ liệu CSV/XML, tìm kiếm/lọc theo thôn/xóm và nhóm tuổi, cùng với mô-đun phân loại phản hồi bằng học máy. 
 
 Kiến trúc tổng quan: 
 - Máy chủ `Flask` xử lý nghiệp vụ, REST routes theo blueprint (`blueprints/`). 
 - Giao diện web sử dụng `Jinja2` + `Bootstrap 5`. 
 - Cơ sở dữ liệu `SQLite` (tệp `instance/commune_admin.db`). 
 - Mô-đun ML phân loại phản hồi (`services/feedback_classifier.py`) và scripts huấn luyện (`scripts/`). 
 
 Các đặc điểm nổi bật: 
 - Quản lý hộ gia đình và nhân khẩu (thêm/sửa/xóa, liên kết hộ). 
 - Xuất dữ liệu dân cư CSV/XML theo thôn/xóm (lọc `hamlet`). 
 - Tìm kiếm + lọc nhanh trên bảng dân cư, hộ gia đình. 
 - Quản lý tạm trú/tạm vắng, trợ cấp, loại giấy tờ, và yêu cầu giấy tờ. 
 - Bản tin, thông báo, và hệ thống người dùng công dân. 
 - Phân quyền truy cập bằng decorator (`admin_required`, `viewer_allowed`, `admin_or_self`). 
 - Phản hồi người dân được phân loại tự động, hỗ trợ gửi email (cấu hình trong `config/`). 
 
 --- 
 
 ## 2. Ngôn ngữ & Công nghệ sử dụng 
 <div align="center"> 
 
 [![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/) 
 [![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/) 
 [![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/) 
 [![Bootstrap 5](https://img.shields.io/badge/Bootstrap-5-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com/) 
 [![Jinja2](https://img.shields.io/badge/Jinja2-FFD43B?style=for-the-badge&logo=jinja&logoColor=black)](https://jinja.palletsprojects.com/) 
 [![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/) 
 [![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)](https://scikit-learn.org/) 
 
 </div> 
 
 --- 
 
 ## 3. Hình ảnh các chức năng 
 <p align="center"> 
   <img src="images/dkquantri.jpg" alt="Bảng điều khiển quản trị" width="1000"/> 
   <br/> 
   <em>Hình 1. 🖥️ Bảng điều khiển quản trị</em><br/> 
 </p> 
 --- 
 <p align="center"> 
   <img src="images/quanlydancu.jpg" alt="Quản lý dân cư" width="1000"/> 
   <br/> 
   <em>Hình 2. 🖥️ Quản lý dân cư (tìm kiếm, lọc, xuất CSV/XML)</em><br/> 
 </p> 
 --- 
 <p align="center"> 
   <img src="images/quanlyho.jpg" alt="Quản lý hộ gia đình" width="1000"/> 
   <br/> 
   <em>Hình 3. 🖥️ Quản lý hộ gia đình</em><br/> 
 </p> 
 --- 
 <p align="center"> 
   <img src="images/phanhoinguoidan.jpg" alt="Phản hồi người dân" width="1000"/> 
   <br/> 
   <em>Hình 4. 🖥️ Phản hồi người dân và phân loại mức độ</em><br/> 
 </p>  
 --- 
 
 ## 4. Các bước cài đặt 
 1. **Cài đặt môi trường**  
    - Python 3.10 trở lên  
    - pip, virtualenv (khuyến nghị)  
    - IDE khuyến nghị: VS Code / PyCharm  
 
 2. **Chuẩn bị cơ sở dữ liệu**  
    - Mặc định dùng SQLite với tệp `instance/commune_admin.db`.  
    - Lần chạy đầu, DB sẽ được tạo tự động nếu chưa tồn tại.  
 
 3. **Cài đặt phụ thuộc**  
    - Tạo và kích hoạt môi trường ảo:  
      - Windows (PowerShell):  
        ```powershell
        python -m venv .venv
        .\.venv\Scripts\Activate.ps1
        ```
      - Cài đặt dependencies:  
        ```bash
        pip install -r requirements.txt
        ```
 
 4. **Chạy ứng dụng**  
    - Chạy server ở chế độ phát triển:  
      ```bash
      python main.py
      ```
    - Truy cập: `http://127.0.0.1:5000/`  
    - Khu vực quản trị: `http://127.0.0.1:5000/admin`  
 
 5. **Tài khoản & phân quyền**  
    - Đăng ký và đăng nhập qua giao diện (`/auth/login`, `/auth/register`).  
    - Phân quyền dựa trên decorator trong `utils.py`: `admin_required`, `viewer_allowed`, `admin_or_self`.  
 
 6. **Xuất dữ liệu CSV/XML**  
    - Tại trang Quản lý Dân cư, dùng nút "Xuất dữ liệu".  
    - Có thể lọc theo thôn/xóm:  
      - CSV: `/admin/export/residents?format=csv&hamlet=<ten_thon_xom>`  
      - XML: `/admin/export/residents?format=xml&hamlet=<ten_thon_xom>`  
 
 7. **Cấu hình email & AI**  
    - Email: `config/mail_config.json`  
    - Cấu hình API: `config/api_config.json`  
    - Mô-đun ML: `services/feedback_classifier.py`, mô hình trong thư mục `models/`.  
    - Scripts huấn luyện/tái huấn luyện: `scripts/` (ví dụ `train_model.py`).  
 
 8. **Tài liệu thủ tục**  
    - Xem tệp: `Thu_tuc_giay_to.md` để tham khảo tóm tắt thủ tục tại xã.
 
 --- 
 
 ## 5. Lộ trình tính năng (gợi ý) 
 - Bộ lọc nâng cao: nhóm tuổi, trạng thái tạm trú/tạm vắng. 
 - Nhật ký hoạt động và kiểm toán thay đổi dữ liệu. 
 - Tích hợp thông báo qua email/SMS cho bản tin và kết quả xử lý giấy tờ. 
 - Xuất dữ liệu theo định dạng thêm (JSON, Excel). 
 
 --- 
 
 ## 6. Thông tin liên hệ  
 Họ tên: Hoàng Mạnh Linh.  
 Lớp: CNTT 16-03.  
 Email: linhmanhhoang03@gmail.com.  
 
 © 2025 AIoTLab, Faculty of Information Technology, DaiNam University. All rights reserved. 
 
---
 
### Ghi chú triển khai 
- Kho mã nguồn chính nằm ở thư mục gốc (Flask app: `app.py`, `main.py`, blueprints trong `blueprints/`, templates trong `templates/`).  
- Nếu gặp lỗi khi xuất dữ liệu do nhân khẩu chưa gắn hộ, hệ thống đã xử lý null an toàn trong `utils.py` (hàm `export_residents_to_csv/xml`).  
- Với UI Bootstrap 5, bảo đảm các nút dropdown dùng `data-bs-toggle="dropdown"` và đã nạp `bootstrap.bundle.min.js` trong `templates/admin/base_admin.html`.
