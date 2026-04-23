import { useState } from 'react';
import './App.css';
import Chatbot from './Chatbot';
import DocumentUpload from './DocumentUpload';

function App() {
    const [tab, setTab] = useState('chat');

    return (
        <div className="App">
            <nav className="app-nav">
                <button
                    className={`nav-tab${tab === 'chat' ? ' active' : ''}`}
                    onClick={() => setTab('chat')}
                >
                    💬 Chat
                </button>
                <button
                    className={`nav-tab${tab === 'docs' ? ' active' : ''}`}
                    onClick={() => setTab('docs')}
                >
                    📄 Documents
                </button>
            </nav>
            {tab === 'chat' ? <Chatbot /> : <DocumentUpload />}
        </div>
    );
}

export default App;
