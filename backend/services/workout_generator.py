import re
from typing import Optional, List, Dict, Any
from backend.models import User, UserProfile


EXERCISE_DATABASE = {
    "chest": [
        {"name": "Barbell Flat Bench Press", "type": "compound", "target": "Middle & Lower Pectorals"},
        {"name": "Incline Dumbbell Bench Press", "type": "compound", "target": "Clavicular (Upper) Pectorals"},
        {"name": "Cable Chest Flyes", "type": "isolation", "target": "Sternal Pecs Peak Contraction"},
        {"name": "Dips (Chest Focus)", "type": "compound", "target": "Lower Pectorals"},
        {"name": "Push-Ups", "type": "compound", "target": "Pectorals & Core"}
    ],
    "back": [
        {"name": "Conventional Barbell Deadlift", "type": "compound", "target": "Posterior Chain, Trapezius & Lats"},
        {"name": "Barbell Bent-Over Row", "type": "compound", "target": "Latissimus Dorsi & Rhomboids"},
        {"name": "Lat Pulldown (Wide Grip)", "type": "compound", "target": "Upper Lats & Teres Major"},
        {"name": "Seated Cable Row (Close Grip)", "type": "compound", "target": "Mid-Back Thickness & Lower Lats"},
        {"name": "Single-Arm Dumbbell Row", "type": "compound", "target": "Unilateral Lat Development"}
    ],
    "shoulders": [
        {"name": "Overhead Barbell Military Press", "type": "compound", "target": "Anterior & Lateral Deltoids"},
        {"name": "Seated Dumbbell Shoulder Press", "type": "compound", "target": "Anterior & Lateral Deltoids"},
        {"name": "Dumbbell Lateral Raises", "type": "isolation", "target": "Lateral (Side) Deltoids"},
        {"name": "Cable Face Pulls", "type": "isolation", "target": "Rear Deltoids & Rotator Cuff"},
        {"name": "Reverse Pec Deck Flyes", "type": "isolation", "target": "Posterior Deltoids"}
    ],
    "biceps": [
        {"name": "Standing Barbell Bicep Curl", "type": "isolation", "target": "Biceps Brachii (Short & Long Head)"},
        {"name": "Incline Dumbbell Hammer Curls", "type": "isolation", "target": "Brachialis & Brachioradialis"},
        {"name": "Preacher EZ-Bar Curl", "type": "isolation", "target": "Biceps Peak Isolation"},
        {"name": "Cable Rope Hammer Curls", "type": "isolation", "target": "Forearms & Brachialis"}
    ],
    "triceps": [
        {"name": "Triceps Cable Rope Pushdown", "type": "isolation", "target": "Lateral & Medial Triceps Heads"},
        {"name": "Skull Crushers (Lying EZ-Bar Extension)", "type": "isolation", "target": "Triceps Long Head"},
        {"name": "Overhead Dumbbell Triceps Extension", "type": "isolation", "target": "Triceps Long Head Stretch"},
        {"name": "Close-Grip Barbell Bench Press", "type": "compound", "target": "Triceps & Inner Chest"}
    ],
    "legs": [
        {"name": "Barbell Back Squats", "type": "compound", "target": "Quadriceps & Gluteus Maximus"},
        {"name": "Romanian Deadlift (RDL)", "type": "compound", "target": "Hamstrings & Gluteal Fold"},
        {"name": "Leg Press Machine", "type": "compound", "target": "Quadriceps & Adductors"},
        {"name": "Walking Dumbbell Lunges", "type": "compound", "target": "Glutes, Quads & Stabilizers"},
        {"name": "Lying Leg Curls", "type": "isolation", "target": "Hamstring Knee Flexion"},
        {"name": "Standing Calf Raises", "type": "isolation", "target": "Gastrocnemius & Soleus"}
    ],
    "arms": [
        {"name": "Standing Barbell Bicep Curl", "type": "isolation", "target": "Biceps Brachii"},
        {"name": "Incline Dumbbell Hammer Curls", "type": "isolation", "target": "Brachialis & Forearms"},
        {"name": "Skull Crushers (Lying Tricep Extension)", "type": "isolation", "target": "Triceps Long Head"},
        {"name": "Triceps Cable Rope Pushdown", "type": "isolation", "target": "Triceps Lateral Head"}
    ],
    "abs": [
        {"name": "Hanging Leg Raises", "type": "isolation", "target": "Lower Rectus Abdominis"},
        {"name": "Plank Hold", "type": "isolation", "target": "Transverse Abdominis & Core Stability"}
    ]
}


