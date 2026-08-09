from database import (
    setup_database,
    mark_job_as_applied_by_url,
    mark_stale_jobs_inactive,
    remove_job,
    get_top_jobs,
    get_applied_jobs,
    get_top_unapplied_jobs
    )

from importers.adzuna import fetch_jobs_adzuna
from importers.reed import fetch_jobs_reed

from job_service import process_jobs

# To activate venv:
# .\.venv\Scripts\Activate.ps1

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

            adzuna_jobs, adzuna_success = fetch_jobs_adzuna()
            reed_jobs, reed_success = fetch_jobs_reed()

            all_jobs.extend(adzuna_jobs)
            all_jobs.extend(reed_jobs)

            matched_jobs, rejected_jobs = process_jobs(all_jobs)

            if adzuna_success:
                mark_stale_jobs_inactive(source="Adzuna")
            if reed_success:
                mark_stale_jobs_inactive(source="Reed")
            
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

