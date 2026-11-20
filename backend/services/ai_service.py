import os
import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from backend.models import User, UserProfile, AIConversation
from backend.services.workout_generator import (
    extract_requested_training_days,
    build_personalized_workout_plan,
    validate_and_enforce_workout_days
)

load_dotenv()


def is_openai_configured() -> bool:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    return bool(api_key and not api_key.startswith("your_") and len(api_key) > 10)


def generate_rule_based_response(
    query: str,
    user: User,
    profile: Optional[UserProfile],
    requested_days_override: Optional[int] = None,
    preferred_split_override: Optional[str] = None
) -> str:
    """Generates rich, profile-personalized responses when OpenAI API is not configured."""
    q = query.lower()
    name = user.full_name or user.username
    goal = profile.fitness_goal if (profile and profile.fitness_goal) else "Fitness"
    diet = profile.dietary_preference if (profile and profile.dietary_preference) else "Balanced"

    # Only use real profile values — never substitute another user's personal data
    has_weight = profile and profile.current_weight_kg
    has_targets = profile and profile.target_calories and profile.target_protein_g

    weight_str = f"{profile.current_weight_kg} kg" if has_weight else "your current weight (please complete your profile)"
    target_cal_str = str(int(profile.target_calories)) if has_targets else "not set — complete your profile to get personalized targets"
    target_pro_str = f"{profile.target_protein_g}g" if has_targets else "not set — complete your profile"

    # For numeric use in calculations (fat-loss deficit, muscle-building targets)
    weight_num = profile.current_weight_kg if has_weight else None
    target_cal_num = int(profile.target_calories) if has_targets else None
    target_pro_num = profile.target_protein_g if has_targets else None

    # 1. Check for specific training days request first (e.g. "Make me a 6-day workout")
    requested_days = requested_days_override or extract_requested_training_days(query)
    is_workout_query = any(k in q for k in ["workout", "routine", "split", "plan", "train", "exercise", "schedule"])
    if requested_days is not None or is_workout_query:
        effective_days = requested_days or (
            profile.workout_frequency_days if (profile and profile.workout_frequency_days) else 4
        )
        return build_personalized_workout_plan(effective_days, user, profile, query_text=query)

    # 2. Nutrition & Protein
    if any(k in q for k in ["diet", "food", "eat", "protein", "nutrition", "calorie", "meal", "macros"]):
        veg_str = (
            "For a Vegetarian/Vegan diet, prioritize: Paneer, Soya Chunks (52g protein per 100g dry), "
            "Moong Dal, Greek Yogurt/Curd, Chickpeas/Chole, and a high-quality Whey or Plant Protein isolate."
            if diet in ["Vegetarian", "Vegan", "Jain"] else
            "For your Non-Vegetarian/Eggetarian diet, prioritize: Grilled Chicken Breast, Whole Eggs, Egg Whites, "
            "Fish (Rohu/Salmon), Paneer, and Whey Protein."
        )
        return (
            f"Namaste {name}! Here is your personalized DesiFit nutrition breakdown for **{goal}**:\n\n"
            f"- **Daily Calorie Target**: ~{target_cal_str}\n"
            f"- **Daily Protein Target**: ~{target_pro_str} (aim for ~1.6g - 2.0g per kg of bodyweight)\n\n"
            f"**Recommended Protein Sources ({diet})**:\n{veg_str}\n\n"
            f"**Key Nutrition Guidelines**:\n"
            f"1. **Macro Distribution**: 40% Carbs (complex sources like Oats, Roti, Brown/Basmati Rice), "
            f"30% Protein, and 30% Healthy Fats (Nuts, Olive/Mustard oil in moderation).\n"
            f"2. **Meal Timing**: Distribute protein evenly across 3-4 meals (~30-40g protein per meal) "
            f"to optimize muscle protein synthesis.\n"
            f"3. **Hydration**: Drink at least 3.5 to 4 Liters of water daily, especially around workout hours."
        )

    # 3. Fat Loss / Cutting / Deficit
    if any(k in q for k in ["fat loss", "lose fat", "burn fat", "lose weight", "weight loss", "cut", "cutting", "shred", "belly", "slim", "cardio"]):
        if target_cal_num:
            deficit_target = f"~{max(1300, target_cal_num - 450)} kcal/day"
        else:
            deficit_target = "a 300–500 kcal deficit from your maintenance (complete your profile for a personalized target)"
        pro_advice = f"~{target_pro_num}g/day" if target_pro_num else "~1.8–2.0g per kg of your bodyweight"
        return (
            f"To achieve effective **Fat Loss** without losing muscle mass ({name}):\n\n"
            f"1. **Moderate Caloric Deficit**: Target {deficit_target}. "
            f"Avoid crash diets which strip away hard-earned muscle.\n"
            f"2. **High Protein Priority**: Keep protein high at {pro_advice} to protect lean muscle tissue.\n"
            f"3. **Resistance Training**: Continue heavy lifting so your body maintains muscle as an essential metabolic asset.\n"
            f"4. **Daily Step Count (NEAT)**: Aim for 8,000 to 10,000 steps daily.\n"
            f"5. **Cardio**: 20-25 minutes of Zone 2 cardio (incline treadmill walk or cycling) 3x per week post-lifting."
        )

    # 4. General Workout Planning & Splits (unspecified days)
    if any(k in q for k in ["workout", "routine", "split", "plan", "train", "exercise", "schedule"]):
        effective_days = requested_days or (profile.workout_frequency_days if (profile and profile.workout_frequency_days) else 4)
        return build_personalized_workout_plan(effective_days, user, profile, query_text=query)

    # 5. Muscle Building / Hypertrophy
    if any(k in q for k in ["muscle", "hypertrophy", "bulk", "bulking", "gain", "bicep", "chest", "size"]):
        pro_advice = f"at least {target_pro_num}g" if target_pro_num else "~1.8–2.0g per kg of your bodyweight"
        weight_line = f"at your current weight of {weight_str}" if has_weight else f"({weight_str})"
        return (
            f"Hey {name}, here is the scientific blueprint for **Muscle Building** {weight_line}:\n\n"
            f"1. **Caloric Surplus / High Protein**: Consume a slight surplus of ~200-300 kcal above maintenance, "
            f"with {pro_advice} of protein daily.\n"
            f"2. **Mechanical Tension & Rep Range**: Train in the 6–12 rep range with 1–2 reps in reserve (RIR). "
            f"Control the eccentric (lowering) phase for 2-3 seconds.\n"
            f"3. **Frequency**: Hit each major muscle group 2 times per week for optimal hypertrophy.\n"
            f"4. **Rest Between Sets**: Rest 2 to 3 minutes on compound lifts (Squats, Bench, Deadlifts) "
            f"and 60-90 seconds on isolation exercises."
        )

    # 6. Recovery & Sleep
    if any(k in q for k in ["recovery", "rest", "sleep", "sore", "soreness", "doms", "injury"]):
        return (
            f"Recovery is where muscle repair and real progress actually occur, {name}:\n\n"
            f"1. **Sleep**: Strive for 7.5 to 8.5 hours of quality, uninterrupted sleep. Growth hormone peaks during deep REM sleep.\n"
            f"2. **Hydration & Electrolytes**: Drink adequate water and include minerals (sodium, potassium, magnesium).\n"
            f"3. **DOMS (Delayed Onset Muscle Soreness)**: Light active recovery (brisk walking, gentle foam rolling, stretching) "
            f"promotes blood circulation and nutrient delivery to sore tissues.\n"
            f"4. **Rest Days**: Take at least 1-2 complete rest days per week from heavy resistance training."
        )

    # General fitness advice fallback
    cal_line = f"Target Calories: **{int(profile.target_calories)} kcal**" if has_targets else "Target Calories: **not set** (complete your profile)"
    pro_line = f"Target Protein: **{profile.target_protein_g}g**" if has_targets else "Target Protein: **not set**"
    return (
        f"Namaste {name}! I am your **DesiFit AI Fitness Companion**.\n\n"
        f"Based on your profile (Goal: **{goal}**, Weight: **{weight_str}**, Diet: **{diet}**):\n"
        f"- {cal_line} | {pro_line}\n\n"
        f"I can help you build custom workout splits, analyze desi & international meals, explain exercise technique, "
        f"and guide your fat loss or muscle building journey. Ask me anything about:\n"
        f"• *'Make me a 6-day workout'* or *'5-day workout split'*\n"
        f"• *'How much protein is in paneer and soya chunks?'*\n"
        f"• *'How should I structure my fat loss meals?'*\n"
        f"• *'Best exercises for bigger shoulders and arms'*"
    )


