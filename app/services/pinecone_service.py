from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.configs.model_config import HuggingFace
from app.database import PineconeDatabase
import json
from langchain.schema import Document

def prepare_documents(data: list, chunk_size: int = 768, chunk_overlap: int = 0) -> list[Document]:
    """
    Chia nhỏ văn bản và tạo Document object để insert vào vector store.
    """
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    documents = []

    for item in data:
        chunks = text_splitter.split_text(item["text"])
        for i, chunk in enumerate(chunks):
            metadata = {
                "url": item["url"],
                "title": item["title"],
                "timestamp": item["timestamp"],
                "category": (
                    "Trang chủ" if "trang-chu" in item["url"] or item["url"] == "https://climpingrose.com/"
                    else "Sản phẩm" if "paintings" in item["url"]
                    else "Hướng dẫn thanh toán" if "payment-instruction" in item["url"]
                    else "Hướng dẫn tô" if "paintings/" in item["url"]
                    else "Đánh giá"
                ),
                "content_type": "text",
                "language": "vi",
                "source": "climpingrose.com",
                "chunk_id": f"{item['url']}_chunk_{i}"
            }

            documents.append(Document(page_content=chunk, metadata=metadata))

    return documents


def upsert_documents(documents: list[Document]) -> None:
    """
    Insert các document vào Pinecone thông qua Langchain vectorstore.
    """
    pinecone_db = PineconeDatabase()
    vectorstore = pinecone_db.connect()

    vectorstore.add_documents(documents)
    print(f"✅ Đã upsert {len(documents)} documents vào Pinecone qua Langchain.")


def main():
    with open("./app/database/output.json", "r", encoding="utf-8") as f:
        sample_data = json.load(f)

    print("🔧 Đang chuẩn bị Document...")
    documents = prepare_documents(sample_data, chunk_size=700, chunk_overlap=200)
    print(f"✅ Đã chuẩn bị {len(documents)} documents.")

    print("🚀 Đang upsert vào Pinecone...")
    upsert_documents(documents)
    print("✅ Upsert hoàn tất.")

if __name__ == "__main__":
    main()