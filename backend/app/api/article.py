from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["article"])


class ArticleRequest(BaseModel):
    text: str
    language_code: str


class ArticleResponse(BaseModel):
    vocabulary: list


@router.post("/article", response_model=ArticleResponse, summary="Extract vocabulary from article")
async def extract_vocabulary(body: ArticleRequest) -> ArticleResponse:
    # Stub: NLP extraction will be implemented in Phase 1.2–1.4
    return ArticleResponse(vocabulary=[])
