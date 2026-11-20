from datetime import date


def test_record_body_measurement(client, auth_headers):
    payload = {
        "weight_kg": 72.5,
        "chest_cm": 102.0,
        "waist_cm": 82.0,
        "arm_cm": 38.0,
        "thigh_cm": 58.0,
        "notes": "Starting new hypertrophy cycle",
        "date": str(date.today())
    }
    res = client.post("/api/v1/progress/measurements", json=payload, headers=auth_headers)
    assert res.status_code == 201
    meas = res.json()
    assert meas["weight_kg"] == 72.5
    assert meas["chest_cm"] == 102.0

    # Verify profile current_weight was synced
    prof_res = client.get("/api/v1/profile", headers=auth_headers)
    assert prof_res.status_code == 200
    assert prof_res.json()["current_weight_kg"] == 72.5

    # Fetch list
    list_res = client.get("/api/v1/progress/measurements", headers=auth_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


def test_dashboard_stats(client, auth_headers):
    res = client.get("/api/v1/dashboard/stats", headers=auth_headers)
    assert res.status_code == 200
    stats = res.json()
    assert "current_weight_kg" in stats
    assert "daily_calorie_target" in stats
    assert "weekly_activity" in stats
    assert len(stats["weekly_activity"]) == 7


def test_measurement_limit_returns_most_recent_records_in_chronological_order(client, auth_headers):
    dates = [date(2026, 1, 1), date(2026, 2, 1), date(2026, 3, 1)]
    for idx, measured_on in enumerate(dates):
        res = client.post("/api/v1/progress/measurements", json={
            "weight_kg": 70 + idx, "date": str(measured_on)
        }, headers=auth_headers)
        assert res.status_code == 201

    res = client.get("/api/v1/progress/measurements?limit=2", headers=auth_headers)
    assert res.status_code == 200
    assert [item["date"] for item in res.json()] == ["2026-02-01", "2026-03-01"]
