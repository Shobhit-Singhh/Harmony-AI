import React, { useState, useEffect, useRef } from "react";

import { Loader2 } from "lucide-react";

const ConfirmationModal = ({ isOpen, onClose, onConfirm }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-sm w-full mx-4">
        <h3 className="text-lg font-semibold mb-4">Skip Question</h3>
        <p className="text-gray-600 mb-6">Are you sure you want to skip this question?</p>
        <div className="flex justify-end space-x-4">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
          >
            Confirm Skip
          </button>
        </div>
      </div>
    </div>
  );
};

const chatboticon = () => {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="44" height="44" viewBox="0 0 1024 1024"><path d="M738.3 287.6H285.7c-59 0-106.8 47.8-106.8 106.8v303.1c0 59 47.8 106.8 106.8 106.8h81.5v111.1c0 .7.8 1.1 1.4.7l166.9-110.6 41.8-.8h117.4l43.6-.4c59 0 106.8-47.8 106.8-106.8V394.5c0-59-47.8-106.9-106.8-106.9zM351.7 448.2c0-29.5 23.9-53.5 53.5-53.5s53.5 23.9 53.5 53.5-23.9 53.5-53.5 53.5-53.5-23.9-53.5-53.5zm157.9 267.1c-67.8 0-123.8-47.5-132.3-109h264.6c-8.6 61.5-64.5 109-132.3 109zm110-213.7c-29.5 0-53.5-23.9-53.5-53.5s23.9-53.5 53.5-53.5 53.5 23.9 53.5 53.5-23.9 53.5-53.5 53.5zM867.2 644.5V453.1h26.5c19.4 0 35.1 15.7 35.1 35.1v121.1c0 19.4-15.7 35.1-35.1 35.1h-26.5zM95.2 609.4V488.2c0-19.4 15.7-35.1 35.1-35.1h26.5v191.3h-26.5c-19.4 0-35.1-15.7-35.1-35.1zM561.5 149.6c0 23.4-15.6 43.3-36.9 49.7v44.9h-30v-44.9c-21.4-6.5-36.9-26.3-36.9-49.7 0-28.6 23.3-51.9 51.9-51.9s51.9 23.3 51.9 51.9z" /></svg>
  );
};

const ChatbotMessage = ({ text }) => {
  return (
    <div className="chatbot-message flex items-end space-x-3 -mx-4 py-2">
      <div className="flex items-center rounded-full gap-2 bg-white h-10 w-10 justify-center border-2 border-lime-600">
        {chatboticon()}
      </div>
      <p className="bg-gray-300 p-2 rounded-tl-2xl rounded-tr-2xl rounded-br-2xl rounded-bl-md max-w-[290px] text-sm ">{text}</p>
    </div>
  );
};

const UserMessage = ({ text }) => {
  return (
    <div className="user-message flex items-end space-x-3 flex-row-reverse gap-2 py-2 -mx-4">
      <i className="fa-regular fa-user bg-lime-600 h-10 w-10 rounded-full flex items-center justify-center text-white text-xl"></i>
      <p className="bg-lime-200 p-2 rounded-tl-2xl rounded-tr-2xl rounded-bl-2xl rounded-br-md max-w-[290px] text-sm">{text}</p>
    </div>
  );
};

const renderJsonHierarchy = (data) => {
  if (typeof data === "object" && data !== null) {
    return (
      <ul>
        {Object.entries(data).map(([key, value], index) => (
          <li key={index}>
            <strong>{key}:</strong>
            {typeof value === "object" ? (
              <div className="ml-4">{renderJsonHierarchy(value)}</div>
            ) : (
              <span> {value}</span>
            )}
          </li>
        ))}
      </ul>
    );
  } else {
    return <span>{data}</span>;
  }
};

const LogsList = ({ text }) => {
  return (
    <div className="bg-green-300 p-4 rounded-xl text-left border-2 border-green-400 my-2">
      {typeof text === "object" ? (
        renderJsonHierarchy(text)
      ) : (
        <p className="text-xs text-gray-800 text-left">{text}</p>
      )}
    </div>
  );
};



