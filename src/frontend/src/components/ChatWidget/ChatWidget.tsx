import React, { useState, useEffect, useRef } from 'react';
import {
    MessageSquare,
    X,
    Plus,
    Send,
    Hash,
    Loader2,
    Maximize2,
    Minimize2
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import './ChatWidget.css';

interface Message {
    id: string;
    user_message: string;
    assistant_message: string;
    timestamp: string;
    metadata?: any;
}

interface Session {
    session_id: string;
    session_name: string;
    flow_id: string;
    created_at: string;
}

export const ChatWidget: React.FC = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [sessions, setSessions] = useState<Session[]>([]);
    const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isInitializing, setIsInitializing] = useState(true);
    const [isMaximized, setIsMaximized] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);


    // Initialize: load sessions if any
    useEffect(() => {
        const fetchSessions = async () => {
            try {
                // We'll assume a way to list widget sessions, for now we might just create one if none exist
                // Or if we don't have a list endpoint, we'll use localStorage to store session IDs
                const storedSessions = localStorage.getItem('langflow_widget_sessions');
                if (storedSessions) {
                    const parsed = JSON.parse(storedSessions);
                    setSessions(parsed);
                    if (parsed.length > 0) {
                        setActiveSessionId(parsed[0].session_id);
                    }
                }
            } catch (error) {
                console.error("Failed to load sessions", error);
            } finally {
                setIsInitializing(false);
            }
        };
        fetchSessions();
    }, []);

    // Load messages when active session changes
    useEffect(() => {
        if (activeSessionId) {
            const fetchHistory = async () => {
                try {
                    const response = await axios.get(`/api/v1/chat/history/${activeSessionId}`);
                    setMessages(response.data.messages || []);
                } catch (error) {
                    console.error("Failed to load history", error);
                }
            };
            fetchHistory();
        } else {
            setMessages([]);
        }
    }, [activeSessionId]);

    // Scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isLoading]);

    const createNewSession = async () => {
        try {
            const sessionName = `Chat ${sessions.length + 1}`;
            const response = await axios.post('/api/v1/chat/session', {
                flow_id: "00000000-0000-0000-0000-000000000000", // Placeholder or dynamic if needed
                session_name: sessionName
            });

            const newSession = {
                session_id: response.data.session_id,
                session_name: response.data.session_name,
                flow_id: response.data.flow_id,
                created_at: response.data.created_at
            };

            const updatedSessions = [...sessions, newSession];
            setSessions(updatedSessions);
            setActiveSessionId(newSession.session_id);
            localStorage.setItem('langflow_widget_sessions', JSON.stringify(updatedSessions));
        } catch (error) {
            console.error("Failed to create session", error);
        }
    };

    const handleSendMessage = async (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!inputValue.trim() || isLoading || !activeSessionId) return;

        const currentSession = sessions.find(s => s.session_id === activeSessionId);
        if (!currentSession) return;

        const userMsg = inputValue;
        setInputValue('');
        setIsLoading(true);

        try {
            const response = await axios.post<Message>('/api/v1/chat/widget', {
                session_id: activeSessionId,
                message: userMsg,
                flow_id: currentSession.flow_id || "00000000-0000-0000-0000-000000000000"
            });

            setMessages(prev => [...prev, response.data]);
        } catch (error) {
            console.error("Failed to send message", error);
        } finally {
            setIsLoading(false);
        }
    };

    const deleteSession = (sessionId: string) => {
        const updated = sessions.filter(s => s.session_id !== sessionId);
        setSessions(updated);
        localStorage.setItem('langflow_widget_sessions', JSON.stringify(updated));
        if (activeSessionId === sessionId) {
            setActiveSessionId(updated.length > 0 ? updated[0].session_id : null);
        }
    };

    return (
        <div className="chat-widget-container">
            {/* Floating Action Button */}
            <motion.button
                className="chat-fab"
                onClick={() => setIsOpen(!isOpen)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
            >
                {isOpen ? <X size={24} /> : <MessageSquare size={24} />}
            </motion.button>

            {/* Chat Window */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        className={`chat-window shadow-2xl overflow-hidden flex flex-col ${isMaximized ? 'maximized' : ''}`}
                        initial={{ opacity: 0, y: 20, scale: 0.9 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 20, scale: 0.9 }}
                        transition={{ type: 'spring', damping: 20, stiffness: 300 }}
                    >
                        {/* Header / Tabs */}
                        <div className="chat-header p-2 border-b flex items-center justify-between gap-2 bg-background/80 backdrop-blur-md">
                            <div className="flex items-center gap-2 overflow-x-auto scrollbar-hide flex-1">
                                {sessions.map((session) => (
                                    <div
                                        key={session.session_id}
                                        className={`chat-tab flex items-center gap-2 px-3 py-1.5 rounded-lg cursor-pointer transition-all ${activeSessionId === session.session_id
                                            ? 'bg-primary text-primary-foreground shadow-sm'
                                            : 'hover:bg-muted'
                                            }`}
                                        onClick={() => setActiveSessionId(session.session_id)}
                                    >
                                        <Hash size={14} className="opacity-50" />
                                        <span className="text-sm font-medium whitespace-nowrap">{session.session_name}</span>
                                        <X
                                            size={12}
                                            className="hover:text-destructive transition-colors ml-1"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                deleteSession(session.session_id);
                                            }}
                                        />
                                    </div>
                                ))}
                            </div>
                            <div className="flex items-center gap-1">
                                <button
                                    onClick={createNewSession}
                                    className="p-1.5 rounded-lg hover:bg-muted transition-colors"
                                    title="New Chat"
                                >
                                    <Plus size={18} />
                                </button>
                                <button
                                    onClick={() => setIsMaximized(!isMaximized)}
                                    className="p-1.5 rounded-lg hover:bg-muted transition-colors"
                                    title={isMaximized ? "Restore" : "Maximize"}
                                >
                                    {isMaximized ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
                                </button>
                                <button
                                    onClick={() => setIsOpen(false)}
                                    className="p-1.5 rounded-lg hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
                                    title="Close"
                                >
                                    <X size={18} />
                                </button>
                            </div>
                        </div>

                        {/* Chat Content */}
                        <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
                            {!activeSessionId ? (
                                <div className="h-full flex flex-col items-center justify-center text-center p-8 opacity-60">
                                    <div className="bg-muted p-4 rounded-full mb-4">
                                        <MessageSquare size={32} />
                                    </div>
                                    <h3 className="text-lg font-semibold">Welcome to Chat</h3>
                                    <p className="text-sm mt-2">Start a new conversation to get started with the powerful GPT-5.2 assistant.</p>
                                    <button
                                        onClick={createNewSession}
                                        className="mt-6 px-4 py-2 bg-primary text-primary-foreground rounded-full hover:shadow-lg transition-all"
                                    >
                                        Create New Tab
                                    </button>
                                </div>
                            ) : (
                                <>
                                    {messages.map((msg) => (
                                        <React.Fragment key={msg.id}>
                                            {/* User Message */}
                                            <motion.div
                                                initial={{ opacity: 0, x: 10 }}
                                                animate={{ opacity: 1, x: 0 }}
                                                className="flex justify-end"
                                            >
                                                <div className="max-w-[85%] bg-primary text-primary-foreground px-4 py-2 rounded-2xl rounded-tr-none shadow-sm">
                                                    <p className="text-sm leading-relaxed">{msg.user_message}</p>
                                                </div>
                                            </motion.div>

                                            {/* Assistant Message */}
                                            <motion.div
                                                initial={{ opacity: 0, x: -10 }}
                                                animate={{ opacity: 1, x: 0 }}
                                                className="flex justify-start"
                                            >
                                                <div className="max-w-[85%] bg-muted border px-4 py-2 rounded-2xl rounded-tl-none shadow-sm backdrop-blur-sm">
                                                    <p className="text-sm leading-relaxed text-foreground">{msg.assistant_message}</p>
                                                </div>
                                            </motion.div>
                                        </React.Fragment>
                                    ))}
                                    {isLoading && (
                                        <div className="flex justify-start">
                                            <div className="bg-muted border p-3 rounded-2xl rounded-tl-none shadow-sm">
                                                <div className="typing-indicator flex items-center gap-1">
                                                    <span className="dot"></span>
                                                    <span className="dot"></span>
                                                    <span className="dot"></span>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                    <div ref={messagesEndRef} />
                                </>
                            )}
                        </div>

                        {/* Input Area */}
                        {activeSessionId && (
                            <form
                                onSubmit={handleSendMessage}
                                className="p-4 border-t bg-background/50 backdrop-blur-md flex items-center gap-2"
                            >
                                <input
                                    type="text"
                                    value={inputValue}
                                    onChange={(e) => setInputValue(e.target.value)}
                                    placeholder="Type your message..."
                                    className="flex-1 bg-muted/50 border-none focus:ring-1 focus:ring-primary rounded-xl px-4 py-2.5 text-sm transition-all outline-none"
                                    disabled={isLoading}
                                />
                                <motion.button
                                    type="submit"
                                    disabled={!inputValue.trim() || isLoading}
                                    className={`p-2.5 rounded-xl flex items-center justify-center transition-all ${inputValue.trim() && !isLoading ? 'bg-primary text-primary-foreground shadow-md' : 'bg-muted opacity-50'
                                        }`}
                                    whileHover={{ scale: inputValue.trim() ? 1.05 : 1 }}
                                    whileTap={{ scale: 0.95 }}
                                >
                                    {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
                                </motion.button>
                            </form>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};
