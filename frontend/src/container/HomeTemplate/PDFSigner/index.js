import React, { useState, useRef } from 'react';
import { 
    Container, Row, Col, Card, Button, Alert, 
    Spinner, Form, Badge, ListGroup 
} from 'react-bootstrap';
import { PKI_ENDPOINTS, pkiRequest, getAuthHeader } from '../../../config/pkiApi';
import './index.css';

const PDFSigner = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    
    // File states
    const [selectedFile, setSelectedFile] = useState(null);
    const [signedFile, setSignedFile] = useState(null);
    
    // Verification results
    const [verificationResult, setVerificationResult] = useState(null);
    
    // Signing options
    const [signOptions, setSignOptions] = useState({
        reason: 'Ký số điện tử',
        location: '',
    });
    
    // Certificates for signing
    const [certificates, setCertificates] = useState([]);
    const [selectedCertId, setSelectedCertId] = useState('');
    
    const fileInputRef = useRef(null);
    const verifyInputRef = useRef(null);

    // Load user's certificates
    React.useEffect(() => {
        loadCertificates();
    }, []);

    const loadCertificates = async () => {
        try {
            const data = await pkiRequest(PKI_ENDPOINTS.MY_CERTIFICATES);
            const validCerts = (data.certificates || []).filter(c => c.is_valid);
            setCertificates(validCerts);
            if (validCerts.length > 0) {
                setSelectedCertId(validCerts[0].id.toString());
            }
        } catch (err) {
            console.error('Failed to load certificates:', err);
        }
    };

    const handleFileSelect = (e) => {
        const file = e.target.files[0];
        if (file && file.type === 'application/pdf') {
            setSelectedFile(file);
            setSignedFile(null);
            setError(null);
        } else {
            setError('Vui lòng chọn file PDF');
        }
    };

    const handleSign = async () => {
        if (!selectedFile || !selectedCertId) {
            setError('Vui lòng chọn file PDF và chứng chỉ');
            return;
        }

        setLoading(true);
        setError(null);
        setSuccess(null);

        try {
            const formData = new FormData();
            formData.append('file', selectedFile);
            formData.append('certificate_id', selectedCertId);
            formData.append('reason', signOptions.reason);
            formData.append('location', signOptions.location);

            const response = await fetch(PKI_ENDPOINTS.PDF_SIGN, {
                method: 'POST',
                headers: getAuthHeader(),
                body: formData,
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || 'Ký PDF thất bại');
            }

            const blob = await response.blob();
            setSignedFile(blob);
            setSuccess('Ký PDF thành công!');
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleDownloadSigned = () => {
        if (signedFile) {
            const url = window.URL.createObjectURL(signedFile);
            const a = document.createElement('a');
            a.href = url;
            a.download = `signed_${selectedFile.name}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        }
    };

    const handleVerify = async (e) => {
        const file = e.target.files[0];
        if (!file || file.type !== 'application/pdf') {
            setError('Vui lòng chọn file PDF');
            return;
        }

        setLoading(true);
        setError(null);
        setVerificationResult(null);

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('verify_pq_signature', 'true');

            const response = await fetch(PKI_ENDPOINTS.PDF_VERIFY, {
                method: 'POST',
                headers: getAuthHeader(),
                body: formData,
            });

            const result = await response.json();
            setVerificationResult(result);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (dateString) => {
        if (!dateString) return '-';
        return new Date(dateString).toLocaleDateString('vi-VN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    return (
        <Container className="pdf-signer py-4">
            <Row className="mb-4">
                <Col>
                    <h2>
                        <i className="fas fa-file-signature me-2"></i>
                        Ký số & Xác thực PDF
                    </h2>
                    <p className="text-muted">
                        Ký và xác thực tài liệu PDF với chữ ký số hậu lượng tử
                    </p>
                </Col>
            </Row>

            {error && <Alert variant="danger" onClose={() => setError(null)} dismissible>{error}</Alert>}
            {success && <Alert variant="success" onClose={() => setSuccess(null)} dismissible>{success}</Alert>}

            <Row>
                {/* Sign PDF Section */}
                <Col lg={6} className="mb-4">
                    <Card className="h-100">
                        <Card.Header className="bg-primary text-white">
                            <i className="fas fa-pen-nib me-2"></i>
                            Ký số PDF
                        </Card.Header>
                        <Card.Body>
                            {certificates.length === 0 ? (
                                <Alert variant="warning">
                                    Bạn chưa có chứng chỉ hợp lệ để ký. 
                                    <a href="/certificates"> Yêu cầu chứng chỉ mới</a>
                                </Alert>
                            ) : (
                                <>
                                    <Form.Group className="mb-3">
                                        <Form.Label>Chọn chứng chỉ ký</Form.Label>
                                        <Form.Select 
                                            value={selectedCertId}
                                            onChange={(e) => setSelectedCertId(e.target.value)}
                                        >
                                            {certificates.map((cert) => (
                                                <option key={cert.id} value={cert.id}>
                                                    {cert.certificate_type} - {cert.key_algorithm} + {cert.pq_algorithm}
                                                </option>
                                            ))}
                                        </Form.Select>
                                    </Form.Group>

                                    <Form.Group className="mb-3">
                                        <Form.Label>File PDF</Form.Label>
                                        <Form.Control 
                                            type="file"
                                            accept=".pdf"
                                            ref={fileInputRef}
                                            onChange={handleFileSelect}
                                        />
                                        {selectedFile && (
                                            <Form.Text className="text-success">
                                                <i className="fas fa-check me-1"></i>
                                                {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                                            </Form.Text>
                                        )}
                                    </Form.Group>

                                    <Form.Group className="mb-3">
                                        <Form.Label>Lý do ký</Form.Label>
                                        <Form.Control 
                                            type="text"
                                            value={signOptions.reason}
                                            onChange={(e) => setSignOptions({...signOptions, reason: e.target.value})}
                                            placeholder="Phê duyệt hồ sơ"
                                        />
                                    </Form.Group>

                                    <Form.Group className="mb-3">
                                        <Form.Label>Địa điểm</Form.Label>
                                        <Form.Control 
                                            type="text"
                                            value={signOptions.location}
                                            onChange={(e) => setSignOptions({...signOptions, location: e.target.value})}
                                            placeholder="TP. Hồ Chí Minh"
                                        />
                                    </Form.Group>

                                    <div className="d-grid gap-2">
                                        <Button 
                                            variant="primary" 
                                            onClick={handleSign}
                                            disabled={!selectedFile || loading}
                                        >
                                            {loading ? (
                                                <>
                                                    <Spinner size="sm" className="me-2" />
                                                    Đang ký...
                                                </>
                                            ) : (
                                                <>
                                                    <i className="fas fa-signature me-2"></i>
                                                    Ký PDF
                                                </>
                                            )}
                                        </Button>

                                        {signedFile && (
                                            <Button variant="success" onClick={handleDownloadSigned}>
                                                <i className="fas fa-download me-2"></i>
                                                Tải file đã ký
                                            </Button>
                                        )}
                                    </div>
                                </>
                            )}
                        </Card.Body>
                    </Card>
                </Col>

                {/* Verify PDF Section */}
                <Col lg={6} className="mb-4">
                    <Card className="h-100">
                        <Card.Header className="bg-success text-white">
                            <i className="fas fa-check-circle me-2"></i>
                            Xác thực chữ ký
                        </Card.Header>
                        <Card.Body>
                            <Form.Group className="mb-3">
                                <Form.Label>Chọn PDF cần xác thực</Form.Label>
                                <Form.Control 
                                    type="file"
                                    accept=".pdf"
                                    ref={verifyInputRef}
                                    onChange={handleVerify}
                                />
                            </Form.Group>

                            {loading && (
                                <div className="text-center py-3">
                                    <Spinner animation="border" variant="primary" />
                                    <p className="mt-2">Đang xác thực...</p>
                                </div>
                            )}

                            {verificationResult && (
                                <div className="verification-result">
                                    <Alert variant={verificationResult.is_valid ? 'success' : 'danger'}>
                                        <h5>
                                            {verificationResult.is_valid ? (
                                                <>
                                                    <i className="fas fa-check-circle me-2"></i>
                                                    Chữ ký hợp lệ
                                                </>
                                            ) : (
                                                <>
                                                    <i className="fas fa-times-circle me-2"></i>
                                                    Chữ ký không hợp lệ
                                                </>
                                            )}
                                        </h5>
                                    </Alert>

                                    <ListGroup>
                                        <ListGroup.Item>
                                            <strong>Người ký:</strong> {verificationResult.signer_name}
                                        </ListGroup.Item>
                                        <ListGroup.Item>
                                            <strong>Email:</strong> {verificationResult.signer_email}
                                        </ListGroup.Item>
                                        <ListGroup.Item>
                                            <strong>Thời gian ký:</strong> {formatDate(verificationResult.signing_time)}
                                        </ListGroup.Item>
                                        <ListGroup.Item>
                                            <strong>Chữ ký cổ điển:</strong>{' '}
                                            <Badge bg={verificationResult.classical_signature_valid ? 'success' : 'danger'}>
                                                {verificationResult.classical_signature_valid ? 'Hợp lệ' : 'Không hợp lệ'}
                                            </Badge>
                                            {' '}({verificationResult.classical_algorithm})
                                        </ListGroup.Item>
                                        {verificationResult.pq_signature_present && (
                                            <ListGroup.Item>
                                                <strong>Chữ ký hậu lượng tử:</strong>{' '}
                                                <Badge bg={verificationResult.pq_signature_valid ? 'success' : 'danger'}>
                                                    {verificationResult.pq_signature_valid ? 'Hợp lệ' : 'Không hợp lệ'}
                                                </Badge>
                                                {' '}({verificationResult.pq_algorithm})
                                            </ListGroup.Item>
                                        )}
                                        <ListGroup.Item>
                                            <strong>Chuỗi chứng chỉ:</strong>{' '}
                                            <Badge bg={verificationResult.chain_valid ? 'success' : 'warning'}>
                                                {verificationResult.chain_valid ? 'Hợp lệ' : 'Cảnh báo'}
                                            </Badge>
                                        </ListGroup.Item>
                                    </ListGroup>
                                </div>
                            )}
                        </Card.Body>
                    </Card>
                </Col>
            </Row>

            {/* Info Section */}
            <Row>
                <Col>
                    <Card className="bg-light">
                        <Card.Body>
                            <h5>
                                <i className="fas fa-info-circle text-primary me-2"></i>
                                Về chữ ký số hậu lượng tử
                            </h5>
                            <p>
                                Hệ thống sử dụng chữ ký lai (Hybrid Signature) kết hợp:
                            </p>
                            <ul>
                                <li>
                                    <strong>Chữ ký cổ điển (RSA/ECDSA):</strong> Tương thích với các hệ thống hiện tại
                                </li>
                                <li>
                                    <strong>Chữ ký hậu lượng tử (Dilithium):</strong> Bảo vệ khỏi tấn công từ máy tính lượng tử trong tương lai
                                </li>
                            </ul>
                            <p className="mb-0 text-muted">
                                <i className="fas fa-shield-alt me-1"></i>
                                Thuật toán Dilithium đã được NIST chuẩn hóa (FIPS 204) cho chữ ký số kháng lượng tử.
                            </p>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>
        </Container>
    );
};

export default PDFSigner;
