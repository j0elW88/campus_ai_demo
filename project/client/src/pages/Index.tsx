import { useEffect, useState, useRef } from "react";
import { RedStripe } from "@/components/RedStripe";
import { TwinklingStars } from "@/components/TwinklingStars";
import CampusLogo from "@/assets/CampusLogo.png";
import ReactMarkdown from "react-markdown";
import "@/global.css";

const Index = () => {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const chatBoxRef = useRef<HTMLDivElement>(null);
  const [showRating, setShowRating] = useState(false);
  const panelRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
      const handleClickOutside = (event: MouseEvent) => {
        if (panelRef.current && !panelRef.current.contains(event.target as Node)) {
          setShowRating(false);
        }
      };

      if (showRating) {
        document.addEventListener("mousedown", handleClickOutside);
      }

      return () => {
        document.removeEventListener("mousedown", handleClickOutside);
      };
    }, [showRating]);


  const handleRating = async (rating: 'good' | 'bad') => {
    console.log(`User rated the chat as: ${rating}`);
    setShowRating(false);
    try {
      const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:5000";
      await fetch(`${baseUrl}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating, messages }),
      });
    } catch (err) {
      console.error("⚠️ Error submitting review:", err);
    }
    setMessages([]);
    setInput('');
  };

  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    setMessages([]);
  }, []);
  

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;
    const userMessage = { role: "user", content: input };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInput("");
    setIsLoading(true);
    try {
      const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:5000";
      const res = await fetch(`${baseUrl}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: updatedMessages }),
      });
      const data = await res.json();
      const botMessage = { role: "assistant", content: data.reply };
      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "⚠️ Error getting response" },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      <TwinklingStars />
      <RedStripe />

      {/* Logo in top-left */}
      <img src={CampusLogo} alt="Campus Logo" className="campus-logo-top absolute left-4 top-2 w-auto z-50" />

      <div className="relative z-20 min-h-screen flex flex-col items-center justify-start pt-10">
      <header className="relative w-full max-w-[1000px] h-[5rem] mt-4 mb-6">
        {/* Centered Derek title */}
        <h1 className="empower-title text-glow absolute left-1/2 transform -translate-x-1/2 top-0 text-center z-0">
            Derek.
          </h1>
      </header>


        <div className="flex-1 flex items-center justify-center px-4 py-8">
          <div className="w-[75vw] min-w-[320px] max-w-[1000px] glass-effect depth-shadow rounded-[20px] pt-10 pb-20 px-10 mx-auto relative">
            <div className="chat-box overflow-y-auto max-h-[500px]" ref={chatBoxRef}>
              {messages.length === 0 ? (
                <div className="h-full flex items-center justify-center text-gray-400 text-lg text-center">
                  Hello, I am DEREK. Your Dynamic, Empowering, Reliable & Efficient Knowledge-Base! <br /> How can I help you today?
                </div>
              ) : (
                <div className="space-y-4">
                  {messages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                      <div className={`message-bubble ${msg.role === "user" ? "user" : "bot"}`}>
                        <div className="message-label">{msg.role === "user" ? "You" : "Derek"}</div>
                        <div className="text-base whitespace-pre-wrap">
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>
                      </div>
                    </div>
                  ))}
                  {isLoading && (
                    <div className="flex justify-start">
                      <div className="bot">
                        <div className="text-sm font-medium mb-1 opacity-90">DEREK</div>
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
                onKeyDown={handleKeyDown}
                placeholder="Ask me anything..."
                disabled={isLoading}
              />
              <button onClick={sendMessage} disabled={!input.trim() || isLoading}>Send</button>
            </div>
          </div>
        </div>
          {/* Feedback Area - Glass Container */}
          <div className="w-[75vw] max-w-[1000px] mx-auto mt-8 flex flex-col items-center space-y-4">
          {/* Start New Chat Button (only show when rating panel is hidden) */}
          {!showRating && (
            <button
              onClick={() => setShowRating(true)}
              className="norm_feedback-button faint-glow-button flex justify-center w-full mt-6 mb-[20px] glass-effect depth-shadow rounded-2xl text-center text-white font-semibold transition hover:bg-[#ff3030] disabled:bg-[#555]"
            >
              Start New Chat?
            </button>
          )}

            {/* Feedback Panel */}
            {showRating && (
              <div className="feedback-container w-full max-w-sm px-4 py-6">
                <div
                  ref={panelRef}
                  className="glass-effect depth-shadow rounded-2xl px-6 py-5 w-full max-w-md text-center"
                >
                  <p className="text-white text-base font-bold mb-1 font-sans">How Was Your Chat?</p>
                  <div className="flex flex-row justify-center gap-6 mt-6">
                    <button onClick={() => handleRating("good")} className="pos_feedback-button">Good</button>
                    <button onClick={() => handleRating("bad")} className="neg_feedback-button">Bad</button>
                  </div>
                </div>
              </div>
            )}


        </div>
      </div>
    </div>
  );
};

export default Index;
