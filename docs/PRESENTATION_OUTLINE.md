# Post-Quantum PKI E-Government System
## Presentation for Master in Information Security - PKI Course
### NT208 - Chính quyền điện tử PKI
---

# SLIDE OUTLINE (30-45 slides)

---

## PART 1: INTRODUCTION (Slides 1-8)

### Slide 1: Title Slide
- **Title**: Hệ thống Chính quyền Điện tử sử dụng Hạ tầng Khóa công khai Hậu Lượng tử
- **Subtitle**: Post-Quantum PKI E-Government System
- **Course**: NT208 - Chính quyền điện tử PKI
- **Program**: Thạc sĩ An toàn Thông tin
- **Date**: December 2024

---

### Slide 2: Agenda / Mục lục
1. Giới thiệu về PKI (Public Key Infrastructure)
2. Giới thiệu về Mật mã Hậu lượng tử (Post-Quantum Cryptography)
3. Tổng quan Hệ thống (Kiến trúc & Vấn đề giải quyết)
4. Phân tích Đa ngành (Pháp lý, Kinh tế, Kỹ thuật, Xã hội)
5. Hướng dẫn Triển khai
6. Kết luận & Thảo luận

---

### Slide 3: PKI là gì? (Introduction to PKI)
**Định nghĩa:**
- PKI = Public Key Infrastructure (Hạ tầng Khóa công khai)
- Hệ thống quản lý chứng thư số, khóa mã hóa và định danh số

**Các thành phần chính:**
- **Certificate Authority (CA)**: Tổ chức cấp chứng thư
- **Registration Authority (RA)**: Xác minh danh tính
- **Certificate Repository**: Lưu trữ chứng thư
- **Certificate Revocation List (CRL)**: Danh sách thu hồi

**Ứng dụng:**
- Chữ ký số, Xác thực, Mã hóa, Non-repudiation

---

### Slide 4: PKI - Không chỉ là Công nghệ
**PKI là Hệ thống Đa ngành (Socio-Technical-Legal-Economic System):**

```
┌─────────────────────────────────────────────────────────────┐
│                         PKI ECOSYSTEM                        │
├─────────────┬─────────────┬─────────────┬──────────────────┤
│   KỸ THUẬT  │   PHÁP LÝ   │  KINH TẾ    │    XÃ HỘI       │
├─────────────┼─────────────┼─────────────┼──────────────────┤
│ Cryptography│ Luật GDĐT   │ Chi phí CA  │ Tin tưởng người │
│ X.509 Certs │ Nghị định   │ HSM costs   │ dùng            │
│ CRL/OCSP    │ CP/CPS      │ ROI         │ Đào tạo         │
│ Algorithms  │ Compliance  │ Business    │ Usability       │
└─────────────┴─────────────┴─────────────┴──────────────────┘
```

---

### Slide 5: Lịch sử Phát triển PKI (30 năm triển khai toàn cầu)
**Timeline:**
| Năm | Sự kiện |
|-----|---------|
| 1976 | Diffie-Hellman: Khái niệm PKC |
| 1978 | RSA algorithm ra đời |
| 1988 | X.509 v1 certificate standard |
| 1996 | VeriSign thương mại hóa CA |
| 2000 | Các nước ban hành luật Chữ ký số |
| 2005 | Vietnam: Luật Giao dịch điện tử |
| 2011 | DigiNotar breach - bài học lớn |
| 2017 | Certificate Transparency bắt buộc |
| 2022-24 | NIST Post-Quantum Standards |

**Bài học từ 30 năm:**
- Centralized trust có rủi ro (DigiNotar)
- Governance quan trọng hơn technology
- User experience quyết định adoption

---

### Slide 6: Mối đe dọa Lượng tử (Quantum Threat)
**Thuật toán Shor (1994):**
- Máy tính lượng tử có thể phá RSA, ECDSA, DH
- Thời gian: O(n³) thay vì O(2^n)

**Timeline dự kiến:**
- 2030-2035: Quantum computers đủ mạnh (ước tính)
- **Harvest Now, Decrypt Later**: Dữ liệu thu thập hôm nay có thể bị giải mã trong tương lai

**Các thuật toán bị ảnh hưởng:**
| Thuật toán | Độ dài khóa hiện tại | Sau khi có Quantum |
|------------|---------------------|-------------------|
| RSA-2048 | 112-bit security | ❌ BỊ PHÁ |
| ECDSA P-256 | 128-bit security | ❌ BỊ PHÁ |
| AES-256 | 256-bit | ⚠️ Giảm còn 128-bit |
| SHA-256 | 128-bit collision | ⚠️ Giảm còn 85-bit |

---

### Slide 7: Post-Quantum Cryptography (PQC)
**Định nghĩa:**
- Thuật toán mật mã có thể chống lại cả máy tính cổ điển và lượng tử

**NIST Standardization (2016-2024):**
- Vòng 1: 69 ứng viên
- Vòng 2: 26 ứng viên
- Vòng 3: 7 ứng viên (finalist + alternates)
- **Tiêu chuẩn (2024)**: ML-KEM (Kyber), ML-DSA (Dilithium), SLH-DSA (SPHINCS+)

**Các họ thuật toán PQC:**
| Họ | Cơ sở toán học | Ví dụ |
|----|---------------|-------|
| Lattice-based | Shortest Vector Problem | Dilithium, Kyber |
| Hash-based | Hash function security | SPHINCS+ |
| Code-based | Decoding random codes | Classic McEliece |
| Isogeny-based | Elliptic curve isogeny | SIKE (đã bị phá) |

