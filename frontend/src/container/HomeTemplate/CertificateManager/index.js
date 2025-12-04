import React, { useState, useEffect } from 'react';
import { 
    Container, Row, Col, Card, Button, Table, Badge, 
    Alert, Spinner, Modal, Form, Tab, Tabs 
} from 'react-bootstrap';
import { PKI_ENDPOINTS, pkiRequest, downloadFile } from '../../../config/pkiApi';
import './index.css';

const CertificateManager = () => {
    const [loading, setLoading] = useState(true);
    const [certificates, setCertificates] = useState([]);
    const [requests, setRequests] = useState([]);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [activeTab, setActiveTab] = useState('certificates');
    
    // Modal states
    const [showRequestModal, setShowRequestModal] = useState(false);
    const [showDetailModal, setShowDetailModal] = useState(false);
    const [selectedCert, setSelectedCert] = useState(null);
    
    // Request form state
    const [requestForm, setRequestForm] = useState({
        certificate_type: 'CITIZEN',
        common_name: '',
        organization: '',
        organizational_unit: '',
        country: 'VN',
        state: '',
        locality: '',
        key_algorithm: 'RSA-4096',
        pq_algorithm: 'DILITHIUM3',
    });

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setLoading(true);
        setError(null);
        try {
            const [certData, requestData] = await Promise.all([
                pkiRequest(PKI_ENDPOINTS.MY_CERTIFICATES),
                pkiRequest(PKI_ENDPOINTS.REQUEST_LIST),
            ]);
            setCertificates(certData.certificates || []);
            setRequests(requestData.results || requestData || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleRequestSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        try {
            await pkiRequest(PKI_ENDPOINTS.REQUEST_CREATE, {
                method: 'POST',
                body: JSON.stringify(requestForm),
            });
            setSuccess('Yêu cầu chứng chỉ đã được gửi thành công!');
            setShowRequestModal(false);
            loadData();
        } catch (err) {
            setError(err.message);
        }
    };

    const handleDownload = async (certId, format = 'pem') => {
        try {
            const blob = await pkiRequest(`${PKI_ENDPOINTS.CERT_DOWNLOAD(certId)}?format=${format}`);
            downloadFile(blob, `certificate_${certId}.${format}`);
        } catch (err) {
            setError(err.message);
        }
    };

    const handleViewDetails = (cert) => {
        setSelectedCert(cert);
        setShowDetailModal(true);
    };

    const getCertStatusBadge = (cert) => {
        if (cert.is_revoked) {
            return <Badge bg="danger">Đã thu hồi</Badge>;
        }
        if (cert.is_valid) {
            return <Badge bg="success">Hợp lệ</Badge>;
        }
        return <Badge bg="warning">Hết hạn</Badge>;
    };

    const getRequestStatusBadge = (status) => {
        switch (status) {
            case 'PENDING':
                return <Badge bg="warning">Đang chờ</Badge>;
            case 'APPROVED':
                return <Badge bg="info">Đã duyệt</Badge>;
            case 'ISSUED':
                return <Badge bg="success">Đã cấp</Badge>;
            case 'REJECTED':
                return <Badge bg="danger">Từ chối</Badge>;
            default:
                return <Badge bg="secondary">{status}</Badge>;
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

    if (loading) {
        return (
            <Container className="text-center py-5">
                <Spinner animation="border" variant="primary" />
                <p className="mt-3">Đang tải dữ liệu...</p>
            </Container>
        );
    }

    return (
        <Container className="certificate-manager py-4">
            <Row className="mb-4">
                <Col>
                    <h2>
                        <i className="fas fa-certificate me-2"></i>
                        Quản lý Chứng chỉ số
                    </h2>
                    <p className="text-muted">
                        Quản lý chứng chỉ PKI với hỗ trợ mã hóa hậu lượng tử
                    </p>
                </Col>
                <Col xs="auto">
                    <Button variant="primary" onClick={() => setShowRequestModal(true)}>
                        <i className="fas fa-plus me-2"></i>
                        Yêu cầu chứng chỉ mới
                    </Button>
                </Col>
            </Row>

            {error && <Alert variant="danger" onClose={() => setError(null)} dismissible>{error}</Alert>}
            {success && <Alert variant="success" onClose={() => setSuccess(null)} dismissible>{success}</Alert>}

            <Tabs activeKey={activeTab} onSelect={setActiveTab} className="mb-4">
                <Tab eventKey="certificates" title={`Chứng chỉ của tôi (${certificates.length})`}>
                    <Card>
                        <Card.Body>
                            {certificates.length === 0 ? (
                                <Alert variant="info">
                                    Bạn chưa có chứng chỉ nào. Hãy yêu cầu chứng chỉ mới!
                                </Alert>
                            ) : (
                                <Table responsive hover>
                                    <thead>
                                        <tr>
                                            <th>Số serial</th>
                                            <th>Loại</th>
                                            <th>Thuật toán</th>
                                            <th>Hiệu lực đến</th>
                                            <th>Trạng thái</th>
                                            <th>Thao tác</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {certificates.map((cert) => (
                                            <tr key={cert.id}>
                                                <td>
                                                    <code>{cert.serial_number?.substring(0, 16)}...</code>
                                                </td>
                                                <td>
                                                    <Badge bg={cert.certificate_type === 'OFFICER' ? 'primary' : 'secondary'}>
                                                        {cert.certificate_type === 'OFFICER' ? 'Cán bộ' : 'Công dân'}
                                                    </Badge>
                                                </td>
                                                <td>
                                                    <small>
                                                        {cert.key_algorithm}<br/>
                                                        <span className="text-primary">{cert.pq_algorithm}</span>
                                                    </small>
                                                </td>
                                                <td>{formatDate(cert.valid_until)}</td>
                                                <td>{getCertStatusBadge(cert)}</td>
                                                <td>
                                                    <Button 
                                                        size="sm" 
                                                        variant="outline-info" 
                                                        className="me-1"
                                                        onClick={() => handleViewDetails(cert)}
                                                    >
                                                        <i className="fas fa-eye"></i>
                                                    </Button>
                                                    <Button 
                                                        size="sm" 
                                                        variant="outline-primary" 
                                                        className="me-1"
                                                        onClick={() => handleDownload(cert.id, 'pem')}
                                                    >
                                                        <i className="fas fa-download"></i>
                                                    </Button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </Table>
                            )}
                        </Card.Body>
                    </Card>
                </Tab>

                <Tab eventKey="requests" title={`Yêu cầu chứng chỉ (${requests.length})`}>
                    <Card>
                        <Card.Body>
                            {requests.length === 0 ? (
                                <Alert variant="info">
                                    Không có yêu cầu chứng chỉ nào.
                                </Alert>
                            ) : (
                                <Table responsive hover>
                                    <thead>
                                        <tr>
                                            <th>ID</th>
                                            <th>Loại</th>
                                            <th>Tên</th>
                                            <th>Ngày tạo</th>
                                            <th>Trạng thái</th>
                                            <th>Ghi chú</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {requests.map((req) => (
                                            <tr key={req.id}>
                                                <td>#{req.id}</td>
                                                <td>
                                                    <Badge bg={req.certificate_type === 'OFFICER' ? 'primary' : 'secondary'}>
                                                        {req.certificate_type === 'OFFICER' ? 'Cán bộ' : 'Công dân'}
                                                    </Badge>
                                                </td>
                                                <td>{req.common_name}</td>
                                                <td>{formatDate(req.created_at)}</td>
                                                <td>{getRequestStatusBadge(req.status)}</td>
                                                <td>
                                                    {req.rejection_reason && (
                                                        <small className="text-danger">{req.rejection_reason}</small>
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </Table>
                            )}
                        </Card.Body>
                    </Card>
                </Tab>
            </Tabs>

            {/* Request Certificate Modal */}
            <Modal show={showRequestModal} onHide={() => setShowRequestModal(false)} size="lg">
                <Modal.Header closeButton>
                    <Modal.Title>Yêu cầu chứng chỉ mới</Modal.Title>
                </Modal.Header>
                <Form onSubmit={handleRequestSubmit}>
                    <Modal.Body>
                        <Row>
                            <Col md={6}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Loại chứng chỉ</Form.Label>
                                    <Form.Select 
                                        value={requestForm.certificate_type}
                                        onChange={(e) => setRequestForm({...requestForm, certificate_type: e.target.value})}
                                    >
                                        <option value="CITIZEN">Công dân</option>
                                        <option value="OFFICER">Cán bộ nhà nước</option>
                                    </Form.Select>
                                </Form.Group>
                            </Col>
                            <Col md={6}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Tên đầy đủ (Common Name)</Form.Label>
                                    <Form.Control 
                                        type="text"
                                        value={requestForm.common_name}
                                        onChange={(e) => setRequestForm({...requestForm, common_name: e.target.value})}
                                        placeholder="Nguyễn Văn A"
                                    />
                                </Form.Group>
                            </Col>
                        </Row>
                        <Row>
                            <Col md={6}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Tổ chức</Form.Label>
                                    <Form.Control 
                                        type="text"
                                        value={requestForm.organization}
                                        onChange={(e) => setRequestForm({...requestForm, organization: e.target.value})}
                                        placeholder="Tên cơ quan/tổ chức"
                                    />
                                </Form.Group>
                            </Col>
                            <Col md={6}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Đơn vị</Form.Label>
                                    <Form.Control 
                                        type="text"
                                        value={requestForm.organizational_unit}
                                        onChange={(e) => setRequestForm({...requestForm, organizational_unit: e.target.value})}
                                        placeholder="Phòng/Ban"
                                    />
                                </Form.Group>
                            </Col>
                        </Row>
                        <Row>
                            <Col md={4}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Quốc gia</Form.Label>
                                    <Form.Control 
                                        type="text"
                                        value={requestForm.country}
                                        onChange={(e) => setRequestForm({...requestForm, country: e.target.value})}
                                        maxLength={2}
                                    />
                                </Form.Group>
                            </Col>
                            <Col md={4}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Tỉnh/Thành phố</Form.Label>
                                    <Form.Control 
                                        type="text"
                                        value={requestForm.state}
                                        onChange={(e) => setRequestForm({...requestForm, state: e.target.value})}
                                        placeholder="TP. Hồ Chí Minh"
                                    />
                                </Form.Group>
                            </Col>
                            <Col md={4}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Quận/Huyện</Form.Label>
                                    <Form.Control 
                                        type="text"
                                        value={requestForm.locality}
                                        onChange={(e) => setRequestForm({...requestForm, locality: e.target.value})}
                                        placeholder="Quận 1"
                                    />
                                </Form.Group>
                            </Col>
                        </Row>
                        <hr />
                        <h6 className="text-primary">Cấu hình mật mã</h6>
                        <Row>
                            <Col md={6}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Thuật toán khóa cổ điển</Form.Label>
                                    <Form.Select 
                                        value={requestForm.key_algorithm}
                                        onChange={(e) => setRequestForm({...requestForm, key_algorithm: e.target.value})}
                                    >
                                        <option value="RSA-2048">RSA-2048</option>
                                        <option value="RSA-4096">RSA-4096 (Khuyến nghị)</option>
                                        <option value="ECDSA-P256">ECDSA P-256</option>
                                    </Form.Select>
                                </Form.Group>
                            </Col>
                            <Col md={6}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Thuật toán hậu lượng tử</Form.Label>
                                    <Form.Select 
                                        value={requestForm.pq_algorithm}
                                        onChange={(e) => setRequestForm({...requestForm, pq_algorithm: e.target.value})}
                                    >
                                        <option value="DILITHIUM2">Dilithium2</option>
                                        <option value="DILITHIUM3">Dilithium3 (Khuyến nghị)</option>
                                        <option value="DILITHIUM5">Dilithium5</option>
                                    </Form.Select>
                                    <Form.Text className="text-muted">
                                        Thuật toán chữ ký số kháng lượng tử (NIST chuẩn hóa)
                                    </Form.Text>
                                </Form.Group>
                            </Col>
                        </Row>
                    </Modal.Body>
                    <Modal.Footer>
                        <Button variant="secondary" onClick={() => setShowRequestModal(false)}>
                            Hủy
                        </Button>
                        <Button variant="primary" type="submit">
                            <i className="fas fa-paper-plane me-2"></i>
                            Gửi yêu cầu
                        </Button>
                    </Modal.Footer>
                </Form>
            </Modal>

            {/* Certificate Detail Modal */}
            <Modal show={showDetailModal} onHide={() => setShowDetailModal(false)} size="lg">
                <Modal.Header closeButton>
                    <Modal.Title>Chi tiết chứng chỉ</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    {selectedCert && (
                        <>
                            <Row>
                                <Col md={6}>
                                    <p><strong>Số serial:</strong></p>
                                    <code className="d-block mb-3">{selectedCert.serial_number}</code>
                                </Col>
                                <Col md={6}>
                                    <p><strong>Fingerprint:</strong></p>
                                    <code className="d-block mb-3">{selectedCert.fingerprint}</code>
                                </Col>
                            </Row>
                            <Row>
                                <Col md={6}>
                                    <p><strong>Loại:</strong> {selectedCert.certificate_type}</p>
                                    <p><strong>Thuật toán cổ điển:</strong> {selectedCert.key_algorithm}</p>
                                    <p><strong>Thuật toán PQ:</strong> <span className="text-primary">{selectedCert.pq_algorithm}</span></p>
                                </Col>
                                <Col md={6}>
                                    <p><strong>CA cấp:</strong> {selectedCert.ca_name}</p>
                                    <p><strong>Có hiệu lực từ:</strong> {formatDate(selectedCert.valid_from)}</p>
                                    <p><strong>Hết hạn:</strong> {formatDate(selectedCert.valid_until)}</p>
                                </Col>
                            </Row>
                            <hr />
                            <p><strong>Chứng chỉ (PEM):</strong></p>
                            <pre className="bg-light p-3" style={{maxHeight: '200px', overflow: 'auto'}}>
                                {selectedCert.certificate_pem}
                            </pre>
                        </>
                    )}
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="outline-primary" onClick={() => handleDownload(selectedCert?.id, 'pem')}>
                        <i className="fas fa-download me-2"></i>Tải PEM
                    </Button>
                    <Button variant="outline-primary" onClick={() => handleDownload(selectedCert?.id, 'der')}>
                        <i className="fas fa-download me-2"></i>Tải DER
                    </Button>
                    <Button variant="secondary" onClick={() => setShowDetailModal(false)}>
                        Đóng
                    </Button>
                </Modal.Footer>
            </Modal>
        </Container>
    );
};

export default CertificateManager;
