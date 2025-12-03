# engine.py
from dataclasses import dataclass
import copy

@dataclass
class Request:
    id: int
    cylinder: int

class TraceStep:
    def __init__(self, step, head, moved, served_id, cumulative):
        self.step = step
        self.head = head
        self.moved = moved
        self.served_id = served_id
        self.cumulative = cumulative

class SimulationEngine:
    def __init__(self, num_cylinders=200, initial_head=50, initial_direction=1):
        self.num_cylinders = num_cylinders
        self.initial_head = initial_head
        self.initial_direction = 1 if initial_direction >= 0 else -1

    def run(self, requests, algorithm="FCFS"):
        algorithm = algorithm.upper()
        pending = copy.deepcopy(requests)
        trace = []
        head = self.initial_head
        direction = self.initial_direction
        cumulative = 0
        step = 0

        def serve(req):
            nonlocal head, cumulative, step
            dist = abs(req.cylinder - head)
            cumulative += dist
            head = req.cylinder
            trace.append(TraceStep(step, head, dist, req.id, cumulative))
            step += 1

        if algorithm == "FCFS":
            for req in pending:
                serve(req)

        elif algorithm == "SSTF":
            while pending:
                pending.sort(key=lambda r: abs(r.cylinder - head))
                serve(pending.pop(0))

        elif algorithm == "SCAN":
            pending.sort(key=lambda r: r.cylinder)
            while pending:
                candidates = [r for r in pending if (r.cylinder - head) * direction >= 0]
                if candidates:
                    next_req = candidates[0] if direction > 0 else candidates[-1]
                    serve(next_req)
                    pending.remove(next_req)
                else:
                    direction *= -1

        elif algorithm in ("C-SCAN", "CSCAN"):
            pending.sort(key=lambda r: r.cylinder)
            while pending:
                candidates = [r for r in pending if r.cylinder >= head]
                if candidates:
                    serve(candidates[0])
                    pending.remove(candidates[0])
                else:
                    head = 0

        return trace

    def metrics(self, trace):
        if not trace:
            return {"total": 0, "average": 0}
        total = trace[-1].cumulative
        avg = total / len(trace)
        return {"total": total, "average": avg}
