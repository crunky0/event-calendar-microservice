-- Create the invites table
CREATE TABLE IF NOT EXISTS invites (
    id SERIAL PRIMARY KEY,
    event_id INTEGER NOT NULL,
    username VARCHAR(100) NOT NULL,
    invitation_status VARCHAR(30) DEFAULT 'Pending'
);
