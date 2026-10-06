from pydantic import BaseModel
from datetime import datetime

class TranslationRequest(BaseModel):
    text: str
    target_lang: str
    source_lang: str = "auto"

class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    timestamp: datetime

class SimilarityRequest(BaseModel):
    text1: str
    text2: str

class SimilarityResponse(BaseModel):
    text1: str
    text2: str
    similarity_score: float
    
class PlagiarismRequest(BaseModel):
    text: str
    threshold: float = 0.85

class PlagiarismMatch(BaseModel):
    text: str
    score: float

class PlagiarismResponse(BaseModel):
    text: str
    is_plagiarized: bool
    matches: list[PlagiarismMatch]