"""Run periodic job discovery with persistent deduplication."""
import argparse
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from app.integrations.job_discovery.models import CandidateJobProfile
from app.integrations.job_discovery.service import JobDiscoveryService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_once(profile, output="data/job_discovery_snapshot.json"):
    path = Path(output)
    old = {}
    if path.exists():
        old = json.loads(path.read_text(encoding="utf-8"))

    seen = set(old.get("seen_keys", []))
    result = JobDiscoveryService().search(profile)
    fresh = []

    for job in result.jobs:
        key = f"{job.source}:{job.company}:{job.external_id}"
        if key not in seen:
            fresh.append(job.model_dump(mode="json"))
        seen.add(key)

    snapshot = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "total_found": len(result.jobs),
        "new_jobs": len(fresh),
        "seen_keys": sorted(seen),
        "jobs": [job.model_dump(mode="json") for job in result.jobs],
        "new_job_details": fresh,
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    temp.replace(path)
    return snapshot

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("profile")
    parser.add_argument("--minutes", type=int, default=60)
    args = parser.parse_args()

    if args.minutes < 1:
        parser.error("--minutes must be positive")

    profile = CandidateJobProfile.model_validate_json(
        Path(args.profile).read_text(encoding="utf-8")
    )

    print("Discovery scheduler started. Ctrl+C to stop.")
    try:
        while True:
            try:
                result = run_once(profile)
                print(
                    f"Found {result['total_found']} jobs; "
                    f"{result['new_jobs']} new."
                )
            except Exception:
                logger.exception("Discovery failed")
            time.sleep(args.minutes * 60)
    except KeyboardInterrupt:
        print("Scheduler stopped.")

if __name__ == "__main__":
    main()
