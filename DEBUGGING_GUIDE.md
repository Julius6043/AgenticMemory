# Supabase Integration Debugging Guide

## Identifizierte Probleme und Lösungen

### 1. **LLM Controller Zugriff Fehler**

**Problem**: `llm_controller.llm.get_completion()` - doppelter `.llm` Zugriff
**Lösung**: Korrigiert zu `llm_controller.get_completion()`

### 2. **Embedding Speicherung**

**Problem**: Embeddings werden nicht korrekt als PostgreSQL Vector gespeichert
**Lösung**: Konvertierung zu String-Format `[1.0,2.0,3.0]` für PostgreSQL vector type

### 3. **RPC Funktionen**

**Problem**: RPC-Funktionen `search_similar_memories` und `hybrid_search_memories` existieren möglicherweise nicht
**Lösung**: Fallback auf Text-Suche wenn RPC fehlschlägt

### 4. **Chat Session Erstellung**

**Problem**: Chat-Nachrichten werden ohne Session-Erstellung gespeichert
**Lösung**: Automatische Session-Erstellung vor Nachrichten-Speicherung

### 5. **Memory Statistics**

**Problem**: RPC-Funktion `get_memory_statistics` existiert nicht
**Lösung**: Implementierung über direkte SQL-Abfragen

## Debugging-Schritte

### 1. Umgebungsvariablen prüfen

```bash
# Windows
echo %SUPABASE_URL%
echo %SUPABASE_ANON_KEY%
echo %SUPABASE_SERVICE_ROLE_KEY%
echo %OPENAI_API_KEY%

# Linux/Mac
echo $SUPABASE_URL
echo $SUPABASE_ANON_KEY
echo $SUPABASE_SERVICE_ROLE_KEY
echo $OPENAI_API_KEY
```

### 2. Debug-Script ausführen

```bash
python debug_supabase.py
```

### 3. Supabase-Datenbank prüfen

1. Gehen Sie zu [Supabase Dashboard](https://app.supabase.com)
2. Öffnen Sie Ihr Projekt
3. Gehen Sie zu "SQL Editor"
4. Prüfen Sie die Tabellen:
   ```sql
   SELECT * FROM memories LIMIT 5;
   SELECT * FROM chat_sessions LIMIT 5;
   SELECT * FROM chat_messages LIMIT 5;
   ```

### 4. Vector Extension prüfen

```sql
-- Prüfen ob Vector Extension installiert ist
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Prüfen ob Embedding-Spalte existiert
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'memories' AND column_name = 'embedding';
```

### 5. API-Tests ausführen

```bash
# Server starten
python src/api/start_server.py

# In anderem Terminal - Tests ausführen
python src/api/test_supabase_api.py
```

## Häufige Probleme und Lösungen

### Problem: "Vector extension not found"

**Lösung**: In Supabase SQL Editor ausführen:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Problem: "Table does not exist"

**Lösung**: Schema aus `supabase_schema.sql` ausführen:

```bash
# Kopieren Sie den Inhalt von src/database/supabase_schema.sql
# und führen Sie ihn in Supabase SQL Editor aus
```

### Problem: "Embedding not stored"

**Lösung**: Prüfen Sie die Embedding-Dimension:

```sql
-- Prüfen der Embedding-Spalte
SELECT embedding FROM memories WHERE embedding IS NOT NULL LIMIT 1;
```

### Problem: "RPC function does not exist"

**Lösung**: Funktionen aus `supabase_schema.sql` ausführen:

```sql
-- Alle Funktionen aus der Schema-Datei kopieren und ausführen
```

### Problem: "Authentication failed"

**Lösung**:

1. Prüfen Sie die Row Level Security (RLS) Policies
2. Temporär RLS deaktivieren für Tests:
   ```sql
   ALTER TABLE memories DISABLE ROW LEVEL SECURITY;
   ```

## Verbesserungsvorschläge

1. **Bessere Fehlerbehandlung**: Mehr detaillierte Fehlermeldungen
2. **Retry-Mechanismus**: Automatische Wiederholung bei temporären Fehlern
3. **Connection Pooling**: Bessere Verbindungsverwaltung
4. **Logging**: Strukturiertes Logging für bessere Debugging
5. **Monitoring**: Überwachung der Supabase-Performance

## Nächste Schritte

1. Führen Sie `debug_supabase.py` aus
2. Beheben Sie die identifizierten Probleme
3. Testen Sie die API mit `test_supabase_api.py`
4. Überwachen Sie die Logs für weitere Probleme

## Kontakt

Bei weiteren Problemen prüfen Sie:

- Supabase-Dokumentation: https://supabase.com/docs
- AgenticMemory GitHub Issues
- Supabase Discord Community