---

### Slide 8: Hybrid Cryptography - Phương pháp tiếp cận
**Tại sao Hybrid?**
1. PQC algorithms còn mới, chưa được kiểm chứng 20+ năm như RSA
2. Có thể có lỗ hổng chưa được phát hiện
3. Đảm bảo backward compatibility
4. Tuân thủ pháp lý hiện hành (sử dụng thuật toán đã được công nhận)

**Chiến lược:**
```
Chữ ký Hybrid = Chữ ký RSA/ECDSA + Chữ ký Dilithium
                  ↓                    ↓
          Pháp lý hiện hành    Bảo mật tương lai
```

**Xác minh:**
- Cả hai chữ ký phải hợp lệ → Văn bản được chấp nhận
- Nếu một thuật toán bị phá → Thuật toán còn lại vẫn bảo vệ

---

## PART 2: SYSTEM OVERVIEW (Slides 9-16)

### Slide 9: Tổng quan Kiến trúc Hệ thống
```
┌────────────────────────────────────────────────────────────────────┐
│                      FRONTEND (React + Redux)                       │
│   • Đăng nhập/Đăng ký    • Nộp hồ sơ    • Quản lý chứng thư       │
└───────────────────────────────────────────────────────────────────┘
                              │
                    REST API (JWT + Certificate Auth)
                              │
┌────────────────────────────────────────────────────────────────────┐
│                  BACKEND (Django REST Framework)                    │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                    PKI APPLICATION                          │   │
│  │  • CA Service         • Certificate Service                 │   │
│  │  • Crypto Module      • PDF Signing Service                 │   │
│  │  (RSA + Dilithium)    • Audit Logging                       │   │
│  └────────────────────────────────────────────────────────────┘   │
│  ┌──────────────┐  ┌──────────────────┐  ┌─────────────────┐     │
│  │Authentication│  │ HoSo (Hồ sơ)    │  │ Social Auth     │     │
│  │(Users/JWT)   │  │ (Quản lý văn bản)│  │ (Google/FB)     │     │
│  └──────────────┘  └──────────────────┘  └─────────────────┘     │
└────────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │   PostgreSQL      │
                    │   Database        │
                    └───────────────────┘
```

---

### Slide 10: Certificate Hierarchy (Mô hình Tin cậy)
```
                    ┌─────────────────────────────┐
                    │       ROOT CA               │
                    │  "E-Gov Root CA VN"         │
                    │  Hybrid: RSA-4096 +         │
                    │         Dilithium3          │
                    │  Validity: 20 years         │
                    │  [OFFLINE - Air-gapped]     │
                    └─────────────┬───────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│  OFFICER SUB-CA   │ │  CITIZEN SUB-CA   │ │  SERVICE SUB-CA   │
│  Cán bộ/Công chức │ │  Công dân         │ │  Ứng dụng         │
│  Validity: 10 yrs │ │  Validity: 10 yrs │ │  Validity: 5 yrs  │
└────────┬──────────┘ └────────┬──────────┘ └────────┬──────────┘
         │                     │                     │
         ▼                     ▼                     ▼
   ┌───────────┐         ┌───────────┐         ┌───────────┐
   │ Officer   │         │ Citizen   │         │ Service   │
   │ Certs     │         │ Certs     │         │ Certs     │
   │ (2 yrs)   │         │ (3 yrs)   │         │ (1 yr)    │
   └───────────┘         └───────────┘         └───────────┘
```

**Trust Model**: Hierarchical (phân cấp) - phù hợp với cấu trúc hành chính Việt Nam

---

### Slide 11: Vấn đề Giải quyết
**Vấn đề hiện tại của E-Government Việt Nam:**

| Vấn đề | Mô tả | Giải pháp của Hệ thống |
|--------|-------|----------------------|
| Quantum Threat | PKI hiện tại sẽ bị phá trong 10-15 năm | ✅ Hybrid PQC |
| Chữ ký số phức tạp | Người dùng cần USB Token riêng | ✅ Web-based signing |
| Tích hợp rời rạc | Mỗi bộ ngành hệ thống khác | ✅ Unified PKI |
| Chi phí cao | HSM, CA license đắt đỏ | ✅ Open-source |
| Thiếu audit trail | Khó truy vết sự cố | ✅ Tamper-proof logging |

---

### Slide 12: Thuật toán Mật mã Triển khai
**Chữ ký số (ML-DSA - FIPS 204):**

| Thuật toán | NIST Level | Key Size | Signature | Sử dụng |
|------------|-----------|----------|-----------|---------|
| Dilithium2 | Level 2 | 1.3 KB | 2.4 KB | Basic |
| **Dilithium3** | Level 3 | 1.9 KB | 3.3 KB | **Mặc định** |
| Dilithium5 | Level 5 | 2.6 KB | 4.6 KB | High security |

**Trao đổi khóa (ML-KEM - FIPS 203):**

| Thuật toán | NIST Level | Public Key | Ciphertext |
|------------|-----------|------------|------------|
| Kyber512 | Level 1 | 800 B | 768 B |
| **Kyber768** | Level 3 | 1,184 B | 1,088 B |
| Kyber1024 | Level 5 | 1,568 B | 1,568 B |

---

