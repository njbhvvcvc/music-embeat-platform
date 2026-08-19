import time
from collections import deque


class Metrics:
    def __init__(self, window: int = 60):
        self.window = window
        self.latencies: deque = deque()

    def record(self, latency_ms: float):
        self.latencies.append((time.time(), latency_ms))

    def snapshot(self) -> tuple[float, float]:
        now = time.time()
        while self.latencies and self.latencies[0][0] < now - self.window:
            self.latencies.popleft()
        if not self.latencies:
            return 0.0, 0.0
        qps = len(self.latencies) / self.window
        avg = sum(l for _, l in self.latencies) / len(self.latencies)
        return round(qps, 2), round(avg, 2)


metrics = Metrics()