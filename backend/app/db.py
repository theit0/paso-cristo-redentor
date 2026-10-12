import sqlite3

from app.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS pass_status (
    id INTEGER PRIMARY KEY,
    fetched_at TEXT NOT NULL,        -- UTC ISO
    source_time TEXT,                -- fecha_hora_consulta de la fuente (hora AR)
    estado TEXT,                     -- ABIERTO / CERRADO
    estado_vialidad TEXT,            -- HABILITADA / ...
    horario TEXT,
    horario_cancilleria TEXT,        -- suele indicar apertura parcial ("solo cargas")
    raw TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS forecast (
    id INTEGER PRIMARY KEY,
    fetched_at TEXT NOT NULL,
    location TEXT NOT NULL,
    raw TEXT NOT NULL                -- respuesta completa de Open-Meteo
);
CREATE INDEX IF NOT EXISTS ix_status_fetched ON pass_status(fetched_at);
CREATE INDEX IF NOT EXISTS ix_forecast_fetched ON forecast(location, fetched_at);
"""


# ponytail: sqlite3 de stdlib alcanza para el registrador; pasar a Postgres/SQLAlchemy si hay escrituras concurrentes.
def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn
