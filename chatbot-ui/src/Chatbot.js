import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { IoMdSend } from 'react-icons/io';

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
                `${API_BASE}/ai/chat/string/client?message=${encodeURIComponent(text)}`
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
        <div className="flex flex-col justify-center items-center h-screen bg-gray-100 p-5 box-border">
            <div className="w-full max-w-xl flex justify-between items-center mb-5">
                <img src="/ai-chatbot-logo.png" alt="Chatbot Logo" className="h-24 mr-2.5" />
            </div>

            <div
                className="bg-white w-full max-w-xl h-[70vh] rounded-xl overflow-y-auto shadow-md p-5 flex flex-col gap-2.5"
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

            <div className="flex justify-center items-center w-full max-w-xl mt-5">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Type your message..."
                    disabled={loading}
                    className="w-full p-2.5 border border-gray-300 rounded text-base mr-2.5 focus:outline-none focus:border-indigo-400 disabled:opacity-60 disabled:cursor-not-allowed"
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
    );
};

export default Chatbot;
