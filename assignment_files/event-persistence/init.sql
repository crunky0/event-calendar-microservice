-- Create the events table with the updated structure
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    owner VARCHAR(100) NOT NULL,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    event_date DATE NOT NULL,
    event_type VARCHAR(10) NOT NULL  -- New column to specify if the event is public or private
);
