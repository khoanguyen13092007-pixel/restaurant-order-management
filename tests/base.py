"""Lớp test dùng chung: mỗi test có một DB SQLite tạm, đã seed dữ liệu mẫu."""
import os
import tempfile
import unittest

from app import create_app
from seed import seed

# id trong dữ liệu mẫu (seed.py)
GOI_CUON, PHO, COM_GA, TRA_DA, COM_RANG, MANGO = 1, 2, 3, 4, 5, 6   # COM_RANG is sold out
T01, T02, T03 = 1, 2, 3


class AppTestCase(unittest.TestCase):
    csrf = False

    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.app = create_app({"DATABASE": self.db_path, "TESTING": True,
                               "CSRF_ENABLED": self.csrf})
        with self.app.app_context():
            seed()
        self.client = self.app.test_client()

    def tearDown(self):
        os.remove(self.db_path)

    def login(self, username, password):
        return self.client.post("/login", data={"username": username, "password": password})

    def browser(self, username=None, password=None):
        """Một 'trình duyệt' riêng (cookie riêng), tự gắn token CSRF khi POST."""
        b = Browser(self.app)
        if username:
            b.login(username, password)
        return b


class Browser:
    def __init__(self, app):
        self.client = app.test_client()

    def token(self):
        with self.client.session_transaction() as s:
            return s.get("_csrf", "")

    def get(self, url, **kw):
        return self.client.get(url, **kw)

    def post(self, url, data=None, **kw):
        data = dict(data or {})
        data.setdefault("_csrf", self.token())
        return self.client.post(url, data=data, **kw)

    def login(self, username, password):
        self.client.get("/login")
        r = self.post("/login", {"username": username, "password": password}, follow_redirects=True)
        return r
