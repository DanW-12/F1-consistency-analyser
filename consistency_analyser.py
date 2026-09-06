"""
Lap Time Consistency Analyser

Splits a driver's race into stints (using FastF1's own stint numbering) and
quantifies how consistent their lap times were within each stint.

Metrics per stint:
    - mean lap time
    - standard deviation
    - IQR (Q3 - Q1)
    - coefficient of variation (std / mean, as a %) -- this is the key metric,
      since it lets you compare consistency across stints run at very
      different absolute paces (e.g. a fuel-heavy opening stint vs a
      late-race sprint on fresh tyres), where raw std dev alone would be
      misleading.
"""
import os
import fastf1
import fastf1.plotting
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


YEAR = 2023
EVENT = "Azerbaijan"
SESSION_TYPE = "R"
DRIVER = "ALO"

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)
fastf1.plotting.setup_mpl(mpl_timedelta_support=False, color_scheme="fastf1")


def load_driver_laps(year, event, session_type, driver):
    """Load a session and return (session, cleaned laps) for one driver."""
    session = fastf1.get_session(year, event, session_type)
    session.load()

    laps = (
        session.laps.pick_drivers(driver)
        .pick_quicklaps()
        .pick_accurate()
        .reset_index(drop=True)
    )
    laps["LapTime(s)"] = laps["LapTime"].dt.total_seconds()
    return session, laps


def stint_consistency(laps):
    """Compute consistency stats for each stint. Returns a tidy DataFrame."""
    rows = []
    for stint_num, stint_laps in laps.groupby("Stint"):
        laptimes = stint_laps["LapTime(s)"]
        mean = laptimes.mean()
        std = laptimes.std()
        q1, q3 = laptimes.quantile([0.25, 0.75])

        rows.append({
            "Stint": int(stint_num),
            "Compound": stint_laps["Compound"].iloc[0],
            "Laps": len(stint_laps),
            "LapRange": f"{int(stint_laps['LapNumber'].min())}-{int(stint_laps['LapNumber'].max())}",
            "MeanLapTime(s)": round(mean, 3),
            "StdDev(s)": round(std, 3),
            "IQR(s)": round(q3 - q1, 3),
            "CV(%)": round(std / mean * 100, 3),
        })

    return (
        pd.DataFrame(rows)
        .sort_values("Stint")
        .reset_index(drop=True)
    )


def plot_consistency(session, laps, summary, driver, year, event):
    """Two-panel figure: lap time scatter shaded by stint, plus a
    stint-by-stint consistency (CV%) bar chart."""
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(9, 10), gridspec_kw={"height_ratios": [2, 1]}
    )

    compound_colors = fastf1.plotting.get_compound_mapping(session=session)

    # --- Top panel: lap times, shaded by stint ---
    sns.scatterplot(
        data=laps, x="LapNumber", y="LapTime(s)",
        hue="Compound", palette=compound_colors,
        s=70, linewidth=0, ax=ax1,
    )

    ymax = laps["LapTime(s)"].max()
    for _, row in summary.iterrows():
        lap_min, lap_max = (int(x) for x in row["LapRange"].split("-"))
        ax1.axvspan(lap_min - 0.5, lap_max + 0.5, color="white", alpha=0.06)
        ax1.text(
            (lap_min + lap_max) / 2, ymax + 0.3, f"Stint {row['Stint']}",
            ha="center", fontsize=9, color="white",
        )

    ax1.invert_yaxis()
    ax1.set_xlabel("Lap Number")
    ax1.set_ylabel("Lap Time (s)")
    ax1.set_title(f"{driver} Lap Times by Stint \u2014 {year} {event} GP")

    # --- Bottom panel: consistency (CV%) per stint ---
    bar_colors = [compound_colors.get(c, "gray") for c in summary["Compound"]]
    bars = ax2.bar(summary["Stint"].astype(str), summary["CV(%)"], color=bar_colors)

    for bar, cv in zip(bars, summary["CV(%)"]):
        ax2.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
            f"{cv:.2f}%", ha="center", fontsize=9,
        )

    ax2.set_xlabel("Stint")
    ax2.set_ylabel("Consistency (CV %, lower = more consistent)")
    ax2.set_title("Stint-by-Stint Consistency")

    plt.tight_layout()
    return fig


if __name__ == "__main__":
    session, laps = load_driver_laps(YEAR, EVENT, SESSION_TYPE, DRIVER)
    summary = stint_consistency(laps)

    print(f"\n{DRIVER} \u2014 {YEAR} {EVENT} GP \u2014 Stint Consistency Summary\n")
    print(summary.to_string(index=False))

    fig = plot_consistency(session, laps, summary, DRIVER, YEAR, EVENT)
    fig.savefig(f"{DRIVER}_{YEAR}_{EVENT}_consistency.png", dpi=150, bbox_inches="tight")
    plt.show()
