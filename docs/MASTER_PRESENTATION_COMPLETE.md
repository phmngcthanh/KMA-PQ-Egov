# E-Government System using Post-Quantum PKI
## Complete Master's Presentation (30-45 Slides)

**Course:** Public Key Infrastructure  
**Program:** Master in Information Security  
**Project:** NT208 - Chính quyền điện tử sử dụng hạ tầng khóa công khai PKI  

---

# 📊 COMPLETE SLIDE CONTENT

---

# PHẦN 1: GIỚI THIỆU (SLIDES 1-8)

---

## Slide 1: Title Slide

# Hệ thống Chính quyền Điện tử  
# sử dụng Hạ tầng Khóa công khai Hậu Lượng tử

### E-Government System using Post-Quantum PKI

**Môn học:** Hạ tầng Khóa công khai (PKI)  
**Chương trình:** Thạc sĩ An toàn Thông tin  

**Nhóm thực hiện:**
- 19520958 Phạm Ngọc Thành
- 19520543 Nguyễn Gia Hiếu  
- 19520643 Trần Anh Khoa

**Tháng 12, 2025**

---

## Slide 2: Nội dung trình bày (Agenda)

### I. Giới thiệu về PKI
### II. Mật mã Hậu lượng tử (Post-Quantum Cryptography)
### III. Tổng quan hệ thống
### IV. Phân tích đa ngành (18 khía cạnh)
### V. Hướng dẫn triển khai
### VI. Kết luận & Thảo luận

---

## Slide 3: Giới thiệu về PKI

### PKI là gì?

**Public Key Infrastructure (Hạ tầng Khóa công khai)** là:
- Hệ thống quản lý **chứng thư số** và **khóa mật mã**
- Cho phép **xác thực danh tính** trong môi trường số
- Đảm bảo **toàn vẹn** và **không thể chối bỏ** của dữ liệu

### Các thành phần chính

| Thành phần | Chức năng |
|------------|-----------|
| **CA (Certificate Authority)** | Cấp và quản lý chứng thư |
| **RA (Registration Authority)** | Xác minh danh tính |
| **Chứng thư số (Certificate)** | Giấy chứng nhận danh tính số |
| **CRL/OCSP** | Kiểm tra thu hồi chứng thư |
| **Trust Store** | Danh sách CA tin cậy |

---

## Slide 4: PKI - Không chỉ là Công nghệ

### PKI là Hệ thống Đa ngành (Socio-Technical-Legal-Economic)

```
┌─────────────────────────────────────────────────────────────┐
│                         PKI                                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Công nghệ  │  │   Pháp lý    │  │    Kinh tế       │  │
│  │   (Tech)     │  │   (Legal)    │  │    (Economic)    │  │
│  │              │  │              │  │                  │  │
│  │ • Mật mã     │  │ • Luật GDĐT  │  │ • Chi phí CA     │  │
│  │ • X.509      │  │ • Chữ ký số  │  │ • ROI            │  │
│  │ • HSM        │  │ • Tuân thủ   │  │ • Business model │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    Xã hội (Social)                    │   │
│  │  • Niềm tin công chúng  • Khả năng sử dụng           │   │
│  │  • Khoảng cách số       • Đào tạo người dùng         │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Slide 5: Mô hình tin cậy (Trust Model)

### Mô hình Phân cấp (Hierarchical PKI)

```
                  ┌─────────────────────┐
                  │   ROOT CA           │  ← Neo tin cậy (Trust Anchor)
                  │   (Offline, HSM)    │     Hiệu lực: 20 năm
                  └──────────┬──────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
   │  CA Cán bộ   │  │  CA Công dân │  │  CA Dịch vụ  │
   │  (10 năm)    │  │  (10 năm)    │  │  (5 năm)     │
   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
          │                 │                 │
          ▼                 ▼                 ▼
     [Chứng thư        [Chứng thư       [Chứng thư
      Cán bộ]           Công dân]        Dịch vụ]
