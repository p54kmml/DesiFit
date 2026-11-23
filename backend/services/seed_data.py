from sqlalchemy.orm import Session
from backend.models import Exercise, FoodItem


INITIAL_EXERCISES = [
    # CHEST
    {
        "name": "Barbell Bench Press",
        "muscle_group": "Chest",
        "equipment": "Barbell & Bench",
        "difficulty": "Intermediate",
        "instructions": "Lie flat on the bench. Grip the barbell with hands slightly wider than shoulder-width. Lower the bar smoothly to your mid-chest, pause briefly, then press upwards explosively to arm lockout."
    },
    {
        "name": "Incline Dumbbell Press",
        "muscle_group": "Chest",
        "equipment": "Dumbbells & Incline Bench",
        "difficulty": "Intermediate",
        "instructions": "Set bench to 30-45 degrees. Hold dumbbells at shoulder level with palms facing forward. Press upward until arms are extended, squeeze upper chest, then lower slowly."
    },
    {
        "name": "Cable Chest Flyes",
        "muscle_group": "Chest",
        "equipment": "Cable Machine",
        "difficulty": "Beginner",
        "instructions": "Set pulleys to shoulder height. Step forward, keep a slight bend in your elbows, and bring your hands together in front of your chest in a hugging motion."
    },
    {
        "name": "Dips (Chest Focus)",
        "muscle_group": "Chest",
        "equipment": "Parallel Dip Bars",
        "difficulty": "Advanced",
        "instructions": "Suspend yourself on the parallel bars. Lean your torso slightly forward to target the lower chest. Lower your body until elbows reach 90 degrees, then push back up."
    },
    {
        "name": "Push-Ups",
        "muscle_group": "Chest",
        "equipment": "Bodyweight",
        "difficulty": "Beginner",
        "instructions": "Place hands shoulder-width apart on the floor. Maintain a straight plank line from head to heels. Lower chest to floor and press back up with controlled core tension."
    },

    # BACK
    {
        "name": "Conventional Barbell Deadlift",
        "muscle_group": "Back",
        "equipment": "Barbell",
        "difficulty": "Advanced",
        "instructions": "Stand with feet hip-width apart, barbell over mid-foot. Hinge at hips, grip the bar firmly, brace core, keep spine neutral, and drive through heels to stand upright."
    },
    {
        "name": "Barbell Bent-Over Row",
        "muscle_group": "Back",
        "equipment": "Barbell",
        "difficulty": "Intermediate",
        "instructions": "Hinge at the hips with knees slightly bent and back flat at roughly 45 degrees. Pull the barbell towards your lower ribcage, driving elbows back, then lower with control."
    },
    {
        "name": "Lat Pulldown",
        "muscle_group": "Back",
        "equipment": "Cable Pulldown Machine",
        "difficulty": "Beginner",
        "instructions": "Sit securely under the pads. Grip the bar wide. Keeping your chest puffed out, pull the bar down smoothly to your upper chest while squeezing your lats."
    },
    {
        "name": "Single-Arm Dumbbell Row",
        "muscle_group": "Back",
        "equipment": "Dumbbell & Bench",
        "difficulty": "Beginner",
        "instructions": "Place one knee and hand on the bench for support. Hold dumbbell with the other hand, pull dumbbell towards hip pocket, retracting the shoulder blade."
    },
    {
        "name": "Seated Cable Row",
        "muscle_group": "Back",
        "equipment": "Cable Machine",
        "difficulty": "Beginner",
        "instructions": "Sit with knees slightly bent. Grasp V-handle. Keeping torso upright, pull handle towards your navel, squeezing the mid-back and rhomboids."
    },

    # SHOULDERS
    {
        "name": "Overhead Barbell Military Press",
        "muscle_group": "Shoulders",
        "equipment": "Barbell",
        "difficulty": "Intermediate",
        "instructions": "Stand tall with core braced and glutes squeezed. Hold barbell at collarbone height. Press straight overhead until elbows are fully extended, then lower with control."
    },
    {
        "name": "Dumbbell Lateral Raise",
        "muscle_group": "Shoulders",
        "equipment": "Dumbbells",
        "difficulty": "Beginner",
        "instructions": "Stand upright holding dumbbells at sides. Raise arms outward to shoulder level with pinkies slightly tilted up to isolate lateral deltoids. Lower slowly."
    },
    {
        "name": "Face Pulls",
        "muscle_group": "Shoulders",
        "equipment": "Cable Machine & Rope",
        "difficulty": "Beginner",
        "instructions": "Set rope attachment to eye level. Pull rope towards your face, flaring elbows outward and externally rotating shoulders to strengthen rear delts and rotator cuffs."
    },
    {
        "name": "Seated Dumbbell Shoulder Press",
        "muscle_group": "Shoulders",
        "equipment": "Dumbbells & Bench",
        "difficulty": "Intermediate",
        "instructions": "Sit on an upright bench. Hold dumbbells at ear level. Press overhead smoothly without clanking dumbbells together, then lower to ears."
    },

    # BICEPS
    {
        "name": "Barbell Bicep Curl",
        "muscle_group": "Biceps",
        "equipment": "Barbell / EZ Bar",
        "difficulty": "Beginner",
        "instructions": "Stand with feet shoulder-width apart. Hold barbell with underhand grip. Curl weight toward shoulders while keeping elbows pinned to ribs. Squeeze biceps at peak."
    },
    {
        "name": "Incline Dumbbell Curl",
        "muscle_group": "Biceps",
        "equipment": "Dumbbells & Incline Bench",
        "difficulty": "Intermediate",
        "instructions": "Sit back on a 45-60 degree incline bench. Arms hanging down to stretch the long head of the bicep. Curl dumbbells up without swinging elbows."
    },
    {
        "name": "Hammer Curls",
        "muscle_group": "Biceps",
        "equipment": "Dumbbells",
        "difficulty": "Beginner",
        "instructions": "Hold dumbbells with neutral grip (palms facing each other). Curl up focusing on brachialis and forearm thickness. Squeeze at top and control the descent."
    },

    # TRICEPS
    {
        "name": "Triceps Rope Pushdown",
        "muscle_group": "Triceps",
        "equipment": "Cable Machine & Rope",
        "difficulty": "Beginner",
        "instructions": "Attach rope to high pulley. Keep elbows pinned tight against torso. Push down and spread the rope ends apart at the bottom to contract lateral tricep head."
    },
    {
        "name": "Skull Crushers (Lying Triceps Extension)",
        "muscle_group": "Triceps",
        "equipment": "EZ Bar & Flat Bench",
        "difficulty": "Intermediate",
        "instructions": "Lie on bench holding EZ bar with narrow grip above shoulders. Keeping upper arms vertical, bend elbows to lower bar towards forehead, then extend elbows."
    },
    {
        "name": "Overhead Dumbbell Tricep Extension",
        "muscle_group": "Triceps",
        "equipment": "Dumbbell",
        "difficulty": "Beginner",
        "instructions": "Sit upright, hold one dumbbell with both hands overhead. Lower weight behind head by bending elbows, then press back up to emphasize the long head."
    },

    # LEGS
    {
        "name": "Barbell Back Squat",
        "muscle_group": "Legs",
        "equipment": "Barbell & Squat Rack",
        "difficulty": "Intermediate",
        "instructions": "Place bar on upper traps. Stand shoulder-width apart. Push hips back and bend knees until thighs are at least parallel to floor. Drive up through midfoot."
    },
    {
        "name": "Romanian Deadlift (RDL)",
        "muscle_group": "Legs",
        "equipment": "Barbell or Dumbbells",
        "difficulty": "Intermediate",
        "instructions": "Stand upright with soft knees. Push hips backward while keeping barbell sliding close along legs. Feel deep stretch in hamstrings and glutes, then drive hips forward."
    },
    {
        "name": "Leg Press",
        "muscle_group": "Legs",
        "equipment": "Leg Press Machine",
        "difficulty": "Beginner",
        "instructions": "Place feet hip-width on sled platform. Release safety locks. Lower sled until knees reach 90 degrees without rounding lower back. Press sled away without locking knees."
    },
    {
        "name": "Walking Dumbbell Lunges",
        "muscle_group": "Legs",
        "equipment": "Dumbbells",
        "difficulty": "Beginner",
        "instructions": "Step forward with one leg, lowering hips until both knees are bent at 90 degrees. Push through front heel and step forward into next lunge."
    },
    {
        "name": "Standing Calf Raises",
        "muscle_group": "Legs",
        "equipment": "Calf Machine / Platform",
        "difficulty": "Beginner",
        "instructions": "Place balls of feet on edge of platform. Lower heels below platform for deep calf stretch, then rise up as high as possible on toes, pausing at top."
    },

    # ABS & CORE
    {
        "name": "Hanging Leg Raises",
        "muscle_group": "Abs",
        "equipment": "Pull-Up Bar",
        "difficulty": "Intermediate",
        "instructions": "Hang from pull-up bar with overhand grip. Keeping legs straight or slightly bent, engage core and raise legs until parallel to floor or higher. Lower slowly."
    },
    {
        "name": "Cable Woodchoppers",
        "muscle_group": "Abs",
        "equipment": "Cable Machine",
        "difficulty": "Beginner",
        "instructions": "Set pulley high. Grip handle with both hands. Rotate torso diagonally downward across body toward opposite knee, engaging obliques and core rotation."
    },
    {
        "name": "Plank Hold",
        "muscle_group": "Abs",
        "equipment": "Bodyweight & Mat",
        "difficulty": "Beginner",
        "instructions": "Rest on forearms and toes. Keep spine neutral, glutes clamped tight, and belly button pulled toward spine. Breathe steadily and hold without sagging."
    },

    # ADDITIONAL CHEST & DESI FITNESS
    {
        "name": "Incline Barbell Bench Press",
        "muscle_group": "Chest",
        "equipment": "Barbell & Incline Bench",
        "difficulty": "Intermediate",
        "instructions": "Set bench to 30-45 degrees. Lower bar to upper chest and press up with control."
    },
    {
        "name": "Decline Dumbbell Press",
        "muscle_group": "Chest",
        "equipment": "Dumbbells & Decline Bench",
        "difficulty": "Intermediate",
        "instructions": "Lie on decline bench. Press dumbbells upward over lower chest."
    },
    {
        "name": "Dumbbell Pullover",
        "muscle_group": "Chest",
        "equipment": "Dumbbell & Flat Bench",
        "difficulty": "Intermediate",
        "instructions": "Lie across bench with shoulders supported. Lower dumbbell back overhead for a deep chest and serratus stretch."
    },
    {
        "name": "Diamond Push-Ups",
        "muscle_group": "Chest",
        "equipment": "Bodyweight",
        "difficulty": "Intermediate",
        "instructions": "Form diamond shape with thumbs and index fingers under chest. Lower down and press up."
    },
    {
        "name": "Desi Dand (Hindu Push-Ups)",
        "muscle_group": "Chest",
        "equipment": "Bodyweight",
        "difficulty": "Intermediate",
        "instructions": "Traditional Indian akhada exercise. Start in downward dog, swoop chest down close to the floor, arch into cobra, and reverse smoothly."
    },

    # ADDITIONAL BACK
    {
        "name": "Wide-Grip Pull-Ups",
        "muscle_group": "Back",
        "equipment": "Pull-Up Bar",
        "difficulty": "Advanced",
        "instructions": "Overhand grip wider than shoulders. Pull up until chin clears the bar."
    },
    {
        "name": "Underhand Chin-Ups",
        "muscle_group": "Back",
        "equipment": "Pull-Up Bar",
        "difficulty": "Intermediate",
        "instructions": "Underhand grip at shoulder width. Pull up emphasizing lower lats and biceps."
    },
    {
        "name": "T-Bar Row",
        "muscle_group": "Back",
        "equipment": "T-Bar Platform or Landmine",
        "difficulty": "Intermediate",
        "instructions": "Straddle the bar, hinge hips, keep back flat and pull handle toward upper abs."
    },
    {
        "name": "Hyperextensions (Back Extension)",
        "muscle_group": "Back",
        "equipment": "Hyperextension Bench",
        "difficulty": "Beginner",
        "instructions": "Hinge at the waist on the 45-degree bench. Raise torso until aligned with legs."
    },
    {
        "name": "Straight-Arm Cable Pulldown",
        "muscle_group": "Back",
        "equipment": "Cable Machine",
        "difficulty": "Beginner",
        "instructions": "With arms straight, sweep cable bar from shoulder height down to thighs."
    },

    # ADDITIONAL SHOULDERS
    {
        "name": "Arnold Dumbbell Press",
        "muscle_group": "Shoulders",
        "equipment": "Dumbbells",
        "difficulty": "Intermediate",
        "instructions": "Start with palms facing you. Rotate palms outward as you press overhead."
    },
    {
        "name": "Dumbbell Shrugs",
        "muscle_group": "Shoulders",
        "equipment": "Dumbbells",
        "difficulty": "Beginner",
        "instructions": "Elevate shoulders straight up towards ears, squeeze traps for 1 second, and lower smoothly."
    },
    {
        "name": "Front Dumbbell Raise",
        "muscle_group": "Shoulders",
        "equipment": "Dumbbells",
        "difficulty": "Beginner",
        "instructions": "Raise dumbbells in front to shoulder level with controlled tempo."
    },
    {
        "name": "Reverse Pec Deck Fly",
        "muscle_group": "Shoulders",
        "equipment": "Pec Deck Machine",
        "difficulty": "Beginner",
        "instructions": "Sit facing machine pad. Pull handles back horizontally to isolate rear deltoids."
    },
    {
        "name": "Cable Lateral Raise",
        "muscle_group": "Shoulders",
        "equipment": "Cable Machine",
        "difficulty": "Beginner",
        "instructions": "Attach low cable to far hand. Raise arm out to side to keep constant deltoid tension."
    },

    # ADDITIONAL ARMS
    {
        "name": "Preacher Curl",
        "muscle_group": "Biceps",
        "equipment": "EZ Bar & Preacher Bench",
        "difficulty": "Beginner",
        "instructions": "Rest upper arms on preacher pad. Curl bar smoothly without lifting elbows."
    },
    {
        "name": "Concentration Curl",
        "muscle_group": "Biceps",
        "equipment": "Dumbbell",
        "difficulty": "Beginner",
        "instructions": "Sit with elbow pressed against inner thigh. Curl dumbbell focusing on bicep peak."
    },
    {
        "name": "Cable Bicep Curl",
        "muscle_group": "Biceps",
        "equipment": "Cable Machine",
        "difficulty": "Beginner",
        "instructions": "Stand facing low pulley with straight bar. Curl up against smooth cable resistance."
    },
    {
        "name": "Reverse Barbell Curl",
        "muscle_group": "Biceps",
        "equipment": "Barbell",
        "difficulty": "Intermediate",
        "instructions": "Overhand grip. Curl weight to build brachioradialis and forearm thickness."
    },
    {
        "name": "Close-Grip Barbell Bench Press",
        "muscle_group": "Triceps",
        "equipment": "Barbell & Flat Bench",
        "difficulty": "Intermediate",
        "instructions": "Grip bar shoulder-width. Keep elbows tucked close to ribs to recruit triceps."
    },
    {
        "name": "Bench Dips",
        "muscle_group": "Triceps",
        "equipment": "Flat Bench",
        "difficulty": "Beginner",
        "instructions": "Hands on edge of bench behind you. Lower hips by bending elbows to 90 degrees."
    },
    {
        "name": "Cable Overhead Tricep Extension",
        "muscle_group": "Triceps",
        "equipment": "Cable Machine & Rope",
        "difficulty": "Beginner",
        "instructions": "Face away from high cable. Extend rope overhead to stretch and squeeze triceps long head."
    },

    # ADDITIONAL LEGS
    {
        "name": "Front Squat",
        "muscle_group": "Legs",
        "equipment": "Barbell & Rack",
        "difficulty": "Advanced",
        "instructions": "Rest bar across front deltoids. Keep elbows high and squat deep with upright torso."
    },
    {
        "name": "Goblet Squat",
        "muscle_group": "Legs",
        "equipment": "Dumbbell or Kettlebell",
        "difficulty": "Beginner",
        "instructions": "Hold weight vertically against chest. Squat between knees keeping chest proud."
    },
    {
        "name": "Bulgarian Split Squat",
        "muscle_group": "Legs",
        "equipment": "Dumbbells & Bench",
        "difficulty": "Intermediate",
        "instructions": "Rear foot elevated on bench. Lower hips until front thigh is parallel to floor."
    },
    {
        "name": "Leg Extension",
        "muscle_group": "Legs",
        "equipment": "Leg Extension Machine",
        "difficulty": "Beginner",
        "instructions": "Extend knees fully against pad to isolate quadriceps. Pause at the top."
    },
    {
        "name": "Lying Hamstring Leg Curl",
        "muscle_group": "Legs",
        "equipment": "Leg Curl Machine",
        "difficulty": "Beginner",
        "instructions": "Lie face down. Curl heels toward glutes to isolate hamstrings."
    },
    {
        "name": "Barbell Hip Thrust",
        "muscle_group": "Legs",
        "equipment": "Barbell & Bench",
        "difficulty": "Intermediate",
        "instructions": "Upper back against bench, bar across hips. Drive hips up into full extension."
    },
    {
        "name": "Seated Calf Raise",
        "muscle_group": "Legs",
        "equipment": "Seated Calf Machine",
        "difficulty": "Beginner",
        "instructions": "Knees bent under pad. Push through toes to isolate the soleus muscle."
    },
    {
        "name": "Desi Baithak (Hindu Squats)",
        "muscle_group": "Legs",
        "equipment": "Bodyweight",
        "difficulty": "Beginner",
        "instructions": "Traditional akhada bodyweight squat with rhythmic arm swings, rising onto balls of feet."
    },

    # ADDITIONAL ABS & FULL BODY
    {
        "name": "Surya Namaskar (Sun Salutation)",
        "muscle_group": "Full Body",
        "equipment": "Bodyweight & Mat",
        "difficulty": "Beginner",
        "instructions": "Dynamic 12-step traditional yogic flow activating full body flexibility and core endurance."
    },
    {
        "name": "Ab Wheel Rollout",
        "muscle_group": "Abs",
        "equipment": "Ab Wheel",
        "difficulty": "Advanced",
        "instructions": "Kneel on mat and roll wheel forward with straight arms, bracing core, then roll back."
    },
    {
        "name": "Russian Twists",
        "muscle_group": "Abs",
        "equipment": "Bodyweight or Dumbbell",
        "difficulty": "Beginner",
        "instructions": "Sit with knees bent, lean back 45 degrees, and rotate torso side-to-side."
    },
    {
        "name": "Bicycle Crunches",
        "muscle_group": "Abs",
        "equipment": "Bodyweight & Mat",
        "difficulty": "Beginner",
        "instructions": "Alternate touching opposite elbow to knee in a pedaling motion to target obliques."
    }
]


