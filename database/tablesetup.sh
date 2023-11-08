#!/bin/bash

# File path to the .env file in your repository
ENV_FILE="./.env"

# Source the .env file to get the stored secrets
source $ENV_FILE

# Ensure the env variables are set
if [ -z "$PG_HOST" ] || [ -z "$PG_USER" ] || [ -z "$PG_PASS" ]; then
    echo "Error: Missing PostgreSQL login information in .env file."
    exit 1
fi

# Connect to PostgreSQL and set up tables
PGPASSWORD=$PG_PASS psql -h $PG_HOST -U $PG_USER -d cognimesh -a <<EOF

-- Create the vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the 'users' table
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL, -- Considering hashing for security
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create the 'documents' table
CREATE TABLE IF NOT EXISTS documents (
    doc_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_path VARCHAR(255), -- To store the file path of the uploaded file
    file_name VARCHAR(255) DEFAULT '', -- To store the file name
    file_size INT, -- To store the file size in bytes
    file_sha1 VARCHAR(40), -- To store the SHA-1 hash of the file
    vectors_ids UUID[] DEFAULT '{}', -- To store an array of vector UUIDs
    file_extension VARCHAR(10) DEFAULT '', -- To store the file extension
    chunk_size INT DEFAULT 500, -- To store the chunk size
    chunk_overlap INT DEFAULT 0, -- To store the chunk overlap size
    content TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    doi VARCHAR(255), -- To store the DOI of the document
    isbn VARCHAR(17) -- To store the ISBN of the document
);

-- Create the 'vectors' table
CREATE TABLE IF NOT EXISTS vectors (
    vector_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- Changed to UUID to handle unique vector IDs
    doc_id UUID NOT NULL, 
    vector_index INT NOT NULL,
    embeddings VECTOR(1536) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
);

-- Create (or replace) the match_documents function
CREATE OR REPLACE FUNCTION match_documents (
  query_embedding vector(1536),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  id UUID,
  content TEXT,
  similarity FLOAT
)
LANGUAGE SQL STABLE
AS \$\$
  SELECT
    d.doc_id,
    d.content,
    1 - (v.embeddings <=> query_embedding) AS similarity
  FROM documents d
  JOIN vectors v ON d.doc_id = v.doc_id
  WHERE 1 - (v.embeddings <=> query_embedding) > match_threshold
  ORDER BY similarity DESC
  LIMIT match_count;
\$\$;

EOF

# Check the exit status
STATUS=$?
if [ $STATUS -ne 0 ]; then
    echo "Error occurred while setting up the tables."
    exit $STATUS
else
    echo "Tables successfully set up."
fi
