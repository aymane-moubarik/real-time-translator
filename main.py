from fastapi import FastAPI, UploadFile, File
from models import TranslationRequest, TranslationResponse, SimilarityRequest, SimilarityResponse
from services.translator import translate_text
from services.embeddings import get_embedding, cosine_similarity
from services.es_client import es, create_indices, INDEX_TEXT, INDEX_IMAGE
from services.clip_service import get_image_embedding, get_text_embedding_clip
from db import translations_collection
from datetime import datetime
import shutil
import os

app = FastAPI(title="Real Time Translator API")

@app.on_event("startup")
def startup_event():
    create_indices()

@app.post("/translate", response_model=TranslationResponse)
def translate(req: TranslationRequest):
    translated = translate_text(req.text, req.target_lang, req.source_lang)
    embedding = get_embedding(req.text)

    doc = {
        "original_text": req.text,
        "translated_text": translated,
        "source_lang": req.source_lang,
        "target_lang": req.target_lang,
        "embedding": embedding,
        "timestamp": datetime.utcnow()
    }
    translations_collection.insert_one(doc)

    # Indexer aussi dans Elasticsearch pour la recherche
    es.index(index=INDEX_TEXT, document={
        "text": req.text,
        "translated_text": translated,
        "embedding": embedding,
        "timestamp": datetime.utcnow()
    })

    return doc

@app.post("/similarity", response_model=SimilarityResponse)
def similarity(req: SimilarityRequest):
    emb1 = get_embedding(req.text1)
    emb2 = get_embedding(req.text2)
    score = cosine_similarity(emb1, emb2)
    return {
        "text1": req.text1,
        "text2": req.text2,
        "similarity_score": round(score, 4)
    }

@app.get("/search/text")
def search_text(query: str, top_k: int = 5):
    query_embedding = get_embedding(query)

    response = es.search(index=INDEX_TEXT, body={
        "knn": {
            "field": "embedding",
            "query_vector": query_embedding,
            "k": top_k,
            "num_candidates": 50
        },
        "_source": ["text", "translated_text", "timestamp"]
    })

    results = [
        {
            "score": hit["_score"],
            "text": hit["_source"]["text"],
            "translated_text": hit["_source"].get("translated_text")
        }
        for hit in response["hits"]["hits"]
    ]
    return {"query": query, "results": results}

@app.post("/upload/image")
async def upload_image(file: UploadFile = File(...), description: str = ""):
    # Validation du type de fichier
    allowed_extensions = (".jpg", ".jpeg", ".png", ".webp", ".bmp")
    if not file.filename.lower().endswith(allowed_extensions):
        return {"error": f"Format non supporté. Utilisez : {', '.join(allowed_extensions)}"}

    os.makedirs("uploaded_images", exist_ok=True)
    file_path = f"uploaded_images/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        embedding = get_image_embedding(file_path)
    except Exception as e:
        return {"error": f"Impossible de traiter l'image : {str(e)}"}

    es.index(index=INDEX_IMAGE, document={
        "filename": file.filename,
        "description": description,
        "embedding": embedding,
        "timestamp": datetime.utcnow()
    })

    return {"filename": file.filename, "description": description, "status": "indexed"}

@app.get("/search/image")
def search_image(query: str, top_k: int = 5):
    query_embedding = get_text_embedding_clip(query)

    response = es.search(index=INDEX_IMAGE, body={
        "knn": {
            "field": "embedding",
            "query_vector": query_embedding,
            "k": top_k,
            "num_candidates": 50
        },
        "_source": ["filename", "description", "timestamp"]
    })

    results = [
        {
            "score": hit["_score"],
            "filename": hit["_source"]["filename"],
            "description": hit["_source"].get("description")
        }
        for hit in response["hits"]["hits"]
    ]
    return {"query": query, "results": results}
    
    
from models import (
    TranslationRequest, TranslationResponse,
    SimilarityRequest, SimilarityResponse,
    PlagiarismRequest, PlagiarismResponse, PlagiarismMatch
)

@app.post("/plagiarism/check", response_model=PlagiarismResponse)
def check_plagiarism(req: PlagiarismRequest):
    query_embedding = get_embedding(req.text)

    response = es.search(index=INDEX_TEXT, body={
        "knn": {
            "field": "embedding",
            "query_vector": query_embedding,
            "k": 10,
            "num_candidates": 100
        },
        "_source": ["text"]
    })

    matches = []
    for hit in response["hits"]["hits"]:
        # Le score kNN d'Elasticsearch est déjà normalisé entre 0 et 1 pour la similarité cosinus
        score = hit["_score"]
        if score >= req.threshold:
            matches.append(PlagiarismMatch(text=hit["_source"]["text"], score=round(score, 4)))

    return PlagiarismResponse(
        text=req.text,
        is_plagiarized=len(matches) > 0,
        matches=matches
    )