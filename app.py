"""
Advanced Disk Scheduling Simulator - Backend
--------------------------------------------
This Flask application:
1. Receives disk scheduling inputs from frontend
2. Runs selected disk scheduling algorithm
3. Calculates performance metrics
4. Sends results back as JSON
"""

from flask import Flask, request, jsonify
from flask_cors import CORS

# Create Flask app
app = Flask(__name__)

# Enable CORS so frontend (HTML/JS) can talk to backend
CORS(app)

# -------------------------------
# Disk Scheduling Algorithms
# -------------------------------

def fcfs(requests, head):
    """
    First Come First Serve Algorithm
    Services requests in the order they arrive
    """
    seek_sequence = [head]
    total_seek_time = 0

    for req in requests:
        total_seek_time += abs(head - req)
        head = req
        seek_sequence.append(head)

    return seek_sequence, total_seek_time


def sstf(requests, head):
    """
    Shortest Seek Time First Algorithm
    Always services the closest request
    """
    remaining = requests.copy()
    seek_sequence = [head]
    total_seek_time = 0

    while remaining:
        # Find request with minimum seek time
        closest = min(remaining, key=lambda x: abs(x - head))
        total_seek_time += abs(head - closest)
        head = closest
        seek_sequence.append(head)
        remaining.remove(closest)

    return seek_sequence, total_seek_time


def scan(requests, head, disk_size):
    """
    SCAN (Elevator Algorithm)
    Head moves in one direction, servicing requests,
    then reverses direction
    """
    left = sorted([r for r in requests if r < head])
    right = sorted([r for r in requests if r >= head])

    seek_sequence = [head]
    total_seek_time = 0

    # Move towards higher tracks first
    for r in right:
        total_seek_time += abs(head - r)
        head = r
        seek_sequence.append(head)

    # Go to end of disk
    total_seek_time += abs(head - (disk_size - 1))
    head = disk_size - 1
    seek_sequence.append(head)

    # Reverse direction
    for r in reversed(left):
        total_seek_time += abs(head - r)
        head = r
        seek_sequence.append(head)

    return seek_sequence, total_seek_time


def cscan(requests, head, disk_size):
    """
    C-SCAN (Circular SCAN Algorithm)
    Head moves in one direction only and jumps back
    """
    left = sorted([r for r in requests if r < head])
    right = sorted([r for r in requests if r >= head])

    seek_sequence = [head]
    total_seek_time = 0

    # Move right
    for r in right:
        total_seek_time += abs(head - r)
        head = r
        seek_sequence.append(head)

    # Go to end
    total_seek_time += abs(head - (disk_size - 1))
    head = disk_size - 1
    seek_sequence.append(head)

    # Jump to beginning
    total_seek_time += (disk_size - 1)
    head = 0
    seek_sequence.append(head)

    # Continue servicing left side
    for r in left:
        total_seek_time += abs(head - r)
        head = r
        seek_sequence.append(head)

    return seek_sequence, total_seek_time


# -------------------------------
# API Endpoint
# -------------------------------

@app.route("/simulate", methods=["POST"])
def simulate():
    """
    Main API endpoint
    Receives JSON data from frontend
    Runs selected algorithm
    Returns results
    """

    data = request.get_json()

    disk_size = int(data["disk_size"])
    requests = list(map(int, data["requests"]))
    head = int(data["head_position"])
    algorithm = data["algorithm"]

    # Run selected algorithm
    if algorithm == "FCFS":
        sequence, total_seek = fcfs(requests, head)

    elif algorithm == "SSTF":
        sequence, total_seek = sstf(requests, head)

    elif algorithm == "SCAN":
        sequence, total_seek = scan(requests, head, disk_size)

    elif algorithm == "CSCAN":
        sequence, total_seek = cscan(requests, head, disk_size)

    else:
        return jsonify({"error": "Invalid Algorithm"}), 400

    # Performance Metrics
    average_seek_time = round(total_seek / len(requests), 2)
    throughput = round(len(requests) / total_seek, 4) if total_seek != 0 else 0

    # Send response to frontend
    return jsonify({
        "seek_sequence": sequence,
        "total_seek_time": total_seek,
        "average_seek_time": average_seek_time,
        "throughput": throughput
    })


# -------------------------------
# Run Flask Server
# -------------------------------

if __name__ == "__main__":
    app.run(debug=True)
