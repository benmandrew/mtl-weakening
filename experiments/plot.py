import csv
import pathlib

import matplotlib.pyplot as plt
import numpy as np

rows = []
with pathlib.Path("weakenings.csv").open(encoding="utf-8") as f:
    csv_reader = csv.reader(f)
    rows = [
        [0 if x.isspace() or x == "" else int(x) for x in row]
        for row in csv_reader
    ]
    cex_len, left_interval, right_interval = zip(*rows)

fig, ax = plt.subplots()
ax.grid()

ax.set_xticks(np.arange(0, len(cex_len) + 1, 20))
ax.set_yticks(range(max(right_interval) + 1))
ax.plot(right_interval, label="Right Interval")
ax.set_xlabel("Run")
ax.set_ylabel("Value")
ax.set_title("MTL Weakening Results")
ax.legend()
plt.show()
