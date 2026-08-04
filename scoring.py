from config import keywords


def score_job(title, description, location, salary_min):
    score = 0
    matched_keywords = []

    # Title matches
    if "graduate" in title:
        score += 3
    if "junior" in title:
        score += 3
    if "entry level" in title:
        score += 5

    # Role type
    if "software engineer" in title:
        score += 5
        matched_keywords.append("SE-title")
    if "software developer" in title:
        score += 5
        matched_keywords.append("SD-title")
    if "python" in title:
        score += 5
        matched_keywords.append("python-title")
    if "java" in title:
        score += 5
        matched_keywords.append("java-title")
    if "backend" in title:
        score += 4
        matched_keywords.append("backend-title")
    if "games" in title:
        score += 10
        matched_keywords.append("games-title")

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

    # Penalties
    if "intern" in title or "internship" in title:
        score -= 5
    if "sales" in title:
        score -= 8
    if "recruitment" in title:
        score -= 8
    if "consultant" in title and "software" not in title:
        score -= 5
    if "support" in title and "developer" not in title:
        score -= 5

    return score, matched_keywords