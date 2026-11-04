
import logging
import os
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from app.integrations.job_discovery.models import CandidateJobProfile
from app.integrations.job_discovery.scheduler import run_once

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
PROFILE_PATH = ROOT / "sample_data/job_discovery_profile.example.json"
OUTPUT_PATH = ROOT / "data/job_discovery_snapshot.json"

def discover_jobs():
    try:
        profile = CandidateJobProfile.model_validate_json(
            PROFILE_PATH.read_text(encoding="utf-8")
        )

        result = run_once(profile, output=str(OUTPUT_PATH))

        logger.info(
            "SUCCESS | Total jobs: %s | New jobs: %s",
            result["total_found"],
            result["new_jobs"]
        )

    except Exception:
        logger.exception("Scheduled discovery failed")

def main():
    os.chdir(ROOT)

    scheduler = BlockingScheduler(timezone="UTC")

    scheduler.add_job(
        discover_jobs,
        trigger="interval",
        minutes=30,
        id="talentflow_job_discovery",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
        replace_existing=True
    )

    logger.info("TalentFlow scheduler started")
    logger.info("Automatic job discovery every 30 minutes")

    discover_jobs()
    scheduler.start()

if __name__ == "__main__":
    main()
