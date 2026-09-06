# F1 Lap Time Consistency Analyser

A tool for measuring how consistent a Formula 1 driver's lap times were during a race, stint by stint. Pick a year, event, session, and driver in a simple web UI, and get back consistency stats plus a plot.



## What it does

For a chosen driver and session, the tool splits the race into stints (using FastF1's own stint numbering) and computes, per stint:

- **Mean lap time**
- **Standard deviation**
- **Interquartile range (IQR)**
- **Coefficient of variation (CV%)** — the key metric

CV% (`std dev / mean`, as a percentage) is what makes stints comparable. Raw standard deviation is misleading when comparing, say, a fuel-heavy opening stint to a late-race sprint on fresh tyres, because those stints run at very different absolute paces. CV% normalises for that, so a lower CV% reliably means "more consistent," regardless of how fast the stint was.

## Example

In the 2023 Azerbaijan GP, Alonso's medium-tyre opening stint had a CV of **0.47%**, while his hard-tyre stint had a CV of **0.93%** — meaning his lap times were about twice as consistent on the mediums, even though the two stints were run at different absolute paces.

## Tech stack

- [FastF1](https://github.com/theOehrly/Fast-F1) — official F1 timing data
- pandas — data wrangling
- matplotlib / seaborn — plotting
- Streamlit — interactive web UI

## How to run

```bash
git clone <your-repo-url>
cd <your-repo-name>
pip install -r requirements.txt
streamlit run app.py
```

This opens the app in your default browser. Pick a year, event, session type, and driver in the sidebar, click **Load session**, and the consistency summary and plot will appear.

> Note: the first load for a given session can take a minute while FastF1 downloads and caches timing data. Subsequent loads of the same session are much faster thanks to local caching.

## Project structure

```
.
├── app.py                     # Streamlit GUI
├── consistency_analyser.py    # Core analysis + plotting logic
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.9+
- streamlit
- fastf1
- pandas
- matplotlib
- seaborn

## License

MIT
