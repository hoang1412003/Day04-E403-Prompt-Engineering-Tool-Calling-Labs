import { useState, useRef, useEffect } from 'react'
import './App.css'

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: 'Xin chào! Mình là trợ lý AI bán hàng. Bạn đang muốn tìm mua thiết bị điện tử gì hôm nay?' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: 'user', content: input.trim() };
    const newMessages = [...messages, userMessage];
    
    setMessages(newMessages);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ messages: newMessages }),
      });

      if (!response.ok) {
        throw new Error('API response was not ok');
      }

      const data = await response.json();
      setMessages(prev => [...prev, { role: data.role, content: data.content }]);
    } catch (error) {
      console.error('Error fetching chat:', error);
      setMessages(prev => [...prev, { role: 'assistant', content: 'Xin lỗi, đã có lỗi xảy ra khi kết nối tới hệ thống Backend. Hãy đảm bảo API đang chạy ở port 8000.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="header-info">
          <h1>Order Agent AI</h1>
          <p>Trợ lý ảo bán hàng thông minh</p>
        </div>
      </div>

      <div className="messages-area">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message-wrapper ${msg.role}`}>
            <div className="message-bubble">
              {msg.content.split('\n').map((line, i) => (
                <span key={i}>
                  {line}
                  <br />
                </span>
              ))}
            </div>
            <span className="message-time">
              {msg.role === 'user' ? 'Bạn' : 'Agent'}
            </span>
          </div>
        ))}
        {isLoading && (
          <div className="message-wrapper assistant">
            <div className="typing-indicator">
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
            </div>
            <span className="message-time">Agent đang nhập...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-area">
        <form onSubmit={handleSubmit} className="input-form">
          <input
            type="text"
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Nhập tin nhắn để bắt đầu mua sắm..."
            disabled={isLoading}
          />
          <button type="submit" className="send-button" disabled={!input.trim() || isLoading}>
            <svg className="send-icon" viewBox="0 0 24 24">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  )
}

export default App
