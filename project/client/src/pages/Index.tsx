import { useEffect, useState, useRef } from "react";
import { RedStripe } from "@/components/RedStripe";
import { TwinklingStars } from "@/components/TwinklingStars";
import CampusLogo from "@/assets/CampusLogo.png";
import "@/global.css";

const Index = () => {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const chatBoxRef = useRef<HTMLDivElement>(null);

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
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: updatedMessages }), // ✅ send all messages
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
      {/* Background Visuals */}
      <TwinklingStars />
      <RedStripe />



      {/* Main Layout */}
      <div className="relative z-20 min-h-screen flex flex-col items-center justify-start pt-10">
        {/* Header with Logo and Title */}
        <header className="pt-4 md:pt-6 pb-2 text-center px-4">
          <img src={CampusLogo} alt="Campus Logo" className="campus-logo" />
          <h1 className="empower-title cursor-default">
            <span className="text-glow">Derek.</span>
          </h1>
        </header>

        {/* Chat Interface */}
        <div className="flex-1 flex items-center justify-center px-4 py-8">
          <div className="w-[75vw] min-w-[320px] max-w-[1000px] glass-effect depth-shadow rounded-[20px] pt-10 pb-20 px-10 mx-auto relative">
            {/* Chat Messages */}
            <div className="chat-box overflow-y-auto max-h-[500px]" ref={chatBoxRef}>
              {messages.length === 0 ? (
                <div className="h-full flex items-center justify-center text-gray-400 text-lg text-center">
                  Hello, I am DEREK. Your Dyanmic, Empowering, Reliable & Efficient Knowledge-Base! 
                  <br /> 
                  How can I help you today?
                </div>
              ) : (
                <div className="space-y-4">
                  {messages.map((msg, i) => (
                    <div
                      key={i}
                      className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                      <div className={`message-bubble ${msg.role === "user" ? "user" : "bot"}`}>
                        <div className="message-label">
                          {msg.role === "user" ? "You" : "EMPOWER"}
                        </div>
                        <div className="text-base">{msg.content}</div>
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

            {/* Input Field and Send Button */}
            <div className="input-area">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask me anything..."
                disabled={isLoading}
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || isLoading}
              >
                Send
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
