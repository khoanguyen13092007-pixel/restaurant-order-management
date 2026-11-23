"""Repository Pattern: lớp cha dùng chung, mọi repository kế thừa lớp này."""
from app.database import get_db


class BaseRepository:
    table = None  # tên bảng, ví dụ "USER"
    pk = None     # tên cột khoá chính, ví dụ "user_id"

    def _q(self):
        return f'"{self.table}"'

    def get_by_id(self, pk_value):
        return get_db().execute(
            f"SELECT * FROM {self._q()} WHERE {self.pk} = ?", (pk_value,)
        ).fetchone()

    def get_all(self):
        return get_db().execute(f"SELECT * FROM {self._q()}").fetchall()

    def add(self, data):
        cols = ", ".join(data.keys())
        marks = ", ".join("?" for _ in data)
        cur = get_db().execute(
            f"INSERT INTO {self._q()} ({cols}) VALUES ({marks})", tuple(data.values())
        )
        get_db().commit()
        return cur.lastrowid

    def update(self, pk_value, data):
        sets = ", ".join(f"{k} = ?" for k in data)
        get_db().execute(
            f"UPDATE {self._q()} SET {sets} WHERE {self.pk} = ?",
            (*data.values(), pk_value),
        )
        get_db().commit()

    def delete(self, pk_value):
        get_db().execute(f"DELETE FROM {self._q()} WHERE {self.pk} = ?", (pk_value,))
        get_db().commit()