### Slide 13: Luồng Nghiệp vụ - Nộp Hồ sơ
```
┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌─────────────┐
│ Công dân │    │   Hệ thống   │    │   Cán bộ    │    │  Công dân   │
│          │    │              │    │             │    │  (Nhận KQ)  │
└────┬─────┘    └──────┬───────┘    └──────┬──────┘    └──────┬──────┘
     │                 │                   │                  │
     │ 1. Đăng nhập   │                   │                  │
     │ (JWT/Cert)     │                   │                  │
     │───────────────>│                   │                  │
     │                 │                   │                  │
     │ 2. Nộp hồ sơ   │                   │                  │
     │ (PDF + data)   │                   │                  │
     │───────────────>│                   │                  │
     │                 │ 3. Thông báo     │                  │
     │                 │─────────────────>│                  │
     │                 │                   │                  │
     │                 │ 4. Xem xét       │                  │
     │                 │<─────────────────│                  │
     │                 │                   │                  │
     │                 │ 5. Ký số         │                  │
     │                 │ (Hybrid:         │                  │
     │                 │  RSA+Dilithium)  │                  │
     │                 │<─────────────────│                  │
     │                 │                   │                  │
     │                 │ 6. Gửi kết quả   │                  │
     │                 │──────────────────────────────────> │
     │                 │                   │                  │
```

---

### Slide 14: Demo - Giao diện Hệ thống
**Screenshots:**
1. Trang đăng nhập (Email/Social Auth)
2. Dashboard công dân
3. Form nộp hồ sơ
4. Quản lý chứng thư số
5. Xác minh chữ ký PDF

---

### Slide 15: Công nghệ Sử dụng
| Tầng | Công nghệ | Phiên bản |
|------|-----------|-----------|
| **Frontend** | React, Redux, SCSS | 17.x |
| **Backend** | Django, DRF | 4.x |
| **Database** | PostgreSQL | 14+ |
| **Crypto (Classical)** | cryptography library | 41+ |
| **Crypto (PQ)** | liboqs-python | 0.9+ |
| **PDF Signing** | PDFNetPython3 | Latest |
| **Container** | Docker, Docker Compose | 24+ |
| **Auth** | SimpleJWT, Social Auth | 5.x |

---

### Slide 16: API Endpoints
**PKI Endpoints (`/api/pki/`):**

| Endpoint | Method | Chức năng |
|----------|--------|-----------|
| `/ca/` | GET, POST | Quản lý CA |
| `/ca/{id}/chain/` | GET | Lấy chuỗi chứng thư |
| `/certificates/` | GET | Danh sách chứng thư |
| `/certificates/{id}/revoke/` | POST | Thu hồi chứng thư |
| `/requests/` | GET, POST | Yêu cầu cấp chứng thư |
| `/sign-pdf/` | POST | Ký văn bản PDF |
| `/verify-pdf/` | POST | Xác minh chữ ký |
| `/challenge/request/` | POST | Challenge-Response Auth |

---

## PART 3: MULTI-DIMENSIONAL ANALYSIS (Slides 17-35)
### (Phân tích Đa ngành - 18 Khía cạnh)

---

### Slide 17: 1. Trust Model & Root of Trust
**Mô hình Tin cậy của Hệ thống:**

| Khía cạnh | Triển khai | Đánh giá |
|-----------|------------|----------|
| Hierarchy | 3-tier (Root → Intermediate → End-entity) | ✅ Phù hợp hành chính VN |
| Root CA | Offline, air-gapped (khuyến nghị) | ⚠️ Cần HSM thực tế |
| Key Ceremony | Chưa định nghĩa formal | ⚠️ Cần bổ sung |
| Trust Anchor | Root CA certificate | ✅ Standard X.509 |

**So sánh với PKI thực tế:**
- VNPT-CA: Hierarchical, 2-3 tier
- NACENCOMM (NEAC): Government PKI
- Viettel-CA: Commercial CA

**Khuyến nghị:**
- Bổ sung Key Ceremony procedure
- Tích hợp HSM (FIPS 140-2 Level 3)
- Định kỳ audit Root CA

---

### Slide 18: 2. Governance & Policy (CP/CPS)
**Certificate Policy (CP) - Chính sách Chứng thư:**

| Loại chứng thư | Mục đích | Validity | Verification |
|----------------|----------|----------|--------------|
| Officer | Ký văn bản hành chính | 2 năm | Xác minh qua HR |
| Citizen | Giao dịch công dân | 3 năm | eKYC/CCCD |
| Service | Xác thực hệ thống | 1 năm | Domain validation |

**Certification Practice Statement (CPS) - Quy trình:**
```
1. Identity Verification → 2. Key Generation → 3. Certificate Issuance
        ↓                        ↓                      ↓
   RA validates           User's device or     CA signs with
   (eKYC, documents)      CA (server-side)     hybrid keys
```

**Gap Analysis:**
- ❌ Chưa có formal CP/CPS document
- ❌ Chưa định nghĩa audit frequency
- ⚠️ Key escrow policy chưa rõ ràng

---

### Slide 19: 3. Legal & Compliance (Pháp lý)
**Khung Pháp lý Việt Nam:**

