import os
from pathlib import Path
from app.integrations.job_discovery.models import CandidateJobProfile
from app.integrations.job_discovery.scheduler import run_once

root = Path(__file__).resolve().parent
os.chdir(root)

profile = CandidateJobProfile.model_validate_json(
    (root / "sample_data/job_discovery_profile.example.json").read_text(encoding="utf-8")
)

result = run_once(profile)
print("Total jobs:", result["total_found"])
print("New jobs:", result["new_jobs"])