```

### Tại sao chọn Hierarchical PKI?
- ✅ Phù hợp cấu trúc hành chính Việt Nam
- ✅ Tương thích với NEAC (Trung tâm CTKQG)
- ✅ Quy mô lớn, kiểm soát tập trung

---

## Slide 6: Vòng đời Chứng thư (Certificate Lifecycle)

```
┌───────────────────────────────────────────────────────────────────┐
│                    VÒNG ĐỜI CHỨNG THƯ                              │
├───────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────┐   ┌──────────┐   ┌─────────┐   ┌─────────────────┐  │
│  │  Yêu cầu │──▶│ Xác minh │──▶│ Cấp     │──▶│ Sử dụng         │  │
│  │  (CSR)   │   │ Danh tính│   │ Cert    │   │ (Active)        │  │
│  └─────────┘   └──────────┘   └─────────┘   └────────┬────────┘  │
│                                                       │           │
│                              ┌────────────────────────┼───────┐  │
│                              ▼                        ▼       ▼  │
│                        ┌─────────┐            ┌─────────┐ ┌────┐ │
│                        │ Thu hồi │            │ Gia hạn │ │Hết │ │
│                        │ Revoke  │            │ Renew   │ │hạn │ │
│                        └─────────┘            └─────────┘ └────┘ │
└───────────────────────────────────────────────────────────────────┘
```

### Thời hạn chứng thư trong hệ thống
| Loại | Thời hạn | Đối tượng |
|------|----------|-----------|
| Root CA | 20 năm | CA gốc |
| Sub-CA | 5-10 năm | CA trung gian |
| Cán bộ | 2 năm | Công chức |
| Công dân | 3 năm | Người dân |
| Dịch vụ | 1 năm | Ứng dụng |

---

## Slide 7: Mối đe dọa Lượng tử (Quantum Threat)

### Tại sao cần Post-Quantum?

| Thuật toán | Hiện tại | Khi có Quantum Computer |
|------------|----------|-------------------------|
| RSA-2048 | ✅ An toàn | ❌ Bị phá bởi Shor |
| ECDSA P-256 | ✅ An toàn | ❌ Bị phá bởi Shor |
| AES-256 | ✅ An toàn | ⚠️ Yếu đi (Grover) |
| **Dilithium3** | ✅ An toàn | ✅ Vẫn an toàn |
| **Kyber768** | ✅ An toàn | ✅ Vẫn an toàn |

### Timeline
- **2030-2035:** Máy tính lượng tử quy mô lớn có thể xuất hiện
- **"Harvest Now, Decrypt Later":** Thu thập dữ liệu mã hóa hôm nay → giải mã trong tương lai
- **NIST (8/2024):** Chuẩn hóa thuật toán hậu lượng tử

---

## Slide 8: Chuẩn NIST Post-Quantum (2024)

### Các thuật toán được chuẩn hóa

| FIPS | Thuật toán | Loại | Ứng dụng |
|------|-----------|------|----------|
| **203** | ML-KEM (Kyber) | Lattice-based | Trao đổi khóa |
| **204** | ML-DSA (Dilithium) | Lattice-based | Chữ ký số |
| **205** | SLH-DSA (SPHINCS+) | Hash-based | Chữ ký số |
| **206** | FN-DSA (Falcon) | Lattice-based | Chữ ký số |

### So sánh kích thước khóa

| | RSA-4096 | Dilithium3 | Ghi chú |
|---|---|---|---|
| Public Key | 512 bytes | **1,952 bytes** | Lớn hơn ~4x |
| Signature | 512 bytes | **3,293 bytes** | Lớn hơn ~6x |
| Tốc độ ký | ~50ms | ~5ms | Nhanh hơn ~10x |

---

# PHẦN 2: TỔNG QUAN HỆ THỐNG (SLIDES 9-14)

---

## Slide 9: Kiến trúc Hệ thống

```
┌─────────────────────────────────────────────────────────────────────┐
│                       FRONTEND (React 18)                            │
│   ┌─────────────────┐  ┌───────────────┐  ┌───────────────────────┐ │
│   │ Quản lý         │  │  Nộp          │  │    Xác thực           │ │
│   │ Chứng thư       │  │  Hồ sơ        │  │ (Password/OAuth/Cert) │ │
│   └─────────────────┘  └───────────────┘  └───────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                              │ REST API (JWT + Certificate Auth)
┌─────────────────────────────────────────────────────────────────────┐
│                   BACKEND (Django REST Framework)                    │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                      Ứng dụng PKI                                ││
│  │  ┌──────────────┐  ┌───────────────┐  ┌───────────────────────┐ ││
│  │  │ CA Service   │  │ Cert Service  │  │ Crypto Module         │ ││
│  │  │ • Root/SubCA │  │ • Cấp/Thu hồi │  │ • RSA/ECDSA           │ ││
│  │  │ • CRL/OCSP   │  │ • Xác thực    │  │ • Dilithium/Kyber     │ ││
│  │  └──────────────┘  └───────────────┘  │ • Hybrid              │ ││
│  │                                        └───────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────┘│
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │Authentication│  │ Hồ sơ (Docs)│  │   Ký PDF                 │   │
│  │  + Audit Log │  │              │  │                          │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                     ┌────────┴────────┐
                     │   PostgreSQL    │
                     │    Database     │
                     └─────────────────┘
