# Graduate Job Finder
A Python project that searches graduate and junior software engineering jobs using the Adzuna API.

The project:
- fetches real UK software jobs
- filters irrelevant roles
- scores jobs based on keywords and salary
- removes duplicates
- stores jobs in SQLite
- exports matched/rejected jobs to CSV

## Technologies Used
- Python
- Requests
- SQLite3
- dotenv
- REST APIs

## Setup
Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:
```env
ADZUNA_APP_ID=your_app_id
ADZUNA_API_KEY=your_api_key

REED_API_KEY=your_api_key
```

Run:
```bash
python main.py
```

## Future Improvements
- Flask dashboard
- Email notifications
- Better scoring system
- Multi-source job aggregation

## Author
Cheydon Wiercx
