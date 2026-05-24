import csv
from config import locations, keywords, required_tech_terms, banned_phrases, search_locations, search_terms, minimum_salary
import requests
import os
from dotenv import load_dotenv
import sqlite3
from datetime import date

load_dotenv()
APP_ID = os.getenv("ADZUNA_APP_ID")
API_KEY = os.getenv("ADZUNA_API_KEY")

matched_jobs = []
rejected_jobs = []
seen_urls = set()

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
    (title, company, location, salary_min, salary_max, url, score, date_found)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job["title"],
        job["company"],
        job["location"],
        job.get("salary_min", 0),
        job.get("salary_max", 0),
        job["url"],
        job["score"],
        str(date.today())
    ))

    connection.commit()
    connection.close()

def view_top_jobs():
    print("TITLE, COMPANY, LOCATION, SCORE, SALARY")
    connection = sqlite3.connect("jobs.db")
    cursor = connection.cursor()

    cursor.execute("""
    SELECT title, company, location, score, salary_min
    FROM jobs
    ORDER BY score DESC
    LIMIT 10
    """)
    jobs = cursor.fetchall()

    for job in jobs:
        print(job)
    
    connection.commit()
    connection.close()    

# fetch jobs using Adzuna API
def fetch_jobs():
    all_jobs = []

    for search_term in search_terms:
        formatted_search = search_term.replace(" ", "+")
        
        for location in search_locations:
            formatted_location = location.replace(" ", "+")

            for page in range(1, 4):
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
                        "title": job["title"],
                        "company": job["company"]["display_name"],
                        "location": job["location"]["display_name"],
                        "description": job["description"],
                        "url": job["redirect_url"]
                    }

                    all_jobs.append(cleaned_job)

    return all_jobs

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

        if not any(term in title or term in description for term in required_tech_terms):
            reasons.append("Not a software/technical role")

        if "grad" not in title and "junior" not in title:
            reasons.append("Title not junior or graduate")

        if any(phrase in description for phrase in banned_phrases):
            reasons.append("Experience level too high")

        if not any(place in location for place in locations):
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

def main():
    setup_database()
    jobs = fetch_jobs()
    load_jobs(jobs)

    matched_fieldnames = [
    "title",
    "company",
    "location",
    "description",
    "url",
    "score",
    "matched_keywords"
    ]
    rejected_fieldnames = [
        "title",
        "company",
        "location",
        "description",
        "url",
        "rejection_reason"
    ]

    save_csv("matched_jobs.csv", matched_jobs, matched_fieldnames)
    save_csv("rejected_jobs.csv", rejected_jobs, rejected_fieldnames)

    view_top_jobs()

main()