```

---

## Slide 10: Vấn đề Giải quyết

### Các thách thức của hệ thống cũ

| Vấn đề | Cách làm truyền thống | Giải pháp PKI |
|--------|----------------------|---------------|
| **Giả mạo tài liệu** | Con dấu, chữ ký tay | Chữ ký số với chứng thư |
| **Xác minh danh tính** | Kiểm tra CMND trực tiếp | Xác thực bằng chứng thư |
| **Đe dọa lượng tử** | Không bảo vệ | Mật mã hybrid hậu lượng tử |
| **Audit trail** | Sổ sách giấy (dễ sửa) | Log mật mã chain-linked |
| **Kiểm tra thu hồi** | Không có | CRL/OCSP tự động |

### Quy trình E-Government

```
Công dân nộp hồ sơ → Cán bộ xét duyệt → 
Ký bằng chứng thư số → Công dân tải kết quả có chữ ký
```

---

## Slide 11: Công nghệ sử dụng

| Tầng | Công nghệ | Mục đích |
|------|-----------|----------|
| **Frontend** | React 18, Redux, Bootstrap | Giao diện người dùng |
| **Backend** | Django 4.x, DRF | REST API |
| **Database** | PostgreSQL 15 | Lưu trữ dữ liệu |
| **Mật mã cổ điển** | cryptography (Python) | RSA-4096, ECDSA P-384 |
| **Mật mã PQ** | liboqs-python | Dilithium3, Kyber768 |
| **Ký PDF** | PDFNetPython3 | Chữ ký tài liệu |
| **Triển khai** | Docker, Nginx, Gunicorn | Containerization |

### Thư viện Open Quantum Safe (liboqs)
- NIST standardized algorithms
- Python bindings: `pip install liboqs-python`
- Active development & maintenance

---

## Slide 12: Mật mã Hybrid

### Tại sao Hybrid?

- **Defense-in-Depth:** Hai hệ thống mật mã độc lập
- **Algorithm Agility:** Có thể cập nhật thuật toán PQ mà không phải rebuild
- **Backward Compatible:** Chữ ký cổ điển vẫn hợp pháp
- **Khuyến nghị NIST:** Hybrid trong giai đoạn chuyển đổi

### Quy trình ký Hybrid

```
Tài liệu ──┬──▶ Hash (SHA-384)
           │         │
           │    ┌────┴────┐
           │    ▼         ▼
           │ RSA-4096  Dilithium3
           │   Ký        Ký
           │    │         │
           │    ▼         ▼
           └──▶ CHỮ KÝ HYBRID {
                  classical_sig: "...",
                  pq_sig: "..."
                }
```

### Xác thực: Cả hai chữ ký phải hợp lệ

---

## Slide 13: Các tính năng đã triển khai

### ✅ Tính năng PKI
- [x] Tạo Root CA & Intermediate CA
- [x] Cấp và thu hồi chứng thư
- [x] Sinh CRL (Certificate Revocation List)
- [x] Chữ ký hậu lượng tử (Dilithium3)
- [x] Mật mã hybrid (RSA + Dilithium)
- [x] Audit logging chống giả mạo

### ✅ Tính năng E-Government
- [x] Đăng ký và xác thực người dùng
- [x] Quy trình nộp hồ sơ
- [x] Ký PDF với chữ ký hybrid
- [x] Xác thực bằng chứng thư
- [x] Đăng nhập mạng xã hội (Google, Facebook)
- [x] Thông báo email

---

## Slide 14: Mô hình dữ liệu

### Certificate Authority Model
```python
class CertificateAuthority(models.Model):
    name: str                    # "E-Gov Root CA VN"
    ca_type: ROOT|INTERMEDIATE   # Cấp trong hierarchy
    parent_ca: FK                # CA cha
    certificate_pem: str         # Chứng thư X.509
    private_key_encrypted: bytes # Khóa riêng mã hóa AES-256-GCM
    pq_public_key: bytes         # Khóa công khai Dilithium
    pq_private_key_encrypted: bytes
```

### User Certificate Model
```python
class UserCertificate(models.Model):
    user: FK(User)              # Chủ sở hữu
    issuing_ca: FK(CA)          # CA cấp
    certificate_pem: str        # Chứng thư X.509
    pq_public_key: bytes        # Khóa PQ
    status: ACTIVE|REVOKED|EXPIRED
    fingerprint_sha256: str     # Định danh nhanh
```

---

# PHẦN 3: PHÂN TÍCH ĐA NGÀNH (SLIDES 15-32)
## Trả lời 18 câu hỏi của Thầy

---

## Slide 15: 1. Trust Model & Root of Trust

### Mô hình tin cậy trong hệ thống

```
┌─────────────────────────────────────────────┐
│           NEO TIN CẬY (Trust Anchor)         │
│  ┌─────────────────────────────────────────┐│
│  │       ROOT CA (E-Gov Root CA VN)        ││
│  │  • Lưu trữ offline (khuyến nghị)        ││
│  │  • Bảo vệ HSM (yêu cầu)                 ││
│  │  • Hiệu lực 20 năm                      ││
│  │  • Khóa hybrid: RSA-4096 + Dilithium    ││
│  └─────────────────────────────────────────┘│
└─────────────────────────────────────────────┘
            │
     Tin cậy lan truyền xuống
            ↓
    Sub-CAs → Chứng thư người dùng
