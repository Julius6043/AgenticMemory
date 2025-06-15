# AgenticMemory Chat API

Diese Flask-API stellt das AgenticMemory-System als Chat-Agent zur Verfügung, mit dem Frontend-Anwendungen über eine RESTful-Schnittstelle kommunizieren können.

## Installation

1. Installiere die erforderlichen Pakete:

```bash
pip install -r requirements_api.txt
```

2. Stelle sicher, dass die Hauptanforderungen installiert sind:

```bash
pip install -r ../../requirements.txt
```

3. Setze deine OpenAI API-Schlüssel als Umgebungsvariable:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Verwendung

### Server starten

```bash
python chat_api.py
```

Der Server läuft standardmäßig auf `http://localhost:5000`

### API-Endpunkte

#### 1. Health Check

```
GET /health
```

Überprüft den Status der API und des Memory-Systems.

#### 2. Chat mit dem Agent

```
POST /chat
```

Sendet eine Nachricht an den Chat-Agent.

**Request Body:**

```json
{
  "message": "Hallo, wie geht es dir?",
  "session_id": "optional-session-id"
}
```

**Response:**

```json
{
  "response": "Hallo! Mir geht es gut, danke der Nachfrage...",
  "session_id": "uuid-session-id",
  "memory_ids": ["memory-id-1", "memory-id-2"],
  "related_memories_count": 2,
  "timestamp": "2025-06-15T10:30:00"
}
```

#### 3. Memory hinzufügen

```
POST /memory/add
```

Fügt eine neue Erinnerung direkt zum System hinzu.

**Request Body:**

```json
{
  "content": "Der Benutzer mag Pizza",
  "context": "Präferenzen",
  "category": "Benutzer-Info"
}
```

#### 4. Memory durchsuchen

```
POST /memory/search
```

Sucht nach verwandten Erinnerungen.

**Request Body:**

```json
{
  "query": "Was mag der Benutzer?",
  "k": 5
}
```

#### 5. Spezifische Memory abrufen

```
GET /memory/get/<memory_id>
```

Ruft eine bestimmte Erinnerung anhand ihrer ID ab.

#### 6. Session-Verlauf

```
GET /session/<session_id>/history
```

Ruft den Chat-Verlauf für eine bestimmte Session ab.

#### 7. Alle Sessions auflisten

```
GET /sessions
```

Listet alle aktiven Chat-Sessions auf.

#### 8. Memory-Statistiken

```
GET /memory/stats
```

Zeigt Statistiken über das Memory-System an.

## Frontend-Integration

### JavaScript-Beispiel

```javascript
class AgenticMemoryClient {
  constructor(baseUrl = "http://localhost:5000") {
    this.baseUrl = baseUrl;
    this.sessionId = null;
  }

  async sendMessage(message) {
    const response = await fetch(`${this.baseUrl}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: message,
        session_id: this.sessionId,
      }),
    });

    const data = await response.json();
    this.sessionId = data.session_id;
    return data;
  }

  async searchMemories(query, k = 5) {
    const response = await fetch(`${this.baseUrl}/memory/search`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: query,
        k: k,
      }),
    });

    return await response.json();
  }

  async addMemory(content, context = "User Added", category = "Manual") {
    const response = await fetch(`${this.baseUrl}/memory/add`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        content: content,
        context: context,
        category: category,
      }),
    });

    return await response.json();
  }
}

// Verwendung
const client = new AgenticMemoryClient();

// Nachricht senden
client.sendMessage("Hallo, ich bin Max und mag Pizza").then((response) => {
  console.log("Agent:", response.response);
});

// Erinnerungen durchsuchen
client.searchMemories("Was mag Max?").then((response) => {
  console.log("Gefundene Erinnerungen:", response.results);
});
```

### React-Beispiel

```jsx
import React, { useState, useEffect } from "react";

function ChatComponent() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [client] = useState(new AgenticMemoryClient());

  const sendMessage = async () => {
    if (!input.trim()) return;

    // Benutzer-Nachricht hinzufügen
    const userMessage = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);

    try {
      // Nachricht an Agent senden
      const response = await client.sendMessage(input);

      // Agent-Antwort hinzufügen
      const agentMessage = { sender: "agent", text: response.response };
      setMessages((prev) => [...prev, agentMessage]);
    } catch (error) {
      console.error("Fehler beim Senden der Nachricht:", error);
    }

    setInput("");
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>
            <strong>{msg.sender}:</strong> {msg.text}
          </div>
        ))}
      </div>
      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Nachricht eingeben..."
        />
        <button onClick={sendMessage}>Senden</button>
      </div>
    </div>
  );
}

export default ChatComponent;
```

## Konfiguration

Die API verwendet die Konfiguration aus `../config.py`. Du kannst die folgenden Umgebungsvariablen setzen:

- `OPENAI_API_KEY`: Dein OpenAI API-Schlüssel
- Weitere Konfigurationen können in der config.py-Datei angepasst werden

## Produktionsbereitstellung

Für die Produktion verwende Gunicorn:

```bash
gunicorn --bind 0.0.0.0:5000 chat_api:app
```

Oder mit mehr Arbeitsprozessen:

```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 chat_api:app
```

## Fehlerbehandlung

Die API bietet umfassende Fehlerbehandlung und Logging. Alle Endpunkte geben strukturierte JSON-Antworten zurück, auch bei Fehlern.

## CORS-Unterstützung

Die API unterstützt Cross-Origin Resource Sharing (CORS), sodass sie von Frontend-Anwendungen auf verschiedenen Domains verwendet werden kann.
