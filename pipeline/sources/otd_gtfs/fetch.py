"""Fetch the Swiss national GTFS timetable (opentransportdata.swiss, GTFS2020 flavour).

The dataset page lists one resource per feed version (twice weekly). The resource download URL
302-redirects to a presigned Cloudflare R2 URL: HEAD answers 403, GET works (requests follows the
redirect). The feed has no shapes.txt; stops.txt carries a `didok` column.

The feed version is pinned (FEED) so that rebuilds are reproducible; bump it deliberately
(terms of use 5.2: state the feed version/date used in the app).
"""
from __future__ import annotations

from pipeline.common import fetch

SOURCE = "otd_gtfs"
DATASET = "https://data.opentransportdata.swiss/dataset/3d2c18f9-9ef1-463f-a249-5c67604efd74"
# timetable year 2026 (valid 2025-12-14 .. 2026-12-12)
FEEDS = {
    "gtfs_fp2026_20261107.zip": f"{DATASET}/resource/c3608677-bb3c-46c1-94d2-a03731725e00/download/gtfs_fp2026_20261107.zip",
}
FEED = "gtfs_fp2026_20261107.zip"


def gtfs(feed: str = FEED):
    return fetch(FEEDS[feed], SOURCE, feed, timeout=1800)


if __name__ == "__main__":
    print(gtfs())
