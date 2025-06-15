-- =============================================================================
-- AgenticMemory Supabase Database Schema
-- =============================================================================
-- This schema creates the necessary tables and functions for the AgenticMemory system
-- in Supabase. It includes proper indexing, RLS policies, and optimizations.
-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
-- =============================================================================
-- TABLES
-- =============================================================================
-- Main memories table
CREATE TABLE IF NOT EXISTS memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content TEXT NOT NULL,
    context TEXT DEFAULT 'General',
    category TEXT DEFAULT 'Uncategorized',
    keywords TEXT [] DEFAULT '{}',
    tags TEXT [] DEFAULT '{}',
    importance_score REAL DEFAULT 1.0,
    retrieval_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    -- Vector embedding for semantic search (1536 dimensions for OpenAI embeddings)
    embedding VECTOR(384),
    -- Using 384 for all-MiniLM-L6-v2 model
    -- Metadata and evolution tracking
    evolution_count INTEGER DEFAULT 0,
    evolution_history JSONB DEFAULT '[]',
    -- User/session tracking
    user_id TEXT,
    session_id TEXT,
    -- Full-text search
    content_tsvector TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('english', content || ' ' || context)
    ) STORED
);
-- Memory links table for relationships between memories
CREATE TABLE IF NOT EXISTS memory_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    target_memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    link_type TEXT DEFAULT 'related',
    strength REAL DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    -- Prevent duplicate links
    UNIQUE(source_memory_id, target_memory_id, link_type)
);
-- Chat sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT UNIQUE NOT NULL,
    user_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);
-- Chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT NOT NULL,
    message_type TEXT NOT NULL CHECK (message_type IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    -- Related memory IDs
    memory_ids UUID [] DEFAULT '{}',
    -- Metadata
    metadata JSONB DEFAULT '{}'
);
-- Memory statistics table for analytics
CREATE TABLE IF NOT EXISTS memory_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date DATE DEFAULT CURRENT_DATE,
    total_memories INTEGER DEFAULT 0,
    total_retrievals INTEGER DEFAULT 0,
    total_evolutions INTEGER DEFAULT 0,
    categories_breakdown JSONB DEFAULT '{}',
    contexts_breakdown JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    -- Ensure one record per date
    UNIQUE(date)
);
-- =============================================================================
-- INDEXES
-- =============================================================================
-- Performance indexes for memories table
CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memories_user_id ON memories(user_id);
CREATE INDEX IF NOT EXISTS idx_memories_session_id ON memories(session_id);
CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category);
CREATE INDEX IF NOT EXISTS idx_memories_context ON memories(context);
CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance_score DESC);
-- Full-text search index
CREATE INDEX IF NOT EXISTS idx_memories_content_tsvector ON memories USING GIN(content_tsvector);
-- Array indexes for keywords and tags
CREATE INDEX IF NOT EXISTS idx_memories_keywords ON memories USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_memories_tags ON memories USING GIN(tags);
-- Vector similarity index (for semantic search)
CREATE INDEX IF NOT EXISTS idx_memories_embedding ON memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
-- Memory links indexes
CREATE INDEX IF NOT EXISTS idx_memory_links_source ON memory_links(source_memory_id);
CREATE INDEX IF NOT EXISTS idx_memory_links_target ON memory_links(target_memory_id);
-- Chat sessions and messages indexes
CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON chat_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at DESC);
-- =============================================================================
-- FUNCTIONS AND TRIGGERS
-- =============================================================================
-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column() RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = NOW();
RETURN NEW;
END;
$$ language 'plpgsql';
-- Trigger for memories table
CREATE TRIGGER update_memories_updated_at BEFORE
UPDATE ON memories FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
-- Trigger for chat_sessions table
CREATE TRIGGER update_chat_sessions_updated_at BEFORE
UPDATE ON chat_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
-- Function to increment retrieval count
CREATE OR REPLACE FUNCTION increment_retrieval_count(memory_id UUID) RETURNS VOID AS $$ BEGIN
UPDATE memories
SET retrieval_count = retrieval_count + 1,
    last_accessed = NOW()
WHERE id = memory_id;
END;
$$ LANGUAGE plpgsql;
-- Function for semantic similarity search
CREATE OR REPLACE FUNCTION search_similar_memories(
        query_embedding VECTOR(384),
        similarity_threshold FLOAT DEFAULT 0.5,
        max_results INTEGER DEFAULT 10,
        exclude_memory_id UUID DEFAULT NULL
    ) RETURNS TABLE(
        id UUID,
        content TEXT,
        context TEXT,
        category TEXT,
        keywords TEXT [],
        tags TEXT [],
        importance_score REAL,
        similarity FLOAT,
        created_at TIMESTAMP WITH TIME ZONE
    ) AS $$ BEGIN RETURN QUERY