| Văn bản | Nội dung | Tương thích |
|---------|----------|-------------|
| Luật GDĐT 2005 (sửa đổi 2023) | Công nhận chữ ký số | ⚠️ Cần CA được công nhận |
| Nghị định 130/2018/NĐ-CP | Chi tiết chữ ký số | ⚠️ Yêu cầu lưu trữ khóa |
| Nghị định 13/2023/NĐ-CP | Bảo vệ dữ liệu cá nhân | ✅ Cần đánh giá DPIA |
| Thông tư 16/2019/TT-BTTTT | Tiêu chuẩn CA | ❌ Cần chứng nhận NEAC |

**Thách thức Pháp lý với PQC:**
1. Dilithium chưa được công nhận chính thức tại VN
2. Cần sử dụng thuật toán RSA/ECDSA song song để đảm bảo hiệu lực pháp lý
3. Giải pháp: **Hybrid signature** - RSA cho pháp lý, Dilithium cho tương lai

**Roadmap tuân thủ:**
- Short-term: Hybrid mode (legal compliance)
- Mid-term: Lobby for PQC recognition
- Long-term: Pure PQC when standardized in Vietnam

---

### Slide 20: 4. Economic & Business Model (Kinh tế)
**Chi phí Triển khai (Ước tính):**

| Hạng mục | Chi phí một lần | Chi phí hàng năm |
|----------|----------------|------------------|
| HSM (FIPS 140-2 L3) | $50,000-150,000 | $10,000 (maintenance) |
| Server infrastructure | $20,000 | $5,000 |
| Development | $100,000 | $30,000 (updates) |
| Audit & Compliance | - | $20,000 |
| Training | $10,000 | $5,000 |
| **TỔNG** | **$180,000-280,000** | **$70,000/năm** |

**So sánh với giải pháp thương mại:**
| Giải pháp | Chi phí/năm | Ưu điểm | Nhược điểm |
|-----------|-------------|---------|------------|
| VNPT-CA | $30-50/cert | Pháp lý đầy đủ | Không có PQC |
| Viettel-CA | $25-40/cert | Hỗ trợ tốt | Không có PQC |
| **Hệ thống này** | Self-hosted | PQC ready, tùy biến | Cần đầu tư ban đầu |

**ROI Analysis:**
- Break-even: ~3 năm với 10,000+ users
- Long-term value: Quantum-safe từ đầu

---

### Slide 21: 5. Real-world Breaches & Lessons
**Case Studies - PKI Failures:**

| Sự cố | Năm | Nguyên nhân | Bài học |
|-------|-----|-------------|---------|
| **DigiNotar** | 2011 | Hacker xâm nhập, cấp cert giả cho Google | Network segmentation, audit logs |
| **Comodo** | 2011 | RA compromised | Strong RA verification |
| **Symantec** | 2017 | Cấp cert sai quy trình | Certificate Transparency |
| **Let's Encrypt** | 2020 | CAA bug, thu hồi 3M certs | Automated validation |

**Áp dụng cho Hệ thống:**
- ✅ Audit log với hash chain (tamper-proof)
- ✅ Role-based access control
- ⚠️ Cần thêm Certificate Transparency
- ⚠️ Cần automated monitoring

**Recommendations:**
```
1. Integrate with CT logs (Google, Apple)
2. Implement automated anomaly detection
3. Regular penetration testing
4. Incident response plan document
```

---

### Slide 22: 6. Interoperability & Standards
**Tiêu chuẩn Tuân thủ:**

| Tiêu chuẩn | Mô tả | Trạng thái |
|------------|-------|------------|
| X.509 v3 (RFC 5280) | Certificate format | ✅ Hoàn toàn |
| PKCS#10 (RFC 2986) | CSR format | ✅ Hoàn toàn |
| CRL (RFC 5280) | Revocation list | ✅ Cơ bản |
| OCSP (RFC 6960) | Online status check | ⚠️ Chưa triển khai |
| NIST FIPS 203 (ML-KEM) | PQ Key Exchange | ✅ Kyber |
| NIST FIPS 204 (ML-DSA) | PQ Signatures | ✅ Dilithium |
| IETF Draft (PQ X.509) | PQ in certificates | ⚠️ Experimental |

**Interoperability Challenges:**
1. PQ certificate extensions chưa chuẩn hóa hoàn toàn
2. Browser/OS chưa hỗ trợ native PQ
3. HSM vendors đang update firmware

**Strategy:**
- Hiện tại: Classical cert + PQ metadata extension
- Tương lai: Full PQ composite certificates

---

### Slide 23: 7. Usability & Human Factors
**Thiết kế UX của Hệ thống:**

| Tính năng | Mô tả | User-friendliness |
|-----------|-------|-------------------|
| Web-based signing | Không cần USB token | ⭐⭐⭐⭐⭐ |
| Social login | Google, Facebook auth | ⭐⭐⭐⭐⭐ |
| Certificate auto-renewal | Thông báo trước 30 ngày | ⭐⭐⭐⭐ |
| Mobile responsive | Hỗ trợ smartphone | ⭐⭐⭐⭐ |

**So sánh với hệ thống hiện tại:**
| Tiêu chí | USB Token truyền thống | Hệ thống Web-based |
|----------|------------------------|-------------------|
| Cài đặt driver | Cần | Không |
| Tương thích | Windows only | Cross-platform |
| Portable | Cần mang token | Anywhere |
| Security | Hardware-bound | Server-side (cần HSM) |

**Trade-offs:**
- ⚠️ Server-side key storage: Cần HSM và strong access control
- ⚠️ Cần 2FA để bù đắp việc không có hardware token

---

### Slide 24: 8. Scalability & Performance
**Performance Benchmarks (Dilithium3):**

