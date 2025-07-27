from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.configs.model_config import HuggingFace
from app.database import PineconeDatabase

def prepare_data(data: list, chunk_size: int = 768, chunk_overlap: int = 0) -> tuple[list, list]:
    """
    Chia nhỏ văn bản và tạo metadata từ dữ liệu JSON.
    
    Args:
        data (list): Danh sách các mục dữ liệu JSON (url, title, timestamp, text).
        chunk_size (int): Kích thước tối đa của mỗi đoạn văn bản.
        chunk_overlap (int): Độ chồng lấn giữa các đoạn.
    
    Returns:
        tuple: (texts, metadatas) - Danh sách các đoạn văn bản và metadata tương ứng.
    """
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    texts = []
    metadatas = []
    
    for item in data:
        # Chia nhỏ văn bản
        chunks = text_splitter.split_text(item["text"])
        for i, chunk in enumerate(chunks):
            texts.append(chunk)
            # Tạo metadata
            metadata = {
                "url": item["url"],
                "title": item["title"],
                "timestamp": item["timestamp"],
                "category": (
                    "Trang chủ" if "trang-chu" in item["url"] or item["url"] == "https://climpingrose.com/" 
                    else "Sản phẩm" if "paintings" in item["url"] 
                    else "Hướng dẫn thanh toán" if "payment-instruction" in item["url"] 
                    else "Đánh giá"
                ),
                "content_type": "text",
                "language": "vi",
                "source": "climpingrose.com",
                "chunk_id": f"{item['url']}_chunk_{i}"
            }
            # Thêm product_id và price nếu có trong dữ liệu sản phẩm
            if "paintings" in item["url"]:
                metadata["product_id"] = item["url"].split("/")[-1]
                # Giả sử giá được trích xuất từ văn bản (nếu có)
                metadata["price"] = 700 if "¥700" in item["text"] else None
                metadata["tags"] = ["tranh số hóa", "phong cảnh Phật", "bộ màu vẽ"]
            
            metadatas.append(metadata)
    
    return texts, metadatas


def embed_texts(texts: list) -> list:
    """
    Chuyển đổi văn bản thành vector nhúng.
    
    Args:
        texts (list): Danh sách các đoạn văn bản.
        openai_api_key (str): API key của OpenAI.
        model (str): Mô hình nhúng (mặc định text-embedding-ada-002).
    
    Returns:
        list: Danh sách các vector nhúng.
    """
    embeddings = HuggingFace().embeddings()
    vectors = embeddings.embed_documents(texts)
    return vectors

def upsert_to_pinecone(vectors: list, metadatas: list) -> None:
    """
    Đưa dữ liệu vào Pinecone.
    
    Args:
        index (Pinecone.Index): Đối tượng chỉ mục Pinecone.
        vectors (list): Danh sách các vector nhúng.
        metadatas (list): Danh sách metadata tương ứng.
        namespace (str): Namespace trong Pinecone.
    """
    pinecone_db = PineconeDatabase()
    pinecone = pinecone_db.connect()


    records = [
        {
            "id": f"doc_{i}",
            "values": vector,
            "metadata": metadata
        }
        for i, (vector, metadata) in enumerate(zip(vectors, metadatas))
    ]
    
    # Upsert dữ liệu
    pinecone.index.upsert(vectors=records, namespace=pinecone_db._index_name)
    print(f"Đã đưa {len(records)} bản ghi vào Pinecone trong namespace {pinecone_db._index_name}.")