SELECT m.id,
    m.content,
    m.context,
    m.category,
    m.keywords,
    m.tags,
    m.importance_score,
    (1 - (m.embedding <=> query_embedding)) AS similarity,
    m.created_at
FROM memories m
WHERE m.embedding IS NOT NULL
    AND (
        exclude_memory_id IS NULL
        OR m.id != exclude_memory_id
    )
    AND (1 - (m.embedding <=> query_embedding)) >= similarity_threshold
ORDER BY m.embedding <=> query_embedding
LIMIT max_results;
END;
$$ LANGUAGE plpgsql;
-- Function for hybrid search (full-text + semantic)
CREATE OR REPLACE FUNCTION hybrid_search_memories(
        search_query TEXT,
        query_embedding VECTOR(384) DEFAULT NULL,
        max_results INTEGER DEFAULT 10,
        semantic_weight FLOAT DEFAULT 0.5
    ) RETURNS TABLE(
        id UUID,
        content TEXT,
        context TEXT,
        category TEXT,
        keywords TEXT [],
        tags TEXT [],
        importance_score REAL,
        score FLOAT,
        created_at TIMESTAMP WITH TIME ZONE
    ) AS $$ BEGIN RETURN QUERY
SELECT m.id,
    m.content,
    m.context,
    m.category,
    m.keywords,
    m.tags,
    m.importance_score,
    CASE
        WHEN query_embedding IS NOT NULL
        AND m.embedding IS NOT NULL THEN (1 - semantic_weight) * ts_rank(
            m.content_tsvector,
            plainto_tsquery('english', search_query)
        ) + semantic_weight * (1 - (m.embedding <=> query_embedding))
        ELSE ts_rank(
            m.content_tsvector,
            plainto_tsquery('english', search_query)
        )
    END AS score,
    m.created_at
FROM memories m
WHERE m.content_tsvector @@ plainto_tsquery('english', search_query)
    OR (
        query_embedding IS NOT NULL
        AND m.embedding IS NOT NULL
    )
ORDER BY score DESC
LIMIT max_results;
END;
$$ LANGUAGE plpgsql;
-- Function to get memory statistics
CREATE OR REPLACE FUNCTION get_memory_statistics() RETURNS JSONB AS $$
DECLARE stats JSONB;
BEGIN
SELECT jsonb_build_object(
        'total_memories',
        COUNT(*),
        'total_retrievals',
        SUM(retrieval_count),
        'total_evolutions',
        SUM(evolution_count),
        'categories',
        jsonb_object_agg(category, category_count),
        'contexts',
        jsonb_object_agg(context, context_count),
        'avg_importance',
        AVG(importance_score),
        'last_updated',
        NOW()
    ) INTO stats
FROM (
        SELECT category,
            context,
            retrieval_count,
            evolution_count,
            importance_score,
            COUNT(*) OVER (PARTITION BY category) AS category_count,
            COUNT(*) OVER (PARTITION BY context) AS context_count
        FROM memories
    ) subquery;
RETURN stats;
END;
$$ LANGUAGE plpgsql;
-- =============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =============================================================================
-- Enable RLS on all tables
ALTER TABLE memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_stats ENABLE ROW LEVEL SECURITY;
-- Policies for memories table
CREATE POLICY "Users can view their own memories" ON memories FOR
SELECT USING (
        auth.uid()::text = user_id
        OR user_id IS NULL
    );
CREATE POLICY "Users can insert their own memories" ON memories FOR
INSERT WITH CHECK (
        auth.uid()::text = user_id
        OR user_id IS NULL
    );
CREATE POLICY "Users can update their own memories" ON memories FOR
UPDATE USING (
        auth.uid()::text = user_id
        OR user_id IS NULL
    );
CREATE POLICY "Users can delete their own memories" ON memories FOR DELETE USING (
    auth.uid()::text = user_id
    OR user_id IS NULL
);
-- Policies for memory_links table
CREATE POLICY "Users can view their own memory links" ON memory_links FOR
SELECT USING (
        EXISTS (
            SELECT 1
            FROM memories m
            WHERE (
                    m.id = source_memory_id
                    OR m.id = target_memory_id
                )
                AND (
                    auth.uid()::text = m.user_id
                    OR m.user_id IS NULL
                )
        )
    );
