# Graduate Job Finder

A Python application that searches, filters, scores and tracks graduate and junior software engineering jobs from multiple job APIs.

The project is designed to reduce the amount of manual searching involved in finding suitable entry-level software roles.

## Features

* Fetches UK software jobs from the Adzuna and Reed APIs
* Searches multiple job titles and locations
* Normalises job data from different APIs into a common format
* Filters unsuitable or overly senior roles
* Scores jobs based on technologies, job title and salary
* Removes duplicate jobs across multiple sources
* Stores accepted jobs in SQLite
* Tracks when jobs were first found and last seen
* Marks stale jobs as inactive
* Tracks whether jobs have been applied for
* Displays top and unapplied jobs through a CLI
* Includes an early Flask web interface for viewing active unapplied jobs
* Uses environment variables for API credentials
* Includes automated tests for scoring, filtering, database operations, API importers and job processing

## Technologies Used

* Python
* Flask
* SQLite
* Requests
* python-dotenv
* REST APIs
* unittest
* Git / GitHub

## Project Structure

```text
graduate-job-finder/
├── main.py
├── database.py
├── scoring.py
├── job_service.py
├── config.py
├── app.py
├── importers/
│   ├── adzuna.py
│   └── reed.py
├── templates/
│   └── index.html
├── tests/
│   ├── test_scoring.py
│   ├── test_database.py
│   ├── test_adzuna.py
│   ├── test_reed.py
│   └── test_job_service.py
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

Clone the repository and create a Python virtual environment.

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
ADZUNA_APP_ID=your_app_id
ADZUNA_API_KEY=your_api_key
REED_API_KEY=your_api_key
```

API credentials are not stored in the repository.

## Running the CLI

Run:

```bash
python main.py
```

The CLI can currently:

1. Fetch new jobs
2. View top jobs
3. Mark a job as applied
4. View applied jobs
5. View top unapplied jobs
6. Remove a job

## Running the Flask Interface

Run:

```bash
python app.py
```

The current Flask interface is an early proof of concept and displays active jobs that have not yet been applied for.

## Running Tests

Run the full test suite with:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

## Job Scoring and Filtering

Jobs are scored using configurable rules in `config.py`.

Examples include:

* graduate and junior job titles
* Java, Python and C++
* backend development
* API and REST experience
* game development technologies
* salary level

Jobs can also be rejected when they contain unsuitable criteria such as senior-level titles or excessive experience requirements.

## Data Storage

SQLite is used as the application's current single source of truth.

Each stored job includes information such as:

* title
* company
* location
* salary
* source
* URL
* score
* date first found
* date last seen
* active/inactive state
* applied state

The local database is excluded from Git because it contains runtime and user-specific data.

## Future Improvements

The next major phase is to replace the current proof-of-concept Flask interface with a Django web application.

Planned improvements include:

* full browser-based job management
* richer application statuses such as saved, applied, interviewing, rejected and offer
* notes and application deadlines
* coding assessment and interview tracking
* improved job recommendation explanations
* additional job sources
* scheduled job imports
* multi-user support
* PostgreSQL
* deployment as a web application
* possible Progressive Web App support

## Author

Cheydon Wiercx