def extract_requested_training_days(query: str, profile: Optional[UserProfile] = None) -> Optional[int]:
    """Extracts explicit number of training days requested by user (1 to 7) from query or profile."""
    q = query.lower()
    word_to_num = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7
    }

    # Regex patterns capturing days
    patterns = [
        r'\b([1-7])\s*[-]?\s*days?\b',
        r'\b(one|two|three|four|five|six|seven)\s*[-]?\s*days?\b',
        r'\btrain\s*(?:for\s*)?([1-7]|one|two|three|four|five|six|seven)\s*days?\b',
        r'\b([1-7]|one|two|three|four|five|six|seven)\s*(?:times|x)\s*(?:a|per)\s*week\b',
        r'\bsplit\s*(?:of|for)?\s*([1-7]|one|two|three|four|five|six|seven)\b',
        r'\bworkout\s*(?:for)?\s*([1-7]|one|two|three|four|five|six|seven)\s*days?\b',
        r'\b([1-7]|one|two|three|four|five|six|seven)\s*day\s*split\b'
    ]

    for pat in patterns:
        m = re.search(pat, q)
        if m:
            val = m.group(1).lower()
            return word_to_num.get(val, int(val) if val.isdigit() else None)

    # Check if query contains an enumerated split list (e.g. 1. Chest ... 2. Back ... 6. Back ... 7. Rest)
    day_matches = re.findall(r'(?:day\s*(\d+)|\b(\d+)\.\s*[A-Za-z]+)', q)
    if day_matches:
        numbers = [int(m[0] or m[1]) for m in day_matches if (m[0] or m[1]).isdigit()]
        if numbers:
            max_day = max(numbers)
            # If 7 days with rest, active days is 6
            if max_day in [6, 7]:
                return 6 if ("rest" in q or max_day == 6) else max_day

    # Do not infer a workout request from profile frequency alone. Callers should
    # apply the saved frequency only after establishing that the message is about
    # workout planning; otherwise nutrition questions can become workout plans.
    return None


def count_training_days(text: str) -> int:
    """Counts the number of distinct active training days defined in a response text."""
    seen_days = set()
    lines = text.split("\n")
    for line in lines:
        m = re.search(r'\bDay\s*(\d+)\b', line, re.IGNORECASE)
        if m:
            d_num = int(m.group(1))
            # Check if this line is a rest/recovery day
            is_rest = any(r in line.lower() for r in ["rest", "recovery", "off day", "mobility only", "stretching only"])
            if not is_rest and d_num not in seen_days:
                seen_days.add(d_num)
    return len(seen_days)


def parse_split_schedule(text: str) -> Optional[List[Dict[str, str]]]:
    """Parses a structured line-by-line custom split schedule from text if present."""
    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
    parsed = []
    for line in lines:
        # Match '1. Chest + Triceps' or 'Day 1: Chest + Triceps'
        m = re.search(r'(?:Day\s*)?(\d+)[:\.\-\)]\s*(.+)', line, re.IGNORECASE)
        if m:
            d_num = int(m.group(1))
            focus = m.group(2).strip()
            is_rest = any(r in focus.lower() for r in ["rest", "recovery", "off"])
            parsed.append({"day": d_num, "focus": focus, "is_rest": is_rest})
    return parsed if len(parsed) >= 3 else None


def get_rep_rest_schemes(goal: str):
    goal_l = goal.lower()
    if "strength" in goal_l:
        return "4-6 reps", "6-8 reps", "2-3 mins", "90s"
    elif "fat loss" in goal_l or "cutting" in goal_l:
        return "8-10 reps", "12-15 reps", "60-90s", "45-60s"
    elif "endurance" in goal_l:
        return "12-15 reps", "15-20 reps", "45-60s", "30-45s"
    else:  # Hypertrophy / Muscle Gain
        return "6-10 reps", "10-12 reps", "90-120s", "60-75s"


