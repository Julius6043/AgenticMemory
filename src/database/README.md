# Supabase Integration für AgenticMemory

Diese Integration ermöglicht es, das AgenticMemory-System mit Supabase als persistentes Backend zu verwenden, anstatt lokale Speicherung zu nutzen.

## 🚀 Features

- **Persistente Speicherung**: Memories werden in einer Supabase PostgreSQL-Datenbank gespeichert
- **Vektorsuch**: Semantische Suche mit pgvector-Erweiterung
- **Benutzer-Isolation**: Multi-User-Unterstützung mit Row Level Security (RLS)
- **Chat-Verlauf**: Vollständige Chat-Session-Verwaltung
- **Statistiken**: Umfassende Analytics und Reporting
- **Backup/Restore**: Vollständige Backup- und Wiederherstellungstools
- **Migration**: Tools zum Migrieren von lokalen Daten

## 📋 Voraussetzungen

1. **Supabase-Projekt**: Erstellen Sie ein kostenloses Konto bei [supabase.com](https://supabase.com)
2. **Python 3.8+**: Mit den erforderlichen Paketen
3. **Umgebungsvariablen**: Konfiguration der Supabase-Verbindung

## 🛠 Installation

### 1. Pakete installieren

```bash
pip install -r requirements_supabase.txt
```

### 2. Supabase-Projekt einrichten

1. Gehen Sie zu [app.supabase.com](https://app.supabase.com)
2. Erstellen Sie ein neues Projekt
3. Warten Sie, bis das Projekt vollständig eingerichtet ist
4. Führen Sie das Schema-Setup aus (siehe unten)

### 3. Datenbank-Schema erstellen

Führen Sie das SQL-Schema in Ihrem Supabase-Projekt aus:

1. Gehen Sie zu Ihrem Supabase Dashboard
2. Klicken Sie auf "SQL Editor"
3. Erstellen Sie eine neue Query
4. Kopieren Sie den Inhalt von `supabase_schema.sql` und führen Sie ihn aus

```sql
-- Der gesamte Inhalt von supabase_schema.sql hier einfügen
```

### 4. Umgebungsvariablen konfigurieren

Erstellen Sie eine `.env`-Datei im Projekt-Root:

```env
# Supabase Konfiguration
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_DB_PASSWORD=your_database_password

# OpenAI (für LLM)
OPENAI_API_KEY=sk-...
```

**So finden Sie diese Werte:**

1. **SUPABASE_URL & KEYS**:

   - Dashboard → Settings → API
   - Kopieren Sie URL und anon/service_role keys

2. **SUPABASE_DB_PASSWORD**:
   - Dashboard → Settings → Database
   - Kopieren oder setzen Sie das Database-Passwort

## 🎯 Verwendung

### Grundlegende Verwendung

```python
from src.database.supabase_memory_adapter import SupabaseAgenticMemorySystem

# Memory System initialisieren
memory_system = SupabaseAgenticMemorySystem(
    user_id="your_user_id",  # Für Multi-User-Isolation
    llm_backend="openai",
    llm_model="gpt-4o-mini"
)

# Memory hinzufügen
memory_id = memory_system.add_note(
    content="Der Benutzer mag Pizza und italienisches Essen",
    context="Benutzer-Präferenzen",
    category="Food"
)

# Related Memories finden
related = memory_system.get_related_memories("Was mag der Benutzer?", k=5)

# Memory suchen
results = memory_system.search_memories("italienisches Essen")
```

### Mit Flask API verwenden

```python
# In chat_api.py - Supabase Backend verwenden
from src.database.supabase_memory_adapter import SupabaseAgenticMemorySystem

def initialize_memory_system():
    global memory_system

    # Supabase-basiertes Memory System verwenden
    memory_system = SupabaseAgenticMemorySystem(
        model_name=Config.DEFAULT_EMBEDDING_MODEL,
        llm_backend=Config.DEFAULT_LLM_BACKEND,
        llm_model=Config.DEFAULT_LLM_MODEL,
        evo_threshold=Config.DEFAULT_EVO_THRESHOLD,
        api_key=Config.get_openai_key(),
        user_id="api_user"  # Oder dynamisch basierend auf Session
    )
```

### Direkter Supabase-Client

```python
from src.database.supabase_client import SupabaseMemoryClient

# Direkter Client für erweiterte Operationen
client = SupabaseMemoryClient()

# Memory erstellen
memory_id = client.create_memory(
    content="Wichtige Information",
    embedding=[0.1, 0.2, ...],  # 384-dimensionaler Vektor
    context="Business",
    keywords=["wichtig", "business"],
    user_id="user123"
)

# Semantische Suche
results = client.search_memories_by_embedding(
    embedding=query_embedding,
    similarity_threshold=0.7,
    limit=10
)

# Hybrid-Suche (Text + Semantik)
results = client.hybrid_search_memories(
    query="Geschäftsstrategie",
    embedding=query_embedding,
    semantic_weight=0.6
)
```

## 🔧 Erweiterte Features

### Migration von lokalen Daten

```python
from src.database.supabase_utils import SupabaseMigrationTool
from src.memory import AgenticMemorySystem

# Lokales System laden
local_system = AgenticMemorySystem()
# ... lokale Daten laden ...

# Migration durchführen
migration_tool = SupabaseMigrationTool(client)
results = migration_tool.migrate_local_memories_to_supabase(
    local_system,
    user_id="migrated_user"
)

print(f"Migriert: {results['migrated_memories']} Memories")
```

### Backup und Restore

```python
from src.database.supabase_utils import SupabaseBackupTool

backup_tool = SupabaseBackupTool(client)

# Backup erstellen
backup_results = backup_tool.create_backup(
    backup_path="./backups/2025-06-15",
    user_id="user123",
    include_chat_history=True
)

# Backup wiederherstellen
restore_results = backup_tool.restore_backup(
    backup_path="./backups/2025-06-15",
    user_id="restored_user",
    overwrite_existing=False
)
```

### Wartung und Optimierung

```python
from src.database.supabase_utils import SupabaseMaintenanceTool

maintenance_tool = SupabaseMaintenanceTool(client)

# Alte Memories bereinigen
cleanup_results = maintenance_tool.cleanup_old_memories(
    days_old=365,
    min_retrieval_count=1,
    dry_run=False
)

# Embeddings optimieren
optimization_results = maintenance_tool.optimize_embeddings()

# Statistiken abrufen
stats = maintenance_tool.get_database_statistics()
```

## 📊 Datenbank-Schema

### Haupttabellen

- **`memories`**: Haupt-Memory-Tabelle mit Vektorindizierung
- **`memory_links`**: Verbindungen zwischen Memories
- **`chat_sessions`**: Chat-Session-Verwaltung
- **`chat_messages`**: Einzelne Chat-Nachrichten
- **`memory_stats`**: Aggregierte Statistiken

### Indizes und Optimierung

- **Vektor-Index**: IVFFlat für schnelle Ähnlichkeitssuche
- **Full-Text-Index**: GIN-Index für Textsuche
- **Array-Indizes**: Für Keywords und Tags
- **Performance-Indizes**: Für häufige Abfragen

## 🔒 Sicherheit

### Row Level Security (RLS)

- **Benutzer-Isolation**: Benutzer sehen nur ihre eigenen Daten
- **API-basierte Authentifizierung**: Sichere Token-basierte Zugriffe
- **Service-Role**: Für Admin-Operationen

### Datenschutz

- **EU-Server**: Supabase unterstützt EU-Hosting
- **Verschlüsselung**: Daten werden verschlüsselt übertragen und gespeichert
- **Backup-Encryption**: Backups können verschlüsselt werden

## 🚀 Performance

### Optimierungen

- **Verbindungs-Pooling**: Effiziente Datenbankverbindungen
- **Batch-Operationen**: Bulk-Inserts für bessere Performance
- **Caching**: Memory-Cache für häufig verwendete Daten
- **Lazy Loading**: Memories werden bei Bedarf geladen

### Monitoring

```python
# Performance-Statistiken
stats = client.get_memory_statistics()
print(f"Total Memories: {stats['total_memories']}")
print(f"Average Retrieval Count: {stats['avg_retrieval_count']}")

# Beliebte Memories
popular = client.get_popular_memories(limit=10)
```

## 🐛 Troubleshooting

### Häufige Probleme

1. **Verbindungsfehler**:

   ```python
   # Connection testen
   if not client.test_connection():
       print("Supabase-Verbindung fehlgeschlagen!")
   ```

2. **Schema-Probleme**:

   ```sql
   -- Überprüfen ob Tabellen existieren
   SELECT table_name FROM information_schema.tables
   WHERE table_schema = 'public' AND table_name LIKE 'memories%';
   ```

3. **Embedding-Dimensionen**:
   ```python
   # Sicherstellen, dass Embedding-Dimensionen übereinstimmen
   # Standard: 384 für all-MiniLM-L6-v2
   ```

### Debugging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Detaillierte Logs für Supabase-Operationen
```

## 📈 Skalierung

### Horizontal Scaling

- **Read Replicas**: Für bessere Leseperformance
- **Connection Pooling**: pgBouncer für viele gleichzeitige Verbindungen
- **CDN**: Für statische Inhalte

### Vertikal Scaling

- **Compute-Upgrade**: Mehr CPU/RAM für Supabase-Instanz
- **Storage-Upgrade**: Mehr Speicherplatz für große Datensätze
- **Dedicated Resources**: Für High-Performance-Anwendungen

## 🤝 Beitrag leisten

1. Fork das Repository
2. Erstellen Sie einen Feature-Branch
3. Implementieren Sie Verbesserungen
4. Fügen Sie Tests hinzu
5. Erstellen Sie einen Pull Request

## 📄 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert.

## 🆘 Support

- **GitHub Issues**: Für Bugs und Feature-Requests
- **Supabase Docs**: [supabase.com/docs](https://supabase.com/docs)
- **AgenticMemory Docs**: Siehe Haupt-README

---

## 🎉 Erste Schritte

1. **Setup prüfen**:

   ```python
   from src.database.supabase_utils import setup_supabase_environment

   if setup_supabase_environment():
       print("✅ Supabase ist bereit!")
   ```

2. **Erstes Memory erstellen**:

   ```python
   from src.database.supabase_utils import get_supabase_memory_system

   system = get_supabase_memory_system("test_user")
   memory_id = system.add_note("Hallo Supabase!")
   print(f"Memory erstellt: {memory_id}")
   ```

3. **API starten mit Supabase**:

   ```bash
   # Umgebungsvariablen setzen
   export SUPABASE_URL="..."
   export SUPABASE_ANON_KEY="..."

   # API starten
   python src/api/chat_api.py
   ```

Viel Erfolg mit Ihrer Supabase-Integration! 🚀
