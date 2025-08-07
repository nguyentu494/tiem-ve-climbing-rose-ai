from sqlalchemy.orm import Session
import uuid

# --- Phần có sẵn ---
from app.database.base import engine
from app.models.base_model import Base
from app.models.user import User
from app.models.message import ChatMessage, MessageRole
from sqlalchemy import inspect

print("Creating tables...")
print(Base.metadata.tables.keys())
Base.metadata.create_all(engine)
print("Done.")

inspector = inspect(engine)
print("Available tables:", inspector.get_table_names())

# # --- Phần test thêm vào ---
# print("\n=== Running basic ORM tests ===")

# with Session(engine) as session:
#     # Tạo user mới
#     user_id = "f0f7b019-649c-4b11-866e-96bbe63df2ba"

#     # Gắn message cho user
#     message = ChatMessage(user_id=user_id, role=MessageRole.USER, content="Hello from test!")
#     session.add(message)
#     session.commit()
#     print("✅ Inserted test chat message")

#     # Kiểm tra relationship
#     fetched_user = session.get(User, user_id)
#     print(f"📥 User {user_id} has {len(fetched_user.messages)} message(s)")
#     for msg in fetched_user.messages:
#         print("📝", msg.content)