def generate_day_exercises(focus: str, comp_reps: str, iso_reps: str, comp_rest: str, iso_rest: str) -> Dict[str, Any]:
    """Dynamically assigns matching exercises from EXERCISE_DATABASE for specified muscle groups."""
    f = focus.lower()
    exercises = []
    target_muscles = []

    # Map target muscle groups
    has_chest = "chest" in f or "pec" in f
    has_triceps = "tricep" in f or "tri" in f
    has_back = "back" in f or "lat" in f
    has_biceps = "bicep" in f or "bi" in f
    has_legs = "leg" in f or "quad" in f or "hamstring" in f
    has_shoulders = "shoulder" in f or "delt" in f
    has_arms = ("arm" in f or ("bicep" in f and "tricep" in f)) and not (has_chest or has_back)

    if has_chest:
        target_muscles.append("Pectoralis Major & Minor")
        exercises.append(f"**Barbell Flat Bench Press**: 4 sets × {comp_reps} | Rest: {comp_rest} *(Explosive drive, full control)*")
        exercises.append(f"**Incline Dumbbell Press**: 3 sets × {iso_reps} | Rest: {iso_rest} *(Targets clavicular upper chest)*")
        if not has_shoulders:
            exercises.append(f"**Cable Chest Flyes**: 3 sets × 12-15 reps | Rest: 60s *(Continuous tension and peak stretch)*")

    if has_triceps and not has_arms:
        target_muscles.append("Triceps Brachii (All 3 Heads)")
        exercises.append(f"**Triceps Cable Rope Pushdown**: 4 sets × {iso_reps} | Rest: 60s *(Flared contraction at lockout)*")
        exercises.append(f"**Overhead Dumbbell Triceps Extension**: 3 sets × {iso_reps} | Rest: 60s *(Maximizes long-head stretch)*")

    if has_back:
        target_muscles.append("Latissimus Dorsi, Rhomboids & Trapezius")
        if has_shoulders:
            exercises.append(f"**Conventional Deadlift or Barbell Row**: 4 sets × {comp_reps} | Rest: {comp_rest} *(Braced core, neutral spine)*")
            exercises.append(f"**Lat Pulldown (Wide Grip)**: 3 sets × {iso_reps} | Rest: {iso_rest} *(Elbows driving to hips)*")
            exercises.append(f"**Seated Cable Row (Close Grip)**: 3 sets × {iso_reps} | Rest: 60s")
        else:
            exercises.append(f"**Barbell Bent-Over Row**: 4 sets × {comp_reps} | Rest: {comp_rest} *(Full lat contraction)*")
            exercises.append(f"**Lat Pulldown (Wide Grip)**: 3 sets × {iso_reps} | Rest: {iso_rest}")
            exercises.append(f"**Seated Cable Row (Close Grip)**: 3 sets × {iso_reps} | Rest: 60s")

    if has_biceps and not has_arms:
        target_muscles.append("Biceps Brachii & Brachialis")
        exercises.append(f"**Standing Barbell Bicep Curl**: 4 sets × {iso_reps} | Rest: 60s *(Strict form, no hip swinging)*")
        exercises.append(f"**Incline Dumbbell Hammer Curls**: 3 sets × {iso_reps} | Rest: 60s *(Builds forearm & brachialis thickness)*")

    if has_legs:
        target_muscles.append("Quadriceps, Hamstrings, Glutes & Calves")
        exercises.append(f"**Barbell Back Squats**: 4 sets × {comp_reps} | Rest: {comp_rest} *(Full depth, heels grounded)*")
        exercises.append(f"**Romanian Deadlift (RDL)**: 4 sets × {comp_reps} | Rest: {comp_rest} *(Hips back, hamstring stretch)*")
        exercises.append(f"**Leg Press Machine**: 3 sets × {iso_reps} | Rest: {iso_rest}")
        exercises.append(f"**Walking Dumbbell Lunges**: 3 sets × 10 reps/leg | Rest: 60s")
        exercises.append(f"**Standing Calf Raises**: 4 sets × 15 reps | Rest: 45s")

    if has_shoulders:
        target_muscles.append("Anterior, Lateral & Posterior Deltoids")
        exercises.append(f"**Overhead Barbell Military Press**: 4 sets × {comp_reps} | Rest: {comp_rest} *(Overhead lockout, tight glutes)*")
        exercises.append(f"**Dumbbell Lateral Raises**: 4 sets × 12-15 reps | Rest: 60s *(Elbows lead upward for round shoulders)*")
        exercises.append(f"**Cable Face Pulls**: 3 sets × 15 reps | Rest: 60s *(Shoulder health and rear delt focus)*")

    if has_arms:
        target_muscles.append("Biceps Brachii, Brachialis & Triceps Brachii")
        exercises.append(f"**Standing Barbell Bicep Curl**: 4 sets × {iso_reps} | Rest: 60s")
        exercises.append(f"**Incline Dumbbell Hammer Curls**: 3 sets × {iso_reps} | Rest: 60s")
        exercises.append(f"**Preacher EZ-Bar Curls**: 3 sets × {iso_reps} | Rest: 60s")
        exercises.append(f"**Skull Crushers (Lying EZ-Bar Extension)**: 4 sets × {iso_reps} | Rest: 60s")
        exercises.append(f"**Triceps Cable Rope Pushdown**: 4 sets × {iso_reps} | Rest: 60s")

    # If no specific matches, default balanced compound exercises
    if not exercises:
        target_muscles.append(focus)
        exercises.append(f"**Compound Lift**: 4 sets × {comp_reps} | Rest: {comp_rest}")
        exercises.append(f"**Secondary Movement**: 3 sets × {iso_reps} | Rest: {iso_rest}")
        exercises.append(f"**Isolation Finisher**: 3 sets × 12-15 reps | Rest: 60s")

    # Format numbered list
    ex_list = "\n".join([f"  {i+1}. {ex}" for i, ex in enumerate(exercises)])
    target_str = ", ".join(target_muscles) if target_muscles else focus

    return {
        "target": target_str,
        "exercises": ex_list
    }


def build_custom_split_routine(
    schedule: List[Dict[str, Any]],
    user: User,
    profile: Optional[UserProfile],
    goal: str,
    exp: str,
    header: str
) -> str:
    """Builds a complete, formatted markdown routine from a custom parsed schedule."""
    comp_reps, iso_reps, comp_rest, iso_rest = get_rep_rest_schemes(goal)
    active_days = [d for d in schedule if not d["is_rest"]]
    rest_days = [d for d in schedule if d["is_rest"]]

    sections = [
        f"{header} + **{len(rest_days)} Dedicated Rest Day{'s' if len(rest_days) > 1 else ''}**.\n"
        f"This personalized program is directly tailored to your preferred muscle group schedule.",
        "\n---"
    ]

    for item in schedule:
        d_num = item["day"]
        focus = item["focus"]
        if item["is_rest"]:
            sections.append(
                f"\n### **Day {d_num}: Dedicated Rest & Active Recovery**\n"
                f"- **🎯 Focus**: Rest, muscular regeneration, CNS reset, hydration & light mobility.\n"
                f"- **Activities**: 20-30 min gentle walk, gentle stretching, sleep optimization."
            )
        else:
            day_data = generate_day_exercises(focus, comp_reps, iso_reps, comp_rest, iso_rest)
            sections.append(
                f"\n### **Day {d_num}: {focus}**\n"
                f"- **🎯 Target Muscles**: {day_data['target']}\n"
                f"- **Exercises**:\n{day_data['exercises']}"
            )
        sections.append("\n---")

    rest_summary = f"Only Day {rest_days[0]['day']} is the rest day" if len(rest_days) == 1 else f"Days {', '.join(str(d['day']) for d in rest_days)} are rest days"
    sections.append(
        f"\n### **Summary**: Exactly **{len(active_days)} Active Training Days** + **{len(rest_days)} Rest Day{'s' if len(rest_days) > 1 else ''}** ({rest_summary})."
    )

    return "\n".join(sections)


