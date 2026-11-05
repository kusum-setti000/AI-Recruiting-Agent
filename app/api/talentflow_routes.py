import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.integrations.job_discovery.greenhouse import GreenhouseProvider
from app.integrations.job_discovery.models import CandidateJobProfile
from app.integrations.job_discovery.matcher import calculate_match_score
from app.integrations.job_discovery.theirstack_provider import TheirStackProvider

router = APIRouter(prefix="/api/jobs", tags=["TalentFlow"])

BOARDS = [
    "greenhouse", "datadog", "cloudflare", "figma",
    "databricks", "mongodb", "elastic", "stripe", "reddit"
]
_cache = {"expires": 0, "jobs": [], "errors": []}
_lock = threading.Lock()


def fetch_board(board):
    try:
        provider = GreenhouseProvider(board_tokens=[board])
        jobs = provider.search(CandidateJobProfile())
        return [j.model_dump(mode="json") for j in jobs], None
    except Exception as exc:
        return [], f"{board}: {type(exc).__name__}"


def get_jobs(refresh=False):
    with _lock:
        if not refresh and time.time() < _cache["expires"]:
            return _cache["jobs"], _cache["errors"]

        jobs, errors, seen = [], [], set()
        with ThreadPoolExecutor(max_workers=9) as pool:
            futures = [pool.submit(fetch_board, b) for b in BOARDS]
            for future in as_completed(futures):
                found, error = future.result()
                if error:
                    errors.append(error)
                for job in found:
                    key = (
                        job["source"],
                        job["company"],
                        job["external_id"],
                    )
                    if key not in seen:
                        seen.add(key)
                        jobs.append(job)

        jobs.sort(key=lambda j: (
            j["company"].lower(), j["title"].lower()
        ))
        _cache.update(
            jobs=jobs,
            errors=errors,
            expires=time.time() + 900 if jobs else 0,
        )
        return jobs, errors


@router.get("/browse")
def browse(
    refresh: bool = False,
    page: int = 1,
    page_size: int = 15,
    keyword: str = "",
    location: str = "",
    company: str = "All",
    remote_only: bool = False,
    sort: str = "default",
):
    jobs, errors = get_jobs(refresh)

    companies = sorted({
        j.get("company", "")
        for j in jobs
        if j.get("company")
    })

    words = keyword.lower().strip().split()
    location_filter = location.lower().strip()

    def matches_filters(job):
        title = (job.get("title") or "").lower()
        employer = (job.get("company") or "").lower()
        place = (job.get("location") or "").lower()
        searchable = title + " " + employer

        if not all(word in searchable for word in words):
            return False
        if location_filter and location_filter not in place:
            return False
        if company != "All" and job.get("company") != company:
            return False
        if remote_only and not any(
            term in place
            for term in ("remote", "anywhere", "work from home")
        ):
            return False
        return True

    filtered = [j for j in jobs if matches_filters(j)]

    if sort == "title":
        filtered.sort(key=lambda j: (j.get("title") or "").lower())
    elif sort == "company":
        filtered.sort(key=lambda j: (j.get("company") or "").lower())

    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    total = len(filtered)
    total_pages = max(1, (total + page_size - 1) // page_size)
    start = (page - 1) * page_size

    return {
        "jobs": filtered[start:start + page_size],
        "total_found": total,
        "total_pages": total_pages,
        "page": page,
        "page_size": page_size,
        "has_next": page < total_pages,
        "companies": companies,
        "source_errors": errors,
    }


class MatchRequest(BaseModel):
    profile: CandidateJobProfile
    minimum_score: int = Field(default=80, ge=0, le=100)
    include_theirstack: bool = False


@router.post("/matches")
def matches(request: MatchRequest):
    from app.integrations.job_discovery.models import DiscoveredJob
    from app.integrations.job_discovery.explanations import explain_match
    from app.integrations.job_discovery.recommendations import build_recommendation

    jobs, errors = get_jobs()
    candidates = list(jobs)

    if request.include_theirstack:
        try:
            extra = TheirStackProvider(limit=10).search(request.profile)
            candidates.extend(
                j.model_dump(mode="json") for j in extra
            )
        except Exception as exc:
            errors = list(errors) + [
                f"TheirStack: {type(exc).__name__}"
            ]

    seen = set()
    results = []

    for raw in candidates:
        try:
            job = DiscoveredJob.model_validate(raw)
            key = str(job.job_url).rstrip("/").lower()
            if key in seen:
                continue
            seen.add(key)

            score = calculate_match_score(request.profile, job)
            if score < request.minimum_score:
                continue

            job.match_score = score
            job.match_explanation = explain_match(
                request.profile, job
            )
            job.recommendation_summary = build_recommendation(
                job.match_explanation
            )
            results.append(job.model_dump(mode="json"))
        except Exception:
            continue

    results.sort(
        key=lambda job: job.get("match_score") or 0,
        reverse=True,
    )
    return {
        "jobs": results,
        "total_found": len(results),
        "source_errors": errors,
    }


from fastapi import File, Form, UploadFile
from app.agents.document_loader import ResumeValidationError
from app.integrations.job_discovery.resume_profiler import profile_from_resume


@router.post("/profile")
async def resume_profile_only(
    resume: UploadFile = File(...),
    location: str | None = Form(default=None),
    remote_only: bool = Form(default=False),
):
    try:
        content = await resume.read()
        profile = profile_from_resume(
            filename=resume.filename or "",
            file_bytes=content,
            location=location,
            remote_only=remote_only,
        )
        return {"candidate_profile": profile.model_dump()}
    except (ResumeValidationError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
