import csv
from config import locations, keywords, banned_phrases

matched_jobs = []
rejected_jobs = []

#func to score job
def score_job(description, location):
    score = 0
    matched_keywords = []

    for keyword, points in keywords.items():
        if keyword in description:
            score += points
            matched_keywords.append(keyword)
    return score, matched_keywords

#func to reject job
def reject_job(job, reasons):
    job["rejection_reason"] = reasons
    rejected_jobs.append(job)

#func to read job file
def load_jobs(filename):
    with open(filename, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for job in reader:

            title = job["title"].lower()
            description = job["description"].lower()
            location = job["location"].lower()

            score, matched_keywords = score_job(description, location)
            reasons = [] # reasons for rejecting

            if "graduate" not in title and "junior" not in title:
                reasons.append("Title not junior or graduate")

            if any(phrase in description for phrase in banned_phrases):
                reasons.append("Experience level too high")

            if not any(place in location for place in locations):
                reasons.append("Location not allowed")

            if len(reasons) == 0:
                job["score"] = score
                job["matched_keywords"] = ", ".join(matched_keywords)
                matched_jobs.append(job)

                print(job["title"], "-", job["company"], "- Score:", score, "- Matched keywords:", job["matched_keywords"])

            else:
                reject_job(job, "; ".join(reasons))

    # sort by score
    matched_jobs.sort(key=lambda job: job["score"], reverse=True)

#func to save to csv file
def save_csv(filename, data, fieldnames):
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(data)

def main():
    load_jobs("jobs.csv")

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

main()