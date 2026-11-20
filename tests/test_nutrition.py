from datetime import date


def test_get_food_items(client, auth_headers):
    res = client.get("/api/v1/nutrition/foods", headers=auth_headers)
    assert res.status_code == 200
    foods = res.json()
    assert len(foods) > 0
    names = [f["name"] for f in foods]
    assert any("Paneer" in n for n in names)
    assert any("Whey" in n for n in names)


def test_log_meal_and_check_summary(client, auth_headers):
    foods_res = client.get("/api/v1/nutrition/foods", headers=auth_headers)
    food = foods_res.json()[0]
    food_id = food["id"]

    today_str = str(date.today())
    log_res = client.post("/api/v1/nutrition/logs", json={
        "food_item_id": food_id,
        "meal_type": "Breakfast",
        "servings": 2.0,
        "date": today_str
    }, headers=auth_headers)
    assert log_res.status_code == 201
    log_data = log_res.json()
    assert log_data["servings"] == 2.0
    assert log_data["total_calories"] == round(food["calories"] * 2.0, 1)

    # Check summary
    summary_res = client.get(f"/api/v1/nutrition/summary?log_date={today_str}", headers=auth_headers)
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["calories_consumed"] >= log_data["total_calories"]
    assert summary["protein_consumed_g"] >= log_data["total_protein_g"]
