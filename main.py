# main.py
from engine import SimulationEngine, Request

def parse_requests(input_str):
    nums = list(map(int, input_str.split(",")))
    return [Request(id=i, cylinder=n) for i, n in enumerate(nums)]

def print_trace(trace):
    for t in trace:
        print(f"Step {t.step}: Head at {t.head}, Moved {t.moved}, Served {t.served_id}")

def main():
    print("=== Disk Scheduling Simulator ===")
    req_input = input("Enter request cylinders (comma separated): ")
    requests = parse_requests(req_input)
    initial = int(input("Initial head position: "))

    engine = SimulationEngine(initial_head=initial)

    for alg in ["FCFS", "SSTF", "SCAN", "C-SCAN"]:
        trace = engine.run(requests, algorithm=alg)
        metrics = engine.metrics(trace)
        print("\n---", alg, "---")
        print("Total head movement:", metrics["total"])
        print("Average seek:", metrics["average"])
        print_trace(trace)

if __name__ == "__main__":
    main()
