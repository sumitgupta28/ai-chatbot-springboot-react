import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { IoMdSend } from 'react-icons/io';
import './Chatbot.css';

const API_BASE = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8080';

const Chatbot = () => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
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
                `${API_BASE}/ai/chat/string?message=${encodeURIComponent(text)}`
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
        <div className="chatbot-container">
            <div className="chat-header">
                <img src="/ai-chatbot-logo.png" alt="Chatbot Logo" className="chat-logo" />
                <span className="breadcrumb">Home &gt; Chatbot</span>
            </div>

            <div className="chatbox" ref={chatboxRef} role="log" aria-live="polite">
                {messages.map((msg) => (
                    <div key={msg.id} className={`message-container ${msg.sender}`}>
                        {msg.sender === 'ai' && (
                            <img src="/ai-assistant.png" alt="AI Avatar" className="avatar" />
                        )}
                        <div className={`message ${msg.sender}`}>{msg.text}</div>
                        {msg.sender === 'user' && (
                            <img src="/user-icon.png" alt="User Avatar" className="avatar" />
                        )}
                    </div>
                ))}
                {loading && (
                    <div className="message-container ai">
                        <img src="/ai-assistant.png" alt="AI Avatar" className="avatar" />
                        <div className="message ai">...</div>
                    </div>
                )}
            </div>

            <div className="input-container">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Type your message..."
                    disabled={loading}
                />
                <button onClick={sendMessage} disabled={loading} aria-label="Send message">
                    <IoMdSend size={20} />
                </button>
            </div>
        </div>
    );
};

export default Chatbot;
