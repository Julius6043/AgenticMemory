-- Update SQL functions to support user filtering
-- This script updates the existing functions to include user_id filtering
-- Drop existing functions
DROP FUNCTION IF EXISTS search_similar_memories(VECTOR(384), FLOAT, INTEGER, UUID);
DROP FUNCTION IF EXISTS hybrid_search_memories(TEXT, VECTOR(384), INTEGER, FLOAT);
-- Function for semantic similarity search with user filtering
CREATE OR REPLACE FUNCTION search_similar_memories(
        query_embedding VECTOR(384),
        similarity_threshold FLOAT DEFAULT 0.5,
        max_results INTEGER DEFAULT 10,
        exclude_memory_id UUID DEFAULT NULL,
        filter_user_id TEXT DEFAULT NULL
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
    AND (
        filter_user_id IS NULL
        OR m.user_id = filter_user_id
    )
ORDER BY m.embedding <=> query_embedding
LIMIT max_results;
END;
$$ LANGUAGE plpgsql;
-- Function for hybrid search with user filtering
CREATE OR REPLACE FUNCTION hybrid_search_memories(
        search_query TEXT,
        query_embedding VECTOR(384) DEFAULT NULL,
        max_results INTEGER DEFAULT 10,
        semantic_weight FLOAT DEFAULT 0.5,
        filter_user_id TEXT DEFAULT NULL
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
WHERE (
        m.content_tsvector @@ plainto_tsquery('english', search_query)
        OR (
            query_embedding IS NOT NULL
            AND m.embedding IS NOT NULL
        )
    )
    AND (
        filter_user_id IS NULL
        OR m.user_id = filter_user_id
    )
ORDER BY score DESC
LIMIT max_results;
END;
$$ LANGUAGE plpgsql;
-- Log completion
DO $$ BEGIN RAISE NOTICE 'Search functions updated successfully with user filtering!';
END $$;