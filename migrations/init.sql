CREATE TABLE users(
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL, 
    username TEXT, 
    first_name TEXT, 
    last_name TEXT, 
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_messages(
    id SERIAL PRIMARY KEY, 
    user_id INT REFERENCES users(id) ON DELETE CASCADE, 
    message_text TEXT NOT NULL, 
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bot_responses( 
    id SERIAL PRIMARY KEY, 
    user_message_id INT REFERENCES user_messages(id) ON DELETE CASCADE, 
    response_text TEXT NOT NULL, 
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
