from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.services.nlp import LanguageCode, PosLabel, extract_vocabulary

router = APIRouter(prefix="/api", tags=["article"])


class ArticleRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50_000)
    language_code: LanguageCode


class VocabItem(BaseModel):
    source: str
    translations: list[str]
    pos: PosLabel


class ArticleResponse(BaseModel):
    vocabulary: list[VocabItem]


@router.post("/article", response_model=ArticleResponse, summary="Extract vocabulary from article")
async def extract_vocabulary_endpoint(body: ArticleRequest) -> ArticleResponse:
    try:
        raw = await run_in_threadpool(extract_vocabulary, body.text, body.language_code)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return ArticleResponse(vocabulary=[VocabItem(**item) for item in raw])
