// src/App.js
import React, { useState, useEffect } from "react";
import axios from "axios";
import { TwinklingStars } from "./components/TwinklingStars";
import { RedStripe } from "./components/RedStripe";
import CampusLogo from "./CampusLogo.png";
import "./App.css";

function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    setMessages([]); // reset chat on component mount
  }, []);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await axios.post("http://localhost:5000/chat", {
        message: input,
      });

      const botMessage = { role: "assistant", content: res.data.reply };
      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "⚠️ Error getting response" },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      <TwinklingStars />
      <RedStripe />

      <div className="relative z-20 min-h-screen flex flex-col">
        <header className="pt-6 md:pt-8 pb-4 text-center px-4">
          <img src={CampusLogo} alt="Logo" className="mx-auto h-16 mb-4" />
          <h1 className="group text-4xl md:text-6xl font-bold text-white cursor-default">
            EMPOWER <span className="text-blue-500">AI</span>
          </h1>
        </header>

        <div className="flex-1 flex items-center justify-center p-4">
          <div className="w-full max-w-4xl glass-effect depth-shadow rounded-2xl p-4 md:p-8">
            <div className="chat-box">
              {messages.length === 0 ? (
                <div className="h-full flex items-center justify-center text-gray-400 text-lg">
                  Welcome to Empower AI. How can I help you today?
                </div>
              ) : (
                <div className="space-y-4">
                  {messages.map((msg, i) => (
                    <div
                      key={i}
                      className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                      <div
                        className={`message-bubble ${
                          msg.role === "user" ? "user" : "bot"
                        }`}
                      >
                        <div className="text-sm font-medium mb-1 opacity-70">
                          {msg.role === "user" ? "You" : "EMPOWER"}
                        </div>
                        <div className="text-base">{msg.content}</div>
                      </div>
                    </div>
                  ))}
                  {isLoading && (
                    <div className="flex justify-start">
                      <div className="bot">
                        <div className="text-sm font-medium mb-1 opacity-70">EMPOWER</div>
                        <div className="flex items-center space-x-1">
                          <div className="dot"></div>
                          <div className="dot delay-100"></div>
                          <div className="dot delay-200"></div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="input-area">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Ask me anything..."
                disabled={isLoading}
              />
              <button onClick={sendMessage} disabled={!input.trim() || isLoading}>
                Send
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
