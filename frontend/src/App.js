import React, { useState, useEffect, useRef } from "react";
import Peer from "simple-peer";
import process from "process";

const App = () => {
  const [peer, setPeer] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState("Disconnected");
  const [socket, setSocket] = useState(null);
  const localVideoRef = useRef(null);

  useEffect(() => {
    // Create WebSocket connection
    const ws = new WebSocket("ws://127.0.0.1:8000/screen-share");
    setSocket(ws);

    const newPeer = new Peer({ initiator: true, trickle: false });

    ws.onopen = () => {
      setConnectionStatus("Connected");

      // Send signaling data when peer generates it
      newPeer.on("signal", (data) => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "signal", payload: data }));
        }
      });

      // Handle incoming signaling data
      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.type === "signal") {
          newPeer.signal(message.payload);
        }
      };
    };

    ws.onclose = () => setConnectionStatus("Disconnected");

    // Handle peer events
    newPeer.on("connect", () => console.log("Peer connection established"));
    newPeer.on("stream", (stream) => {
      // Attach remote stream to video element
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }
    });

    setPeer(newPeer);

    return () => {
      ws.close();
      newPeer.destroy();
    };
  }, []);

  const startScreenShare = () => {
    navigator.mediaDevices
      .getDisplayMedia({ video: true })
      .then((stream) => {
        if (peer) {
          peer.addStream(stream);
        }

        // Attach local screen share to video element
        if (localVideoRef.current) {
          localVideoRef.current.srcObject = stream;
        }
      })
      .catch((error) => console.error("Error starting screen share:", error));
  };

  return (
    <div style={{ textAlign: "center", marginTop: "50px" }}>
      <h1>Real-Time Multimodal AI</h1>
      <p>Status: {connectionStatus}</p>
      <button
        onClick={startScreenShare}
        disabled={connectionStatus !== "Connected"}
      >
        Start Screen Sharing
      </button>
      <div style={{ marginTop: "20px" }}>
        <video
          ref={localVideoRef}
          autoPlay
          muted
          style={{ width: "80%" }}
        ></video>
      </div>
    </div>
  );
};

export default App;
