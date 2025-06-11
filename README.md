# 🔐 Ứng dụng Machine Learning trong Phòng chống tấn công DDoS

---

## 👨‍💻 Thành viên thực hiện

| Tên                | Lớp      | MSSV      |
|--------------------|----------|-----------|
| Đào Hữu Phi Quân   | Mạng máy tính và Truyền thông dữ liệu | 52000386 |
| Nguyễn Thanh Triều | Mạng máy tính và Truyền thông dữ liệu | 52100495 |


---

## 📌 Tổng quan

Dự án triển khai giải pháp phát hiện và ngăn chặn tấn công từ chối dịch vụ phân tán (DDoS) sử dụng mô hình **Convolutional Neural Network (CNN)** và môi trường **Software Defined Networking (SDN)**.  
Thông qua việc mô phỏng các cuộc tấn công như **UDP Flood, TCP SYN Flood, ICMP Flood** trên **Mininet**, bộ điều khiển **Ryu** sẽ phân tích lưu lượng theo thời gian thực để phân loại và chặn tấn công.

---

## 🗂 Cấu trúc thư mục

```bash
Intelligent_DDoS_Detection/
│
├── ML/                      # Thư mục huấn luyện mô hình Machine Learning
│   ├── cnn_model.py
│   └── utils.py
│
├── controller/              # Mã nguồn Ryu Controller
│   └── controller.py
│
├── models/
│   └── cnn_ddos_model.tflite
│
├── data/
│   └── dataset.csv          # (Bỏ qua trong Git vì >100MB)
│
├── report/
│   └── report.pdf         # Báo cáo cuối kỳ
│
├── .gitignore
└── README.md
```
## ⚙️ Yêu cầu cài đặt

Để chạy được dự án, hệ thống cần cài đặt các thành phần sau:

- Python `3.10.x`
- Ryu Controller `4.34`
- Mininet `2.3.0`
- TensorFlow Lite Runtime (`tflite-runtime`)
- 🖥Hệ điều hành: **Ubuntu 20.04+** hoặc **WSL2** (Windows Subsystem for Linux)

> 💡 Bạn nên cài đặt Mininet và Ryu theo hướng dẫn chính thức để tránh lỗi.
 ----------------
## 🧰 Installation

- Install [VirtualBox](https://www.virtualbox.org/wiki/Downloads) hoặc VMware Workstation
- Install [Mininet-VM](https://github.com/mininet/mininet/releases/)
- Install [Ubuntu](https://ubuntu.com/download/desktop)
- Install [Ryu Controller](https://ryu.readthedocs.io/en/latest/getting_started.html) 


--------------
## 🚀 Cài môi trường ảo và các thư viện cần thiết

```bash
git clone https://github.com/notQ1301/intelligent-ddos-detection.git
cd intelligent-ddos-detection

python -m venv venv
source venv/bin/activate     # Linux / macOS
venv\Scripts\activate        # Windows

pip install -r requirements.txt
```

-------------------

## 📊 Dataset

Dữ liệu sử dụng để huấn luyện được trích xuất từ các mô phỏng tấn công thật bằng Mininet, gồm:

- Lưu lượng bình thường (HTTP, ping...)
- Lưu lượng tấn công (UDP, TCP, ICMP flood)

> **🔹 File `dataset.csv` > 100MB nên không được đẩy lên GitHub.**  
> Bạn có thể tạo lại bằng cách chạy mô phỏng hoặc liên hệ nhóm để xin dữ liệu.

---

## 🧠 Huấn luyện mô hình

```bash
cd ML/
python cnn_model.py
```

Mô hình sau khi huấn luyện sẽ được lưu thành cnn_ddos_model.tflite để tích hợp vào controller.
---------------------
## Triển khai hệ thống phát hiện DDoS

Sau khi huấn luyện mô hình, bạn có thể triển khai vào hệ thống SDN với controller Ryu và mô phỏng mạng Mininet.

---

### 🧠 Bước 1: Chạy Controller với mô hình CNN

```bash
cd controller/
ryu-manager controller.py
```
Controller sẽ tự động load mô hình cnn_ddos_model.tflite và bắt đầu phân tích lưu lượng mạng theo thời gian thực.
-------------------

### 🔧 Bước 2: Chạy Mininet và khởi tạo mô hình mạng

Mở một terminal khác và chạy lệnh khởi tạo Mininet:

```bash
sudo mn --custom topology.py --topo mytopo --controller=remote
```

Topology mô phỏng gồm các host sinh lưu lượng bình thường và tấn công để kiểm thử mô hình.

### 🧪 Bước 3: Sinh lưu lượng để kiểm thử mô hình

Sau khi khởi tạo mạng, mở xterm các host trong Mininet:

```bash
xterm h1 h2
```

- Tại h1: Gửi các lệnh mô phỏng tấn công như ICMP Flood, UDP Flood,...

- Tại h2: Chạy các dịch vụ (HTTP server, Iperf...) để nhận lưu lượng.

Có thể sử dụng các script tự động nếu đã cấu hình trong thư mục mininet/.

--------

## Cơ chế phản ứng khi phát hiện tấn công

Khi mô hình CNN phát hiện một luồng dữ liệu có dấu hiệu là **tấn công DDoS**, hệ thống sẽ thực hiện các hành động phản ứng sau:

-  **Chặn IP nguồn**: Tự động cài đặt luật `drop` trong switch thông qua controller để chặn địa chỉ IP độc hại.
-  **Gửi cảnh báo qua email** cho quản trị viên với thông tin chi tiết về IP tấn công và thời điểm phát hiện.
-  **Ghi log vào file**:
  - `ddos_log.txt`: Ghi lại lịch sử các cuộc tấn công bị phát hiện.
  - `blocked_ip.txt`: Danh sách IP đã bị block để tránh xử lý trùng lặp.

>  Mọi phản ứng diễn ra **tự động và theo thời gian thực** nhờ kiến trúc linh hoạt của SDN.
---------
## Cảnh báo qua Email

Hệ thống sử dụng SMTP để gửi email cảnh báo khi phát hiện một cuộc tấn công DDoS.  
Bạn cần cấu hình thông tin tài khoản trong file `.env` như sau:
```bash
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password
EMAIL_TO=admin_email@gmail.com
```


> **Lưu ý**: Sử dụng [App Password](https://support.google.com/accounts/answer/185833) nếu dùng Gmail và bật xác minh 2 bước.

> Không đẩy file `.env` lên GitHub – đã được thêm vào `.gitignore` để tránh rò rỉ thông tin cá nhân.
----------------
# 📈 Đánh giá kết quả

Mô hình CNN sau khi huấn luyện và triển khai cho kết quả tốt trong môi trường mô phỏng:

- **Độ chính xác cao** trong việc phân loại lưu lượng tấn công và bình thường.
- **Phản ứng nhanh** khi phát hiện tấn công, với độ trễ rất thấp.
- **Tự động chặn IP** và gửi cảnh báo tức thì giúp giảm thiểu thiệt hại.
- Mô hình được kiểm thử với các kiểu tấn công phổ biến:
  - UDP Flood
  - TCP SYN Flood
  - ICMP Flood

> Kết quả cho thấy việc kết hợp Machine Learning với kiến trúc SDN là một hướng tiếp cận hiệu quả trong việc phòng chống DDoS hiện đại.
----------------

## Contact
Đào Hữu Phi Quân: kevinquan2002@gmail.com   

> Dự án được thực hiện trong khuôn khổ môn học **Dự án Công nghệ Thông Tin** – Trường Đại học Tôn Đức Thắng (TDTU), năm 2025.
