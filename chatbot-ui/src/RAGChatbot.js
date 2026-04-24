import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { IoMdSend } from 'react-icons/io';

const API_BASE = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8080';

const GradientSlider = ({ label, value, min, max, step, onChange, formatValue }) => {
    const pct = ((value - min) / (max - min)) * 100;

    const trackStyle = {
        background: `linear-gradient(to right,
            #e53e3e 0%,
            #dd6b20 20%,
            #d69e2e 40%,
            #a0c334 60%,
            #48bb78 80%,
            #2f855a 100%)`
    };

    const thumbColor =
        pct < 20 ? '#e53e3e' :
        pct < 40 ? '#dd6b20' :
        pct < 60 ? '#d69e2e' :
        pct < 80 ? '#a0c334' : '#48bb78';

    return (
        <div className="mb-6">
            <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-semibold text-gray-700">{label}</span>
                <span
                    className="text-sm font-bold px-2 py-0.5 rounded-full text-white min-w-[2.5rem] text-center"
                    style={{ backgroundColor: thumbColor }}
                >
                    {formatValue ? formatValue(value) : value}
                </span>
            </div>

            <div className="relative h-3 rounded-full mt-3" style={trackStyle}>
                <input
                    type="range"
                    min={min}
                    max={max}
                    step={step}
                    value={value}
                    onChange={(e) => onChange(Number(e.target.value))}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    style={{ margin: 0 }}
                />
                <div
                    className="absolute top-1/2 -translate-y-1/2 w-5 h-5 rounded-full border-2 border-white shadow-md pointer-events-none transition-all"
                    style={{ left: `calc(${pct}% - 10px)`, backgroundColor: thumbColor }}
                />
                <div
                    className="absolute pointer-events-none"
                    style={{ left: `calc(${pct}% - 6px)`, top: '-16px' }}
                >
                    <div style={{
                        width: 0, height: 0,
                        borderLeft: '6px solid transparent',
                        borderRight: '6px solid transparent',
                        borderTop: `8px solid ${thumbColor}`
                    }} />
                </div>
            </div>

            <div className="flex justify-between mt-2">
                <span className="text-xs text-gray-400">{min}</span>
                <span className="text-xs text-gray-400">{max}</span>
            </div>
        </div>
    );
};

const ModeToggle = ({ value, onChange }) => (
    <div className="mb-6">
        <span className="text-sm font-semibold text-gray-700 block mb-2">RAG Mode</span>
        <div className="flex rounded-lg border border-gray-200 overflow-hidden">
            {['soft', 'strict'].map((m) => (
                <button
                    key={m}
                    onClick={() => onChange(m)}
                    className={`flex-1 py-1.5 text-sm font-medium transition-colors capitalize ${
                        value === m
                            ? 'bg-indigo-500 text-white'
                            : 'bg-white text-gray-500 hover:bg-gray-50'
                    }`}
                >
                    {m}
                </button>
            ))}
        </div>
        <p className="text-xs text-gray-400 mt-1.5">
            {value === 'soft'
                ? 'Uses docs + falls back to general knowledge'
                : 'Answers strictly from indexed documents only'}
        </p>
    </div>
);