```

### Bảo mật khóa CA
| Phương thức | Triển khai hiện tại | Production |
|-------------|---------------------|------------|
| Mã hóa khóa | AES-256-GCM | ✅ |
| HSM | ❌ Chưa có | **Bắt buộc** |
| Offline Root | ⚠️ Khuyến nghị | **Bắt buộc** |

---

## Slide 16: 2. Quản trị & Chính sách (CP/CPS)

### Khung Chính sách Chứng thư (Certificate Policy)

| Yếu tố | Triển khai |
|--------|------------|
| **Loại chứng thư** | Cán bộ (2 năm), Công dân (3 năm), Dịch vụ (1 năm) |
| **Xác minh danh tính** | Email verification + Admin approval |
| **Quản lý khóa** | Server-side generation, encrypted storage |
| **Chính sách thu hồi** | CRL mỗi 24h, ngay lập tức nếu key compromise |
| **Chính sách audit** | Ghi log tất cả thao tác với hash chain-linked |

### Cải thiện cần thiết cho Production
- Tài liệu CPS chính thức theo mẫu NEAC
- Kiểm toán bảo mật hàng năm
- Quy trình key ceremony

---

## Slide 17: 3. Pháp lý & Tuân thủ (Vietnam)

### Khung pháp lý hiện hành

| Quy định | Trạng thái | Phân tích |
|----------|------------|-----------|
| **Luật GDĐT 2023** (Luật 20/2023/QH15) | ⚠️ Một phần | Cần chứng nhận NEAC |
| **NĐ 130/2018/NĐ-CP** | ⚠️ Một phần | Yêu cầu HSM cho khóa |
| **TT 16/2019/TT-BTTTT** | ❌ Chưa đạt | Cần giấy phép MIC |
| **NĐ 13/2023/NĐ-CP** (BVDLCN) | ⚠️ Một phần | Cần đánh giá tác động |

### Thách thức pháp lý PQ
- **Chữ ký hậu lượng tử:** Chưa được công nhận rõ ràng trong luật VN
- **Giải pháp:** Chữ ký hybrid = cổ điển (hợp pháp) + PQ (tương lai)

---

## Slide 18: 4. Kinh tế & Chi phí triển khai

### Phân tích chi phí (VND)

| Hạng mục | Chi phí ban đầu | Chi phí/năm |
|----------|-----------------|-------------|
| **Phần cứng** | | |
| HSM | 300M - 500M | 50M |
| Servers (HA) | 200M - 400M | 80M |
| **Phần mềm** | | |
| PDF Library | 100M - 200M | 50M |
| **Vận hành** | | |
| Giấy phép CA (MIC) | 100M | 50M |
| Phát triển & Tích hợp | 300M | 100M |
| **TỔNG** | **1.3B - 1.85B** | **410M** |

### Phân tích ROI
- **Thời gian hoàn vốn:** 2.5 - 3.5 năm
- **Tiết kiệm hàng năm:** 500M - 750M VND
- **Giá trị quantum-proofing:** Tránh chi phí khẩn cấp 2-5B VND

---

## Slide 19: 5. Rủi ro & Case study thất bại

### Các sự cố PKI nổi tiếng

| Sự cố | Năm | Bài học |
|-------|-----|---------|
| **DigiNotar** (Hà Lan) | 2011 | CA bị xâm nhập, 500+ chứng thư giả |
| **Comodo** | 2011 | RA bị xâm nhập → chứng thư giả Google |
| **Symantec** | 2017 | Cấp sai chứng thư, bị loại khỏi trình duyệt |
| **Let's Encrypt** | 2020 | 3 triệu chứng thư thu hồi do bug CAA |

### Bài học áp dụng trong hệ thống
- ✅ Audit logging nghiêm ngặt (tamper-proof)
- ✅ CA hierarchy (root offline, sub-CA online)
- ✅ Kiểm tra trạng thái chứng thư (CRL/OCSP)
- ⚠️ HSM bắt buộc cho production

---

## Slide 20: 6. Khả năng tương tác & Tiêu chuẩn

### Tuân thủ tiêu chuẩn

| Tiêu chuẩn | Hỗ trợ | Ghi chú |
|------------|--------|---------|
| **X.509 v3** | ✅ Full | Định dạng chứng thư |
| **PKCS#10** | ✅ Full | Định dạng CSR |
| **RFC 5280** | ✅ Full | X.509 PKI profile |
| **RFC 6960** | ✅ Partial | OCSP |
| **NIST FIPS 204** (ML-DSA) | ✅ Full | Chữ ký hậu lượng tử |
| **NIST FIPS 203** (ML-KEM) | ✅ Full | KEM hậu lượng tử |

### Khả năng tương tác
- Định dạng xuất: PEM, DER, PKCS#12
- Chữ ký cổ điển tương thích hệ thống hiện có
- PQ extensions lưu trong custom OIDs

---

## Slide 21: 7. Con người & Khả năng sử dụng

### Thiết kế trải nghiệm người dùng

| Loại người dùng | Giao diện | Độ phức tạp |
|-----------------|-----------|-------------|
| **Công dân** | Web portal | Thấp - Form đơn giản |
| **Cán bộ** | Admin dashboard | Trung bình - Workflow |
| **Admin CA** | CLI + API | Cao - Key ceremony |

### Tính năng tiếp cận
- Social login (Google, Facebook) dễ onboarding
- Xác thực đa phương thức (password + certificate)
- Thông báo email về trạng thái chứng thư

### Thách thức
- Khoảng cách số tại vùng nông thôn Việt Nam
- Độ phức tạp quản lý chứng thư
- **Giải pháp:** Đào tạo, hỗ trợ kỹ thuật

---

## Slide 22: 8. Quy mô & Hiệu năng

### Hiệu năng các thuật toán

| Thao tác | RSA-4096 | Dilithium3 | Hybrid |
|----------|----------|------------|--------|
| Sinh khóa | ~500ms | ~20ms | ~520ms |
| Ký | ~50ms | ~5ms | ~55ms |
| Xác thực | ~2ms | ~3ms | ~5ms |

### Kiến trúc mở rộng

```
┌─────────────────────────────────────────────────┐
│              NGINX Load Balancer                │
└─────────────────────────────────────────────────┘
          │              │              │
     ┌────┴────┐    ┌────┴────┐    ┌────┴────┐
     │Django 1 │    │Django 2 │    │Django 3 │
     └────┬────┘    └────┬────┘    └────┬────┘
          └──────────────┼──────────────┘
                         │
                ┌────────┴────────┐
                │   PostgreSQL    │
                │   (Primary)     │
                └────────┬────────┘
                         │
                ┌────────┴────────┐
                │   PostgreSQL    │
                │   (Replica)     │
                └─────────────────┘
