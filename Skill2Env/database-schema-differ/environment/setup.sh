# none — task and verifier use only python3 stdlib (sqlite3); the skill script is pure stdlib.
python3 -c "import sqlite3; print('sqlite', sqlite3.sqlite_version)" >/dev/null
