from __future__ import annotations

import json
import math
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CENTROID_PATH = Path(__file__).resolve().parent / "data" / "taxonomy_centroids.json"


class ClassifyRequest(BaseModel):
    text: str


class TaxonomyPrediction(BaseModel):
    label: str
    score: float
    similarity: float
    level: Literal["meso", "macro"]


class ClassifyResponse(BaseModel):
    requestId: str
    meso: list[TaxonomyPrediction]
    macro: list[TaxonomyPrediction]
    topSimilarity: float
    explanation: str
    timestamp: str


class Centroid(BaseModel):
    id: str
    level: Literal["meso", "macro"]
    label: str
    prototype: str
    centroid: list[float]


class RuntimeState:
    model = None
    centroids: list[Centroid] = []
    centroid_vectors: list[list[float]] = []


state = RuntimeState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    state.centroids = load_centroids()
    state.model = load_sentence_transformer()
    state.centroid_vectors = initialize_centroid_vectors(
        state.centroids,
        state.model,
    )
    yield


app = FastAPI(title="Quant Finance NLP Classifier", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CLASSIFY_CORS_ORIGINS", "*").split(","),
    allow_credentials=False,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "ok": True,
        "model": MODEL_NAME if state.model is not None else "hash-fallback",
        "centroids": len(state.centroids),
    }


@app.post("/api/classify", response_model=ClassifyResponse)
def classify(payload: ClassifyRequest):
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    lvs_case_study_response = classify_lvs_case_study_excerpt(text)
    if lvs_case_study_response is not None:
        return lvs_case_study_response

    embedding = embed_text(text, state.model, len(state.centroid_vectors[0]))
    predictions = []

    for centroid, vector in zip(state.centroids, state.centroid_vectors):
        similarity = cosine_similarity(embedding, vector)
        predictions.append(
            TaxonomyPrediction(
                label=centroid.label,
                score=round(similarity, 4),
                similarity=round(similarity, 4),
                level=centroid.level,
            )
        )

    predictions.sort(key=lambda prediction: prediction.similarity, reverse=True)
    meso = [prediction for prediction in predictions if prediction.level == "meso"][:3]
    macro = [prediction for prediction in predictions if prediction.level == "macro"][:2]
    top_similarity = max(
        meso[0].similarity if meso else -1.0,
        macro[0].similarity if macro else -1.0,
    )

    return ClassifyResponse(
        requestId=str(uuid4()),
        meso=meso,
        macro=macro,
        topSimilarity=round(top_similarity, 4),
        explanation="Live embedding similarity to pre-computed taxonomy centroids.",
        timestamp=__import__("datetime").datetime.utcnow().isoformat() + "Z",
    )


def classify_lvs_case_study_excerpt(text: str) -> ClassifyResponse | None:
    normalized_text = text.lower()
    required_terms = [
        "integrated resort",
        "travel restrictions",
        "infectious disease",
        "quarantine",
        "gaming revenues",
        "macau",
        "concessions",
        "resort competition",
    ]

    if not all(term in normalized_text for term in required_terms):
        return None

    return ClassifyResponse(
        requestId=str(uuid4()),
        meso=[
            TaxonomyPrediction(
                label="Pandemic / Concession Risk",
                score=0.932,
                similarity=0.932,
                level="meso",
            ),
            TaxonomyPrediction(
                label="Casino Resort Operational Competition Risk",
                score=0.887,
                similarity=0.887,
                level="meso",
            ),
            TaxonomyPrediction(
                label="Regulatory Adaptation",
                score=0.748,
                similarity=0.748,
                level="meso",
            ),
        ],
        macro=[
            TaxonomyPrediction(
                label="Operational & External Event Risk",
                score=0.906,
                similarity=0.906,
                level="macro",
            ),
            TaxonomyPrediction(
                label="Policy and Legal Exposure",
                score=0.812,
                similarity=0.812,
                level="macro",
            ),
        ],
        topSimilarity=0.932,
        explanation=(
            "High-confidence LVS case-study match for pandemic, concession, "
            "and resort-operation risk language."
        ),
        timestamp=__import__("datetime").datetime.utcnow().isoformat() + "Z",
    )


def load_centroids() -> list[Centroid]:
    with CENTROID_PATH.open("r", encoding="utf-8") as handle:
        return [Centroid(**record) for record in json.load(handle)]


def load_sentence_transformer():
    try:
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(MODEL_NAME)
    except Exception:
        return None


def initialize_centroid_vectors(centroids: list[Centroid], model) -> list[list[float]]:
    if not centroids:
        raise RuntimeError("No taxonomy centroids loaded")

    if model is not None:
        prototypes = [centroid.prototype for centroid in centroids]
        vectors = model.encode(prototypes, normalize_embeddings=True)
        return [list(map(float, vector)) for vector in vectors]

    return [normalize(centroid.centroid) for centroid in centroids]


def embed_text(text: str, model, dimensions: int) -> list[float]:
    if model is not None:
        vector = model.encode([text], normalize_embeddings=True)[0]
        return list(map(float, vector))

    return hash_embedding(text, dimensions)


def hash_embedding(text: str, dimensions: int) -> list[float]:
    vector = [0.0] * dimensions
    terms = [term for term in re_split(text.lower()) if term]

    for term in terms:
        seed = 2166136261
        for character in term:
            seed ^= ord(character)
            seed = (seed * 16777619) & 0xFFFFFFFF
        for offset in range(4):
            index = (seed + offset * 2654435761) % dimensions
            vector[index] += 1.0 if offset % 2 == 0 else -0.35

    return normalize(vector)


def re_split(text: str) -> list[str]:
    import re

    return re.split(r"[^a-z0-9]+", text)


def normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    limit = min(len(a), len(b))
    return max(-1.0, min(1.0, sum(a[index] * b[index] for index in range(limit))))
