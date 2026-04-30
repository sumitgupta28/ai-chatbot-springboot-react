import { useState, useRef } from 'react';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8080';

function StarRating({ rating }) {
    if (!rating) return null;
    const stars = Math.round(Number(rating));
    return (
        <div className="flex items-center gap-0.5 text-yellow-400 text-sm">
            {[1, 2, 3, 4, 5].map(i => (
                <span key={i} className={i <= stars ? 'text-yellow-400' : 'text-gray-200'}>★</span>
            ))}
            <span className="ml-1 text-gray-500 text-xs">{Number(rating).toFixed(1)}</span>
        </div>
    );
}

function ProductCard({ product }) {
    const [imgError, setImgError] = useState(false);

    return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden flex flex-col hover:shadow-md transition-shadow">
            <div className="relative h-48 bg-gray-50 flex items-center justify-center overflow-hidden">
                {!imgError ? (
                    <img
                        src={product.imageUrl}
                        alt={product.name}
                        className="w-full h-full object-cover"
                        onError={() => setImgError(true)}
                    />
                ) : (
                    <div className="flex flex-col items-center justify-center text-gray-300 h-full w-full bg-gray-50">
                        <span className="text-5xl">📦</span>
                        <span className="text-xs mt-1">No image</span>
                    </div>
                )}
                {product.category && (
                    <span className="absolute top-2 right-2 text-xs px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 font-medium">
                        {product.category}
                    </span>
                )}
            </div>
            <div className="p-4 flex flex-col gap-1 flex-1">
                <h3 className="font-semibold text-gray-800 text-sm leading-snug line-clamp-2">{product.name}</h3>
                {product.brand && (
                    <p className="text-xs text-gray-400">{product.brand}</p>
                )}
                <StarRating rating={product.rating} />
                <p className="text-lg font-bold text-indigo-600 mt-1">${Number(product.price).toFixed(2)}</p>
                {product.description && (
                    <p className="text-xs text-gray-500 leading-relaxed line-clamp-3 mt-1">{product.description}</p>
                )}
                {product.stockCount != null && (
                    <p className={`text-xs mt-auto pt-2 font-medium ${product.stockCount > 0 ? 'text-green-600' : 'text-red-500'}`}>
                        {product.stockCount > 0 ? `${product.stockCount} in stock` : 'Out of stock'}
                    </p>
                )}
            </div>
        </div>
    );
}