const RAGChatbot = () => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [mode, setMode] = useState('soft');
    const [similarityThreshold, setSimilarityThreshold] = useState(0.0);
    const [topK, setTopK] = useState(5);
    const [temperature, setTemperature] = useState(0.7);
    const [maxTokens, setMaxTokens] = useState(1000);
    const chatboxRef = useRef(null);

    useEffect(() => {
        if (chatboxRef.current) {
            chatboxRef.current.scrollTop = chatboxRef.current.scrollHeight;
        }
    }, [messages]);

    const sendMessage = async () => {
        if (!input.trim()) return;

        const text = input;
        setMessages(prev => [...prev, { id: crypto.randomUUID(), text, sender: 'user' }]);
        setInput('');
        setLoading(true);

        try {
            const response = await axios.get(
                `${API_BASE}/rag/ai/chat/string/client` +
                `?message=${encodeURIComponent(text)}` +
                `&topK=${topK}` +
                `&similarityThreshold=${similarityThreshold}` +
                `&mode=${mode}` +
                `&temperature=${temperature}` +
                `&maxTokens=${maxTokens}`
            );
            setMessages(prev => [...prev, { id: crypto.randomUUID(), text: response.data, sender: 'ai' }]);
        } catch (error) {
            console.error('Error fetching AI response:', error);
            setMessages(prev => [...prev, { id: crypto.randomUUID(), text: 'Sorry, something went wrong. Please try again.', sender: 'ai' }]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') sendMessage();
    };

    return (
        <div className="flex h-full bg-gray-100 overflow-hidden">

            {/* Left — RAG Settings panel */}
            <div className="w-72 min-w-[18rem] bg-white border-r border-gray-200 p-6 flex flex-col shadow-sm overflow-y-auto">
                <h2 className="text-base font-bold text-indigo-600 mb-1 tracking-wide uppercase">RAG Settings</h2>
                <p className="text-xs text-gray-400 mb-5">Tune retrieval & generation per query</p>

                <ModeToggle value={mode} onChange={setMode} />

                <div className="border-t border-gray-100 pt-5">
                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-4">Retrieval</p>

                    <GradientSlider
                        label="Similarity Threshold"
                        value={similarityThreshold}
                        min={0.0}
                        max={1.0}
                        step={0.05}
                        onChange={setSimilarityThreshold}
                        formatValue={(v) => v.toFixed(2)}
                    />

                    <GradientSlider
                        label="Top K"
                        value={topK}
                        min={1}
                        max={20}
                        step={1}
                        onChange={setTopK}
                    />
                </div>

                <div className="border-t border-gray-100 pt-5">
                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-4">Generation</p>

                    <GradientSlider
                        label="Temperature"
                        value={temperature}
                        min={0.0}
                        max={1.0}
                        step={0.1}
                        onChange={setTemperature}
                        formatValue={(v) => v.toFixed(1)}
                    />

                    <GradientSlider
                        label="Max Tokens"
                        value={maxTokens}
                        min={100}
                        max={2000}
                        step={100}
                        onChange={setMaxTokens}
                    />
                </div>

                <div className="mt-auto pt-5 border-t border-gray-100">
                    <p className="text-xs text-gray-400 leading-relaxed space-y-1">
                        <span className="block"><strong className="text-gray-500">Threshold:</strong> min similarity for a chunk to be included</span>
                        <span className="block"><strong className="text-gray-500">Top K:</strong> max chunks retrieved per query</span>
                        <span className="block"><strong className="text-gray-500">Temperature:</strong> low = factual, high = creative</span>
                        <span className="block"><strong className="text-gray-500">Max Tokens:</strong> caps the response length</span>
                    </p>
                </div>
            </div>

            {/* Right — Chat area */}
            <div className="flex flex-col flex-1 p-6 min-w-0">

                {/* Summary banner */}
                <div className="mb-3 px-4 py-3 bg-white rounded-xl shadow-sm border-l-4 border-indigo-400 flex-shrink-0">
                    <p className="text-sm font-semibold text-indigo-600 mb-0.5">RAG-Powered Chat</p>
                    <p className="text-xs text-gray-500 leading-relaxed">
                        Each query searches your indexed documents and injects the most relevant chunks as context before calling the AI.
                        Use the settings panel to tune retrieval depth, similarity filtering, and response style.
                    </p>
                </div>

                <div
                    className="bg-white rounded-xl overflow-y-auto shadow-md p-5 flex flex-col gap-2.5 flex-shrink-0"
                    style={{ height: '55vh' }}
                    ref={chatboxRef}
                    role="log"
                    aria-live="polite"
                >
                    {messages.map((msg) => (
                        <div
                            key={msg.id}
                            className={`flex items-start ${msg.sender === 'user' ? 'justify-end' : ''}`}
                        >
                            {msg.sender === 'ai' && (
                                <img src="/ai-assistant.png" alt="AI Avatar" className="w-10 h-10 rounded-full mr-2.5 flex-shrink-0" />
                            )}
                            <div
                                className={`max-w-[80%] px-3 py-2.5 rounded-xl text-base leading-relaxed break-words my-1.5 ${
                                    msg.sender === 'user'
                                        ? 'bg-indigo-500 text-white'
                                        : 'bg-gray-200 text-black'
                                }`}
                            >
                                {msg.text}
                            </div>
                            {msg.sender === 'user' && (
                                <img src="/user-icon.png" alt="User Avatar" className="w-10 h-10 rounded-full ml-2.5 flex-shrink-0" />
                            )}
                        </div>
                    ))}
                    {loading && (
                        <div className="flex items-start">
                            <img src="/ai-assistant.png" alt="AI Avatar" className="w-10 h-10 rounded-full mr-2.5 flex-shrink-0" />
                            <div className="max-w-[80%] px-3 py-2.5 rounded-xl text-base bg-gray-200 text-black my-1.5">...</div>
                        </div>
                    )}
                </div>

                <div className="flex items-center mt-4">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Type your message..."
                        disabled={loading}
                        className="flex-1 p-2.5 border border-gray-300 rounded text-base mr-2.5 focus:outline-none focus:border-indigo-400 disabled:opacity-60 disabled:cursor-not-allowed"
                    />
                    <button
                        onClick={sendMessage}
                        disabled={loading}
                        aria-label="Send message"
                        className="bg-indigo-500 text-white border-none rounded p-2.5 px-4 cursor-pointer text-base flex justify-center items-center hover:bg-indigo-600 active:bg-indigo-700 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
                    >
                        <IoMdSend size={20} />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default RAGChatbot;
