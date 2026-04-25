def calculate_disparity_ratios(records: list) -> list:
    if not records:
        return []

    signals = []
    data_map: dict = {}
    total_count = 0
    for r in records:
        race = r.get("race_ethnicity", "Unknown")
        count = int(r.get("count", 0))
        data_map[race] = data_map.get(race, 0) + count
        total_count += count

    if total_count == 0:
        return []

    avg_count = total_count / len(data_map)

    for race, count in data_map.items():
        ratio = count / avg_count if avg_count > 0 else 0

        if ratio >= 1.2:
            signals.append(
                {
                    "signal_type": "disparity",
                    "severity": "high" if ratio > 1.5 else "medium",
                    "description": f"Group {race} shows a ratio of {ratio:.2f}x compared to the average.",
                    "metadata": {"ratio": ratio, "count": count, "avg_benchmark": avg_count},
                }
            )

    return signals
