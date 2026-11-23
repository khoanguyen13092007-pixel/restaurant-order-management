from app.database import get_db
from app.models.user import user_from_row
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    table = "USER"
    pk = "user_id"

    def find_by_username(self, username):
        row = get_db().execute(
            'SELECT * FROM "USER" WHERE username = ?', (username,)
        ).fetchone()
        return user_from_row(row) if row else None

    def find_by_id(self, user_id):
        row = self.get_by_id(user_id)
        return user_from_row(row) if row else None
