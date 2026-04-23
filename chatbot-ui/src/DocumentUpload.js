import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './DocumentUpload.css';

const API_BASE = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8080';
const ACCEPTED_TYPES = [
    'application/pdf',
    'text/plain',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
];

const DocumentUpload = () => {
    const [documents, setDocuments] = useState([]);
    const [uploading, setUploading] = useState(false);
    const [notice, setNotice] = useState(null);
    const [dragOver, setDragOver] = useState(false);
    const fileInputRef = useRef(null);

    useEffect(() => { fetchDocuments(); }, []);

    const fetchDocuments = async () => {
        try {
            const res = await axios.get(`${API_BASE}/documents`);
            setDocuments(res.data);
        } catch {
            setNotice({ type: 'error', text: 'Could not load document list.' });
        }
    };

    const upload = async (file) => {
        if (!file) return;
        if (!ACCEPTED_TYPES.includes(file.type)) {
            setNotice({ type: 'error', text: 'Unsupported file type. Please upload PDF, TXT, or DOCX.' });
            return;
        }
        setUploading(true);
        setNotice(null);
        const form = new FormData();
        form.append('file', file);
        try {
            await axios.post(`${API_BASE}/documents/upload`, form);
            setNotice({ type: 'success', text: `"${file.name}" uploaded and indexed.` });
            fetchDocuments();
        } catch {
            setNotice({ type: 'error', text: `Upload failed for "${file.name}". Check the server logs.` });
        } finally {
            setUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const handleDelete = async (id, filename) => {
        if (!window.confirm(`Delete "${filename}" and all its indexed content?`)) return;
        try {
            await axios.delete(`${API_BASE}/documents/${id}`);
            fetchDocuments();
        } catch {
            setNotice({ type: 'error', text: `Delete failed for "${filename}".` });
        }
    };

    const fmtSize = (bytes) => {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / 1048576).toFixed(1)} MB`;
    };

    const fmtDate = (dt) => new Date(dt).toLocaleString();

    return (
        <div className="doc-page">
            <div className="doc-upload-box">
                <h2>Upload Document</h2>
                <div
                    className={`drop-zone${dragOver ? ' drag-over' : ''}${uploading ? ' uploading' : ''}`}
                    onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                    onDragLeave={() => setDragOver(false)}
                    onDrop={(e) => { e.preventDefault(); setDragOver(false); upload(e.dataTransfer.files[0]); }}
                    onClick={() => !uploading && fileInputRef.current.click()}
                >
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept=".pdf,.txt,.docx,.doc"
                        style={{ display: 'none' }}
                        onChange={(e) => upload(e.target.files[0])}
                    />
                    {uploading ? (
                        <div className="spinner-wrap">
                            <div className="spinner" />
                            <span>Uploading and indexing…</span>
                        </div>
                    ) : (
                        <>
                            <div className="drop-icon">📄</div>
                            <p>Drag &amp; drop or <span className="link-text">click to browse</span></p>
                            <p className="hint">PDF · TXT · DOCX — max 50 MB</p>
                        </>
                    )}
                </div>
                {notice && <div className={`notice ${notice.type}`}>{notice.text}</div>}
            </div>

            <div className="doc-list-box">
                <h2>Indexed Documents</h2>
                {documents.length === 0 ? (
                    <p className="empty-state">
                        No documents indexed yet. Upload one above to enable RAG.
                    </p>
                ) : (
                    <table className="doc-table">
                        <thead>
                            <tr>
                                <th>Filename</th>
                                <th>Type</th>
                                <th>Size</th>
                                <th>Chunks</th>
                                <th>Uploaded</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {documents.map((doc) => (
                                <tr key={doc.id}>
                                    <td className="filename">{doc.filename}</td>
                                    <td className="type-col">{doc.contentType}</td>
                                    <td>{fmtSize(doc.fileSize)}</td>
                                    <td className="center">{doc.chunkCount}</td>
                                    <td>{fmtDate(doc.uploadTime)}</td>
                                    <td>
                                        <button
                                            className="del-btn"
                                            onClick={() => handleDelete(doc.id, doc.filename)}
                                        >
                                            Delete
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
};

export default DocumentUpload;
