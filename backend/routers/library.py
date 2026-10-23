"""Local PDF RAG API. Data is separated by server-generated collection IDs."""
from pathlib import Path
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from rag.library import Library
from rag.assistant import ResearchAssistant, OpenAIToolModel, OfflineDemoModel
from config import DATA_DIR

router = APIRouter(prefix='/api/library', tags=['PDF RAG'])


def library():
    return Library(Path(DATA_DIR)/'library.sqlite3')


def check(collection):
    store = library()
    try:
        store.require(collection)
    except (ValueError, KeyError):
        raise HTTPException(404, '文献库不存在') from None
    return store


class Search(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=5, ge=1, le=10)


class Ask(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    offline_demo: bool = True


class Article(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    abstract: str = Field(min_length=12, max_length=30000)
    url: str = Field(default='', max_length=2000, pattern=r'^(https?://[^\s]+)?$')


class ArticleImport(BaseModel):
    articles: list[Article] = Field(min_length=1, max_length=100)


@router.post('/collections')
def create():
    return {'collection': library().create()}


@router.get('/{collection}/documents')
def documents(collection: str):
    return {'documents': check(collection).documents(collection)}


@router.post('/{collection}/pdf')
async def upload_pdf(collection: str, file: UploadFile = File(...)):
    store = check(collection)
    try:
        payload = await file.read(20*1024*1024+1)
        return store.add_pdf(collection, Path(file.filename or 'paper.pdf').name, payload)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    finally:
        await file.close()


@router.post('/{collection}/articles')
def import_articles(collection: str, request: ArticleImport):
    store = check(collection)
    try:
        result = [store.add_pages(collection, a.title, [a.abstract], kind='abstract', url=a.url)
                  for a in request.articles]
        return {'imported': result}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None


@router.post('/{collection}/search')
def search(collection: str, request: Search):
    try:
        return {'chunks': check(collection).search(collection, request.query, request.limit),
                'method': 'BM25 lexical retrieval (English words / Chinese bigrams)'}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None


@router.post('/{collection}/ask')
def ask(collection: str, request: Ask):
    store = check(collection)
    try:
        model = OfflineDemoModel() if request.offline_demo else OpenAIToolModel()
        result = ResearchAssistant(store, model).run(collection, request.question)
        return dict(result, mode='offline_demo' if request.offline_demo else 'live_model')
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    except RuntimeError as exc:
        raise HTTPException(502, str(exc)) from None
