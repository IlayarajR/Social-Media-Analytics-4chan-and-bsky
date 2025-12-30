# CS515 Complete Project Portfolio - Fall 2025

**Student:** Ilayaraj Rajmohan (irajmohan@binghamton.edu)  
**Partner:** Sanjitha Praveen (spraveen@binghamton.edu)  
**Course:** CS515 - Social Media Data Science Pipelines  
**Instructor:** Professor Jeremy Blackburn  
**University:** Binghamton University

## Overview

This repository contains all three projects from CS515 Fall 2025:

1. **Project 1:** Social media data collection pipeline (4chan + Bluesky)
2. **Project 2:** Dataset measurements and toxicity analysis
3. **Project 3:** Interactive analytics dashboard

## Project Structure
```
cs515_complete_backup/
├── project1_crawler/          # Data collection system
├── project2_analysis/         # Measurement experiments
├── project3_dashboard/        # Interactive web dashboard
├── project3_working_files/    # Development files
└── README.md                  # This file
```

## Project 1: Data Collection Pipeline

**Directory:** `project1_crawler/`

Social media crawler collecting data from:
- 4chan boards (/sp/ - sports, /pol/ - politics)
- Bluesky social network

**Technologies:**
- Python workers with Faktory job queue
- PostgreSQL + TimescaleDB
- systemd services for continuous collection

**Total Data Collected:** 3.96M+ posts (Nov 1-14, 2025)

## Project 2: Dataset Analysis

**Directory:** `project2_analysis/`

Measurement and analysis experiments including:
- Temporal activity patterns (daily, hourly, heatmaps)
- Toxicity scoring via Google Perspective API
- Platform comparisons

**Key Findings:**
- /sp/ spikes on weekends (sports events)
- /pol/ highest toxicity (mean: 0.253)
- Bluesky lowest toxicity (mean: 0.038)

## Project 3: Interactive Dashboard

**Directory:** `project3_dashboard/`

Web-based analytics dashboard answering three research questions:

1. Event-driven engagement patterns
2. Media vs text-only engagement
3. Sports topic distribution

**Technologies:**
- Flask web framework
- Plotly.js interactive visualizations
- LDA topic modeling (scikit-learn)
- PostgreSQL live data

**URL:** Run locally via SSH port forwarding

## Setup & Running

See individual project README files in each directory for detailed instructions.

### Quick Start (Project 3 Dashboard)
```bash
# SSH with port forwarding
ssh -L 5000:localhost:5000 irajmohan@128.226.29.129

# Start dashboard
cd project3_dashboard
python3 app_flask_fast.py

# Open browser
http://localhost:5000
```

## Data Summary

| Source | Posts Collected | Period |
|--------|----------------|--------|
| 4chan /sp/ | 872,140 | Nov 1-14, 2025 |
| 4chan /pol/ | 2,926,367 | Nov 1-14, 2025 |
| Bluesky | 160,411 | Nov 1-14, 2025 |
| **Total** | **3,958,918** | |

## Important Notes

- `.env` files removed (contain sensitive credentials)
- CSV data files removed (too large for Git)
- Python cache cleaned
- Database credentials must be configured locally

## Academic Honesty

All code is original work by Ilayaraj Rajmohan and Sanjitha Praveen.  
See individual HONESTY.md files in each project directory.

## License

Academic project - Binghamton University CS515 Fall 2025

---

**Last Updated:** December 18, 2025
