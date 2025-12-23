
#Advanced Disk Scheduling Simulator - Backend

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Disk Scheduling Algorithm


def fcfs(requests, head):
    seq = [head]
    seek = 0
    for r in requests:
        seek += abs(head - r)
        head = r
        seq.append(head)
    return seq, seek


def sstf(requests, head):
    remaining = requests.copy()
    seq = [head]
    seek = 0

    while remaining:
        closest = min(remaining, key=lambda x: abs(x - head))
        seek += abs(head - closest)
        head = closest
        seq.append(head)
        remaining.remove(closest)

    return seq, seek


def scan(requests, head, disk_size):
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
    left = sorted([r for r in requests if r < head])
    right = sorted([r for r in requests if r >= head])

    seq = [head]
    seek = 0

    for r in right:
        seek += abs(head - r)
        head = r
        seq.append(head)

    seek += abs(head - (disk_size - 1))
    head = disk_size - 1
    seq.append(head)

    seek += (disk_size - 1)
    head = 0
    seq.append(head)

    for r in left:
        seek += abs(head - r)
        head = r
        seq.append(head)

    return seq, seek

def look(requests, head):
    left = sorted([r for r in requests if r < head])
    right = sorted([r for r in requests if r >= head])

    seek_sequence = [head]
    total_seek_time = 0

    # Mo
    for r in right:
        total_seek_time += abs(head - r)
        head = r
        seek_sequence.append(head)

    # Revrse direti
    for r in reversed(left):
        total_seek_time += abs(head - r)
        head = r
        seek_sequence.append(head)

    return seek_sequence, total_seek_time

def clook(requests, head):
    left = sorted([r for r in requests if r < head])
    right = sorted([r for r in requests if r >= head])

    seek_sequence = [head]
    total_seek_time = 0

    # Moe right
    for r in right:
        total_seek_time += abs(head - r)
        head = r
        seek_sequence.append(head)

    # Jump to first request on lt disk start)
    if left:
        total_seek_time += abs(head - left[0])
        head = left[0]
        seek_sequence.append(head)

        for r in left:
            total_seek_time += abs(head - r)
            head = r
            seek_sequence.append(head)

    return seek_sequence, total_seek_time


# API: SIMULATE


@app.route("/simulate", methods=["POST"])
def simulate():
    data = request.get_json()

    disk_size = int(data["disk_size"])
    requests = list(map(int, data["requests"]))
    head = int(data["head_position"])
    algo = data["algorithm"]

    if head < 0 or head >= disk_size:
        return jsonify({"error": "Invalid head position"}), 400

    if any(r < 0 or r >= disk_size for r in requests):
        return jsonify({"error": "Invalid request values"}), 400

    if algo == "FCFS":
        seq, seek = fcfs(requests, head)
    elif algo == "SSTF":
        seq, seek = sstf(requests, head)
    elif algo == "SCAN":
        seq, seek = scan(requests, head, disk_size)
    elif algo == "CSCAN":
        seq, seek = cscan(requests, head, disk_size)
    elif algo == "LOOK":
        seq, seek = look(requests, head)
    elif algo == "CLOOK":
        seq, seek = clook(requests, head)
    else:
        return jsonify({"error": "Invalid algorithm"}), 400

    return jsonify({
        "seek_sequence": seq,
        "total_seek_time": seek,
        "average_seek_time": round(seek / len(requests), 2),
        "throughput": round(len(requests) / seek, 4) if seek else 0
    })



# API: COMPARE ALL


@app.route("/compare", methods=["POST"])
def compare():
    data = request.get_json()

    disk_size = int(data["disk_size"])
    requests = list(map(int, data["requests"]))
    head = int(data["head_position"])


    results = {}

    for name, func in [
        ("FCFS", lambda: fcfs(requests, head)),
        ("SSTF", lambda: sstf(requests, head)),
        ("SCAN", lambda: scan(requests, head, disk_size)),
        ("CSCAN", lambda: cscan(requests, head, disk_size)),
        ("LOOK", lambda: look(requests, head)),
        ("CLOOK", lambda: clook(requests, head))

    ]:
        seq, seek = func()
        results[name] = {"total_seek_time": seek}

    best = min(results, key=lambda k: results[k]["total_seek_time"])

    return jsonify({
        "comparison": results,
        "best_algorithm": best
    })


if __name__ == "__main__":
    app.run(debug=True)
