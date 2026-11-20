from datetime import datetime, date
from typing import Optional


def format_date(d: Optional[date]) -> str:
    if not d:
        return "Today"
    if isinstance(d, str):
        return d
    return d.strftime("%b %d, %Y")


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    if height_cm <= 0:
        return 0.0
    height_m = height_cm / 100.0
    return round(weight_kg / (height_m * height_m), 1)


def get_bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 24.9:
        return "Normal weight"
    elif bmi < 29.9:
        return "Overweight"
    else:
        return "Obese"