INITIAL_FOODS = [
    # DESI FITNESS SPECIALS
    {
        "name": "Paneer (Low-Fat Cottage Cheese)",
        "serving_size": "100g",
        "calories": 180.0,
        "protein_g": 20.0,
        "carbs_g": 3.0,
        "fat_g": 10.0,
        "fiber_g": 0.0,
        "is_desi_special": True
    },
    {
        "name": "Cooked Yellow Moong Dal",
        "serving_size": "1 bowl (150g)",
        "calories": 150.0,
        "protein_g": 10.5,
        "carbs_g": 22.0,
        "fat_g": 2.0,
        "fiber_g": 6.0,
        "is_desi_special": True
    },
    {
        "name": "Whole Wheat Roti / Chapati",
        "serving_size": "1 medium (35g)",
        "calories": 85.0,
        "protein_g": 3.0,
        "carbs_g": 17.0,
        "fat_g": 0.5,
        "fiber_g": 2.5,
        "is_desi_special": True
    },
    {
        "name": "Soya Chunks (Cooked)",
        "serving_size": "100g cooked",
        "calories": 145.0,
        "protein_g": 24.0,
        "carbs_g": 11.0,
        "fat_g": 0.5,
        "fiber_g": 8.0,
        "is_desi_special": True
    },
    {
        "name": "Chicken Tikka (Grilled)",
        "serving_size": "150g",
        "calories": 220.0,
        "protein_g": 35.0,
        "carbs_g": 4.0,
        "fat_g": 7.0,
        "fiber_g": 1.0,
        "is_desi_special": True
    },
    {
        "name": "Curd / Plain Dahi",
        "serving_size": "1 cup (200g)",
        "calories": 120.0,
        "protein_g": 8.0,
        "carbs_g": 9.0,
        "fat_g": 6.0,
        "fiber_g": 0.0,
        "is_desi_special": True
    },
    {
        "name": "Egg Bhurji (2 Whole Eggs, Spices)",
        "serving_size": "1 serving",
        "calories": 180.0,
        "protein_g": 13.0,
        "carbs_g": 3.0,
        "fat_g": 13.0,
        "fiber_g": 0.5,
        "is_desi_special": True
    },
    {
        "name": "Chana Masala (Chickpeas Curry)",
        "serving_size": "1 bowl (180g)",
        "calories": 210.0,
        "protein_g": 9.0,
        "carbs_g": 32.0,
        "fat_g": 5.0,
        "fiber_g": 7.5,
        "is_desi_special": True
    },

    # STANDARD GYM & NUTRITION STAPLES
    {
        "name": "Whey Protein Isolate (1 Scoop)",
        "serving_size": "1 scoop (30g)",
        "calories": 120.0,
        "protein_g": 25.0,
        "carbs_g": 2.0,
        "fat_g": 1.0,
        "fiber_g": 0.0,
        "is_desi_special": False
    },
    {
        "name": "Boiled Chicken Breast",
        "serving_size": "100g",
        "calories": 165.0,
        "protein_g": 31.0,
        "carbs_g": 0.0,
        "fat_g": 3.6,
        "fiber_g": 0.0,
        "is_desi_special": False
    },
    {
        "name": "Boiled Whole Egg",
        "serving_size": "1 large egg (50g)",
        "calories": 74.0,
        "protein_g": 6.3,
        "carbs_g": 0.4,
        "fat_g": 5.0,
        "fiber_g": 0.0,
        "is_desi_special": False
    },
    {
        "name": "Egg White (Boiled)",
        "serving_size": "1 large egg white (33g)",
        "calories": 17.0,
        "protein_g": 3.6,
        "carbs_g": 0.2,
        "fat_g": 0.1,
        "fiber_g": 0.0,
        "is_desi_special": False
    },
    {
        "name": "Oatmeal (Rolled Oats, Cooked with Water)",
        "serving_size": "1 bowl (40g dry oats)",
        "calories": 150.0,
        "protein_g": 5.0,
        "carbs_g": 27.0,
        "fat_g": 2.5,
        "fiber_g": 4.0,
        "is_desi_special": False
    },
    {
        "name": "Steamed White Basmati Rice",
        "serving_size": "1 cup cooked (150g)",
        "calories": 195.0,
        "protein_g": 4.0,
        "carbs_g": 43.0,
        "fat_g": 0.5,
        "fiber_g": 0.6,
        "is_desi_special": True
    },
    {
        "name": "Peanut Butter",
        "serving_size": "2 tbsp (32g)",
        "calories": 190.0,
        "protein_g": 8.0,
        "carbs_g": 6.0,
        "fat_g": 16.0,
        "fiber_g": 2.0,
        "is_desi_special": False
    },
    {
        "name": "Banana",
        "serving_size": "1 medium (118g)",
        "calories": 105.0,
        "protein_g": 1.3,
        "carbs_g": 27.0,
        "fat_g": 0.3,
        "fiber_g": 3.1,
        "is_desi_special": False
    },
    {
        "name": "Almonds (Raw)",
        "serving_size": "Handful (28g / ~23 nuts)",
        "calories": 164.0,
        "protein_g": 6.0,
        "carbs_g": 6.0,
        "fat_g": 14.0,
        "fiber_g": 3.5,
        "is_desi_special": False
    }
]


def seed_database_if_empty(db: Session):
    """Checks and seeds exercise and nutrition libraries if empty or missing items."""
    existing_exercises = {e.name for e in db.query(Exercise.name).all()}
    for ex_data in INITIAL_EXERCISES:
        if ex_data["name"] not in existing_exercises:
            db.add(Exercise(**ex_data))
    db.commit()

    food_count = db.query(FoodItem).count()
    if food_count == 0:
        for food_data in INITIAL_FOODS:
            food = FoodItem(**food_data)
            db.add(food)
        db.commit()