def build_personalized_workout_plan(
    days: int,
    user: User,
    profile: Optional[UserProfile],
    query_text: Optional[str] = None
) -> str:
    """Constructs an exact N-day workout split strictly matching the requested training frequency and split."""
    name = user.full_name or user.username
    goal = (profile.fitness_goal if profile and profile.fitness_goal else "Muscle Gain")
    exp = (profile.fitness_experience if profile and profile.fitness_experience else "Intermediate")

    comp_reps, iso_reps, comp_rest, iso_rest = get_rep_rest_schemes(goal)

    header = (
        f"Namaste {name}! Here is your customized **{days}-Day Workout Routine** "
        f"optimized for **{goal}** ({exp} level).\n\n"
        f"📌 **Schedule Structure**: Exactly **{days} Active Training Days**"
    )

    # 1. Check if user provided custom day-by-day split in query or profile
    custom_text = None
    if query_text and any(k in query_text.lower() for k in ["chest + triceps", "chest and triceps", "chest+triceps", "back + biceps", "back+biceps"]):
        custom_text = query_text
    elif profile and profile.custom_split_details:
        custom_text = profile.custom_split_details

    if custom_text:
        parsed_schedule = parse_split_schedule(custom_text)
        if parsed_schedule:
            return build_custom_split_routine(parsed_schedule, user, profile, goal, exp, header)

    # 2. Check if preferred_split in profile matches the 6-Day split with chest/back/legs/chest+shoulders/arms/back+shoulders
    pref_split = (profile.preferred_split or "").lower() if profile else ""
    is_user_6day_custom = (
        "chest+tri" in pref_split or
        "chest + triceps" in pref_split or
        ("chest" in pref_split and "shoulders" in pref_split and "arms" in pref_split)
    )

    # 3. Dedicated 6-Day split handling
    if days == 6:
        # If user has configured or requested the specific 6-day split:
        # Day 1: Chest + Triceps
        # Day 2: Back + Biceps
        # Day 3: Legs
        # Day 4: Chest + Shoulders
        # Day 5: Arms (Biceps + Triceps)
        # Day 6: Back + Shoulders
        # Day 7: Rest
        if is_user_6day_custom or (query_text and any(k in query_text.lower() for k in ["chest", "shoulders", "arms", "biceps", "triceps"])):
            body = f"""{header} + **1 Dedicated Rest Day** (Only Day 7 is the rest day).
This personalized 6-day split prioritizes muscle frequency, strategic chest/back development, and focused arm hypertrophy with balanced joint recovery.

---

### **Day 1: Chest + Triceps**
- **🎯 Target Muscles**: Pectoralis Major (Middle & Lower Pecs), Triceps Brachii
- **Exercises**:
  1. **Barbell Flat Bench Press**: 4 sets × {comp_reps} | Rest: {comp_rest} *(Explosive drive from chest, controlled eccentric)*
  2. **Incline Dumbbell Press**: 3 sets × {iso_reps} | Rest: {iso_rest} *(Targets clavicular upper chest)*
  3. **Cable Chest Flyes**: 3 sets × 12-15 reps | Rest: 60s *(Peak squeeze at center, wide stretch)*
  4. **Triceps Cable Rope Pushdown**: 4 sets × {iso_reps} | Rest: 60s *(Flare rope apart at bottom lockout)*
  5. **Overhead Dumbbell Triceps Extension**: 3 sets × {iso_reps} | Rest: 60s *(Full stretch on long head of triceps)*

---

### **Day 2: Back + Biceps**
- **🎯 Target Muscles**: Latissimus Dorsi, Rhomboids, Middle Trapezius, Biceps Brachii
- **Exercises**:
  1. **Barbell Bent-Over Row**: 4 sets × {comp_reps} | Rest: {comp_rest} *(Torso at 45°, pull to lower ribcage)*
  2. **Lat Pulldown (Wide Grip)**: 3 sets × {iso_reps} | Rest: {iso_rest} *(Drive elbows downward for maximum lat width)*
  3. **Seated Cable Row (Close Grip)**: 3 sets × {iso_reps} | Rest: 60s *(Squeeze shoulder blades firmly together)*
  4. **Standing Barbell Bicep Curl**: 4 sets × {iso_reps} | Rest: 60s *(Strict execution, elbows pinned)*
  5. **Incline Dumbbell Hammer Curls**: 3 sets × {iso_reps} | Rest: 60s *(Targets brachialis for arm thickness)*

---

### **Day 3: Legs**
- **🎯 Target Muscles**: Quadriceps, Hamstrings, Gluteus Maximus, Calves
- **Exercises**:
  1. **Barbell Back Squats**: 4 sets × {comp_reps} | Rest: {comp_rest} *(Full depth, drive through mid-foot)*
  2. **Romanian Deadlift (RDL)**: 4 sets × {comp_reps} | Rest: {comp_rest} *(Hips pushed back, feel deep hamstring stretch)*
  3. **Leg Press Machine**: 3 sets × {iso_reps} | Rest: {iso_rest} *(Feet shoulder-width on platform)*
  4. **Walking Dumbbell Lunges**: 3 sets × 10 reps/leg | Rest: 60s
  5. **Standing Calf Raises**: 4 sets × 15 reps | Rest: 45s *(2-second hold at peak stretch)*

---

### **Day 4: Chest + Shoulders**
- **🎯 Target Muscles**: Clavicular Pectorals, Anterior & Lateral Deltoids
- **Exercises**:
  1. **Incline Dumbbell Bench Press**: 4 sets × {iso_reps} | Rest: {iso_rest} *(Upper chest emphasis)*
  2. **Flat Dumbbell Press or Dips**: 3 sets × {iso_reps} | Rest: {iso_rest}
  3. **Overhead Barbell Military Press**: 4 sets × {comp_reps} | Rest: {comp_rest} *(Brace core tight, press overhead to lockout)*
  4. **Dumbbell Lateral Raises**: 4 sets × 12-15 reps | Rest: 60s *(Control eccentric lowering for rounded delts)*
  5. **Cable Face Pulls**: 3 sets × 15 reps | Rest: 60s *(Rear delt engagement & rotator cuff stability)*

---

### **Day 5: Arms (Biceps + Triceps)**
- **🎯 Target Muscles**: Biceps Brachii, Brachialis, Triceps Lateral/Long/Medial Heads
- **Exercises**:
  1. **Standing Barbell Bicep Curl**: 4 sets × {iso_reps} | Rest: 60s
  2. **Incline Dumbbell Hammer Curls**: 3 sets × {iso_reps} | Rest: 60s
  3. **Preacher EZ-Bar Curls**: 3 sets × {iso_reps} | Rest: 60s *(Maximum bicep isolation)*
  4. **Skull Crushers (Lying EZ-Bar Extension)**: 4 sets × {iso_reps} | Rest: 60s *(Targets triceps long head)*
  5. **Triceps Cable Rope Pushdown**: 4 sets × {iso_reps} | Rest: 60s

---

### **Day 6: Back + Shoulders**
- **🎯 Target Muscles**: Latissimus Dorsi, Posterior Deltoid, Mid/Lower Trapezius
- **Exercises**:
  1. **Conventional Deadlift or T-Bar Row**: 4 sets × {comp_reps} | Rest: {comp_rest} *(Heavy posterior drive)*
  2. **Single-Arm Dumbbell Row**: 3 sets × {iso_reps} | Rest: {iso_rest} *(Full lat stretch at bottom)*
  3. **Lat Pulldown (Neutral Grip)**: 3 sets × {iso_reps} | Rest: {iso_rest}
  4. **Seated Dumbbell Shoulder Press**: 3 sets × {comp_reps} | Rest: {comp_rest}
  5. **Reverse Pec Deck / Rear Delt Flyes**: 4 sets × 12-15 reps | Rest: 60s
  6. **Dumbbell Lateral Raises**: 3 sets × 15 reps | Rest: 60s

---

### **Day 7: Dedicated Rest & Active Recovery**
- **🎯 Focus**: Rest, muscle recovery, glycogen replenishment, hydration.
- **Activities**: 30-min gentle walk, foam rolling, rotator cuff mobility work, quality sleep.
- **Summary**: Exactly 6 Training Days (Days 1–6) + 1 Rest Day (Only Day 7 is the rest day)."""
            return body

        # Default standard 6-day split (Push / Pull / Legs x 2)
        body = f"""{header} + **1 Dedicated Rest Day** (Only Day 7 is the rest day).
This 6-day Push/Pull/Legs split trains every muscle group twice per week for maximum stimulus.

---

### **Day 1: Push A (Chest Emphasis, Shoulders, Triceps)**
- **🎯 Target Muscles**: Middle & Upper Pectorals, Anterior Deltoids, Triceps
- **Exercises**:
  1. **Barbell Flat Bench Press**: 4 sets × {comp_reps} | Rest: {comp_rest}
  2. **Incline Dumbbell Press**: 3 sets × {iso_reps} | Rest: {iso_rest}
  3. **Dumbbell Lateral Raises**: 4 sets × 12-15 reps | Rest: 60s
  4. **Triceps Cable Rope Pushdown**: 3 sets × {iso_reps} | Rest: 60s

---

### **Day 2: Pull A (Back Width, Rear Delts, Biceps)**
- **🎯 Target Muscles**: Latissimus Dorsi, Posterior Deltoid, Biceps Brachii
- **Exercises**:
  1. **Conventional Deadlift or Barbell Bent-Over Row**: 3 sets × {comp_reps} | Rest: {comp_rest}
  2. **Lat Pulldown (Wide Grip)**: 3 sets × {iso_reps} | Rest: {iso_rest}
  3. **Cable Face Pulls**: 3 sets × 15 reps | Rest: 60s
  4. **Standing Barbell Bicep Curl**: 3 sets × {iso_reps} | Rest: 60s

---

### **Day 3: Legs A (Quad Dominant, Calves, Core)**
- **🎯 Target Muscles**: Quadriceps, Gluteus Maximus, Gastrocnemius, Core
- **Exercises**:
  1. **Barbell Back Squats**: 4 sets × {comp_reps} | Rest: {comp_rest}
  2. **Leg Press Machine**: 3 sets × 10-12 reps | Rest: {iso_rest}
  3. **Walking Dumbbell Lunges**: 3 sets × 10-12 steps/leg | Rest: 60s
  4. **Standing Calf Raises**: 4 sets × 15 reps | Rest: 45s

---

### **Day 4: Push B (Shoulders & Upper Chest Emphasis, Triceps)**
- **🎯 Target Muscles**: Anterior/Lateral Deltoids, Clavicular Pecs, Triceps Long Head
- **Exercises**:
  1. **Standing Overhead Barbell Military Press**: 4 sets × {comp_reps} | Rest: {comp_rest}
  2. **Incline Dumbbell Flyes**: 3 sets × {iso_reps} | Rest: {iso_rest}
  3. **Cable Lateral Raises**: 4 sets × 12-15 reps | Rest: 60s
  4. **Overhead Dumbbell Triceps Extension**: 3 sets × {iso_reps} | Rest: 60s

---

### **Day 5: Pull B (Back Thickness, Rhomboids, Biceps)**
- **🎯 Target Muscles**: Mid/Lower Trapezius, Rhomboids, Brachialis, Biceps
- **Exercises**:
  1. **Seated Cable Row (Close Grip)**: 4 sets × {comp_reps} | Rest: {comp_rest}
  2. **Single-Arm Dumbbell Row**: 3 sets × {iso_reps} | Rest: {iso_rest}
  3. **Reverse Pec Deck / Rear Delt Flyes**: 3 sets × 15 reps | Rest: 60s
  4. **Incline Dumbbell Hammer Curls**: 3 sets × {iso_reps} | Rest: 60s

---

### **Day 6: Legs B (Hamstrings, Glutes, Calves, Core)**
- **🎯 Target Muscles**: Hamstrings, Gluteus Medius, Core Stability
- **Exercises**:
  1. **Romanian Deadlifts (RDL)**: 4 sets × {comp_reps} | Rest: {comp_rest}
  2. **Lying Leg Curls**: 3 sets × {iso_reps} | Rest: {iso_rest}
  3. **Bulgarian Split Squats**: 3 sets × 10 reps/leg | Rest: {iso_rest}
  4. **Standing Calf Raises**: 4 sets × 15 reps | Rest: 45s

---

### **Day 7: Dedicated Rest & Active Recovery**
- **🎯 Focus**: Rest, recovery, hydration and light mobility.
- **Summary**: Exactly 6 Active Training Days + 1 Rest Day (Only Day 7 is the rest day)."""
        return body

    elif days == 5:
        # 5-DAY SPLIT: Chest/Tri, Back/Bi, Legs, Shoulders/Abs, Upper/Arm Hypertrophy
        body = f"""{header} + **2 Dedicated Rest Days** (e.g. Wednesday & Sunday).
This 5-day setup gives dedicated focus to each major muscle region with balanced fatigue management.

---

### **Day 1: Chest & Triceps**
- **🎯 Target Muscles**: Pectoralis Major, Triceps
- **Exercises**:
  1. **Barbell Bench Press**: 4 sets × {comp_reps} | Rest: {comp_rest}
  2. **Incline Dumbbell Press**: 3 sets × {iso_reps} | Rest: {iso_rest}
  3. **Cable Chest Flyes**: 3 sets × 12-15 reps | Rest: 60s
  4. **Tricep Rope Pushdowns**: 4 sets × {iso_reps} | Rest: 60s

---

### **Day 2: Back & Biceps**
- **🎯 Target Muscles**: Latissimus Dorsi, Rhomboids, Biceps Brachii
- **Exercises**:
  1. **Barbell Bent-Over Row**: 4 sets × {comp_reps} | Rest: {comp_rest}
  2. **Lat Pulldown**: 3 sets × {iso_reps} | Rest: {iso_rest}
  3. **Seated Cable Row**: 3 sets × {iso_reps} | Rest: 60s
  4. **Barbell Bicep Curl**: 4 sets × {iso_reps} | Rest: 60s

---

### **Day 3: Legs & Calves**
- **🎯 Target Muscles**: Quadriceps, Hamstrings, Glutes, Gastrocnemius
- **Exercises**:
  1. **Barbell Back Squats**: 4 sets × {comp_reps} | Rest: {comp_rest}
  2. **Romanian Deadlift (RDL)**: 3 sets × {comp_reps} | Rest: {comp_rest}
  3. **Leg Press**: 3 sets × {iso_reps} | Rest: {iso_rest}
  4. **Standing Calf Raises**: 4 sets × 15 reps | Rest: 45s

---

### **Day 4: Shoulders & Abs**
- **🎯 Target Muscles**: Anterior, Lateral & Posterior Deltoids, Core
- **Exercises**:
  1. **Seated Dumbbell Shoulder Press**: 4 sets × {comp_reps} | Rest: {comp_rest}
  2. **Dumbbell Lateral Raises**: 4 sets × 12-15 reps | Rest: 60s
  3. **Cable Face Pulls**: 3 sets × 15 reps | Rest: 60s
  4. **Hanging Leg Raises**: 3 sets × 15 reps | Rest: 60s

---

### **Day 5: Upper Body Hypertrophy & Arms**
- **🎯 Target Muscles**: Biceps, Triceps, Upper Chest, Lats
- **Exercises**:
  1. **Incline Dumbbell Press**: 3 sets × {iso_reps} | Rest: {iso_rest}
  2. **Chest-Supported Dumbbell Rows**: 3 sets × {iso_reps} | Rest: {iso_rest}
  3. **Hammer Curls**: 3 sets × {iso_reps} | Rest: 60s
  4. **Skull Crushers (Lying Tricep Extension)**: 3 sets × {iso_reps} | Rest: 60s

---

### **Days 6 & 7: Rest & Recovery**
- Take two complete rest days per week to allow muscular and neural recovery.
- **Summary**: Exactly 5 Training Days + 2 Rest Days."""
        return body

    elif days == 4:
        # 4-DAY SPLIT: Upper / Lower A & B
        body = f"""{header} + **3 Rest Days** (e.g. Mon, Tue, Thu, Fri training; Wed, Sat, Sun rest).
The 4-day Upper/Lower split balances frequency, volume, and recovery.

---

### **Day 1: Upper Body A (Strength & Heavy Compounds)**
- **🎯 Target Muscles**: Chest, Upper Back, Shoulders, Triceps
- **Exercises**:
  1. **Barbell Bench Press**: 4 sets × {comp_reps} | Rest: {comp_rest}
  2. **Barbell Bent-Over Row**: 4 sets × {comp_reps} | Rest: {comp_rest}
  3. **Overhead Barbell Military Press**: 3 sets × {comp_reps} | Rest: {comp_rest}
  4. **Triceps Cable Pushdowns**: 3 sets × {iso_reps} | Rest: 60s

---

### **Day 2: Lower Body A (Quad Dominant & Abs)**
- **🎯 Target Muscles**: Quadriceps, Calves, Core
- **Exercises**:
  1. **Barbell Back Squats**: 4 sets × {comp_reps} | Rest: {comp_rest}
  2. **Leg Press Machine**: 3 sets × {iso_reps} | Rest: {iso_rest}
  3. **Walking Lunges**: 3 sets × 10 reps/leg | Rest: 60s
  4. **Hanging Leg Raises**: 3 sets × 12-15 reps | Rest: 60s

---

### **Day 3: Upper Body B (Hypertrophy & Width)**
- **🎯 Target Muscles**: Lats, Clavicular Pecs, Lateral Deltoids, Biceps
- **Exercises**:
  1. **Incline Dumbbell Bench Press**: 4 sets × {iso_reps} | Rest: {iso_rest}
  2. **Lat Pulldowns (Wide-Grip)**: 4 sets × {iso_reps} | Rest: {iso_rest}
  3. **Dumbbell Lateral Raises**: 4 sets × 12-15 reps | Rest: 60s
  4. **Incline Dumbbell Bicep Curls**: 3 sets × {iso_reps} | Rest: 60s

---

### **Day 4: Lower Body B (Posterior Chain Focus)**
- **🎯 Target Muscles**: Hamstrings, Gluteus Maximus, Lower Back, Calves
- **Exercises**:
  1. **Romanian Deadlifts (RDL)**: 4 sets × {comp_reps} | Rest: {comp_rest}
  2. **Lying Leg Curls**: 3 sets × {iso_reps} | Rest: {iso_rest}
  3. **Standing Calf Raises**: 4 sets × 15 reps | Rest: 45s
  4. **Plank Hold**: 3 sets × 60s | Rest: 45s

---

### **Days 5, 6 & 7: Rest Days**
- Enjoy 3 days of rest distributed throughout the week for optimal recovery.
- **Summary**: Exactly 4 Training Days + 3 Rest Days."""
        return body

    elif days == 7:
        # 7-DAY SPLIT WITH RECOVERY CLARIFICATION
        body = f"""{header}.

⚠️ **Physiological Recovery Clarification**:
Training heavy resistance 7 days a week without dedicated rest days can lead to systemic central nervous system (CNS) fatigue, blunted muscle protein synthesis, and increased joint inflammation.
Below is the **Recommended 7-Day Weekly Structure**: **6 High-Intensity Training Days + 1 Active Mobility & Recovery Day**. 
*(If you strictly require 7 lifting sessions, Day 7 can be converted to an ultra-low intensity Core & Forearm session, but active rest is strongly recommended).*

---

### **Day 1: Push (Chest, Shoulders & Triceps)**
- **🎯 Target Muscles**: Pectorals, Anterior Deltoids, Triceps
- **Exercises**:
  1. **Barbell Bench Press**: 3 sets × {comp_reps} | Rest: {comp_rest}
  2. **Incline Dumbbell Press**: 3 sets × {iso_reps} | Rest: {iso_rest}
  3. **Dumbbell Lateral Raises**: 3 sets × 12-15 reps | Rest: 60s
  4. **Cable Tricep Pushdown**: 3 sets × {iso_reps} | Rest: 60s

---

### **Day 2: Pull (Back, Rear Delts & Biceps)**
- **🎯 Target Muscles**: Lats, Rhomboids, Biceps Brachii
- **Exercises**:
  1. **Conventional Deadlift or Barbell Row**: 3 sets × {comp_reps} | Rest: {comp_rest}
  2. **Lat Pulldown**: 3 sets × {iso_reps} | Rest: {iso_rest}
  3. **Cable Face Pulls**: 3 sets × 15 reps | Rest: 60s
  4. **Bicep Curls**: 3 sets × {iso_reps} | Rest: 60s

---

### **Day 3: Legs (Quad Dominant & Calves)**
- **🎯 Target Muscles**: Quadriceps, Calves, Core
- **Exercises**:
  1. **Barbell Squats**: 3 sets × {comp_reps} | Rest: {comp_rest}
  2. **Leg Press**: 3 sets × {iso_reps} | Rest: {iso_rest}
  3. **Standing Calf Raises**: 4 sets × 15 reps | Rest: 45s
  4. **Hanging Leg Raises**: 3 sets × 15 reps | Rest: 60s

---

### **Day 4: Push (Upper Chest & Shoulder Focus)**
- **🎯 Target Muscles**: Deltoids, Clavicular Pecs, Triceps
- **Exercises**:
  1. **Overhead Military Press**: 3 sets × {comp_reps} | Rest: {comp_rest}
  2. **Incline Dumbbell Flyes**: 3 sets × {iso_reps} | Rest: {iso_rest}
  3. **Cable Lateral Raises**: 3 sets × 12-15 reps | Rest: 60s
  4. **Overhead Tricep Extension**: 3 sets × {iso_reps} | Rest: 60s

---

### **Day 5: Pull (Back Thickness & Arms)**
- **🎯 Target Muscles**: Mid-Back, Brachialis, Biceps
- **Exercises**:
  1. **Seated Cable Rows**: 3 sets × {comp_reps} | Rest: {comp_rest}
  2. **Single-Arm Dumbbell Rows**: 3 sets × {iso_reps} | Rest: {iso_rest}
  3. **Hammer Curls**: 3 sets × {iso_reps} | Rest: 60s
  4. **Rear Delt Flyes**: 3 sets × 15 reps | Rest: 60s

---

### **Day 6: Legs (Hamstrings, Glutes & Abs)**
- **🎯 Target Muscles**: Hamstrings, Gluteus, Core
- **Exercises**:
  1. **Romanian Deadlifts (RDL)**: 3 sets × {comp_reps} | Rest: {comp_rest}
  2. **Lying Leg Curls**: 3 sets × {iso_reps} | Rest: {iso_rest}
  3. **Bulgarian Split Squats**: 3 sets × 10 reps/leg | Rest: {iso_rest}
  4. **Plank Hold**: 3 sets × 60s | Rest: 45s

---

### **Day 7: Active Recovery & Mobility (Or Low-Intensity Core)**
- **Focus**: 30-min brisk walk, foam rolling, rotator cuff band work, core breathing exercises.
- **Summary**: Complete 7-Day Structured Schedule with 6 Heavy Lifting Days + 1 Active Recovery Day."""
        return body

    elif days == 3:
        # 3-DAY FULL BODY SPLIT
        body = f"""{header} + **4 Rest Days** (e.g. Mon, Wed, Fri training; Tue, Thu, Sat, Sun rest).
The 3-day Full Body split allows high intensity per session while maximizing recovery time between workouts.

---

### **Day 1: Full Body Workout A**
- **🎯 Target Muscles**: Quads, Chest, Back, Triceps
- **Exercises**:
  1. **Barbell Back Squats**: 4 sets × {comp_reps} | Rest: {comp_rest}
  2. **Barbell Bench Press**: 4 sets × {comp_reps} | Rest: {comp_rest}
  3. **Barbell Bent-Over Rows**: 3 sets × {comp_reps} | Rest: {comp_rest}
  4. **Triceps Cable Pushdowns**: 3 sets × {iso_reps} | Rest: 60s

---

### **Day 2: Full Body Workout B**
- **🎯 Target Muscles**: Hamstrings, Shoulders, Lats, Biceps
- **Exercises**:
  1. **Romanian Deadlifts (RDL)**: 4 sets × {comp_reps} | Rest: {comp_rest}
  2. **Overhead Military Press**: 4 sets × {comp_reps} | Rest: {comp_rest}
  3. **Lat Pulldowns**: 3 sets × {iso_reps} | Rest: {iso_rest}
  4. **Barbell Bicep Curls**: 3 sets × {iso_reps} | Rest: 60s

---

### **Day 3: Full Body Workout C**
- **🎯 Target Muscles**: Legs, Upper Chest, Back Thickness, Core
- **Exercises**:
  1. **Leg Press Machine**: 3 sets × {iso_reps} | Rest: {iso_rest}
  2. **Incline Dumbbell Press**: 3 sets × {iso_reps} | Rest: {iso_rest}
  3. **Seated Cable Rows**: 3 sets × {comp_reps} | Rest: {comp_rest}
  4. **Dumbbell Lateral Raises**: 3 sets × 12-15 reps | Rest: 60s
  5. **Hanging Leg Raises**: 3 sets × 15 reps | Rest: 60s

---

### **Summary**: Exactly 3 Training Days + 4 Rest Days."""
        return body

    else:
        # Generic 2 or 1 day fallback
        body = f"""{header}.
- **Day 1**: Upper Body & Core
- **Day 2**: Lower Body & Posterior Chain
- **Summary**: Exactly {days} Training Days."""
        return body


def validate_and_enforce_workout_days(
    generated_text: str,
    requested_days: Optional[int],
    user: User,
    profile: Optional[UserProfile],
    query_text: Optional[str] = None
) -> str:
    """
    Validates whether the generated response strictly follows the requested number of training days.
    If the response contains fewer or mismatched training days, it replaces it with an exact, validated plan.
    """
    if not requested_days:
        return generated_text

    actual_days = count_training_days(generated_text)

    # For 7 days, 6 training + 1 recovery is standard and acceptable if clarified
    if requested_days == 7 and actual_days in [6, 7]:
        return generated_text

    # Strict check: actual training days must match requested days
    if actual_days != requested_days:
        # Regenerate strictly using the validated engine
        return build_personalized_workout_plan(requested_days, user, profile, query_text=query_text)

    return generated_text
