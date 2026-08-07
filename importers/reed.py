import os
import requests

from dotenv import load_dotenv

from config import search_locations, search_terms


load_dotenv()

REED_API_KEY = os.getenv("REED_API_KEY")


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
