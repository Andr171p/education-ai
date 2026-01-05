import logging
from pathlib import Path
from uuid import UUID

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from ..core import schemas
from ..database import crud, models
from ..settings import QDRANT_PATH, settings
from ..utils import convert_document_to_md

logger = logging.getLogger(__name__)

client = QdrantClient(path=str(QDRANT_PATH))

embeddings = HuggingFaceEmbeddings(
    model_name="deepvk/USER-bge-m3",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": False},
)


async def index_documents(attachment_ids: list[UUID]) -> list[Document]:
    """Выполнение процесса индексации документа:
        - Преобразование в Markdown формат.
        - Обогащение метаданными.
        - Рекурсивное разбиение на чанки.

    :param attachment_ids: Идентификаторы сохранённых файлов.
    :returns: Массив Langchain Document с метаданными.
    """

    documents: list[Document] = []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.rag.chunk_size,
        chunk_overlap=settings.rag.chunk_overlap,
        length_function=len
    )
    for attachment_id in attachment_ids:
        attachment = await crud.read(
            attachment_id, model_class=models.AttachmentModel, schema_class=schemas.Attachment
        )
        if attachment is None:
            raise RuntimeError(f"Attachment {attachment_id} is not loaded!")
        logger.info("Start Markdown convertion for %s file", attachment.original_filename)
        md_text = convert_document_to_md(Path(attachment.filepath))
        logger.info(
            "Conversion to Markdown done for %s file, total text length: %s!",
            attachment.original_filename, len(md_text)
        )
        documents.append(Document(
            page_content=md_text,
            metadata={
                "original_filename": attachment.original_filename,
                "filepath": attachment.filepath,
            }
        ))
    return splitter.split_documents(documents)


async def persist_documents(user_id: int, documents: list[Document]) -> None:
    collection_name = f"materials-{user_id}"
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
        )
        logger.info("Collection %s created!", collection_name)
    vectorstore = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )
    logger.info("Start save %s documents to vector store.", len(documents))
    await vectorstore.aadd_documents(documents)
    logger.info("Documents saved!")


async def search_documents(user_id: int, query: str, top_k: int = 10) -> list[Document]:
    collection_name = f"materials-{user_id}"
    vectorstore = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )
    return await vectorstore.asimilarity_search(query, k=top_k)
