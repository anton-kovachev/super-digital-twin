"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User } from "lucide-react";
import { fetchEventSource } from "@microsoft/fetch-event-source";
import MarkdownPreview from "./markdown-preview";
import SamplePrompts from "./sample-prompts";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export default function Twin() {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>("");

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const didRunRef = useRef(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    // Removed stray 'd;'
  };

  useEffect(() => {
    if (didRunRef.current) return;
    didRunRef.current = true;

    if (inputRef.current) {
      inputRef.current.focus();
    }

    const fetchGreetingStreaming = async () => {
      try {
        await fetchEventSource(`${baseUrl}/greeting`, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
          onopen: async (response) => {
            setIsLoading(true);
            setMessages((prev) => {
              const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                content: "",
                timestamp: new Date(),
              };
              return [...prev, assistantMessage];
            });
          },
          onmessage: (event) => {
            try {
              debugger;
              const data = JSON.parse(event.data);
              const delta = data.response || "";
              const sid = data.session_id;
              if (sid && !sessionId) setSessionId(sid);

              setMessages((prev) => {
                const last = prev[prev.length - 1];
                if (last && last.role === "assistant") {
                  return [
                    ...prev.slice(0, -1),
                    {
                      ...last,
                      content: last.content + delta,
                      timestamp: new Date(),
                    },
                  ];
                }

                prev[prev.length - 1].content += delta;
                return [...prev];
              });
            } catch (err) {
              console.error("Failed to parse SSE event data", err);
            }
          },
          onclose: () => {
            setIsLoading(false);
          },
          onerror: (err) => {
            console.error("SSE error:", err);
            setMessages((prev) => {
              const last = prev[prev.length - 1];
              if (last && last.role === "assistant") {
                return [
                  ...prev.slice(0, -1),
                  {
                    ...last,
                    content: "Sorry, I encountered an error. Please try again.",
                    timestamp: new Date(),
                  },
                ];
              }
              return prev;
            });
            setIsLoading(false);
          },
        });
      } catch (error) {
        console.error("Error using fetchEventSource:", error);
        setIsLoading(false);
      }
    };

    fetchGreetingStreaming();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (prompt: string | null | undefined) => {
    if (!prompt && (!input.trim() || isLoading)) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: prompt ?? input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);

    if (!prompt) {
      setInput("");
    }

    try {
      await fetchEventSource(`${baseUrl}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: userMessage.content,
          session_id: sessionId || undefined,
        }),
        onopen: async (response) => {
          setIsLoading(true);
          // add an empty assistant message to accumulate deltas
          const assistantMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: "",
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, assistantMessage]);
        },
        onmessage: (event) => {
          try {
            const data = JSON.parse(event.data);
            const delta = data.response || "";
            const sid = data.session_id;
            if (sid && !sessionId) setSessionId(sid);

            setMessages((prev) => {
              const last = prev[prev.length - 1];
              if (last && last.role === "assistant") {
                return [
                  ...prev.slice(0, -1),
                  {
                    ...last,
                    content: last.content + delta,
                    timestamp: new Date(),
                  },
                ];
              }
              const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                content: delta,
                timestamp: new Date(),
              };
              return [...prev, assistantMessage];
            });
          } catch (err) {
            console.error("Failed to parse SSE event data", err);
          }
        },
        onclose: () => {
          setIsLoading(false);
          setTimeout(() => inputRef.current?.focus(), 100);
        },
        onerror: (err) => {
          console.error("SSE error:", err);
          setIsLoading(false);
          setMessages((prev) => [
            ...prev,
            {
              id: (Date.now() + 1).toString(),
              role: "assistant",
              content: "Sorry, I encountered an error. Please try again.",
              timestamp: new Date(),
            },
          ]);
        },
      });
    } catch (error) {
      console.error("Error using fetchEventSource:", error);
      setIsLoading(false);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "Sorry, I encountered an error. Please try again.",
          timestamp: new Date(),
        },
      ]);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(null);
    }
  };

  // Check if avatar exists
  const [hasAvatar, setHasAvatar] = useState(false);
  useEffect(() => {
    // Check if avatar.png exists
    fetch("/anton-profile.jpg", { method: "HEAD" })
      .then((res) => setHasAvatar(res.ok))
      .catch(() => setHasAvatar(false));
  }, []);

  // Download CV helper: fetches /cv and triggers a download from a Blob URL
  const downloadCv = async (): Promise<void> => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const resp = await fetch(`${apiUrl}/cv`);
      if (!resp.ok) throw new Error("Failed to download CV");
      const blob = await resp.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "anton_kovachev_cv.pdf";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("CV download failed", err);
    }
  };

  // onClick handler that calls the download helper
  const handleDownloadClick = async () => {
    await downloadCv();
  };

  return (
    <div className="flex flex-col h-full bg-gray-50 rounded-lg shadow-lg">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-700 to-slate-800 text-white p-4 rounded-t-lg">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <Bot className="w-6 h-6" />
          Anton Kovachev AI Twin
        </h2>
        <p className="text-sm text-slate-300 mt-1">AI professional assistant</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            {hasAvatar ? (
              <img
                src="./anton-profile.jpg"
                alt="Digital Twin Avatar"
                className="w-20 h-20 rounded-full mx-auto mb-3 border-2 border-gray-300"
              />
            ) : (
              <Bot className="w-12 h-12 mx-auto mb-3 text-gray-400" />
            )}
            <p>Hello! I&apos;m Anton Kovachev&apos;s Digital Twin.</p>
            <p className="text-sm mt-2">
              Ask me anything about my professional background and me!
            </p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-3 ${
              message.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            {message.role === "assistant" && (
              <div className="flex-shrink-0">
                {hasAvatar ? (
                  <img
                    src="./anton-profile.jpg"
                    alt="Digital Twin Avatar"
                    className="w-8 h-8 rounded-full border border-slate-300"
                  />
                ) : (
                  <div className="w-8 h-8 bg-slate-700 rounded-full flex items-center justify-center">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                )}
              </div>
            )}

            <div
              className={`max-w-[70%] rounded-lg p-3 ${
                message.role === "user"
                  ? "bg-slate-700 text-white"
                  : "bg-white border border-gray-200 text-gray-800"
              }`}
            >
              <div className="flex-1">
                <MarkdownPreview md={message.content} />
              </div>
              <p
                className={`text-xs mt-1 ${
                  message.role === "user" ? "text-slate-300" : "text-gray-500"
                }`}
              >
                {message.timestamp.toLocaleTimeString()}
              </p>
            </div>

            {message.role === "user" && (
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center">
                  <User className="w-5 h-5 text-white" />
                </div>
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-3 justify-start">
            <div className="flex-shrink-0">
              {hasAvatar ? (
                <img
                  src="./anton-profile.jpg"
                  alt="Digital Twin Avatar"
                  className="w-8 h-8 rounded-full border border-slate-300"
                />
              ) : (
                <div className="w-8 h-8 bg-slate-700 rounded-full flex items-center justify-center">
                  <Bot className="w-5 h-5 text-white" />
                </div>
              )}
            </div>
            <div className="bg-white border border-gray-200 rounded-lg p-3">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4 bg-white rounded-b-lg">
        <div className="flex flex-col gap-2">
          <div className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Type your message..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-600 focus:border-transparent text-gray-800"
              disabled={isLoading}
              autoFocus
            />
            <button
              onClick={() => sendMessage(null)}
              disabled={!input.trim() || isLoading}
              className="px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          <SamplePrompts sendMessage={sendMessage} baseUrl={baseUrl} />
          <div className="">
            <button
              onClick={handleDownloadClick}
              className="w-full px-4 py-2 bg-gradient-to-r from-slate-700 to-slate-800 border border-gray-300 rounded-lg text-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-slate-600"
            >
              Download My CV
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