```

---

## Slide 23: 9. Tích hợp vào Việt Nam

### Hệ sinh thái E-Gov Việt Nam hiện tại

```
┌─────────────────────────────────────────────────────┐
│            HẠ TẦNG PKI QUỐC GIA                     │
├─────────────────────────────────────────────────────┤
│                  NEAC Root CA                        │
│       (Trung tâm Chứng thực điện tử quốc gia)       │
└────────────────────────┬────────────────────────────┘
                         │
     ┌───────────────────┼───────────────────┐
     ▼                   ▼                   ▼
┌─────────┐        ┌─────────┐        ┌─────────┐
│ VNPT-CA │        │Viettel-CA│       │  FPT-CA │
└─────────┘        └─────────┘        └─────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │   HỆ THỐNG NÀY     │◄── Quantum-Ready
              │   (PQ Sub-CA)       │    Sub-CA
              └─────────────────────┘
```

### Điểm tích hợp
- **NGSP:** Nền tảng tích hợp dịch vụ
- **VDXP:** Nền tảng trao đổi dữ liệu
- **CSDL Dân cư quốc gia**

---

## Slide 24: 10. Các phương án thay thế PKI

### So sánh các phương án

| Phương án | Ưu điểm | Nhược điểm | Lựa chọn |
|-----------|---------|------------|----------|
| **Hierarchical PKI** | Tin cậy rõ ràng, mở rộng tốt | Single point of failure | ✅ Sử dụng |
| **Web of Trust** | Phi tập trung | Khó quản lý quy mô lớn | ❌ |
| **Blockchain-based** | Minh bạch, bất biến | Hiệu năng, phức tạp | ❌ |
| **Self-sovereign ID** | User control | Tiêu chuẩn chưa mature | ❌ |

### Tại sao chọn Hierarchical PKI?
- Phù hợp cấu trúc hành chính Việt Nam
- Tương thích hạ tầng NEAC hiện có
- Chuỗi trách nhiệm rõ ràng
- Đã chứng minh ở quy mô chính phủ

---

## Slide 25: 11. Tương lai & Post-quantum Readiness

### Triển khai PQ trong hệ thống

| Thành phần | Thuật toán | Tiêu chuẩn NIST | Trạng thái |
|------------|-----------|-----------------|------------|
| Chữ ký | Dilithium3 | FIPS 204 (ML-DSA) | ✅ Đã triển khai |
| KEM | Kyber768 | FIPS 203 (ML-KEM) | ✅ Đã triển khai |
| Hash | SHA-3-256 | FIPS 202 | ✅ Đã triển khai |

### Chiến lược chuyển đổi

```
Giai đoạn 1 (Hiện tại): Hybrid Classical + PQ
    ↓
Giai đoạn 2 (2025-2027): Tăng cường sử dụng PQ
    ↓
