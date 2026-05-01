import psycopg2
from config import DB_CONFIG

def connect_db():
    connection = psycopg2.connect(
        host=DB_CONFIG["host"],
        database=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        port=DB_CONFIG["port"]
    )

    return connection

def setup_database():
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS game_sessions (
            id SERIAL PRIMARY KEY,
            player_id INTEGER REFERENCES players(id),
            score INTEGER NOT NULL,
            level_reached INTEGER NOT NULL,
            played_at TIMESTAMP DEFAULT NOW()
        )
    """)

    connection.commit()
    cursor.close()
    connection.close()

def get_player_id(username):
    username = username.strip()

    if username == "":
        username = "Player"

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute(
        "INSERT INTO players(username) VALUES (%s) ON CONFLICT (username) DO NOTHING",
        (username,)
    )

    cursor.execute(
        "SELECT id FROM players WHERE username = %s",
        (username,)
    )

    row = cursor.fetchone()
    player_id = row[0]

    connection.commit()
    cursor.close()
    connection.close()

    return player_id

def save_result(username, score, level):
    player_id = get_player_id(username)

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO game_sessions(player_id, score, level_reached)
        VALUES (%s, %s, %s)
        """,
        (player_id, int(score), int(level))
    )

    connection.commit()
    cursor.close()
    connection.close()

def get_personal_best(username):
    username = username.strip()

    if username == "":
        username = "Player"

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COALESCE(MAX(gs.score), 0)
        FROM game_sessions gs
        JOIN players p ON p.id = gs.player_id
        WHERE p.username = %s
        """,
        (username,)
    )

    row = cursor.fetchone()
    best_score = row[0]

    cursor.close()
    connection.close()

    return best_score

def get_leaderboard():
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            p.username,
            gs.score,
            gs.level_reached,
            TO_CHAR(gs.played_at, 'YYYY-MM-DD HH24:MI')
        FROM game_sessions gs
        JOIN players p ON p.id = gs.player_id
        ORDER BY gs.score DESC, gs.played_at ASC
        LIMIT 10
        """
    )

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    return rows