| Phép toán | Thời gian | So với RSA-2048 |
|-----------|-----------|-----------------|
| Key Generation | 0.5 ms | 10x nhanh hơn |
| Sign | 1.2 ms | Tương đương |
| Verify | 0.8 ms | 2x nhanh hơn |

**Scalability Analysis:**

| Scale | Users | Certificates/day | Infrastructure |
|-------|-------|------------------|----------------|
| Pilot | 1,000 | 10 | 1 server |
| Department | 10,000 | 100 | 2 servers + LB |
| Province | 100,000 | 1,000 | 4 servers + Redis |
| National | 10M | 50,000 | Cluster + CDN |

**Bottlenecks:**
- Database (PostgreSQL) → Solution: Read replicas
- PDF signing → Solution: Worker queue
- Key ceremony → Solution: Batch processing

---

### Slide 25: 9. Vietnam-specific Context
**Tích hợp Hệ thống Hiện tại:**

| Hệ thống | Cơ quan | Khả năng Tích hợp |
|----------|---------|-------------------|
| Cổng DVCQG | Văn phòng Chính phủ | ⚠️ Cần API gateway |
| VNeID | Bộ Công an | ✅ eKYC integration |
| VGCA (VNPT) | VNPT | ⚠️ Cross-certification |
| eInvoice | Tổng cục Thuế | ✅ PDF signing compatible |

**Lộ trình Tích hợp:**
```
Phase 1: Standalone pilot (6 tháng)
    └── 1 đơn vị thí điểm

Phase 2: Integration (12 tháng)
    └── Kết nối VNeID, eInvoice

Phase 3: Federation (18 tháng)
    └── Cross-cert với VNPT-CA, Viettel-CA

Phase 4: National rollout (24+ tháng)
    └── Tích hợp Cổng DVCQG
```

**Quy định cần tuân thủ:**
- Thông tư 32/2017/TT-BTTTT: Tiêu chuẩn hệ thống CPĐT
- TCVN 7635:2007: Chữ ký số và dịch vụ xác thực
- Circular của NEAC về CA certification

---

### Slide 26: 10. Alternatives & Comparative Analysis
**So sánh các Phương án:**

| Phương án | Ưu điểm | Nhược điểm | PQ-ready |
|-----------|---------|-----------|----------|
| **PKI truyền thống** | Mature, legal | Quantum vulnerable | ❌ |
| **Blockchain-based** | Decentralized | High cost, slow | ⚠️ |
| **Web of Trust (PGP)** | No central CA | Hard to manage | ⚠️ |
| **Identity-based Crypto** | No cert needed | Key escrow issue | ⚠️ |
| **This System (Hybrid PKI)** | PQ-safe, compatible | New, needs testing | ✅ |

**Tại sao chọn Hybrid PKI?**
1. Backward compatible với hệ thống hiện có
2. Legal compliance với luật VN (qua RSA/ECDSA)
3. Future-proof với Dilithium/Kyber
4. Gradually migrate possible

---

### Slide 27: 11. Post-Quantum Readiness
**Algorithm Agility - Thiết kế Linh hoạt:**

```python
# Cấu hình trong settings.py
PKI_DEFAULT_PQ_ALGORITHM = 'DILITHIUM3'  # Có thể đổi
PKI_REQUIRE_HYBRID_SIGNATURES = True

# Crypto module hỗ trợ nhiều thuật toán
SUPPORTED_ALGORITHMS = {
    'classical': ['RSA_2048', 'RSA_4096', 'ECDSA_P256', 'ECDSA_P384'],
    'pq_signature': ['DILITHIUM2', 'DILITHIUM3', 'DILITHIUM5', 
                     'FALCON512', 'FALCON1024', 'SPHINCS_SHA2_128F'],
    'pq_kem': ['KYBER512', 'KYBER768', 'KYBER1024']
}
```

**Migration Plan khi có thuật toán mới:**
1. Add new algorithm to crypto module
2. Issue new certificates with new algorithm
3. Grace period: Accept both old and new
4. Revoke old certificates
5. Remove deprecated algorithm

**NIST Timeline:**
- 2024: FIPS 203, 204, 205 finalized
- 2025-2026: Industry adoption
- 2030: Recommended migration deadline

---

### Slide 28: 12. Incident Response & Disaster Recovery
**Incident Response Plan:**

| Sự cố | Severity | Response Time | Action |
|-------|----------|---------------|--------|
| Root CA compromise | CRITICAL | Immediate | Revoke all, rebuild PKI |
| Intermediate CA compromise | HIGH | 1 hour | Revoke sub-tree |
| End-entity key compromise | MEDIUM | 4 hours | Revoke individual cert |
| CRL server down | MEDIUM | 1 hour | Failover to backup |
| Algorithm vulnerability | HIGH | 24 hours | Disable, issue new certs |

**Disaster Recovery:**
```
RTO (Recovery Time Objective): 4 hours
RPO (Recovery Point Objective): 1 hour

Backup Strategy:
├── Database: PostgreSQL streaming replication
├── CA Keys: Encrypted backup to offline storage
├── Certificates: Daily backup to S3-compatible
└── Audit Logs: Real-time replication + immutable archive
```

**Đề xuất:**
- ⚠️ Cần bổ sung DR documentation chi tiết
- ⚠️ Cần regular DR drills (6 tháng/lần)
- ⚠️ Cần off-site backup location

---

