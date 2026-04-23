import { useState } from 'react';
import Chatbot from './Chatbot';
import DocumentUpload from './DocumentUpload';

function App() {
    const [tab, setTab] = useState('chat');

    const tabClass = (name) =>
        `px-6 py-2 text-sm cursor-pointer border-b-2 rounded-t transition-colors bg-transparent ${
            tab === name
                ? 'text-indigo-500 border-indigo-500 font-semibold'
                : 'text-gray-500 border-transparent hover:text-indigo-400'
        }`;

    return (
        <div className="text-center">
            <nav className="flex justify-center gap-1 px-4 pt-3 bg-white border-b border-gray-200">
                <button className={tabClass('chat')} onClick={() => setTab('chat')}>
                    💬 Chat
                </button>
                <button className={tabClass('docs')} onClick={() => setTab('docs')}>
                    📄 Documents
                </button>
            </nav>
            {tab === 'chat' ? <Chatbot /> : <DocumentUpload />}
        </div>
    );
}

export default App;