Giai đoạn 3 (2030+): PQ-only khi classical bị deprecate
```

### Algorithm Agility
- Thiết kế crypto modular cho phép swap thuật toán
- Hỗ trợ nhiều thuật toán PQ (Falcon, SPHINCS+)

---

## Slide 26: 12. Quy trình khẩn cấp & Quản trị khủng hoảng

### Quy trình ứng phó sự cố

| Loại sự cố | Phản ứng | RTO |
|------------|----------|-----|
| **Key Compromise (User)** | Thu hồi ngay, cập nhật CRL | 1 giờ |
| **Key Compromise (Sub-CA)** | Thu hồi CA, cấp lại chứng thư | 24 giờ |
| **Key Compromise (Root)** | Xây dựng lại PKI | 7 ngày |
| **Database Failure** | Failover sang replica | 15 phút |

### Disaster Recovery
- **Database backup:** Hàng ngày, lưu trữ 30 ngày
- **Root CA backup:** Offline, mã hóa, cách ly địa lý
- **Key escrow:** M-of-N scheme (khuyến nghị)

---

## Slide 27: 13. Bảo mật chuỗi cung ứng khóa & HSM

### Triển khai hiện tại

```
┌─────────────────────────────────────────┐
│         LƯU TRỮ KHÓA (Hiện tại)          │
├─────────────────────────────────────────┤
│  Private Keys → Mã hóa AES-256-GCM      │
│       ↓                                  │
│  Master Key → Biến môi trường            │
│       ↓                                  │
│  Lưu trong Database                      │
└─────────────────────────────────────────┘
```

### Kiến trúc Production (Khuyến nghị)

```
┌─────────────────────────────────────────┐
│        LƯU TRỮ KHÓA (Production)         │
├─────────────────────────────────────────┤
│  Root CA Key → HSM (FIPS 140-2 Level 3) │
│  Sub-CA Keys → HSM hoặc Encrypted DB    │
│  User Keys → Software tokens / Mobile   │
└─────────────────────────────────────────┘
```

### Lựa chọn HSM cho Việt Nam
- Thales Luna Network HSM
- AWS CloudHSM (triển khai cloud)
- Hạ tầng HSM của VNPT

---

## Slide 28: 14. Quyền riêng tư & Bảo vệ DLCN

### Phân loại dữ liệu

| Loại dữ liệu | Độ nhạy cảm | Bảo vệ |
|--------------|-------------|--------|
| Danh tính người dùng | Cao | Mã hóa, kiểm soát truy cập |
| Private Keys | Tối quan trọng | AES-256-GCM, HSM |
| Chứng thư | Công khai | Bảo vệ toàn vẹn |
| Audit Logs | Cao | Hash chain-linked |

### Tuân thủ NĐ 13/2023/NĐ-CP
- [x] Đồng ý người dùng cho thu thập dữ liệu
- [x] Giới hạn mục đích
- [x] Tối thiểu hóa dữ liệu
- [x] Kiểm soát truy cập
- [ ] Đánh giá tác động BVDL (cần thực hiện)

---

## Slide 29: 15. Cross-border & Công nhận quốc tế

### Trạng thái hiện tại

| Khu vực | Công nhận | Ghi chú |
|---------|-----------|---------|
| **Việt Nam** | ⚠️ Một phần | Cần chứng nhận NEAC |
| **ASEAN** | ⚠️ Một phần | ASEAN Agreement on E-Commerce |
| **Quốc tế** | ❌ Chưa | Cần WebTrust/ETSI audit |

### Lộ trình công nhận quốc tế
1. Chứng nhận NEAC (neo tin cậy Việt Nam)
2. WebTrust audit cho CAs
3. Tuân thủ eIDAS (công nhận EU)
4. Cross-certification với CA quốc tế

### Tình trạng PQ quốc tế
- Chưa có khung pháp lý quốc tế cho PQ
- Chữ ký hybrid là cầu nối
- Tiêu chuẩn NIST đang được áp dụng toàn cầu

---

## Slide 30: 16. Đo lường hiệu quả & KPI của PKI

### KPIs đề xuất

| Danh mục | KPI | Mục tiêu |
|----------|-----|----------|
| **Tính sẵn sàng** | System uptime | 99.9% |
| **Hiệu năng** | Thời gian cấp chứng thư | < 5 phút |
| **Bảo mật** | Tỷ lệ xác thực thất bại | < 0.1% |
| **Thu hồi** | Tần suất cập nhật CRL | Mỗi 24 giờ |
| **Áp dụng** | Chứng thư cấp/tháng | Xu hướng tăng |
| **Tuân thủ** | Thời gian xử lý findings | < 30 ngày |

### Giám sát
- Prometheus + Grafana dashboards
- Audit logs chống giả mạo
- Real-time alerting cho sự kiện bảo mật

---

## Slide 31: 17. Đạo đức & Trách nhiệm xã hội

### Cân nhắc đạo đức

| Vấn đề | Cách tiếp cận |
|--------|---------------|
| **Khoảng cách số** | Dịch vụ hybrid (số + giấy) trong chuyển đổi |
| **Quyền riêng tư** | Thu thập dữ liệu tối thiểu, mã hóa |
| **Minh bạch** | Mã nguồn mở, audit logs |
| **Tiếp cận** | Nhiều phương thức xác thực |

### Trách nhiệm xã hội
- Hòa nhập số cho mọi công dân
- Giảm tham nhũng thông qua trách nhiệm giải trình
- Tác động môi trường: Giảm tiêu thụ giấy
- Chương trình đào tạo năng lực số

### Ngăn chặn lạm dụng
- Kiểm soát truy cập nghiêm ngặt
- Audit trails cho mọi thao tác
- Thu hồi chứng thư nếu vi phạm

---

## Slide 32: 18. Lịch sử & Bài học 30 năm triển khai PKI

### Timeline phát triển PKI

| Năm | Mốc quan trọng | Bài học |
|-----|----------------|---------|
| **1995** | Hết hạn patent RSA, PGP lan rộng | Tiêu chuẩn mở thúc đẩy áp dụng |
| **1996** | VeriSign CA thương mại | Thách thức mô hình kinh doanh |
| **2003** | Tiêu chuẩn ETSI cho EU | Quy định tạo niềm tin |
| **2011** | DigiNotar breach | Niềm tin mong manh, audit thiết yếu |
| **2015** | Let's Encrypt ra mắt | Tự động hóa dân chủ hóa PKI |
| **2024** | Tiêu chuẩn NIST PQC | Crypto agility rất quan trọng |

### Bài học áp dụng
1. **Niềm tin xây dựng nhiều năm, mất trong vài giây** → Audit logging mạnh
2. **Tự động hóa giảm lỗi** → API-first design
3. **Chuẩn bị cho thay đổi thuật toán** → Hybrid crypto, modular design
4. **Khung pháp lý thiết yếu** → Liên kết luật Việt Nam
5. **Trải nghiệm người dùng quan trọng** → Nhiều phương thức xác thực

---

# PHẦN 4: HƯỚNG DẪN TRIỂN KHAI (SLIDES 33-38)

---

## Slide 33: Yêu cầu hệ thống

### Yêu cầu tối thiểu

| Thành phần | Yêu cầu |
|------------|---------|
| **OS** | Ubuntu 20.04+ / Windows 10+ |
| **CPU** | 2 cores |
| **RAM** | 4 GB |
| **Storage** | 20 GB |
| **Python** | 3.8+ |
| **Node.js** | 14.x+ |
| **PostgreSQL** | 12+ |
| **Docker** | 20.10+ |

### Yêu cầu Production

| Thành phần | Yêu cầu |
|------------|---------|
| **CPU** | 4+ cores |
| **RAM** | 8+ GB |
| **Storage** | 100 GB SSD |
| **HSM** | FIPS 140-2 Level 3 |

---

## Slide 34: Quick Start với Docker

### Bước 1: Clone repository
```powershell
git clone <repository-url>
cd "code web"
```

### Bước 2: Khởi động services
```powershell
# Build và start tất cả services
docker-compose up --build