### Slide 29: 13. Key Supply Chain & HSM Security
**Hiện trạng Hệ thống:**

| Thành phần | Triển khai hiện tại | Khuyến nghị Production |
|------------|---------------------|----------------------|
| Root CA key | Software (encrypted) | HSM FIPS 140-2 Level 3 |
| Intermediate CA key | Software (encrypted) | HSM FIPS 140-2 Level 3 |
| User private key | Server-side storage | Client-side or HSM |
| Encryption | AES-256-GCM | FIPS-validated |

**HSM Vendors hỗ trợ PQ:**

| Vendor | Model | PQ Support | Cost |
|--------|-------|------------|------|
| Thales | Luna 7 | Firmware update | $50K+ |
| Utimaco | SecurityServer | Dilithium ready | $40K+ |
| AWS | CloudHSM | Coming 2025 | Pay-as-you-go |
| Azure | Managed HSM | Planned | Pay-as-you-go |

**Key Ceremony đề xuất:**
```
1. Air-gapped environment preparation
2. Multiple key custodians (m-of-n threshold)
3. Video recording
4. Auditor presence
5. Key backup to separate HSM
6. Documentation signing
```

---

### Slide 30: 14. Privacy Implications
**Phân tích Quyền riêng tư:**

| Dữ liệu | Thu thập | Mục đích | Bảo vệ |
|---------|----------|----------|--------|
| Email | Bắt buộc | Định danh | Hashed in logs |
| CMND/CCCD | Bắt buộc | Xác minh | Encrypted at rest |
| Hồ sơ PDF | User upload | Xử lý hành chính | Signed, encrypted |
| IP Address | Auto | Audit | Anonymized after 90 days |

**Tuân thủ NĐ 13/2023/NĐ-CP (PDPA VN):**
- ✅ Consent collection
- ✅ Purpose limitation
- ⚠️ Data minimization (cần review)
- ⚠️ Right to erasure (conflict với audit)
- ⚠️ Cross-border transfer (nếu dùng cloud)

**GDPR Mapping (nếu mở rộng EU citizens):**
- Data Protection Impact Assessment (DPIA) required
- Data Processing Agreement với third parties
- Appointed DPO recommended

---

### Slide 31: 15. Cross-border & International Recognition
**Công nhận Quốc tế:**

| Khu vực | Framework | Tương thích |
|---------|-----------|-------------|
| EU | eIDAS 2.0 | ⚠️ Cần EU-VN MRA |
| ASEAN | ASEAN Framework on Digital Data Governance | ✅ Đang phát triển |
| APEC | Cross-Border Privacy Rules | ⚠️ Cần certification |
| China | Digital Signature Law | ❌ Separate system |

**Lộ trình Công nhận Quốc tế:**
1. **Domestic**: NEAC certification (bắt buộc)
2. **ASEAN**: ASEAN Digital Integration Framework
3. **Bilateral**: MRA với các nước (EU, Japan, Korea)
4. **Global**: WebTrust/ETSI audit

**Technical Requirements:**
- Certificate profiles theo ETSI EN 319 412
- Time-stamping theo RFC 3161
- Long-term validation theo ETSI EN 319 102

---

### Slide 32: 16. KPIs & Effectiveness Measurement
**Đo lường Hiệu quả PKI:**

| KPI | Mục tiêu | Đo lường |
|-----|----------|----------|
| **Availability** | 99.9% uptime | Monitoring (Prometheus) |
| **Issuance Time** | < 5 phút | API response time |
| **Revocation Time** | < 1 giờ | Time to CRL update |
| **User Adoption** | 80% eligible users | Registration rate |
| **Error Rate** | < 0.1% | Failed signatures |
| **Audit Compliance** | 100% | External audit results |

**Dashboard Metrics:**
```
┌────────────────────────────────────────────────────────────┐
│                 PKI Operations Dashboard                    │
├──────────────┬──────────────┬───────────────┬─────────────┤
│ Certs Issued │ Certs Active │ Revoked Today │ CRL Updates │
│    1,234     │   45,678     │      12       │     3       │
├──────────────┴──────────────┴───────────────┴─────────────┤
│              Monthly Signing Operations                     │
│ ████████████████████████░░░░░░░░ 78% of capacity           │
└────────────────────────────────────────────────────────────┘
```

---

### Slide 33: 17. Ethics & Social Responsibility
**Cân nhắc Đạo đức:**

| Khía cạnh | Vấn đề | Giải pháp |
|-----------|--------|-----------|
| **Access Equity** | Digital divide (người già, vùng xa) | Hỗ trợ offline, đào tạo |
| **Surveillance** | Audit logs có thể theo dõi người dùng | Data minimization, anonymization |
| **Transparency** | CA operation black box | Public audit reports |
| **Accountability** | Ai chịu trách nhiệm khi sự cố? | Clear liability framework |

**Responsible AI/Automation:**
- Không dùng AI để tự động approve certificates
- Human-in-the-loop cho high-risk operations
- Explainable decision making

**Environmental Impact:**
- PQ algorithms: Larger keys, more storage
- Mitigation: Efficient implementation, green hosting

---

### Slide 34: 18. 30 Years of PKI - Lessons Learned
**Bài học Lịch sử:**

| Thập kỷ | Sự kiện chính | Bài học |
|---------|--------------|---------|
| **1990s** | PKI emergence, expensive, complex | Simplicity matters |
| **2000s** | CA breaches, browser wars | Trust is fragile |
| **2010s** | Let's Encrypt, automation | Free + automated = adoption |
| **2020s** | Quantum threat awareness | Prepare early |

