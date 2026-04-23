import React, { useState } from 'react';
import axios from 'axios';
import { IoMdSend } from 'react-icons/io';
import './Chatbot.css';

const Chatbot = () => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);

    const sendMessage = async () => {
        if (!input.trim()) return;

        const userMessage = { text: input, sender: 'user' };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setLoading(true);

        try {
            const response = await axios.get(
                `http://localhost:8080/ai/chat/string?message=${encodeURIComponent(input)}`
            );
            const aiMessage = { text: response.data, sender: 'ai' };
            setMessages(prev => [...prev, aiMessage]);
        } catch (error) {
            console.error('Error fetching AI response:', error);
            const errorMessage = { text: 'Sorry, something went wrong. Please try again.', sender: 'ai' };
            setMessages(prev => [...prev, errorMessage]);
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

            <div className="chatbox">
                {messages.map((msg, index) => (
                    <div key={index} className={`message-container ${msg.sender}`}>
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
                />
                <button onClick={sendMessage}>
                    <IoMdSend size={20} />
                </button>
            </div>
        </div>
    );
};

export default Chatbot;