def process_chat_message(
    user_message: str,
    user: User,
    db: Session,
    requested_days_override: Optional[int] = None,
    preferred_split_override: Optional[str] = None
) -> Dict[str, Any]:
    """Handles chat message using OpenAI or smart rule-based fallback with strict workout validation."""
    profile = user.profile
    api_available = is_openai_configured()
    
    # Dynamic day determination: override > query parsing > profile saved frequency
    requested_days = requested_days_override or extract_requested_training_days(user_message)
    is_workout_query = (
        requested_days is not None or
        any(k in user_message.lower() for k in ["workout", "routine", "split", "plan", "train", "exercise", "schedule"])
    )
    effective_days = requested_days or (
        (profile.workout_frequency_days if (profile and profile.workout_frequency_days) else 4)
        if is_workout_query else None
    )

    # Save user message
    user_record = AIConversation(
        user_id=user.id,
        role="user",
        content=user_message,
        is_fallback=not api_available
    )
    db.add(user_record)
    db.commit()

    reply_text = ""
    is_fallback = True
    system_notes = None

    if api_available:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

            # Fetch recent conversation history
            recent_chats = (
                db.query(AIConversation)
                .filter(AIConversation.user_id == user.id)
                .order_by(AIConversation.created_at.desc())
                .limit(6)
                .all()
            )
            recent_chats.reverse()

            days_directive = ""
            if effective_days:
                pref_split_note = f"\n- User's Configured Split Preference: {profile.preferred_split}" if (profile and profile.preferred_split) else ""
                custom_split_note = f"\n- User's Custom Split Breakdown:\n{profile.custom_split_details}" if (profile and profile.custom_split_details) else ""
                days_directive = (
                    f"\n\nSTRICT REQUIREMENT: The user has requested a {effective_days}-day workout. "
                    f"You MUST generate EXACTLY {effective_days} distinct active training days (labeled Day 1 through Day {effective_days}). "
                    f"Never provide a 4-day routine when {effective_days} days were requested. "
                    f"Never confuse training days with rest/calendar days. "
                    f"For every day include: Day Number & Muscle Groups, Target Muscles, Exercise Names, Sets, Reps, and Rest periods."
                    f"{pref_split_note}{custom_split_note}"
                )

            system_prompt = (
                "You are DesiFit AI, an elite, motivational, and scientifically grounded fitness & nutrition coach. "
                "You specialize in fitness, muscle building, fat loss, exercise execution, and nutrition (including Indian/Desi diets "
                "such as high-protein vegetarian, eggetarian, and non-vegetarian foods as well as international gym standards).\n\n"
                f"User Profile:\n"
                f"- Name: {user.full_name or user.username}\n"
                f"- Age: {profile.age if (profile and profile.age) else 'Unavailable (not set)'}\n"
                f"- Gender: {profile.gender if (profile and profile.gender) else 'Unavailable (not set)'}\n"
                f"- Current Weight: {f'{profile.current_weight_kg} kg' if (profile and profile.current_weight_kg) else 'Unavailable (not set)'}\n"
                f"- Target Weight: {f'{profile.target_weight_kg} kg' if (profile and profile.target_weight_kg) else 'Unavailable (not set)'}\n"
                f"- Fitness Goal: {profile.fitness_goal if (profile and profile.fitness_goal) else 'General Fitness'}\n"
                f"- Experience: {profile.fitness_experience if (profile and profile.fitness_experience) else 'Unavailable (not set)'}\n"
                f"- Diet Preference: {profile.dietary_preference if (profile and profile.dietary_preference) else 'Unavailable (not set)'}\n"
                f"- Activity Level: {profile.activity_level if (profile and profile.activity_level) else 'Unavailable (not set)'}\n"
                f"- Preferred Training Frequency: {f'{profile.workout_frequency_days} days/week' if (profile and profile.workout_frequency_days) else 'Not set'}\n"
                f"- Preferred Workout Split: {profile.preferred_split if (profile and profile.preferred_split) else 'Not set'}\n"
                f"- Daily Target Calories: {f'{profile.target_calories} kcal' if (profile and profile.target_calories) else 'Unavailable (not set)'}\n"
                f"- Daily Target Protein: {f'{profile.target_protein_g} g' if (profile and profile.target_protein_g) else 'Unavailable (not set)'}\n\n"
                "Note: If key profile metrics are marked as 'Unavailable (not set)', do not invent default values; encourage the user to complete their profile in settings or onboarding.\n"
                "Provide actionable, encouraging, and clear markdown responses. Tailor your recommendations specifically to their goals, preferred split, and diet."
                f"{days_directive}"
            )

            messages = [{"role": "system", "content": system_prompt}]
            for chat in recent_chats[:-1]:  # include previous
                messages.append({"role": chat.role, "content": chat.content})
            messages.append({"role": "user", "content": user_message})

            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            raw_reply = completion.choices[0].message.content

            # Validate generated workout plan to enforce exact training days and user split
            reply_text = validate_and_enforce_workout_days(
                raw_reply,
                effective_days,
                user,
                profile,
                query_text=user_message
            )
            is_fallback = False
            system_notes = "Powered by OpenAI API."

        except Exception as e:
            fallback_ans = generate_rule_based_response(
                user_message,
                user,
                profile,
                requested_days_override=requested_days_override,
                preferred_split_override=preferred_split_override
            )
            reply_text = (
                f"> ℹ️ *OpenAI API call encountered an issue ({str(e)}). Switching seamlessly to DesiFit Rule-Based Assistant:*\n\n"
                + fallback_ans
            )
            is_fallback = True
            system_notes = f"API Error: {str(e)}. Fallback mode engaged."
    else:
        reply_text = generate_rule_based_response(
            user_message,
            user,
            profile,
            requested_days_override=requested_days_override,
            preferred_split_override=preferred_split_override
        )
        is_fallback = True
        system_notes = (
            "OpenAI API key not configured in .env. Running on built-in DesiFit Rule-Based Assistant. "
            "To enable live OpenAI responses, add OPENAI_API_KEY to your .env file."
        )

    # Save assistant response
    assistant_record = AIConversation(
        user_id=user.id,
        role="assistant",
        content=reply_text,
        is_fallback=is_fallback
    )
    db.add(assistant_record)
    db.commit()

    return {
        "reply": reply_text,
        "is_fallback": is_fallback,
        "api_connected": api_available and not is_fallback,
        "system_notes": system_notes
    }