CREATE POLICY "Users can insert their own memory links" ON memory_links FOR
INSERT WITH CHECK (
        EXISTS (
            SELECT 1
            FROM memories m
            WHERE (
                    m.id = source_memory_id
                    OR m.id = target_memory_id
                )
                AND (
                    auth.uid()::text = m.user_id
                    OR m.user_id IS NULL
                )
        )
    );
-- Policies for chat tables
CREATE POLICY "Users can view their own chat sessions" ON chat_sessions FOR
SELECT USING (
        auth.uid()::text = user_id
        OR user_id IS NULL
    );
CREATE POLICY "Users can insert their own chat sessions" ON chat_sessions FOR
INSERT WITH CHECK (
        auth.uid()::text = user_id
        OR user_id IS NULL
    );
CREATE POLICY "Users can view their own chat messages" ON chat_messages FOR
SELECT USING (
        EXISTS (
            SELECT 1
            FROM chat_sessions cs
            WHERE cs.session_id = chat_messages.session_id
                AND (
                    auth.uid()::text = cs.user_id
                    OR cs.user_id IS NULL
                )
        )
    );
CREATE POLICY "Users can insert their own chat messages" ON chat_messages FOR
INSERT WITH CHECK (
        EXISTS (
            SELECT 1
            FROM chat_sessions cs
            WHERE cs.session_id = chat_messages.session_id
                AND (
                    auth.uid()::text = cs.user_id
                    OR cs.user_id IS NULL
                )
        )
    );
-- Public access to memory_stats (for analytics)
CREATE POLICY "Anyone can view memory stats" ON memory_stats FOR
SELECT USING (true);
-- =============================================================================
-- SAMPLE DATA (Optional - for testing)
-- =============================================================================
-- Insert sample memories for testing
INSERT INTO memories (
        content,
        context,
        category,
        keywords,
        tags,
        user_id
    )
VALUES (
        'The user enjoys learning about artificial intelligence and machine learning',
        'User Preferences',
        'Personal',
        ARRAY ['AI', 'machine learning', 'learning'],
        ARRAY ['interests', 'technology'],
        'sample_user'
    ),
    (
        'Python is a versatile programming language used for data science',
        'Technical Knowledge',
        'Programming',
        ARRAY ['Python', 'programming', 'data science'],
        ARRAY ['programming', 'languages'],
        'sample_user'
    ),
    (
        'The weather today is sunny and warm, perfect for outdoor activities',
        'Daily Life',
        'Weather',
        ARRAY ['weather', 'sunny', 'outdoor'],
        ARRAY ['daily', 'activities'],
        'sample_user'
    );
-- Create sample chat session
INSERT INTO chat_sessions (session_id, user_id)
VALUES ('sample_session_001', 'sample_user');
-- =============================================================================
-- VIEWS (Optional - for easier querying)
-- =============================================================================
-- View for memory details with link counts
CREATE OR REPLACE VIEW memory_details AS
SELECT m.*,
    COALESCE(link_counts.outgoing_links, 0) AS outgoing_links,
    COALESCE(link_counts.incoming_links, 0) AS incoming_links,
    COALESCE(link_counts.total_links, 0) AS total_links
FROM memories m
    LEFT JOIN (
        SELECT memory_id,
            SUM(outgoing) AS outgoing_links,
            SUM(incoming) AS incoming_links,
            SUM(outgoing + incoming) AS total_links
        FROM (
                SELECT source_memory_id AS memory_id,
                    COUNT(*) AS outgoing,
                    0 AS incoming
                FROM memory_links
                GROUP BY source_memory_id
                UNION ALL
                SELECT target_memory_id AS memory_id,
                    0 AS outgoing,
                    COUNT(*) AS incoming
                FROM memory_links
                GROUP BY target_memory_id
            ) link_summary
        GROUP BY memory_id
    ) link_counts ON m.id = link_counts.memory_id;
-- =============================================================================
-- COMPLETION MESSAGE
-- =============================================================================
-- Log completion
DO $$ BEGIN RAISE NOTICE 'AgenticMemory database schema created successfully!';
RAISE NOTICE 'Tables created: memories, memory_links, chat_sessions, chat_messages, memory_stats';
RAISE NOTICE 'Functions created: search_similar_memories, hybrid_search_memories, get_memory_statistics';
RAISE NOTICE 'RLS policies enabled for all tables';
RAISE NOTICE 'Ready for AgenticMemory integration!';
END $$;