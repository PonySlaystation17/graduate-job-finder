import csv

from scoring import score_job
from config import required_tech_terms, banned_phrases, search_locations, search_terms, minimum_salary
from database import (
    setup_database,
    save_job_to_db,
    mark_job_as_applied_by_url,
    mark_stale_jobs_inactive,
    remove_job,
    get_top_jobs,
    get_applied_jobs,
    get_top_unapplied_jobs
    )

from importers.adzuna import fetch_jobs_adzuna
from importers.reed import fetch_jobs_reed

# To activate venv:
# .\.venv\Scripts\Activate.ps1

matched_jobs = []
rejected_jobs = []
seen_job_keys = set()


######## DB STUFF #################
def view_top_jobs():
    print("ID, TITLE, COMPANY, LOCATION, SCORE, SALARY, SOURCE")

    jobs = get_top_jobs()

    for job in jobs:
        print(job)

def view_applied_jobs():
    jobs = get_applied_jobs()

    print("\n--- Applied Jobs ---")

    if len(jobs) == 0:
        print("No applied jobs saved.")
    else:
        for job in jobs:
            print(job)

def view_top_unapplied_jobs():
    jobs = get_top_unapplied_jobs()

    print("\n--- Top Unapplied for Jobs ---")

    if len(jobs) == 0:
        print("No unapplied jobs saved.")
    else:
        for job in jobs:
            print(job)


######### Organise Data #############
# reject job
def reject_job(job, reasons):
    job["rejection_reason"] = reasons
    rejected_jobs.append(job)

# read and filter jobs
def load_jobs(jobs):
    for job in jobs:

        title = job["title"].lower()
        description = job["description"].lower()
        location = job["location"].lower()
        salary_min = job.get("salary_min") or 0

        job_key = (
            title.strip(),
            job["company"].lower().strip(),
            location.strip()
        )
        if job_key in seen_job_keys:
            continue
        seen_job_keys.add(job_key)

        score, matched_keywords = score_job(title, description, location, salary_min)
        reasons = [] # reasons for rejecting

        # requirement checks
        if not any(term in title or term in description for term in required_tech_terms):
            reasons.append("Not a software/technical role")

        if "grad" not in title and "junior" not in title:
            reasons.append("Title not junior or graduate")

        if any(phrase in description for phrase in banned_phrases):
            reasons.append("Experience level too high")

        if not any(place in location for place in search_locations):
            reasons.append("Location not allowed")
        
        # reject if salary below min but not if none is shown
        if salary_min < minimum_salary and salary_min != 0:
            reasons.append("Salary below minimum")
        

        if len(reasons) == 0:
            job["score"] = score
            job["matched_keywords"] = ", ".join(matched_keywords)
            matched_jobs.append(job)
            save_job_to_db(job)

            # print(job["title"], "-", job["company"], "- Score:", score, "- Matched keywords:", job["matched_keywords"])

        else:
            reject_job(job, "; ".join(reasons))
        

    # sort by score
    matched_jobs.sort(key=lambda job: job["score"], reverse=True)

    print("----- Number of matches: ", len(matched_jobs), " -----")

# save to csv file
def save_csv(filename, data, fieldnames):
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(data)


########### MAIN ###################
def main():

    setup_database()

    while True:

        print("\n--- Graduate Job Finder ---")
        print("1. Fetch new jobs")
        print("2. View top jobs")
        print("3. Mark job as applied")
        print("4. View applied jobs")
        print("5. View top unapplied for jobs")
        print("6. Remove job from database")
        print("Any other char. Exit")

        choice = input("Choose an option: ")

        if choice == "1":

            all_jobs = []

            all_jobs.extend(fetch_jobs_adzuna())
            all_jobs.extend(fetch_jobs_reed())

            load_jobs(all_jobs)
            mark_stale_jobs_inactive()
            
            matched_fieldnames = [
                "title",
                "company",
                "location",
                "description",
                "url",
                "score",
                "salary_min",
                "salary_max",
                "matched_keywords",
                "source"
            ]
            rejected_fieldnames = [
                "title",
                "company",
                "location",
                "description",
                "url",
                "salary_min",
                "salary_max",
                "rejection_reason",
                "source"
            ]

            save_csv("matched_jobs.csv", matched_jobs, matched_fieldnames)
            save_csv("rejected_jobs.csv", rejected_jobs, rejected_fieldnames)

        elif choice == "2":
            view_top_jobs()

        elif choice == "3":
            job_url = input("Please paste the job URL that you applied for: ")
            mark_job_as_applied_by_url(job_url)
            print("Job marked as applied.")

        elif choice == "4":
            view_applied_jobs()

        elif choice == "5":
            view_top_unapplied_jobs()

        elif choice == "6":
            url_to_remove = input("Please paste the job URL that you would like to remove:")
            remove_job(url_to_remove)
            print("Job removed.")

        else:
            print("Goodbye.")
            break


if __name__ == "__main__":
    main()


