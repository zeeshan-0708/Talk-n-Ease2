CREATE TABLE interactions (
    id INT AUTO_INCREMENT PRIMARY KEY,    -- Automatically increments for each new record
    user_input TEXT,                      -- Stores the user's input as text
    response TEXT,                         -- Stores the generated response as text
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Automatically stores the time when the record was created
);
