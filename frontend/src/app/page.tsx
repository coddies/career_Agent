"use client";

import { useState, useRef, useEffect } from "react";
import { Client } from "@gradio/client";
import { Send, Upload, User, Bot, Loader2, Sparkles, AlertCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

type Message = {
  role: "user" | "assistant";
  content: string;
};

export default function CareerAgent() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [fileLoading, setFileLoading] = useState(false);
  const [traces, setTraces] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  
  const endOfMessagesRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto scroll to bottom
  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, traces]);

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);
    setError(null);

    try {
      // Connect to Hugging Face Space
      const client = await Client.connect("MuhammadBurhan/career-agent-backend");
      
      const result = await client.predict("/chat", { 
        message: userMessage,
      });

      // The API returns [updated_history, traces]
      const data = result.data as any;
      if (data && data[0]) {
        const updatedHistory = data[0];
        setMessages(updatedHistory);
        
        if (data[1]) {
          setTraces((prev) => prev + "\n" + data[1]);
        }
      }
    } catch (err: any) {
      console.error(err);
      setError("Failed to reach the AI agent. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setFileLoading(true);
    setError(null);

    try {
      const client = await Client.connect("MuhammadBurhan/career-agent-backend");
      const result = await client.predict("/upload_cv", { 
        file: file, 
      });

      const data = result.data as any;
      if (data && data[0]) {
        setMessages(data[0]);
        if (data[1]) {
          setTraces((prev) => prev + "\n" + data[1]);
        }
      }
    } catch (err: any) {
      console.error(err);
      setError("Failed to upload CV. Ensure it's a valid PDF.");
    } finally {
      setFileLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div className="flex h-screen w-full bg-[#0a0a0a] text-slate-200 overflow-hidden font-sans">
      
      {/* LEFT PANEL - CHAT */}
      <div className="flex flex-col flex-1 border-r border-slate-800/50">
        
        {/* Header */}
        <header className="h-16 flex items-center justify-between px-6 bg-[#0a0a0a]/80 backdrop-blur-md border-b border-slate-800/50 z-10">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-indigo-500/20 flex items-center justify-center text-indigo-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <h1 className="font-semibold text-lg tracking-tight text-white">career_agent</h1>
          </div>
          <div className="flex items-center gap-4">
            <input 
              type="file" 
              accept=".pdf" 
              className="hidden" 
              ref={fileInputRef}
              onChange={handleFileUpload}
            />
            <button 
              onClick={() => fileInputRef.current?.click()}
              disabled={fileLoading || isLoading}
              className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-sm font-medium rounded-lg transition-colors border border-slate-700/50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {fileLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
              <span>Upload CV</span>
            </button>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 scroll-smooth bg-gradient-to-b from-[#0a0a0a] to-[#111]">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-slate-500 gap-4 opacity-50">
              <Sparkles className="w-12 h-12" />
              <p className="text-sm font-medium">Hello! Upload your CV or type your skills to get started.</p>
            </div>
          )}

          {error && (
            <div className="mx-auto max-w-2xl bg-red-500/10 border border-red-500/20 rounded-xl p-4 flex items-center gap-3 text-red-400">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <p className="text-sm">{error}</p>
            </div>
          )}

          <AnimatePresence initial={false}>
            {messages.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={cn(
                  "flex gap-4 w-full max-w-3xl mx-auto",
                  msg.role === "user" ? "flex-row-reverse" : "flex-row"
                )}
              >
                {/* Avatar */}
                <div className={cn(
                  "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-1 border",
                  msg.role === "user" 
                    ? "bg-slate-800 border-slate-700 text-slate-300"
                    : "bg-indigo-500/20 border-indigo-500/30 text-indigo-400"
                )}>
                  {msg.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>

                {/* Bubble */}
                <div className={cn(
                  "px-5 py-3.5 rounded-2xl max-w-[85%] text-[15px] leading-relaxed shadow-sm",
                  msg.role === "user"
                    ? "bg-indigo-600 text-white rounded-tr-sm"
                    : "bg-[#1a1a1a] border border-slate-800 text-slate-300 rounded-tl-sm"
                )}>
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                </div>
              </motion.div>
            ))}
            
            {isLoading && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex gap-4 w-full max-w-3xl mx-auto flex-row"
              >
                <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-1 border bg-indigo-500/20 border-indigo-500/30 text-indigo-400">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="px-5 py-4 rounded-2xl bg-[#1a1a1a] border border-slate-800 rounded-tl-sm flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
                  <span className="text-sm text-slate-400">Analyzing skills...</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={endOfMessagesRef} className="h-4" />
        </div>

        {/* Input Area */}
        <div className="p-4 bg-[#0a0a0a] border-t border-slate-800/50">
          <form 
            onSubmit={handleSend}
            className="flex gap-3 max-w-3xl mx-auto relative group"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="E.g. I know React, Node, and AWS. What jobs fit me?"
              disabled={isLoading || fileLoading}
              className="flex-1 bg-[#1a1a1a] border border-slate-800 rounded-xl px-5 py-4 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading || fileLoading}
              className="absolute right-2 top-2 bottom-2 aspect-square flex items-center justify-center bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 text-white rounded-lg transition-all"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
          <p className="text-center text-xs text-slate-600 mt-3">
            Powered by Gemini, Groq, and Hugging Face. Connected to HF Spaces.
          </p>
        </div>
      </div>

      {/* RIGHT PANEL - TRACES */}
      <div className="hidden lg:flex w-[400px] flex-col border-l border-slate-800/50 bg-[#0a0a0a]">
        <div className="h-16 flex items-center px-5 border-b border-slate-800/50">
          <h2 className="text-sm font-semibold tracking-wide text-slate-400 uppercase flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            Agent Thought Traces
          </h2>
        </div>
        <div className="flex-1 overflow-y-auto p-5 bg-[#0a0a0a]">
          {traces ? (
            <pre className="font-mono text-[11px] leading-5 text-emerald-400/80 whitespace-pre-wrap break-all">
              {traces}
            </pre>
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-slate-600 italic text-center px-4">
              Developer traces will appear here as the AI reasons through tools.
            </div>
          )}
          <div ref={endOfMessagesRef} />
        </div>
      </div>

    </div>
  );
}
