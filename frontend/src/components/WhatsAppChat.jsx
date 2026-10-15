import React, { useState, useRef, useEffect } from 'react';
import { Send, Phone, Bot, Check, CheckCheck, Sparkles, RefreshCw } from 'lucide-react';
import { api } from '../api';
import { formatApiErrorMessage } from '../utils/errorHandler';

const QUICK_PROMPTS = [
  'Book appointment with Dr. A at 10 AM tomorrow',
  'I need an appointment with Dr. B on 20 October at 3 PM',
  'Book Dr. A today at 10:30 AM',
  'Book Dr. Bob tomorrow at 2 PM',
  'Book Dr. A tomorrow at 10 AM',
  'I want to see a doctor tomorrow'
];

export const WhatsAppChat = ({ onAppointmentBooked }) => {
  const [senderPhone, setSenderPhone] = useState('+14155552671');
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 'welcome_1',
      sender: 'system',
      text: "👋 Welcome to ClinicCare WhatsApp Scheduling! You can book an appointment in natural language.\n\nExample: 'Book appointment with Dr. A at 10 AM tomorrow.'",
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      status: 'info'
    }
  ]);

  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSendMessage = async (textToSend) => {
    const text = (textToSend || inputText).trim();
    if (!text || loading) return;

    const userMessageTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const userMsg = {
      id: 'user_' + Date.now(),
      sender: 'user',
      text: text,
      time: userMessageTime
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setLoading(true);

    try {
      const response = await api.sendWhatsAppMessage({
        sender: senderPhone,
        text: text,
        message_id: 'ui_msg_' + Date.now()
      });

      const replyMsg = {
        id: 'reply_' + Date.now(),
        sender: 'system',
        text: response.reply,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        status: response.status,
        appointment: response.appointment,
        suggested_slots: response.suggested_slots
      };

      setMessages((prev) => [...prev, replyMsg]);

      // If booking was successful, trigger global appointment refresh
      if (response.status === 'success' && onAppointmentBooked) {
        onAppointmentBooked();
      }
    } catch (err) {
      const detailedMessage = formatApiErrorMessage(
        err,
        '❌ Could not connect to webhook server. Please verify backend is running on http://localhost:8000.'
      );
      const isNetworkOrCors = !err.response || err.code === 'ERR_NETWORK' || err.message === 'Network Error';
      const displayText = isNetworkOrCors
        ? `❌ Could not connect to webhook server. (${detailedMessage})`
        : `❌ ${detailedMessage}`;

      const errorMsg = {
        id: 'err_' + Date.now(),
        sender: 'system',
        text: displayText,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        status: 'error'
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: 'welcome_' + Date.now(),
        sender: 'system',
        text: "👋 Chat reset. You can type: 'Book appointment with Dr. A tomorrow at 10 AM'.",
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        status: 'info'
      }
    ]);
  };

  return (
    <div className="phone-mockup">
      {/* Phone Header */}
      <div className="phone-header">
        <div className="phone-contact">
          <div className="avatar">CC</div>
          <div>
            <div className="contact-name">ClinicCare Bot</div>
            <div className="contact-status">online &bull; WhatsApp Verified</div>
          </div>
        </div>
        <button
          onClick={clearChat}
          style={{ background: 'transparent', border: 'none', color: '#FFF', cursor: 'pointer', opacity: 0.8 }}
          title="Reset Chat"
        >
          <RefreshCw size={16} />
        </button>
      </div>

      {/* Mock Sender Phone Input */}
      <div className="sender-selector">
        <label htmlFor="mock-phone-input">Mock Sender:</label>
        <Phone size={14} color="#64748B" />
        <input
          id="mock-phone-input"
          className="sender-input"
          value={senderPhone}
          onChange={(e) => setSenderPhone(e.target.value)}
          placeholder="+14155552671"
        />
      </div>

      {/* Chat Messages Timeline */}
      <div className="chat-area" id="whatsapp-chat-messages">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`chat-bubble ${msg.sender === 'user' ? 'outgoing' : 'incoming'}`}
          >
            <div>{msg.text}</div>

            {/* If there are suggested alternative slots, render clickable buttons */}
            {msg.suggested_slots && msg.suggested_slots.length > 0 && (
              <div style={{ marginTop: '10px' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#475569', marginBottom: '6px' }}>
                  Click to book an alternative slot:
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {msg.suggested_slots.map((slotTime, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendMessage(`Book at ${slotTime}`)}
                      className="chip"
                      style={{ background: '#DCFCE7', borderColor: '#86EFAC', fontWeight: 600 }}
                    >
                      {slotTime}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <span className="bubble-time">
              {msg.time}
              {msg.sender === 'user' && (
                <span style={{ marginLeft: '4px', verticalAlign: 'middle' }}>
                  <CheckCheck size={13} color="#53BDEB" />
                </span>
              )}
            </span>
          </div>
        ))}

        {loading && (
          <div className="chat-bubble incoming" style={{ color: '#64748B', fontStyle: 'italic' }}>
            <span>ClinicCare Bot is typing...</span>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Quick Prompt Chips */}
      <div className="prompt-chips">
        <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', color: '#64748B', fontWeight: 600 }}>
          <Sparkles size={12} color="#128C7E" /> Quick:
        </span>
        {QUICK_PROMPTS.map((prompt, idx) => (
          <button
            key={idx}
            className="chip"
            onClick={() => handleSendMessage(prompt)}
            disabled={loading}
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Message Composer */}
      <form
        className="chat-composer"
        onSubmit={(e) => {
          e.preventDefault();
          handleSendMessage();
        }}
      >
        <input
          id="whatsapp-composer-input"
          className="chat-input"
          placeholder="Type a booking message (e.g. Book Dr. A at 10 AM tomorrow)..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          disabled={loading}
        />
        <button
          type="submit"
          className="send-btn"
          id="whatsapp-send-btn"
          disabled={!inputText.trim() || loading}
          title="Send WhatsApp Message"
        >
          <Send size={18} />
        </button>
      </form>
    </div>
  );
};
