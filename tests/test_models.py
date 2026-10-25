from pathlib import Path

from pydantic import TypeAdapter

from app.models import OpenMeteoResponse

SAMPLE = Path(__file__).parent.parent / "samples" / "open_meteo.json"


def test_open_meteo_sample_parses():
    locs = TypeAdapter(OpenMeteoResponse).validate_json(SAMPLE.read_text())
    assert len(locs) == 4
    assert all(len(loc.hourly.time) == len(loc.hourly.pm2_5) for loc in locs)
    assert locs[0].timezone == "Asia/Kolkata"
