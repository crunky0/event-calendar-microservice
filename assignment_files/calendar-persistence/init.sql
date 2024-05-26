CREATE TABLE IF NOT EXISTS calendar (
    id SERIAL PRIMARY KEY,
    owner VARCHAR(100) UNIQUE NOT NULL,
    event_id_list TEXT[],
    calendar_share_list TEXT[]
);