**Áp dụng cho Dự án:**
1. **Simplicity**: Web-based, no drivers needed
2. **Trust**: Transparent operations, audit logs
3. **Automation**: Auto-renewal, API-first design
4. **Future-proof**: Hybrid PQ from day 1

**Quote:**
> "PKI is not just about technology. It's about creating a system that people can trust, that laws can recognize, and that businesses can afford."

---

## PART 4: DEPLOYMENT & CONCLUSION (Slides 35-40)

### Slide 35: Hướng dẫn Cài đặt (Setup Guide)
**Yêu cầu Hệ thống:**
- Docker & Docker Compose
- PostgreSQL 14+
- 4GB RAM minimum
- Domain name với SSL

**Các bước Cài đặt:**
```bash
# 1. Clone repository
git clone https://github.com/phmngcthanh/KMA-PQ-Egov.git
cd KMA-PQ-Egov

# 2. Cấu hình environment
cp .env.example .env
# Edit .env với các giá trị phù hợp

# 3. Build và chạy với Docker
docker-compose up -d

# 4. Khởi tạo database
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser

# 5. Khởi tạo Root CA
docker-compose exec backend python manage.py init_pki

# 6. Truy cập
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/api/
# Admin: http://localhost:8000/admin/
```

---

### Slide 36: Configuration Reference
**Backend Settings (`pq_egov_pki/settings.py`):**
```python
# PKI Configuration
PKI_MASTER_KEY = os.environ.get('PKI_MASTER_KEY')  # CRITICAL: Change in production
PKI_DEFAULT_PQ_ALGORITHM = 'DILITHIUM3'
PKI_REQUIRE_HYBRID_SIGNATURES = True

# Certificate Validity (days)
PKI_ROOT_CA_VALIDITY = 7300      # 20 years
PKI_INTERMEDIATE_CA_VALIDITY = 3650  # 10 years  
PKI_USER_CERT_VALIDITY = 365     # 1 year
PKI_OFFICER_CERT_VALIDITY = 730  # 2 years
PKI_CITIZEN_CERT_VALIDITY = 1095 # 3 years

# Security Settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

---

### Slide 37: Ưu điểm của Hệ thống (Pros)
**Kỹ thuật:**
- ✅ Post-Quantum ready với NIST standards (Dilithium, Kyber)
- ✅ Hybrid approach đảm bảo backward compatibility
- ✅ Open-source, auditable code
- ✅ Modern stack (Django, React)
- ✅ Containerized deployment

**Kinh tế:**
- ✅ Không phí license
- ✅ Có thể self-host hoặc cloud
- ✅ Lower long-term cost với proper planning

**Pháp lý:**
- ✅ Hybrid mode tuân thủ luật hiện hành
- ✅ Chuẩn bị cho tương lai PQC

**Xã hội:**
- ✅ Web-based UX thân thiện
- ✅ Mobile responsive
- ✅ Multi-language support potential

---

### Slide 38: Hạn chế của Hệ thống (Cons)
**Kỹ thuật:**
- ⚠️ Chưa tích hợp HSM thực tế
- ⚠️ OCSP chưa triển khai
- ⚠️ Certificate Transparency chưa có
- ⚠️ Cần thêm automated testing

**Kinh tế:**
- ⚠️ Chi phí HSM cao nếu production
- ⚠️ Cần đội ngũ vận hành chuyên môn
- ⚠️ Chưa có support commercial

**Pháp lý:**
- ❌ Chưa được NEAC chứng nhận
- ⚠️ PQC chưa được công nhận chính thức tại VN
- ⚠️ Cần formal CP/CPS documents

**Xã hội:**
- ⚠️ Server-side key: Cần trust hệ thống
- ⚠️ Đào tạo người dùng cuối

---

### Slide 39: Lộ trình Phát triển (Roadmap)
```
2024 Q4: Current State
    ├── Core PKI functionality ✅
    ├── Hybrid crypto ✅
    └── Basic e-government features ✅

2025 Q1-Q2: Enhancement
    ├── HSM integration
    ├── OCSP implementation
    ├── Certificate Transparency
    └── Mobile app

2025 Q3-Q4: Compliance
    ├── NEAC certification process
    ├── Formal CP/CPS documents
    ├── Security audit
    └── Pilot deployment

2026+: Scale
    ├── Integration với DVCQG
    ├── Cross-certification với VNPT-CA
    ├── International recognition
    └── Full PQC transition
