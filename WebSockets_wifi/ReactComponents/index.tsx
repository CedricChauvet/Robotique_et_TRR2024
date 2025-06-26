import React, { useEffect, useState } from "react";

function App() {
  const [data, setData] = useState(null);
  const [speed, setSpeed] = useState(50);
  const [socket, setSocket] = useState(null);

  useEffect(() => {
    const ws = new WebSocket("ws://192.168.1.10:81");

    ws.onopen = () => {
      console.log("Connecté à Arduino");
    };
    ws.onmessage = (event) => {
      const message = event.data;
      if (message.startsWith("capteur:")) {
        setData(message.replace("capteur:", ""));
      }
    };
    ws.onerror = (error) => {
      console.error("Erreur WebSocket:", error);
    };
    ws.onclose = () => {
      console.log("Connexion fermée");
    };
    setSocket(ws);

    return () => ws.close();
  }, []);

  const sendSpeed = () => {
    if (socket) {
      socket.send(`setSpeed:${speed}`);
    }
  };

  return (
    <div style={{ fontFamily: "sans-serif", padding: "2rem" }}>
      <h1>Données en temps réel</h1>
      <div>Capteur : {data ?? "Connexion en cours…"}</div>
      <div style={{ marginTop: "1rem" }}>
        <input
          type="number"
          value={speed}
          onChange={(e) => setSpeed(parseInt(e.target.value, 10))}
        />
        <button onClick={sendSpeed}>Envoyer</button>
      </div>
    </div>
  );
}

export default App;
