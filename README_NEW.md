# AgenticMemory - Intelligentes Gedächtnissystem

Ein erweiterbares, KI-gestütztes Gedächtnissystem mit automatischer Metadatenextraktion und selbst-evolvierenden Erinnerungsnetzen.

## Features

- 🧠 **Intelligente Gedächtnisnotizen** mit automatischer Metadatenanalyse
- 🔗 **Selbst-evolvierende Netzwerke** durch LLM-gestützte Verbindungsbildung
- 🔍 **Hybride Suche** (BM25 + semantische Ähnlichkeit)
- 🤖 **Multi-LLM Support** (OpenAI, Ollama)
- 💾 **Persistierung** und Caching von Embeddings
- 📊 **Erweiterbares Design** mit modularer Architektur

## Neue Projektstruktur

```
AgenticMemory/
├── src/                          # Hauptpaket
│   ├── __init__.py              # Paket-Initialisierung
│   ├── memory.py                # Kern-Gedächtnisklassen
│   ├── llm_controllers.py       # LLM Backend-Controller
│   ├── retrievers.py            # Such- und Indizierungssysteme
│   ├── utils.py                 # Hilfsfunktionen
│   └── config.py                # Konfigurationseinstellungen
├── examples/                     # Verwendungsbeispiele
│   ├── basic_usage.py           # Grundlegende Nutzung
│   └── advanced_usage.py        # Erweiterte Demonstrationen
├── tests/                        # Unit Tests
│   └── test_memory_system.py    # Haupttests
├── data/                         # Datenverzeichnis
├── Figure/                       # Dokumentationsbilder
├── requirements.txt              # Python-Abhängigkeiten
├── README.md                     # Diese Datei
└── memory_layer.py              # Original (deprecated)
```

## Installation

```bash
# Repository klonen
git clone <repository-url>
cd AgenticMemory

# Abhängigkeiten installieren
pip install -r requirements.txt

# Umgebungsvariablen setzen (für OpenAI)
export OPENAI_API_KEY="your-api-key-here"
```

## Schnellstart

### Grundlegende Nutzung

```python
from src import AgenticMemorySystem

# System initialisieren
memory_system = AgenticMemorySystem(
    llm_backend="openai",
    llm_model="gpt-4o-mini"
)

# Erinnerungen hinzufügen
memory_id = memory_system.add_note(
    "Neuronale Netze bestehen aus Schichten von Neuronen."
)

# Verwandte Erinnerungen finden
related = memory_system.get_related_memories(
    "Wie funktionieren neuronale Netze?", 
    k=3
)

for memory in related:
    print(f"Inhalt: {memory.content}")
    print(f"Tags: {memory.tags}")
```

### Erweiterte Nutzung

```python
from src import AgenticMemorySystem, MemoryNote

# System mit benutzerdefinierten Einstellungen
memory_system = AgenticMemorySystem(
    model_name="all-MiniLM-L6-v2",
    llm_backend="openai",
    evo_threshold=50  # Evolution alle 50 Hinzufügungen
)

# Manuelle Erinnerungserstellung
note = MemoryNote(
    content="Deep Learning verwendet mehrschichtige neuronale Netze.",
    keywords=["deep learning", "neural networks", "layers"],
    tags=["AI", "machine learning", "technology"],
    importance_score=2.5
)

# Erinnerung zum System hinzufügen
memory_id = memory_system.add_note(note.content)
```

## Hauptkomponenten

### 1. MemoryNote
- Grundlegende Gedächtniseinheit mit Metadaten
- Automatische LLM-basierte Inhaltsanalyse
- Unterstützt Keywords, Tags, Kontext und Verbindungen

### 2. AgenticMemorySystem
- Haupt-Gedächtnismanagementsystem
- Automatische Evolution und Konsolidierung
- Hybrid-Suche für verwandte Erinnerungen

### 3. LLM Controllers
- `OpenAIController`: Integration mit OpenAI GPT-Modellen
- `OllamaController`: Support für lokale Ollama-Modelle
- `LLMController`: Factory-Klasse für Backend-Auswahl

### 4. Retriever
- `SimpleEmbeddingRetriever`: Reine semantische Suche
- `HybridRetriever`: Kombination aus BM25 und semantischer Suche

## Beispiele ausführen

```bash
# Grundlegende Verwendung
python examples/basic_usage.py

# Erweiterte Demonstrationen
python examples/advanced_usage.py

# Tests ausführen
python -m pytest tests/ -v
```

## Konfiguration

Umgebungsvariablen:
- `OPENAI_API_KEY`: OpenAI API-Schlüssel für GPT-Modelle

Konfigurierbare Parameter:
- `model_name`: Sentence Transformer Modell
- `llm_backend`: "openai" oder "ollama"
- `llm_model`: Spezifisches Modell (z.B. "gpt-4o-mini")
- `evo_threshold`: Schwellenwert für Gedächtniskonsolidierung

## Erweiterte Features

### Gedächtnisevolution
Das System analysiert neue Erinnerungen im Kontext existierender Nachbarn und kann:
- Verbindungen zwischen verwandten Erinnerungen stärken
- Metadaten basierend auf Beziehungen aktualisieren
- Kategorien und Tags automatisch verfeinern

### Persistierung
```python
from examples.advanced_usage import MemoryPersistence

# Gedächtnissystem speichern
MemoryPersistence.save_memories(memory_system, "my_memories.json")

# Gedächtnissystem laden
loaded_system = MemoryPersistence.load_memories("my_memories.json")
```

### Hybrid-Suche
Kombiniert keyword-basierte (BM25) und semantische Suche für optimale Ergebnisse:

```python
from src import HybridRetriever

retriever = HybridRetriever(alpha=0.7)  # 70% semantisch, 30% keyword
retriever.add_documents(documents)
results = retriever.retrieve("query", k=5)
```

## Entwicklung

### Neue Retriever hinzufügen
```python
from src.retrievers import SimpleEmbeddingRetriever

class CustomRetriever(SimpleEmbeddingRetriever):
    def __init__(self, custom_param):
        super().__init__()
        self.custom_param = custom_param
    
    def custom_search_method(self, query):
        # Implementierung
        pass
```

### Neue LLM-Backends hinzufügen
```python
from src.llm_controllers import BaseLLMController

class CustomLLMController(BaseLLMController):
    def get_completion(self, prompt, response_format, temperature=0.7):
        # Backend-spezifische Implementierung
        pass
```

## Lizenz

Siehe LICENSE-Datei für Details.

## Beiträge

Beiträge sind willkommen! Bitte erstellen Sie einen Pull Request oder öffnen Sie ein Issue für Diskussionen.
