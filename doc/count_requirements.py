import csv
from pathlib import Path

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
OUTPUT_FILE = Path("doc/requirements.csv")
MIN_COLUMNS = 2


def matches_value(value: str, patterns: list[str]) -> bool:
    return any(value.startswith(pattern) for pattern in patterns)


def count_file(path: Path) -> tuple[int, int, int]:
    total_count = 0
    ext_count = 0
    con_count = 0

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header is None:
            return total_count, ext_count, con_count

        for row in reader:
            if len(row) < MIN_COLUMNS:
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
                msg = f"Unknown timing: {timing} in file {path}"
                raise ValueError(msg)

    return total_count, ext_count, con_count


def main() -> None:
    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as out_handle:
        writer = csv.writer(out_handle)
        writer.writerow(
            [
                "file",
                "total",
                "weakenable",
                "extension-type",
                "contraction-type",
            ],
        )
        for path in Path().glob(INPUT_GLOB):
            if not path.is_file():
                continue
            total_count, ext_count, con_count = count_file(path)
            name = path.stem
            writer.writerow(
                [
                    name,
                    total_count,
                    ext_count + con_count,
                    ext_count,
                    con_count,
                ],
            )


if __name__ == "__main__":
    main()
