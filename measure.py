import csv
import statistics
import sys
import time
from pathlib import Path

import psutil

if len(sys.argv) != 3:
    raise SystemExit("Usage: python3 measure.py BROWSER_PID LABEL")

root = psutil.Process(int(sys.argv[1]))
label = sys.argv[2]
output = Path("benchmarks")
output.mkdir(exist_ok=True)
filename = output / f"{label}-{time.strftime('%Y%m%d-%H%M%S')}.csv"


def snapshot():
    processes = [root] + root.children(recursive=True)
    cpu = {}
    pss = 0
    swap = 0
    missing = 0
    count = 0

    for process in processes:
        try:
            key = (process.pid, process.create_time())
            times = process.cpu_times()
            cpu[key] = times.user + times.system
            count += 1

            try:
                memory = process.memory_full_info()
                pss += memory.pss
                swap += memory.swap
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                missing += 1
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue

    return cpu, pss / 2**20, swap / 2**20, count, missing


previous, *_ = snapshot()
previous_time = time.monotonic()
rows = []

print("Measuring for 60 seconds. Leave the browser tabs unchanged.")

for sample in range(1, 13):
    time.sleep(5)

    try:
        current, pss, swap, count, missing = snapshot()
    except psutil.NoSuchProcess:
        raise SystemExit("Browser exited. Measurement stopped.")

    now = time.monotonic()
    elapsed = now - previous_time

    cpu_seconds = sum(
        max(0, current[key] - previous[key])
        for key in current.keys() & previous.keys()
    )
    cpu_percent = 100 * cpu_seconds / elapsed

    row = {
        "sample": sample,
        "cpu_percent_one_core": round(cpu_percent, 2),
        "pss_mib": round(pss, 2),
        "swap_mib": round(swap, 2),
        "processes": count,
        "memory_unreadable_processes": missing,
    }
    rows.append(row)
    print(
        f"{sample:02d}/12 | CPU {cpu_percent:6.1f}% | "
        f"PSS {pss:7.1f} MiB | swap {swap:6.1f} MiB | "
        f"processes {count} | unreadable {missing}"
    )

    previous = current
    previous_time = now

with filename.open("w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print("\nRESULT:", label)
print("Mean CPU:", round(statistics.mean(
    r["cpu_percent_one_core"] for r in rows
), 2), "%")
print("Mean PSS:", round(statistics.mean(
    r["pss_mib"] for r in rows
), 1), "MiB")
print("Peak sampled PSS:", max(r["pss_mib"] for r in rows), "MiB")
print("CSV saved:", filename)