export default function ProductSearch() {
    const [dragOver, setDragOver] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [uploadResult, setUploadResult] = useState(null);
    const [uploadNotice, setUploadNotice] = useState(null);
    const fileInputRef = useRef();

    const [query, setQuery] = useState('');
    const [searching, setSearching] = useState(false);
    const [results, setResults] = useState(null);
    const [searchNotice, setSearchNotice] = useState(null);

    const handleDrop = (e) => {
        e.preventDefault();
        setDragOver(false);
        const file = e.dataTransfer.files[0];
        if (file) uploadFile(file);
    };

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) uploadFile(file);
        e.target.value = '';
    };

    const uploadFile = async (file) => {
        if (!file.name.match(/\.(xlsx|xls)$/i)) {
            setUploadNotice({ type: 'error', text: 'Only .xlsx or .xls files are supported.' });
            return;
        }
        setUploading(true);
        setUploadResult(null);
        setUploadNotice(null);
        const form = new FormData();
        form.append('file', file);
        try {
            const res = await axios.post(`${API_BASE}/products/upload`, form);
            setUploadResult(res.data);
            setUploadNotice({
                type: 'success',
                text: `Successfully imported ${res.data.imported} product${res.data.imported !== 1 ? 's' : ''}${res.data.skipped > 0 ? `, skipped ${res.data.skipped}` : ''}.`
            });
        } catch (err) {
            const msg = err.response?.data || err.message || 'Upload failed.';
            setUploadNotice({ type: 'error', text: typeof msg === 'string' ? msg : 'Upload failed.' });
        } finally {
            setUploading(false);
        }
    };

    const handleSearch = async () => {
        if (!query.trim()) return;
        setSearching(true);
        setResults(null);
        setSearchNotice(null);
        try {
            const res = await axios.get(`${API_BASE}/products/search`, {
                params: { query: query.trim(), topK: 12, threshold: 0.0 }
            });
            setResults(res.data);
            if (res.data.length === 0) {
                setSearchNotice({ type: 'info', text: 'No matching products found. Try a different description.' });
            }
        } catch (err) {
            setSearchNotice({ type: 'error', text: 'Search failed. Make sure the backend is running.' });
        } finally {
            setSearching(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') handleSearch();
    };

    return (
        <div className="h-full overflow-y-auto bg-gray-100 p-6">
            <div className="max-w-5xl mx-auto space-y-6">

                {/* Upload Section */}
                <div className="bg-white rounded-xl shadow-sm p-6">
                    <h2 className="text-base font-semibold text-gray-700 mb-1">📦 Upload Product Catalog</h2>
                    <p className="text-xs text-gray-400 mb-4">
                        Upload an <strong>.xlsx</strong> file with columns: <code>ProductID, Name, Category, Brand, Description, Price, ImageUrl, Rating, StockCount</code>.
                        Each product is embedded into the vector store for semantic search.
                    </p>

                    <div
                        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                            dragOver
                                ? 'border-indigo-400 bg-indigo-50'
                                : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'
                        } ${uploading ? 'opacity-50 pointer-events-none' : ''}`}
                        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                        onDragLeave={() => setDragOver(false)}
                        onDrop={handleDrop}
                        onClick={() => fileInputRef.current?.click()}
                    >
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept=".xlsx,.xls"
                            className="hidden"
                            onChange={handleFileChange}
                        />
                        {uploading ? (
                            <div className="flex flex-col items-center gap-2 text-indigo-500">
                                <div className="w-6 h-6 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
                                <span className="text-sm">Uploading and indexing products…</span>
                            </div>
                        ) : (
                            <div className="flex flex-col items-center gap-2 text-gray-400">
                                <span className="text-4xl">📊</span>
                                <p className="text-sm font-medium text-gray-600">Drag &amp; drop your .xlsx file here</p>
                                <p className="text-xs">or click to browse</p>
                            </div>
                        )}
                    </div>

                    {uploadNotice && (
                        <div className={`mt-3 text-sm px-4 py-2 rounded-lg ${
                            uploadNotice.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-600 border border-red-200'
                        }`}>
                            {uploadNotice.text}
                        </div>
                    )}

                    {uploadResult && uploadResult.errors?.length > 0 && (
                        <details className="mt-2">
                            <summary className="text-xs text-gray-400 cursor-pointer hover:text-gray-600">
                                {uploadResult.errors.length} row(s) had errors — click to expand
                            </summary>
                            <ul className="mt-1 text-xs text-red-500 space-y-0.5 pl-3">
                                {uploadResult.errors.map((e, i) => <li key={i}>{e}</li>)}
                            </ul>
                        </details>
                    )}
                </div>

                {/* Search Section */}
                <div className="bg-white rounded-xl shadow-sm p-6">
                    <h2 className="text-base font-semibold text-gray-700 mb-1">🔍 Semantic Product Search</h2>
                    <p className="text-xs text-gray-400 mb-4">
                        Describe what you're looking for in natural language — the search uses vector embeddings to find the most relevant products.
                    </p>

                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="e.g. wireless noise-cancelling headphones for travel"
                            className="flex-1 border border-gray-200 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-transparent"
                            disabled={searching}
                        />
                        <button
                            onClick={handleSearch}
                            disabled={searching || !query.trim()}
                            className="px-5 py-2 bg-indigo-500 text-white text-sm font-medium rounded-lg hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                        >
                            {searching ? (
                                <>
                                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                    Searching…
                                </>
                            ) : 'Search'}
                        </button>
                    </div>

                    {searchNotice && (
                        <div className={`mt-3 text-sm px-4 py-2 rounded-lg ${
                            searchNotice.type === 'error'
                                ? 'bg-red-50 text-red-600 border border-red-200'
                                : 'bg-blue-50 text-blue-600 border border-blue-200'
                        }`}>
                            {searchNotice.text}
                        </div>
                    )}

                    {results && results.length > 0 && (
                        <div className="mt-5">
                            <p className="text-xs text-gray-400 mb-3">{results.length} result{results.length !== 1 ? 's' : ''} found</p>
                            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                                {results.map((p) => (
                                    <ProductCard key={p.productId} product={p} />
                                ))}
                            </div>
                        </div>
                    )}
                </div>

            </div>
        </div>
    );
}
