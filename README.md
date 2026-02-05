# Healthcare Shift Scheduling App

A Python designed web app for generating 5-week staff rosters with constraint handling, scenario comparison, and multiple export formats.
Started from my Data Analysis with the Red Cross.

## What it does

- **Generates shift schedules** respecting constraints: weekly hours, max consecutive days, rest after night shifts, Sunday availability
- **Balances workload** automatically across employees (morning/afternoon/night/weekend distribution)
- **Compares scenarios**: current staff vs. hiring a new employee (part-time 28h or full-time 38h)
- **Fills gaps** with "Expert Volunteer" when internal coverage isn't enough
- **Exports** to CSV, Excel, and print-ready PDF
- **Visualizes** hours distribution with a simple bar chart

## Project context

This tool addresses a common challenge in healthcare and emergency services: building fair, constraint-compliant rosters when staff is limited. It's particularly useful for small teams where manual scheduling becomes error-prone and time-consuming.

The app lets managers quickly test "what-if" scenarios (e.g., "What if we hire a part-timer?") and see the impact on coverage and volunteer dependency.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at `http://localhost:8501`

## Deploy on Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app** → select your repo → branch `main` → file `app.py`
4. Click **Deploy**

That's it. Streamlit auto-detects `requirements.txt`.

## How to use

**Sidebar:**
- Set start date (must be a Monday)
- Toggle "Expert Volunteer" fallback
- Toggle night shifts and select which days
- Adjust **Randomness** slider (0 = deterministic, 1 = more variation)
- Use fixed seed for reproducible results

**Main panel:**
- Edit staff table (name, weekly hours, night/Sunday availability)
- Set coverage constraints (min staff per shift)
- Optionally add a new employee for scenario comparison
- Click **Generate** or **Regenerate** for a different variant

**Outputs:**
- Comparison table across scenarios
- Weekly calendar view with highlighted gaps
- Hours summary per person with bar chart
- Download buttons: CSV, Excel, PDF

## Outputs

| Format | Content |
|--------|---------|
| CSV | One row per shift assignment (date, shift, assignee) |
| Excel | Two sheets: Calendar + Summary |
| PDF | Print-ready report with weekly tables and KPIs |
| Chart | Bar chart comparing assigned hours vs. target |

## Project structure

```
├── app.py              # Streamlit UI
├── core/
│   ├── scheduler.py    # Scheduling algorithm with randomization
│   ├── exporters.py    # CSV, Excel, PDF export
│   └── utils.py        # Validation and helpers
├── analysis/           # Problem analysis documentation
├── requirements.txt
└── README.md
```

## Documentation

See the [analysis/](analysis/) folder for detailed documentation:
- [Problem Analysis](analysis/Problem_Analysis.md) - Context and approach
- [Constraints and Assumptions](analysis/Constraints_and_Assumptions.md) - Rules and parameters

## Tech stack

Python, Streamlit, Pandas, Matplotlib, ReportLab, OpenPyXL

## Author

Morgan Germinario

---

*Last updated: February 2026*
