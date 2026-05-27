import csv
from config import keywords, required_tech_terms, banned_phrases, search_locations, search_terms, minimum_salary
import requests
import os
from dotenv import load_dotenv
import sqlite3
from datetime import date

# To activate venv:
# .\.venv\Scripts\Activate.ps1

load_dotenv()
APP_ID = os.getenv("ADZUNA_APP_ID")
API_KEY = os.getenv("ADZUNA_API_KEY")
REED_API_KEY = os.getenv("REED_API_KEY")

matched_jobs = []
rejected_jobs = []
seen_urls = set()


######## DB STUFF #################
def setup_database():
    connection = sqlite3.connect("jobs.db")
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        company TEXT,
        location TEXT,
        salary_min INTEGER,
        salary_max INTEGER,
        url TEXT UNIQUE,
        score INTEGER,           
        date_found TEXT,
        source TEXT,
        applied INTEGER DEFAULT 0,
        UNIQUE(title, company, location)
    )
    """)

    connection.commit()
    connection.close()

def save_job_to_db(job):
    connection = sqlite3.connect("jobs.db")
    cursor = connection.cursor()

    cursor.execute("""
    INSERT OR IGNORE INTO jobs
    (title, company, location, salary_min, salary_max, url, score, date_found, source)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job["title"],
        job["company"],
        job["location"],
        job.get("salary_min", 0),
        job.get("salary_max", 0),
        job["url"],
        job["score"],
        str(date.today()),
        job["source"]
    ))

    connection.commit()
    connection.close()

def view_top_jobs():
    print("ID, TITLE, COMPANY, LOCATION, SCORE, SALARY, SOURCE")
    connection = sqlite3.connect("jobs.db")
    cursor = connection.cursor()

    cursor.execute("""
    SELECT id, title, company, location, score, salary_min, source
    FROM jobs
    ORDER BY score DESC
    LIMIT 10
    """)
    jobs = cursor.fetchall()

    for job in jobs:
        print(job)
    
    connection.commit()
    connection.close()    

def mark_job_as_applied(job_id):
    connection = sqlite3.connect("jobs.db")
    cursor = connection.cursor()

    cursor.execute("""
    UPDATE jobs
    SET applied = 1
    WHERE id = ?
    """, (job_id,))

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

            params = {
                "keywords": search_term,
                "locationName": location,
                "resultsToTake": 20
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
# score job
def score_job(title, description, location, salary_min):
    score = 0
    matched_keywords = []

    if "graduate" in title:
        score += 5
    if "junior" in title:
        score += 3
    if "python" in title:
        score += 5
    if "java" in title:
        score += 5
    if "backend" in title:
        score += 4
    if "games" in title:
        score += 10

    if salary_min >= 40000:
        score += 5
    elif salary_min >= 35000:
        score += 3
    elif salary_min >= 30000:
        score += 1

    for keyword, points in keywords.items():
        if keyword in description:
            score += points
            matched_keywords.append(keyword)
    return score, matched_keywords

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
    all_jobs = []

    all_jobs.extend(fetch_jobs_adzuna())
    all_jobs.extend(fetch_jobs_reed())

    load_jobs(all_jobs)

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

    view_top_jobs()

    mark_job_as_applied(2)

main()