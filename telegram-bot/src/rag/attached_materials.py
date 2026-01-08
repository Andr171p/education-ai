import logging
import time
from pathlib import Path
from uuid import UUID

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ..core import schemas
from ..database import crud, models
from ..utils import convert_document_to_md

logger = logging.getLogger(__name__)

embeddings = HuggingFaceEmbeddings(
    model_name="deepvk/USER-bge-m3",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": False}
)


async def index_attachments(course_id: UUID, attachment_ids: list[UUID]) -> None:
    collection_name = f"attached-materials-{course_id}"
    vectorstore = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=...,
        use_jsonb=True,
    )
    splitter = RecursiveCharacterTextSplitter(
        chunk_overlap=1200,
        chunk_size=50,
        length_function=len
    )
    for i, attachment_id in enumerate(attachment_ids):
        start_time = time.time()
        logger.info(
            "Start `%s` file processing %s/%s, start time - %s",
            attachment_id, i, len(attachment_ids), start_time
        )
        attachment = await crud.read(
            attachment_id, model_class=models.Attachment, schema_class=schemas.Attachment
        )
        if attachment is None:
            logger.warning("File %s not attached or was removed, skip this", attachment_id)
            continue
        md_text = convert_document_to_md(Path(attachment.filepath))
        logger.info(
            "File %s loaded and converted to Markdown, characters length: %s",
            attachment.original_filename, len(md_text)
        )
        chunks = splitter.split_documents([Document(
            page_content=md_text,
            metadata={
                "course_id": course_id,
                "attachment_id": attachment.id,
                "original_filename": attachment.original_filename,
            }
        )])
        logger.info("Addition %s chunks to %s", len(chunks), collection_name)
        await vectorstore.aadd_documents(chunks)
        execution_time = time.time() - start_time
        logger.info(
            "Successfully processed `%s` file, processing duration - %s seconds",
            attachment.id, execution_time
        )


async def search_materials(course_id: UUID, query: str, top_k: int = 10) -> list[str]:
    collection_name = f"attached-materials-{course_id}"
    vectorstore = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=...,
        use_jsonb=True,
    )
    results = await vectorstore.asimilarity_search_with_score(query, k=top_k)
    return [
        f"""**Attachment-ID:** {document.metadata.get("attachment_id")}
        **Filename:** {document.metadata.get("original_filename")}
        **Relevance score:** {score}
        **Content:**
        {document.page_content}
        """
        for document, score in results
    ]
