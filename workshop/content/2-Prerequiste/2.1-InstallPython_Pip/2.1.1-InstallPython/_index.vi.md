---
title: "Cài đặt Python"
date: "" 
weight: 1 
chapter: false
pre: " <b> 2.1.1 </b> "
---

#### Tải xuống và cài đặt Python 3.13.5 cho Windows

1. Truy cập [trang tải xuống Python chính thức](https://www.python.org/downloads/windows/)

2. Nhấp vào nút màu vàng **Download Python 3.13.5** ở đầu trang.

3. Sau khi file `.exe` được tải xuống, nhấp đúp vào nó để khởi chạy trình cài đặt.

4. **Quan trọng:** Đánh dấu vào ô **"Add Python to PATH"** ở cuối cửa sổ cài đặt.

5. Nhấp **Install Now** và đợi quá trình cài đặt hoàn tất.

6. Sau khi cài đặt, mở **Command Prompt (CMD)** và chạy:

{{< copycode >}}
python --version
{{< /copycode >}}

Sau đó kiểm tra pip:

{{< copycode >}}
pip --version
{{< /copycode >}}

Cả hai lệnh đều sẽ trả về phiên bản đã cài đặt của Python và pip.