const App = () => {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [log, setlog] = useState([]);
  const [logs, setlogs] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [placeholder, setPlaceholder] = useState("Lets talk about it...");
  const [showSkipConfirmation, setShowSkipConfirmation] = useState(false);
  const [isSkipAllowed, setIsSkipAllowed] = useState(false);
  const [isWaitingForAI, setIsWaitingForAI] = useState(false);

  const handleSkip = () => {
    if (isWaitingForAI) return;
    setShowSkipConfirmation(true);
  };

  const confirmSkip = () => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      try {
        setIsWaitingForAI(true);
        socket.send(JSON.stringify({ user_response: "" }));
        setMessages((prevMessages) => [
          ...prevMessages,
          { type: "user", text: "Next Question Please" },
        ]);
      } catch (error) {
        console.error("Error sending skip message:", error);
        setIsWaitingForAI(false);
      }
    }
    setShowSkipConfirmation(false);
  };

  useEffect(() => {
    let ws;
    let reconnectTimeout;

    const connectWebSocket = () => {
      // ws = new WebSocket("ws://localhost:8000/ws");
      ws = new WebSocket("wss://harmony-ai-6x1o.onrender.com");

      ws.onopen = () => {
        console.log("Connected to WebSocket");
        setSocket(ws);
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log("Parsed WebSocket data:", data);

          if (data.AIresponce?.question) {
            console.log("Question:", data.AIresponce.question);
            setMessages((prev) => [
              ...prev,
              { type: "chatbot", text: data.AIresponce.question },
            ]);
          }

          if (data.AIresponce?.skip_allowed !== undefined) {
            setIsSkipAllowed(data.AIresponce.skip_allowed);
            setPlaceholder(
              data.AIresponce.skip_allowed
                ? "You can move to the next question"
                : "Wanna talk about it?"
            );
          }

          if (data.AIresponce?.log) {
            try {
              let logData = data.AIresponce.log;

              // Ensure logData is properly formatted as JSON
              if (typeof logData === "string") {
                logData = JSON.parse(logData.trim());
              }

              console.log("Parsed Log:", logData);

              // Store parsed JSON directly instead of converting it to a string
              setlogs((prevLogs) => [...prevLogs, { type: "log", text: logData }]);
            } catch (error) {
              console.error("Error parsing log:", error, "Raw Log Data:", data.AIresponce.log);

              // Fallback: Store raw log safely if parsing fails
              setlogs((prevLogs) => [...prevLogs, { type: "log", text: data.AIresponce.log }]);
            }
          }


          setIsWaitingForAI(false);
        } catch (error) {
          console.error("Error parsing WebSocket message:", error);
          setIsWaitingForAI(false);
        }
      };

      ws.onclose = () => {
        console.log("WebSocket disconnected, reconnecting in 3 seconds...");
        setIsConnected(false);
        reconnectTimeout = setTimeout(connectWebSocket, 3000);
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        ws.close();
      };
    };

    connectWebSocket();

    return () => {
      if (ws) {
        ws.close();
      }
      clearTimeout(reconnectTimeout);
    };
  }, []);


  const handleSend = () => {
    if (!message.trim() || !socket || socket.readyState !== WebSocket.OPEN || isWaitingForAI) {
      return;
    }

    try {
      setIsWaitingForAI(true);
      socket.send(JSON.stringify({ user_response: message }));
      setMessages((prevMessages) => [
        ...prevMessages,
        { type: "user", text: message },
      ]);
      setMessage("");
    } catch (error) {
      console.error("Error sending message:", error);
      setIsWaitingForAI(false);
    }
  };

  return (
    <div className="container p-4">
      {!isOpen && (
        <div
          className="fixed bottom-16 right-4 z-50 flex items-center justify-center w-16 h-16 bg-emerald-500 rounded-full shadow-lg cursor-pointer"
          onClick={() => setIsOpen(true)}
        >
          {chatboticon()}
        </div>
      )}

      {/* ---------------------------- Background Procession Log ---------------------------- */}
      <div className="bg-gray-200 text-gray-800 text-xs text-center items-center justify-center w-full h-full border-2 border-gray-300 rounded-lg shadow-lg">
        <p className="p-2 text-lg font-semibold border-b-2 border-zinc-300" >Harmony AI: Logs</p>
        <div className="overflow-y-auto h-auto">
          <div className="p-8 overflow-y-auto -z-10" style={{ maxHeight: "650px", height: "auto" }}>
            <div>
              {logs.map((msg, index) => (
                <LogsList key={index} text={msg.text} />
              ))}


              {isWaitingForAI && (
                <div className="relative p-40">
                  <div className="absolute inset-0 flex justify-center items-center">
                    <Loader2 className="animate-spin text-emerald-500" size={60} />
                  </div>
                  <div className="absolute inset-0 flex justify-center items-center">
                    {chatboticon()}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div
        className={`fixed left-1/2 top-80 z-50 bg-white rounded-lg shadow-lg overflow-hidden transform transition-transform ${isOpen ? "-translate-y-1/2" : "translate-y-full"}`}
        style={{ transition: "transform 0.3s", width: "400px", height: "600px", marginLeft: "-200px" }}
      >
        <div className="chatbot-popup-container">
          {/* Header */}
          <div className="chatbot-popup-header flex items-center justify-between bg-emerald-500 text-white px-4 py-2 h-16 ">
            <div className="flex items-center rounded-full gap-2 bg-white h-10 w-10 justify-center border-2 border-lime-600">
              {chatboticon()}
            </div>
            <h4 className="text-2xl font-bold">Sage Bot</h4>
            <button
              onClick={() => setIsOpen(false)}
              className="flex items-center space-x-2 bg-red-500 hover:bg-red-800 text-white text-2xl px-2 py-1 border-2 border-red-700 rounded-lg shadow-md transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-red-500"
            >
              <i className="fa fa-times"></i>
            </button>
          </div>

          {/* Body */}
          <div className="flex-grow chatbot-popup-body p-10 overflow-y-auto -z-10 flex flex-col" style={{ maxHeight: "500px", height: "auto" }}>
            <div className="chatbot-popup-message">
              {messages.map((msg, index) =>
                msg.type === "user" ? (
                  <UserMessage key={index} text={msg.text} />
                ) : (
                  <ChatbotMessage key={index} text={msg.text} />
                )
              )}
              {isWaitingForAI && (
                <div className="relative p-32">
                  <div className="absolute inset-0 flex justify-center items-center">
                    <Loader2 className="animate-spin text-emerald-500" size={100} />
                  </div>
                  <div className="absolute inset-0 flex justify-center items-center" size={400}>
                    {chatboticon()}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="fixed bottom-[.1px] chatbot-popup-footer flex items-center bg-gray-200 px-4 py-2 rounded-b-lg w-full">
            <input
              type="text"
              placeholder={isWaitingForAI ? "Please wait for AI response..." : placeholder}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="flex-1 border border-gray-300 rounded-lg p-2 mr-2"
              disabled={isWaitingForAI}
            />
            {message.trim() ? (
              <button
                onClick={handleSend}
                className={`bg-blue-500 text-white px-4 py-2 rounded-lg ${isWaitingForAI ? 'opacity-50 cursor-not-allowed' : ''}`}
                disabled={isWaitingForAI}
              >
                Send
              </button>
            ) : (
              <button
                onClick={handleSkip}
                className={`bg-red-500 text-lime-200 px-4 py-2 rounded-lg border-2 border-red-700 ${isWaitingForAI ? 'opacity-50 cursor-not-allowed' : ''}`}
                disabled={isWaitingForAI}
              >
                Skip
              </button>
            )}
          </div>

        </div>
      </div>

      <ConfirmationModal
        isOpen={showSkipConfirmation}
        onClose={() => setShowSkipConfirmation(false)}
        onConfirm={confirmSkip}
      />
    </div>
  );
};

export default App;