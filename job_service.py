from config import (
    required_tech_terms,
    banned_phrases,
    search_locations,
    minimum_salary
)

from scoring import score_job
from database import save_job_to_db

def get_rejection_reasons(job):

    title = job["title"].lower()
    description = job["description"].lower()
    location = job["location"].lower()
    salary_min = job.get("salary_min") or 0

    reasons = []

    if not any(
        term in title or term in description
        for term in required_tech_terms
    ):
        reasons.append("Not a software/technical role")

    if "grad" not in title and "junior" not in title:
        reasons.append("Title not junior or graduate")

    if any(phrase in description for phrase in banned_phrases):
        reasons.append("Experience level too high")

    if not any(place in location for place in search_locations):
        reasons.append("Location not allowed")

    if salary_min < minimum_salary and salary_min != 0:
        reasons.append("Salary below minimum")

    return reasons

def create_job_key(job):
    return (
        job["title"].lower().strip(),
        job["company"].lower().strip(),
        job["location"].lower().strip()
    )

def process_jobs(jobs):
    new_matches = 0
    matched_jobs = []
    rejected_jobs = []
    seen_job_keys = set()

    for job in jobs:
        title = job["title"].lower()
        description = job["description"].lower()
        location = job["location"].lower()
        salary_min = job.get("salary_min") or 0

        job_key = create_job_key(job)

        if job_key in seen_job_keys:
            continue
        seen_job_keys.add(job_key)

        score, matched_keywords = score_job(title, description, location, salary_min)
        reasons = get_rejection_reasons(job)
        
        if len(reasons) == 0:
            job["score"] = score
            job["matched_keywords"] = ", ".join(matched_keywords)
            matched_jobs.append(job)

            is_new_job = save_job_to_db(job)
            if is_new_job:
                new_matches += 1

            # print(job["title"], "-", job["company"], "- Score:", score, "- Matched keywords:", job["matched_keywords"])

        else:
            rejected_job = reject_job(job, "; ".join(reasons))
            rejected_jobs.append(rejected_job)
        

    # sort by score
    matched_jobs.sort(key=lambda job: job["score"], reverse=True)

    print(f"----- New matches found: {new_matches} -----")

    return matched_jobs, rejected_jobs

def reject_job(job, reasons):
    rejected_job = job.copy()
    rejected_job["rejection_reason"] = reasons

    return rejected_job


