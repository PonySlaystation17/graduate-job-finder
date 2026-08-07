import os
import requests

from dotenv import load_dotenv

from config import search_locations, search_terms


load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
API_KEY = os.getenv("ADZUNA_API_KEY")

seen_urls = set()

def fetch_jobs_adzuna():
    all_jobs = []
    fetch_successful = True

    for search_term in search_terms:
        formatted_search = search_term.replace(" ", "+")
        
        for location in search_locations:
            formatted_location = location.replace(" ", "+")

            for page in range(1, 3):
                url = f"https://api.adzuna.com/v1/api/jobs/gb/search/{page}?app_id={APP_ID}&app_key={API_KEY}&results_per_page=20&what={formatted_search}&where={formatted_location}"

                try:
                    response = requests.get(
                        url,
                        timeout=10
                    )
                except requests.exceptions.RequestException as error:
                    print("Adzuna request failed:", error)
                    fetch_successful = False
                    continue

                # print(response.status_code)
                # print(response.text[:300])

                if response.status_code != 200:
                    print("Adzuna request failed:", response.status_code)
                    fetch_successful = False
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

    return all_jobs, fetch_successful
