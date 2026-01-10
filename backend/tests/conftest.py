import sys
import os
from unittest.mock import MagicMock
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# バックエンドのパスを先に解決しないと、sys.modules設定後にインポート順序で問題が起きるかもしれないが、
# ここでは「モジュール自体をモック」するので、実際のファイルは読み込まれないようにする。

# Mock youtube_client module
mock_youtube_client_module = MagicMock()
# YouTubeClientクラスのモック
mock_youtube_client_class = MagicMock()
mock_youtube_client_module.YouTubeClient = mock_youtube_client_class
sys.modules["youtube_client"] = mock_youtube_client_module

# Mock summarizer module
mock_summarizer_module = MagicMock()
mock_summarizer_class = MagicMock()
mock_summarizer_module.Summarizer = mock_summarizer_class
sys.modules["summarizer"] = mock_summarizer_module

# テスト用に環境変数をセット
os.environ["YOUTUBE_API_KEY"] = "dummy_youtube_key"
os.environ["GEMINI_API_KEY"] = "dummy_gemini_key"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# backendディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database import Base, get_db

# テスト用DB (SQLite インメモリ)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # テーブル作成
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # テーブル削除
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
