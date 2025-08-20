from dotenv import load_dotenv
import os
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langgraph.checkpoint.redis import RedisSaver
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from app.configs.model_config import HuggingFace
from langgraph.checkpoint.base import BaseCheckpointSaver 
from sqlalchemy import inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from app.models.message import ChatMessage
from app.database.base import engine

load_dotenv()

class PostgresDatabase:
    def __init__(self):
        self._url = os.getenv("DATABASE_URL")
        if not self._url:
            raise ValueError("DATABASE_URL is not set in environment variables")
        
        try:
            self._postgres = SQLDatabase.from_uri(self._url)
        except Exception as e:
            raise RuntimeError(f"Failed to connect to database: {e}")
        
        self._run = QuerySQLDatabaseTool(
            db=self._postgres,
            description="Use this tool to query the database"
        )

        self._engine = engine
        self._Session = sessionmaker(bind=self._engine)

    def get_db(self):
        return self._postgres

    def run(self, query: str,) -> str:
        try:
            return self._run.invoke(query)
        except Exception as e:
            return f"❌ Lỗi khi thực thi truy vấn: {e}"

    def get_session(self):
        return self._Session()

    def save_message(self, message: ChatMessage):
        session = self.get_session()
        try:
            session.add(message)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise RuntimeError(f"❌ Lỗi khi lưu message vào database: {e}")
        finally:
            session.close()

    def test_connection(self):
        try:
            inspector = inspect(self._engine)
            tables = inspector.get_table_names()
            print(f"✅ Kết nối thành công. Có {len(tables)} bảng: {tables}")
            print(f"✅ Kết nối thành công. Có {len(tables)} bảng.")
            return tables
        except Exception as e:
            raise RuntimeError(f"❌ Không thể kiểm tra kết nối: {e}")


class RedisDatabase:
    def __init__(self):
        self._redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self._saver = None

    def connect(self) -> BaseCheckpointSaver:
        if not self._saver:
            self._saver = RedisSaver.from_conn_string(self._redis_url).__enter__()
            
            self._saver.setup()
        return self._saver
    
    def delete_by_thread(self, thread_id: str):
        prefixes = ["checkpoint:", "checkpoint_blob:", "checkpoint_write:"]
        for prefix in prefixes:
            key = f"{prefix}{thread_id}"
            self._redis.delete(key)

    def close(self):
        if self._saver:
            self._saver.__exit__(None, None, None)
            self._saver = None

class PineconeDatabase:
    def __init__(self):
        self._api_key = os.getenv("PINECONE_API_KEY")
        self._pc = Pinecone(api_key=self._api_key)
        self._index_name = "climbing-rose-index"
        self._embeddings = HuggingFace().embeddings()

    def connect(self):
        index = self._pc.Index(self._index_name)
        return PineconeVectorStore(
            index=index,
            embedding=self._embeddings,
            distance_strategy="cosine",
        )
    
    def create_index(self):
        if not self._pc.list_indexes():
            self._pc.create_index(
                name=self._index_name,
                dimension=768,  
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
        return self._pc.Index(self._index_name)
    
def test_connection():
    db = PostgresDatabase()
    db.test_connection()

if __name__ == "__main__":
    test_connection()