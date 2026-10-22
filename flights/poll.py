"""Fetch live positions for the callsigns in callsigns.txt and print them as JSON.

Runs in GitHub Actions (see .github/workflows/flights.yml). The trip page reads the output from the
flight-data branch, because the ADS-B feeds don't allow browsers on other sites to call them directly.
"""
import json, sys, time, urllib.request
from pathlib import Path

FEEDS = ["https://api.adsb.lol/v2/callsign/{}", "https://opendata.adsb.fi/api/v2/callsign/{}"]
KEEP = ("lat", "lon", "alt_baro", "alt_geom", "gs", "track", "baro_rate", "seen", "t", "r")


def fetch(cs):
    for url in FEEDS:
        try:
            req = urllib.request.Request(url.format(cs), headers={"User-Agent": "scottsdale-trip-page"})
            d = json.load(urllib.request.urlopen(req, timeout=25))
        except Exception as e:
            print(f"{cs}: {url.split('/')[2]} failed: {e}", file=sys.stderr)
            continue
        ac = [a for a in d.get("ac", []) if a.get("lat") is not None]
        if not ac:
            return None
        a = min(ac, key=lambda a: a.get("seen", 999))
        return {k: a[k] for k in KEEP if k in a} | {"at": int(d.get("now", time.time() * 1000))}
    return "error"


out = {"updated": int(time.time() * 1000), "flights": {}}
for cs in Path(__file__).with_name("callsigns.txt").read_text().split():
    out["flights"][cs] = fetch(cs)
    time.sleep(1.1)  # adsb.fi allows one request a second
print(json.dumps(out))
