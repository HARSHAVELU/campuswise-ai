"use client";

import { useEffect, useRef, useState } from "react";
import { apiPost, ApiClientError } from "@/lib/api-client";
import type { ChatMessage, ChatResponse } from "@/types/api";

const STORAGE_KEY = "campuswise_chat_history";
const MAX_HISTORY_SENT = 12;

const SUGGESTED_PROMPTS = [
  "Find me an easy python elective",
  "Does CS 4375 have a group project?",
  "Build me a 12 credit schedule, no Friday classes",
  "Which professor has the best grades for CS 2336?",
];

function loadHistory(): ChatMessage[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as ChatMessage[]) : [];
  } catch {
    return [];
  }
}

export function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMessages(loadHistory());
  }, []);

  useEffect(() => {
    if (messages.length > 0) {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    }
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function sendMessage(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    const userMessage: ChatMessage = { role: "user", content: trimmed };
    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const response = await apiPost<ChatResponse>("/ai/chat", {
        message: trimmed,
        history: nextMessages.slice(-MAX_HISTORY_SENT - 1, -1),
      });
      setMessages([...nextMessages, { role: "assistant", content: response.reply }]);
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? `I couldn't get a response right now. (${err.message})`
          : "I couldn't reach the assistant right now.",
      );
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    sendMessage(input);
  }

  function clearChat() {
    setMessages([]);
    window.localStorage.removeItem(STORAGE_KEY);
  }

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col items-end">
      {open && (
        <div className="mb-3 flex h-[520px] w-[360px] flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-2xl">
          <div className="flex items-center justify-between border-b border-slate-200 bg-brand px-4 py-3 text-white">
            <div>
              <div className="text-sm font-semibold">CampusWise Assistant</div>
              <div className="text-xs text-blue-100">Ask about courses, professors, or your schedule</div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={clearChat}
                title="Clear conversation"
                className="rounded px-1.5 py-0.5 text-xs text-blue-100 hover:bg-white/10"
              >
                Clear
              </button>
              <button
                onClick={() => setOpen(false)}
                aria-label="Close chat"
                className="rounded px-1.5 py-0.5 text-lg leading-none text-blue-100 hover:bg-white/10"
              >
                ×
              </button>
            </div>
          </div>

          <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto bg-slate-50 px-3 py-3">
            {messages.length === 0 && (
              <div className="space-y-2">
                <p className="text-sm text-slate-500">
                  Hi! I can help you find courses, compare professors, check syllabus policies, or
                  build a schedule. Try one of these:
                </p>
                {SUGGESTED_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => sendMessage(prompt)}
                    className="block w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-left text-xs text-slate-600 hover:border-brand hover:text-brand"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            )}

            {messages.map((message, i) => (
              <div
                key={i}
                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] whitespace-pre-wrap rounded-lg px-3 py-2 text-sm ${
                    message.role === "user"
                      ? "bg-brand text-white"
                      : "border border-slate-200 bg-white text-slate-800"
                  }`}
                >
                  {message.content}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-400">
                  Thinking...
                </div>
              </div>
            )}

            {error && (
              <div className="rounded-md bg-red-50 px-3 py-2 text-xs text-red-700">{error}</div>
            )}
          </div>

          <form onSubmit={handleSubmit} className="flex gap-2 border-t border-slate-200 p-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about a course, professor, or schedule..."
              className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand focus:outline-none"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="rounded-md bg-brand px-3 py-2 text-sm font-medium text-white hover:bg-brand-light disabled:opacity-50"
            >
              Send
            </button>
          </form>
        </div>
      )}

      <button
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? "Close chat assistant" : "Open chat assistant"}
        className="flex h-14 w-14 items-center justify-center rounded-full bg-brand text-2xl text-white shadow-lg hover:bg-brand-light"
      >
        {open ? "×" : "💬"}
      </button>
    </div>
  );
}