```

---

### Slide 40: Kết luận (Conclusion)
**Tổng kết:**

1. **PKI không chỉ là công nghệ** - Đây là hệ thống đa ngành bao gồm pháp lý, kinh tế, xã hội và kỹ thuật

2. **Post-Quantum là bắt buộc** - Với timeline 2030-2035, cần chuẩn bị từ bây giờ

3. **Hybrid approach là thực tế** - Đảm bảo cả tuân thủ pháp lý và bảo mật tương lai

4. **Vietnam context đặc thù** - Cần tích hợp với hệ sinh thái CPĐT hiện có

5. **Continuous improvement** - PKI là hành trình, không phải điểm đến

**Key Takeaways:**
- Hệ thống này là proof-of-concept cho PQ-PKI trong CPĐT VN
- Cần thêm đầu tư để production-ready
- Tiềm năng trở thành mẫu cho các triển khai tương tự

---

### Slide 41: Q&A
**Câu hỏi Thảo luận:**

1. Làm thế nào để thuyết phục leadership đầu tư vào PQ-ready infrastructure?

2. Trade-off giữa usability (web-based keys) và security (hardware tokens)?

3. Timeline thực tế để Vietnam công nhận PQ algorithms?

4. Có nên chờ HSM vendors hỗ trợ PQ hay dùng software-based?

5. Làm thế nào để đo lường ROI của quantum-safe investment?

**Liên hệ:**
- GitHub: https://github.com/phmngcthanh/KMA-PQ-Egov
- Email: [presenter email]

---

### Slide 42: References
**Tài liệu Tham khảo:**

1. NIST FIPS 203 - Module-Lattice-Based Key-Encapsulation Mechanism (ML-KEM)
2. NIST FIPS 204 - Module-Lattice-Based Digital Signature Algorithm (ML-DSA)
3. RFC 5280 - Internet X.509 PKI Certificate and CRL Profile
4. Luật Giao dịch điện tử Việt Nam 2005 (sửa đổi 2023)
5. Nghị định 130/2018/NĐ-CP về chữ ký số
6. Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân
7. Open Quantum Safe Project - https://openquantumsafe.org/
8. DigiNotar Incident Analysis - Various sources
9. ETSI EN 319 412 - Certificate Profiles

---

### Slide 43: Appendix - Technical Deep Dive
**Code Snippet - Hybrid Signing:**
```python
# From backend/pki/crypto/hybrid.py
class HybridSigner:
    def sign(self, data: bytes, private_key_pem: str, 
             pq_private_key: bytes) -> Dict:
        # Classical signature (RSA/ECDSA)
        classical_sig = self.classical_crypto.sign(data, private_key_pem)
        
        # Post-quantum signature (Dilithium)
        pq_sig = self.pq_crypto.sign(data, pq_private_key)
        
        return {
            'classical_signature': classical_sig,
            'pq_signature': pq_sig,
            'algorithm': 'HYBRID_RSA4096_DILITHIUM3'
        }
    
    def verify(self, data: bytes, signatures: Dict, 
               public_key_pem: str, pq_public_key: bytes) -> bool:
        # BOTH must be valid
        classical_valid = self.classical_crypto.verify(
            data, signatures['classical_signature'], public_key_pem)
        pq_valid = self.pq_crypto.verify(
            data, signatures['pq_signature'], pq_public_key)
        
        return classical_valid and pq_valid
```

---

### Slide 44: Appendix - Database Schema
```
┌─────────────────────┐     ┌─────────────────────┐
│ CertificateAuthority│     │   UserCertificate   │
├─────────────────────┤     ├─────────────────────┤
│ id (PK)             │────<│ id (PK)             │
│ name                │     │ user (FK)           │
│ common_name         │     │ issuing_ca (FK)     │
│ private_key_pem     │     │ certificate_pem     │
│ pq_private_key      │     │ public_key_pem      │
│ certificate_pem     │     │ pq_public_key       │
│ pq_public_key       │     │ serial_number       │
│ is_root             │     │ valid_from          │
│ parent_ca (FK)      │     │ valid_until         │
│ key_algorithm       │     │ status              │
│ pq_algorithm        │     │ revoked_at          │
└─────────────────────┘     └─────────────────────┘
           │
           │
           ▼
┌─────────────────────┐     ┌─────────────────────┐
│ CertificateRequest  │     │    PKIAuditLog      │
├─────────────────────┤     ├─────────────────────┤
│ id (PK)             │     │ id (PK)             │
│ user (FK)           │     │ event_type          │
│ certificate_type    │     │ actor (FK)          │
│ status              │     │ certificate (FK)    │
│ csr_pem             │     │ ip_address          │
│ issued_certificate  │     │ timestamp           │
│ reviewed_by (FK)    │     │ previous_hash       │
└─────────────────────┘     └─────────────────────┘
```

---

### Slide 45: Appendix - Deployment Architecture
```
                    ┌─────────────────────────────────────┐
                    │           LOAD BALANCER             │
                    │      (nginx / AWS ALB / HAProxy)    │
                    └────────────────┬────────────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
     ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
     │  Backend Pod 1  │   │  Backend Pod 2  │   │  Backend Pod N  │
     │  (Django + API) │   │  (Django + API) │   │  (Django + API) │
     └────────┬────────┘   └────────┬────────┘   └────────┬────────┘
              │                      │                      │
              └──────────────────────┼──────────────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
     ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
     │   PostgreSQL    │   │     Redis       │   │  HSM (Future)   │
     │   (Primary)     │   │   (Cache/Queue) │   │  (Key Storage)  │
     └────────┬────────┘   └─────────────────┘   └─────────────────┘
              │
              ▼
     ┌─────────────────┐
     │   PostgreSQL    │
     │   (Replica)     │
     └─────────────────┘
```

---

# END OF PRESENTATION OUTLINE

## Notes for Presenter:
1. Total slides: 45 (can be reduced to 35 by combining some slides)
2. Estimated time: 45-60 minutes including Q&A
3. Demo: Prepare live demo or video backup
4. Backup slides: Technical appendix can be used for detailed questions

## Files to Prepare:
1. PowerPoint/Google Slides based on this outline
2. Live demo environment (Docker running)
3. Video backup of demo
4. Handout with key diagrams
5. References list for audience
