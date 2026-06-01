import json
import asyncio
from fastapi import APIRouter, HTTPException, Depends, Query
from sse_starlette.sse import EventSourceResponse
from typing import Optional
from ..schemas import (
    CandidateCreate,
    CandidateUpdate,
    CandidateResponse,
    CandidateDetailResponse,
    ScoreCreate,
    ScoreResponse,
    SummaryResponse,
    PaginatedResponse,
)
from ..services.candidate_service import (
    list_candidates,
    get_candidate,
    create_candidate,
    update_candidate,
    soft_delete_candidate,
    add_score,
    get_scores_for_candidate,
    generate_ai_summary,
)
from ..auth import get_current_user, require_admin, get_current_user_query

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.get("", response_model=PaginatedResponse)
async def get_candidates(
    status: Optional[str] = Query(None),
    role_applied: Optional[str] = Query(None),
    skill: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    page_size: int = Query(20, ge=1, le=50),
    user: dict = Depends(get_current_user),
):
    items, total = await list_candidates(
        status=status,
        role_applied=role_applied,
        skill=skill,
        keyword=keyword,
        offset=offset,
        page_size=page_size,
    )

    result_items = []
    for item in items:
        if user["role"] != "admin":
            item.pop("internal_notes", None)
        result_items.append(CandidateResponse(**item))

    next_offset = offset + page_size if offset + page_size < total else None

    return PaginatedResponse(
        items=result_items,
        total=total,
        page=offset // page_size + 1 if page_size > 0 else 1,
        page_size=page_size,
        next_offset=next_offset,
    )


@router.get("/{candidate_id}", response_model=CandidateDetailResponse, response_model_exclude_none=True)
async def get_candidate_detail(
    candidate_id: int,
    user: dict = Depends(get_current_user),
):
    candidate = await get_candidate(candidate_id, user["role"])
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    scores = await get_scores_for_candidate(candidate_id, user["id"], user["role"])
    candidate.pop("scores", None)

    return CandidateDetailResponse(
        **candidate,
        scores=[ScoreResponse(**s) for s in scores],
    )


@router.post("", response_model=CandidateResponse, status_code=201)
async def create_new_candidate(
    data: CandidateCreate,
    user: dict = Depends(get_current_user),
):
    candidate = await create_candidate(data.model_dump())
    return CandidateResponse(**candidate)


@router.patch("/{candidate_id}", response_model=CandidateResponse)
async def update_existing_candidate(
    candidate_id: int,
    data: CandidateUpdate,
    user: dict = Depends(get_current_user),
):
    update_data = data.model_dump(exclude_unset=True)

    if user["role"] != "admin":
        if "internal_notes" in update_data:
            raise HTTPException(status_code=403, detail="Only admins can edit internal notes")
        if "status" in update_data:
            raise HTTPException(status_code=403, detail="Only admins can change status")

    candidate = await update_candidate(candidate_id, update_data, user["role"])
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return CandidateResponse(**candidate)


@router.delete("/{candidate_id}", status_code=204)
async def delete_candidate(
    candidate_id: int,
    user: dict = Depends(require_admin),
):
    deleted = await soft_delete_candidate(candidate_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Candidate not found")


@router.post("/{candidate_id}/scores", response_model=ScoreResponse, status_code=201)
async def submit_score(
    candidate_id: int,
    data: ScoreCreate,
    user: dict = Depends(get_current_user),
):
    try:
        score = await add_score(candidate_id, data, user["id"])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return ScoreResponse(**score)


@router.get("/{candidate_id}/scores", response_model=list[ScoreResponse])
async def list_scores(
    candidate_id: int,
    user: dict = Depends(get_current_user),
):
    scores = await get_scores_for_candidate(candidate_id, user["id"], user["role"])
    return [ScoreResponse(**s) for s in scores]


@router.post("/{candidate_id}/summary", response_model=SummaryResponse)
async def trigger_summary(
    candidate_id: int,
    user: dict = Depends(get_current_user),
):
    try:
        summary = await generate_ai_summary(candidate_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return SummaryResponse(summary=summary)


@router.get("/{candidate_id}/stream")
async def stream_scores(
    candidate_id: int,
    user: dict = Depends(get_current_user_query),
):
    async def event_generator():
        last_count = 0
        while True:
            scores = await get_scores_for_candidate(candidate_id, user["id"], user["role"])
            count = len(scores)
            if count > last_count:
                last_count = count
                yield {
                    "event": "score_update",
                    "data": json.dumps([dict(s) for s in scores], default=str),
                }
            await asyncio.sleep(2)

    return EventSourceResponse(event_generator())
