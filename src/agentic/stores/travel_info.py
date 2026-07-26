import asyncio
from typing import Sequence

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_core.vectorstores import VectorStoreRetriever

from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.vectorstores import Chroma


from agentic.util.util import load_cred

UK_DESTINATIONS = [
    "Cornwall",
    "North_Cornwall",
    "South_Cornwall",
    "West_Cornwall",
]


async def _build_vectorstore(destinations: Sequence[str]) -> Chroma:
    """Download WikiVoyage pages and create a Chroma vector store."""
    urls = [f"https://en.wikivoyage.org/wiki/{slug}" for slug in destinations]
    loader = AsyncHtmlLoader(urls)
    print(f"Downloading destination pages: {urls} ...")
    docs = await loader.aload()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=128)
    chunks = sum([splitter.split_documents([d]) for d in docs], [])

    print(f"Embedding {len(chunks)} chunks ...")
    vectordb_client = Chroma.from_documents(
        chunks, embedding=OpenAIEmbeddings(api_key=load_cred("openai"))
    )
    print("Vector store ready.\n")
    return vectordb_client


# Singleton. TODO: singletons are a code smell, revise this.
_ti_vectorstore_client: Chroma | None = None


def get_travel_info_vectorstore() -> Chroma:
    # TODO: revise this singleton code smell. I took this code from the exmaple
    # code, but dislike this singleton pattern.
    global _ti_vectorstore_client
    if _ti_vectorstore_client is None:
        _ti_vectorstore_client = asyncio.run(_build_vectorstore(UK_DESTINATIONS))
    return _ti_vectorstore_client


def get_travel_info_retriever() -> VectorStoreRetriever:
    ti_vectorstore_client = get_travel_info_vectorstore()
    return ti_vectorstore_client.as_retriever()
