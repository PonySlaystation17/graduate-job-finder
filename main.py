import csv
import requests
import os
import sqlite3

from dotenv import load_dotenv
from scoring import score_job
from config import required_tech_terms, banned_phrases, search_locations, search_terms, minimum_salary
from database import setup_database

# To activate venv:
# .\.venv\Scripts\Activate.ps1

load_dotenv()
APP_ID = os.getenv("ADZUNA_APP_ID")
API_KEY = os.getenv("ADZUNA_API_KEY")
REED_API_KEY = os.getenv("REED_API_KEY")

matched_jobs = []
rejected_jobs = []
seen_urls = set()
seen_job_keys = set()


######## DB STUFF #################
def view_top_jobs():
    print("ID, TITLE, COMPANY, LOCATION, SCORE, SALARY, SOURCE, SCORE")
    connection = sqlite3.connect("jobs.db")
    cursor = connection.cursor()

    cursor.execute("""
    SELECT id, title, company, location, score, salary_min, source, score
    FROM jobs
    WHERE applied = 0
    ORDER BY score DESC
    LIMIT 10
    """)
    jobs = cursor.fetchall()

    for job in jobs:
        print(job)
    
    connection.commit()
    connection.close()    

def view_applied_jobs():
    connection = sqlite3.connect("jobs.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, title, company, location, source
        FROM jobs
        WHERE applied = 1
        ORDER BY id DESC
        """)

    jobs = cursor.fetchall()

    print("\n--- Applied Jobs ---")
    if len(jobs) == 0:
        print("No applied jobs saved.")
    else:
        for job in jobs:
            print(job)

    connection.close()

def view_top_unapplied_jobs():
    connection = sqlite3.connect("jobs.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, title, company, location, source, score
        FROM jobs
        WHERE applied = 0
        ORDER BY score DESC
        LIMIT 10
        """)

    jobs = cursor.fetchall()

    print("\n--- Top Unapplied for Jobs ---")
    if len(jobs) == 0:
        print("No unapplied jobs saved.")
    else:
        for job in jobs:
            print(job)

    connection.close()

def mark_job_as_applied_by_url(job_url):
    connection = sqlite3.connect("jobs.db")
    cursor = connection.cursor()

    cursor.execute("""
    UPDATE jobs
    SET applied = 1
    WHERE url = ?
    """, (job_url,))

    connection.commit()
    connection.close()

def mark_stale_jobs_inactive(days_old=14):
    connection = sqlite3.connect("jobs.db")
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE jobs
        SET active = 0
        WHERE applied = 0
        AND last_seen < date('now', ?)
    """, (f"-{days_old} days",))

    connection.commit()
    connection.close()

def remove_job(job_url):
    connection = sqlite3.connect("jobs.db")
    cursor = connection.cursor()

    cursor.execute("""
    DELETE FROM jobs
    WHERE url = ?
    """, (job_url,))

    connection.commit()
    connection.close()

######## APIs ##################
# fetch jobs using Adzuna API
def fetch_jobs_adzuna():
    all_jobs = []

    for search_term in search_terms:
        formatted_search = search_term.replace(" ", "+")
        
        for location in search_locations:
            formatted_location = location.replace(" ", "+")

            for page in range(1, 3):
                url = f"https://api.adzuna.com/v1/api/jobs/gb/search/{page}?app_id={APP_ID}&app_key={API_KEY}&results_per_page=20&what={formatted_search}&where={formatted_location}"

                response = requests.get(url)

                # print(response.status_code)
                # print(response.text[:300])

                if response.status_code != 200:
                    print("Request failed:", response.status_code)
                    continue

                try:
                    data = response.json()
                except requests.exceptions.JSONDecodeError:
                    print("Could not read JSON response")
                    continue

                for job in data["results"]:
                    # if url not seen before, add to seen urls. Otherwise skip
                    if job["redirect_url"] in seen_urls:
                        continue
                    seen_urls.add(job["redirect_url"])

                    cleaned_job = {
                        "source": "Adzuna",
                        "title": job["title"],
                        "company": job["company"]["display_name"],
                        "location": job["location"]["display_name"],
                        "description": job["description"],
                        "url": job["redirect_url"]
                    }

                    all_jobs.append(cleaned_job)

    return all_jobs

def fetch_jobs_reed():
    all_jobs = []
    url = "https://www.reed.co.uk/api/1.0/search"
    for search_term in search_terms:
        for location in search_locations:
            for page in range(0, 2):

                results_to_skip = page * 20

                params = {
                    "keywords": search_term,
                    "locationName": location,
                    "resultsToTake": 20,
                    "resultsToSkip": results_to_skip
                }
                response = requests.get(
                    url,
                    params=params,
                    auth=(REED_API_KEY, "")
                )
        
                data = response.json()

                for job in data["results"]:

                    cleaned_job = {
                        "source": "Reed",
                        "title": job["jobTitle"],
                        "company": job["employerName"],
                        "location": job["locationName"],
                        "description": job["jobDescription"],
                        "url": job["jobUrl"],
                        "salary_min": job.get("minimumSalary", 0),
                        "salary_max": job.get("maximumSalary", 0)
                    }
                    all_jobs.append(cleaned_job)

    return all_jobs


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