# Hoặc chạy nền
docker-compose up -d --build
```

### Bước 3: Truy cập ứng dụng
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000/api
- **Admin:** http://localhost:8000/admin

### Các lệnh hữu ích
```powershell
# Xem logs
docker-compose logs -f

# Chạy migrations
docker-compose exec backend python manage.py migrate

# Tạo superuser
docker-compose exec backend python manage.py createsuperuser
```

---

## Slide 35: Cài đặt thủ công - Backend

### Bước 1: Tạo môi trường ảo
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
```

### Bước 2: Cài đặt dependencies
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### Bước 3: Cài đặt liboqs (Post-Quantum)
```bash
# Ubuntu/Debian
sudo apt-get install cmake ninja-build libssl-dev
git clone https://github.com/open-quantum-safe/liboqs.git
cd liboqs && mkdir build && cd build
cmake -GNinja -DBUILD_SHARED_LIBS=ON ..
ninja && sudo ninja install && sudo ldconfig
```

### Bước 4: Cấu hình database & chạy
```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## Slide 36: Cài đặt thủ công - Frontend

### Bước 1: Cài đặt dependencies
```powershell
cd frontend
npm install
```

### Bước 2: Cấu hình
Tạo file `.env`:
```
REACT_APP_API_URL=http://localhost:8000/api
```

### Bước 3: Chạy development server
```powershell
npm start
```

### Build production
```powershell
npm run build
```

---

## Slide 37: Demo - Tạo Root CA

### API Call
```bash
POST /api/pki/ca/
{
    "name": "E-Gov Root CA VN",
    "common_name": "E-Gov Root CA",
    "organization": "Vietnam Government",
    "country": "VN",
    "ca_type": "ROOT",
    "validity_years": 20
}
```

### Kết quả
- Root CA với khóa RSA-4096 + Dilithium3
- Chứng thư X.509 self-signed
- Private keys mã hóa AES-256-GCM

---

## Slide 38: Demo - Ký PDF với Hybrid Signature

### API Call
```bash
POST /api/pki/sign/
Content-Type: multipart/form-data

