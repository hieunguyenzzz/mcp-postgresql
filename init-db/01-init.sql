-- Create a sample schema for testing purposes
-- This will be automatically applied when the Docker container starts

-- Create a test table for users
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create a test table for posts
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create a test table for comments
CREATE TABLE IF NOT EXISTS comments (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for common queries
CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts(user_id);
CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id);
CREATE INDEX IF NOT EXISTS idx_comments_user_id ON comments(user_id);

-- Insert sample data for testing
INSERT INTO users (username, email, password_hash) VALUES
    ('alice', 'alice@example.com', 'hashed_password_1'),
    ('bob', 'bob@example.com', 'hashed_password_2'),
    ('charlie', 'charlie@example.com', 'hashed_password_3')
ON CONFLICT (username) DO NOTHING;

-- Get the IDs we just inserted (or that already existed)
WITH user_ids AS (
    SELECT id FROM users WHERE username IN ('alice', 'bob', 'charlie')
)
INSERT INTO posts (title, content, user_id)
SELECT
    'Sample Post ' || gs || ' by ' || u.username,
    'This is the content of sample post ' || gs || ' written by ' || u.username,
    u.id
FROM
    generate_series(1, 3) AS gs,
    users u
WHERE
    u.username IN ('alice', 'bob')
ON CONFLICT DO NOTHING;

-- Add some comments
WITH post_ids AS (
    SELECT id FROM posts LIMIT 3
),
user_ids AS (
    SELECT id FROM users WHERE username IN ('alice', 'bob', 'charlie')
)
INSERT INTO comments (content, post_id, user_id)
SELECT
    'This is a sample comment ' || gs || ' on this post by ' || u.username,
    p.id,
    u.id
FROM
    generate_series(1, 2) AS gs,
    post_ids p,
    user_ids u
ON CONFLICT DO NOTHING; 