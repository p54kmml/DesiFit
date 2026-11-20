import os
import requests
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000").rstrip("/")
API_PREFIX = f"{BASE_URL}/api/v1"


class DesiFitAPIClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        try:
            data = response.json()
        except Exception:
            data = {"detail": response.text}

        if not response.ok:
            error_msg = data.get("detail", f"Request failed with status {response.status_code}")
            raise Exception(error_msg)
        return data

    # ================= AUTH =================
    def register(self, email: str, username: str, full_name: str, password: str) -> Dict[str, Any]:
        url = f"{API_PREFIX}/auth/register"
        res = requests.post(url, json={
            "email": email,
            "username": username,
            "full_name": full_name,
            "password": password
        }, headers=self._headers(), timeout=10)
        return self._handle_response(res)

    def login(self, username: str, password: str) -> Dict[str, Any]:
        url = f"{API_PREFIX}/auth/login"
        res = requests.post(url, json={
            "username": username,
            "password": password
        }, headers=self._headers(), timeout=10)
        data = self._handle_response(res)
        self.token = data.get("access_token")
        return data

    def get_me(self) -> Dict[str, Any]:
        url = f"{API_PREFIX}/auth/me"
        res = requests.get(url, headers=self._headers(), timeout=10)
        return self._handle_response(res)

    def forgot_password(self, email: str) -> Dict[str, Any]:
        url = f"{API_PREFIX}/auth/forgot-password"
        res = requests.post(url, json={"email": email}, headers=self._headers(), timeout=10)
        return self._handle_response(res)

    def verify_reset_token(self, token: str) -> Dict[str, Any]:
        url = f"{API_PREFIX}/auth/verify-reset-token"
        res = requests.get(url, params={"token": token}, headers=self._headers(), timeout=10)
        return self._handle_response(res)

    def reset_password(self, token: str, new_password: str, confirm_password: str) -> Dict[str, Any]:
        url = f"{API_PREFIX}/auth/reset-password"
        res = requests.post(url, json={
            "token": token,
            "new_password": new_password,
            "confirm_password": confirm_password
        }, headers=self._headers(), timeout=10)
        return self._handle_response(res)

    # ================= PROFILE & ONBOARDING =================
    def get_profile(self) -> Dict[str, Any]:
        url = f"{API_PREFIX}/profile"
        res = requests.get(url, headers=self._headers(), timeout=10)
        return self._handle_response(res)

    def complete_onboarding(self, onboarding_data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{API_PREFIX}/profile/onboard"
        res = requests.post(url, json=onboarding_data, headers=self._headers(), timeout=10)
        return self._handle_response(res)

    def update_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{API_PREFIX}/profile"
        res = requests.put(url, json=profile_data, headers=self._headers(), timeout=10)
        return self._handle_response(res)

    # ================= DASHBOARD =================
    def get_dashboard_stats(self) -> Dict[str, Any]:
        url = f"{API_PREFIX}/dashboard/stats"
        res = requests.get(url, headers=self._headers(), timeout=10)
        return self._handle_response(res)

    # ================= EXERCISES =================
    def get_exercises(self, muscle_group: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{API_PREFIX}/exercises"
        params = {}
        if muscle_group and muscle_group != "All":
            params["muscle_group"] = muscle_group
        if search:
            params["search"] = search
        res = requests.get(url, params=params, headers=self._headers(), timeout=10)
        return self._handle_response(res)

    def create_exercise(self, exercise_data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{API_PREFIX}/exercises"
        res = requests.post(url, json=exercise_data, headers=self._headers(), timeout=10)
        return self._handle_response(res)

    # ================= WORKOUTS =================
    def get_workout_plans(self) -> List[Dict[str, Any]]:
        url = f"{API_PREFIX}/workouts/plans"
        res = requests.get(url, headers=self._headers(), timeout=10)
        return self._handle_response(res)

    def create_workout_plan(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{API_PREFIX}/workouts/plans"
        res = requests.post(url, json=plan_data, headers=self._headers(), timeout=10)
        return self._handle_response(res)

    def delete_workout_plan(self, plan_id: int) -> bool:
        url = f"{API_PREFIX}/workouts/plans/{plan_id}"
        res = requests.delete(url, headers=self._headers(), timeout=10)
        return res.status_code in [200, 204]

    def get_workout_logs(self) -> List[Dict[str, Any]]:
        url = f"{API_PREFIX}/workouts/logs"
        res = requests.get(url, headers=self._headers(), timeout=10)
        return self._handle_response(res)

    def record_workout_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{API_PREFIX}/workouts/logs"
        res = requests.post(url, json=log_data, headers=self._headers(), timeout=10)
        return self._handle_response(res)

    def delete_workout_log(self, log_id: int) -> bool:
        url = f"{API_PREFIX}/workouts/logs/{log_id}"
        res = requests.delete(url, headers=self._headers(), timeout=10)
        return res.status_code in [200, 204]

    # ================= NUTRITION =================
    def get_food_items(self, search: Optional[str] = None, desi_only: bool = False) -> List[Dict[str, Any]]:
        url = f"{API_PREFIX}/nutrition/foods"
        params = {}
        if search:
            params["search"] = search
        if desi_only:
            params["desi_only"] = True
        res = requests.get(url, params=params, headers=self._headers(), timeout=10)
        return self._handle_response(res)

    def create_food_item(self, food_data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{API_PREFIX}/nutrition/foods"
        res = requests.post(url, json=food_data, headers=self._headers(), timeout=10)
        return self._handle_response(res)

    def get_nutrition_logs(self, log_date: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{API_PREFIX}/nutrition/logs"
        params = {"log_date": log_date} if log_date else {}
        res = requests.get(url, params=params, headers=self._headers(), timeout=10)
        return self._handle_response(res)

    def log_meal(self, meal_data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{API_PREFIX}/nutrition/logs"
        res = requests.post(url, json=meal_data, headers=self._headers(), timeout=10)
        return self._handle_response(res)

    def delete_nutrition_log(self, log_id: int) -> bool:
        url = f"{API_PREFIX}/nutrition/logs/{log_id}"
        res = requests.delete(url, headers=self._headers(), timeout=10)
        return res.status_code in [200, 204]

    def get_daily_nutrition_summary(self, log_date: Optional[str] = None) -> Dict[str, Any]:
        url = f"{API_PREFIX}/nutrition/summary"
        params = {"log_date": log_date} if log_date else {}
        res = requests.get(url, params=params, headers=self._headers(), timeout=10)
        return self._handle_response(res)

    # ================= PROGRESS =================
    def get_measurements(self, limit: int = 30) -> List[Dict[str, Any]]:
        url = f"{API_PREFIX}/progress/measurements"
        res = requests.get(url, params={"limit": limit}, headers=self._headers(), timeout=10)
        return self._handle_response(res)

    def record_measurement(self, measurement_data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{API_PREFIX}/progress/measurements"
        res = requests.post(url, json=measurement_data, headers=self._headers(), timeout=10)
        return self._handle_response(res)

    def delete_measurement(self, measurement_id: int) -> bool:
        url = f"{API_PREFIX}/progress/measurements/{measurement_id}"
        res = requests.delete(url, headers=self._headers(), timeout=10)
        return res.status_code in [200, 204]

    # ================= AI ASSISTANT =================
    def chat_ai(self, message: str) -> Dict[str, Any]:
        url = f"{API_PREFIX}/ai/chat"
        res = requests.post(url, json={"message": message}, headers=self._headers(), timeout=30)
        return self._handle_response(res)

    def get_chat_history(self) -> List[Dict[str, Any]]:
        url = f"{API_PREFIX}/ai/history"
        res = requests.get(url, headers=self._headers(), timeout=10)
        return self._handle_response(res)

    def clear_chat_history(self) -> bool:
        url = f"{API_PREFIX}/ai/history"
        res = requests.delete(url, headers=self._headers(), timeout=10)
        return res.status_code in [200, 204]

    def get_ai_status(self) -> Dict[str, Any]:
        url = f"{API_PREFIX}/ai/status"
        res = requests.get(url, headers=self._headers(), timeout=5)
        return self._handle_response(res)
