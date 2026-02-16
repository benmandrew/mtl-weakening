#!/usr/bin/env python3
import csv
import glob
import os

EXTENSION_TYPE = [
    "immediately",
    "at the next timepoint",
    "within ",
    "until buttonUnPressOr60Seconds",
    "until (P_insp >= MaxP_insp | inspClock >= inspiratoryTime)",
]

CONTRACTION_TYPE = [
    "for ",
]

NEITHER_TYPE = [
    "eventually",
    "always",
    "until l0",
    "until p",
    "until off",
    "until (diff(r(i),y(i)) < e)",
    "until (diff(setNL,observedNL) > NLmin)",
    "until (diff(setNL,observedNL) < NLmin)",
    "never",
    "after ",
]

INPUT_GLOB = "doc/requirements/*.csv"
OUTPUT_FILE = "doc/requirements.csv"


def matches_value(value: str, patterns: list[str]):
    for pattern in patterns:
        if value.startswith(pattern):
            return True
    return False


def count_file(path):
    total_count = 0
    ext_count = 0
    con_count = 0

    with open(path, newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header is None:
            return total_count, ext_count, con_count

        for row in reader:
            if len(row) < 2:
                continue
            timing = row[1]
            total_count += 1

            if matches_value(timing, EXTENSION_TYPE):
                ext_count += 1
            elif matches_value(timing, CONTRACTION_TYPE):
                con_count += 1
            elif matches_value(timing, NEITHER_TYPE):
                pass
            else:
                raise ValueError(f"Unknown timing: {timing} in file {path}")

    return total_count, ext_count, con_count


def main():
    with open(OUTPUT_FILE, "w", newline="") as out_handle:
        writer = csv.writer(out_handle)
        writer.writerow(["file", "total", "weakenable", "extension-type", "contraction-type"])
        for path in glob.glob(INPUT_GLOB):
            if not os.path.isfile(path):
                continue
            total_count, ext_count, con_count = count_file(path)
            name = os.path.splitext(os.path.basename(path))[0]
            writer.writerow([name, total_count, ext_count + con_count, ext_count, con_count])


if __name__ == "__main__":
    main()