{
    "pdf_file": <uploaded_file.pdf>,
    "certificate_id": 123
}
```

### Cấu trúc chữ ký Hybrid
```json
{
    "version": "1.0",
    "config": "HYBRID_RSA4096_DILITHIUM3",
    "message_hash": "sha384:...",
    "classical_signature": "base64:...",
    "pq_signature": "base64:...",
    "timestamp": "2025-12-04T10:30:00Z"
}
```

---

# PHẦN 5: KẾT LUẬN (SLIDES 39-42)

---

## Slide 39: Điểm mạnh của Hệ thống

### Điểm mạnh Kỹ thuật
- ✅ **Quantum-Ready:** Hệ thống e-gov VN đầu tiên với thuật toán NIST PQ
- ✅ **Bảo mật Hybrid:** Defense-in-depth, không có single point of crypto failure
- ✅ **Dựa trên Tiêu chuẩn:** X.509, PKCS, RFC-compliant
- ✅ **Mở rộng được:** Thiết kế modular cho thuật toán tương lai
- ✅ **Kiểm toán được:** Logs chain-linked chống giả mạo

### Điểm mạnh Chiến lược
- ✅ Phù hợp Chiến lược E-Government Việt Nam
- ✅ Tương thích hạ tầng NEAC hiện có
- ✅ Kiến trúc mở (không vendor lock-in)
- ✅ Chi phí hiệu quả với stack mã nguồn mở

---

## Slide 40: Hạn chế & Hướng phát triển

### Hạn chế hiện tại

| Hạn chế | Tác động | Giải pháp |
|---------|----------|-----------|
| Lưu trữ khóa phần mềm | Rủi ro bảo mật | Tích hợp HSM |
| Chưa có mobile app | Khả năng tiếp cận | Phát triển tương lai |
| Cần giấy phép CA | Chậm triển khai | Hợp tác CA được cấp phép |
| License PDF library | Chi phí | Đánh giá mã nguồn mở |

### Các bước tiếp theo
1. **Ngay lập tức:** Kiểm toán bảo mật bên thứ ba
2. **Ngắn hạn:** Mua sắm và tích hợp HSM
3. **Trung hạn:** Quy trình chứng nhận NEAC
4. **Dài hạn:** Triển khai thí điểm quốc gia

---

## Slide 41: Tổng kết cho Thầy

### Đáp ứng yêu cầu

1. ✅ **PKI là hệ thống đa ngành:** Phân tích 18 khía cạnh
2. ✅ **Mapping vào PKI thực tế:** Tích hợp hệ sinh thái NEAC Việt Nam
3. ✅ **Giá trị thực tiễn:** Chi phí-lợi ích rõ ràng, phân tích rủi ro, lộ trình triển khai
4. ✅ **Chiều sâu đa ngành:** Phân tích pháp lý, kinh tế, xã hội, kỹ thuật

### Điểm đổi mới
- Prototype PKI hậu lượng tử e-government đầu tiên cho Việt Nam
- Cách tiếp cận mật mã hybrid cho giai đoạn chuyển đổi
- Algorithm agility cho future-proofing
- Audit logging toàn diện cho compliance

---

## Slide 42: Cảm ơn & Hỏi đáp

### Thông tin liên hệ
- **Repository:** [GitHub Link]
- **Tài liệu:** Thư mục `/docs/`

### Câu hỏi gợi ý
1. Làm thế nào tích hợp với CSDL Dân cư Quốc gia?
2. Chiến lược áp dụng cho vùng nông thôn?
3. Xử lý vấn đề pháp lý của chữ ký PQ?
4. Kế hoạch DR cho trường hợp Root CA bị xâm nhập?

### Tài liệu tham khảo
- NIST FIPS 203, 204, 205, 206 (PQC Standards)
- Luật Giao dịch Điện tử 2023
- Open Quantum Safe Project (liboqs)
- RFC 5280 (X.509)

---

# PHỤ LỤC

## A: Tổng hợp công nghệ

```
Backend:
├── Python 3.10+
├── Django 4.x + Django REST Framework
├── PostgreSQL 15
├── cryptography 41+ (mật mã cổ điển)
├── liboqs-python 0.9+ (mật mã hậu lượng tử)
└── PDFNetPython3 (xử lý PDF)

Frontend:
├── React 18.x
├── Redux (quản lý state)
├── Bootstrap 5
└── Axios (API client)

Infrastructure:
├── Docker / Docker Compose
├── Nginx (reverse proxy)
└── Gunicorn (WSGI server)
```

## B: Bảng thuật ngữ

| Tiếng Việt | Tiếng Anh | Viết tắt |
|------------|-----------|----------|
| Tổ chức chứng thực | Certificate Authority | CA |
| Chứng thư số | Digital Certificate | - |
| Danh sách thu hồi | Revocation List | CRL |
| Hạ tầng khóa công khai | Public Key Infrastructure | PKI |
| Hậu lượng tử | Post-Quantum | PQ |
| Mô-đun bảo mật phần cứng | Hardware Security Module | HSM |
| Trung tâm CTĐTQG | National Electronic Authentication Center | NEAC |

## C: Lộ trình triển khai

```
Giai đoạn 1 (6-12 tháng): Thí điểm
├── Triển khai tại 2-3 quận/huyện
├── Giới hạn loại hồ sơ
└── Đào tạo người dùng pilot

Giai đoạn 2 (3-6 tháng): Đánh giá
├── Kiểm toán bảo mật
├── Đánh giá tuân thủ pháp lý
└── Tối ưu hiệu năng

Giai đoạn 3 (12-18 tháng): Mở rộng tỉnh
├── Triển khai toàn tỉnh
├── Tích hợp hệ thống tỉnh
└── Xây dựng hạ tầng hỗ trợ

Giai đoạn 4 (24-36 tháng): Triển khai quốc gia
├── Tích hợp NGSP, VDXP
├── Trao đổi văn bản liên ngành
└── Nỗ lực công nhận quốc tế
```

---

*Bài trình bày chuẩn bị cho NT208 - Electronic Government PKI*  
*Thạc sĩ An toàn Thông tin*  
*Tháng 12, 2025*
