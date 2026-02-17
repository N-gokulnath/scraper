# College Attendance Data Scraper

Automated scraper to extract attendance data from the student portal for all available months.

## Requirements

- Python 3.7+
- Google Chrome browser
- ChromeDriver (automatically managed by Selenium)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Simply run the script:
```bash
python scrape_attendance.py
```

## What the Script Does

1. **Login**: Navigates to the portal and logs in with your credentials
2. **Navigation**: Goes to Masters > Student Attendance
3. **Data Extraction**: 
   - Identifies all available months in the dropdown
   - Loops through each month
   - Extracts attendance data (dates, status, percentage)
4. **Output**: Saves data as JSON file with timestamp

## Output

The script generates:
- **JSON file**: `attendance_data_YYYYMMDD_HHMMSS.json` with all attendance data
- **Screenshots folder**: `screenshots/` containing screenshots of each major step for verification

## Output Format

```json
{
  "student_id": "2313141033008",
  "scrape_date": "2026-02-08",
  "scrape_timestamp": "2026-02-08T21:30:00",
  "monthly_attendance": [
    {
      "month": "February 2026",
      "total_classes": 20,
      "attended": 18,
      "missed": 2,
      "percentage": "90%",
      "daily_records": [
        {"date": "2026-02-01", "status": "Present"},
        {"date": "2026-02-02", "status": "Absent"},
        ...
      ]
    }
  ]
}
```

## Features

- ✅ Robust element detection with multiple selector strategies
- ✅ Automatic screenshots at each step for debugging
- ✅ Comprehensive error handling
- ✅ Detailed console output with progress tracking
- ✅ Extracts data from ALL available months
- ✅ Clean JSON output format

## Troubleshooting

If the script fails:
1. Check the `screenshots/` folder to see where it failed
2. Verify your credentials are correct
3. Ensure Chrome browser is installed
4. Check the console output for specific error messages

## Notes

- The browser will remain open for 5 seconds after completion so you can verify the results
- All credentials are embedded in the script (as per your requirements)
- Screenshots are saved with timestamps for each execution
