# Advanced Disk Scheduling Simulator

A web-based simulator to visualize and compare disk scheduling algorithms used in Operating Systems.

## Features
- Disk scheduling algorithms:
  - FCFS
  - SSTF
  - SCAN (Left / Right direction)
  - C-SCAN
- Custom disk size, request queue, and head position
- Animated disk head movement
- Performance metrics:
  - Total seek time
  - Average seek time
  - Throughput
- Compare all algorithms using bar chart
- Best algorithm recommendation
- Step-by-step execution table
- CSV report download
- Dark mode UI
- Input validation with error messages

## Technologies Used
- Frontend: HTML, CSS, JavaScript, Bootstrap, Chart.js
- Backend: Python, Flask, Flask-CORS

## Project Structure
backend/
app.py
requirements.txt

frontend/
index.html
style.css
script.js

## How to Run

### Backend
cd backend
pip install -r requirements.txt
python app.py

markdown
Copy code

### Frontend
- Open `frontend/index.html` in a web browser  
OR
cd frontend
python -m http.server 8000

pgsql
Copy code

## Purpose
This project is developed for educational purposes to help understand disk scheduling algorithms and analyze their performance through visualization.

## Note
Ensure the Flask backend is running before using the frontend.