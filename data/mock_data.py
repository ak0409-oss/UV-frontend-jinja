import copy

BAD_WORDS = ["stupid", "idiot", "useless", "trash", "hell", "damn", "rubbish", "fucked", "lazy"]

INITIAL_HOSTELS = [
    {"id": "h1", "name": "Kings Palace-1", "gender": "Boys", "totalRooms": 50},
    {"id": "h2", "name": "Queens Castle-2", "gender": "Girls", "totalRooms": 50},
    {"id": "h3", "name": "Royal Residency-3", "gender": "Boys", "totalRooms": 50},
    {"id": "h4", "name": "Grand Heights-4", "gender": "Girls", "totalRooms": 50},
]

_NAMES = [
    "Aarav Sharma", "Vivaan Gupta", "Aditya Patel", "Vihaan Singh", "Arjun Verma",
    "Saanvi Iyer", "Inaya Reddy", "Aarya Joshi", "Zara Khan", "Ananya Das",
    "Ishaan Malhotra", "Sai Kumar", "Krishna Murthy", "Rohan Mehra", "Aryan Bansal",
    "Pari Choudhury", "Kyra Nair", "Diya Mistri", "Anvi Saxena", "Myra Kapoor",
]

HOSTEL_IDS = ["h1", "h2", "h3", "h4"]
MENTOR_IDS = ["m1", "m2", "m3", "m4", "m5"]

INITIAL_USERS = [
    {"id": "u0", "email": "admin@kiit.ac.in", "name": "Super Admin", "password": "12345", "role": "admin"},
    {"id": "w1", "email": "warden@kiit.ac.in", "name": "Warden", "password": "12345", "role": "warden", "hostelId": "h1"},
    {"id": "w2", "email": "warden2@kiit.ac.in", "name": "Warden Name 2", "password": "12345", "role": "warden", "hostelId": "h2"},
    {"id": "w3", "email": "warden3@kiit.ac.in", "name": "Warden Name 3", "password": "12345", "role": "warden", "hostelId": "h3"},
    {"id": "w4", "email": "warden4@kiit.ac.in", "name": "Warden Name 4", "password": "12345", "role": "warden", "hostelId": "h4"},
    {"id": "w5", "email": "warden5@kiit.ac.inm", "name": "Warden Name 5", "password": "12345", "role": "warden"},
    {"id": "m1", "email": "mentor@kiit.ac.in", "name": "Mentor", "password": "12345", "role": "mentor"},
    {"id": "m2", "email": "mentor2@kiit.ac.in", "name": "Mentor Name 2", "password": "12345", "role": "mentor"},
    {"id": "m3", "email": "mentor3@kiit.ac.in", "name": "Mentor Name 3", "password": "12345", "role": "mentor"},
    {"id": "m4", "email": "mentor4@kiit.ac.in", "name": "Mentor Name 4", "password": "12345", "role": "mentor"},
    {"id": "m5", "email": "mentor5@kiit.ac.in", "name": "Mentor Name 5", "password": "12345", "role": "mentor"},
    {"id": "s0", "email": "student@kiit.ac.in", "name": "Student", "password": "12345", "role": "student", "hostelId": "h1", "mentorId": "m1", "roomNumber": "101"},
] + [
    {
        "id": f"s{i+1}",
        "email": f"student{i+1}@kiit.ac.in",
        "name": _NAMES[i],
        "password": "12345",
        "role": "student",
        "hostelId": HOSTEL_IDS[i % 4] if i < 16 else None,
        "mentorId": MENTOR_IDS[i % 5] if i < 16 else None,
        "roomNumber": str(101 + i * 7) if i < 16 else None,
    }
    for i in range(20)
]

INITIAL_COMPLAINTS = [
    {"id": "c1", "heading": "Fan not working", "description": "Ceiling fan in room is completely broken.", "category": "electric", "createdAt": "2025-01-15", "status": "pending", "isUrgent": False, "isAbusive": False, "userId": "s1", "hostelId": "h1"},
    {"id": "c2", "heading": "WiFi very slow", "description": "Internet speed drops to 0 after 10pm.", "category": "wifi", "createdAt": "2025-01-16", "status": "in_progress", "isUrgent": False, "isAbusive": False, "wardenComment": "Checking with ISP", "userId": "s2", "hostelId": "h2"},
    {"id": "c3", "heading": "Toilet leak", "description": "Water leaking from the flush tank continuously.", "category": "toilet", "createdAt": "2025-01-17", "status": "resolved", "isUrgent": False, "isAbusive": False, "wardenComment": "Plumber fixed it", "resolvedAt": "2025-01-19", "userId": "s3", "hostelId": "h3"},
    {"id": "c4", "heading": "Mess food quality", "description": "Food served is cold and stale regularly.", "category": "mess", "createdAt": "2025-01-18", "status": "pending", "isUrgent": True, "isAbusive": False, "mentorComment": "Urgent attention needed", "userId": "s4", "hostelId": "h4"},
    {"id": "c5", "heading": "This is stupid management", "description": "You idiots don't fix anything around here.", "category": "others", "createdAt": "2025-01-20", "status": "flagged", "isUrgent": False, "isAbusive": True, "userId": "s5", "hostelId": "h1"},
    {"id": "c6", "heading": "Light not working", "description": "Tubelight in corridor has been off for a week.", "category": "electric", "createdAt": "2025-01-22", "status": "rejected", "isUrgent": False, "isAbusive": False, "wardenComment": "Not hostel responsibility", "userId": "s6", "hostelId": "h2"},
    {"id": "c7", "heading": "Personal belongings stolen", "description": "My laptop charger was taken from common room.", "category": "personal", "createdAt": "2025-02-01", "status": "pending", "isUrgent": True, "isAbusive": False, "mentorComment": "Please escalate immediately", "userId": "s1", "hostelId": "h1"},
    {"id": "c8", "heading": "Water heater broken", "description": "No hot water in bathrooms for 3 days.", "category": "others", "createdAt": "2025-02-05", "status": "in_progress", "isUrgent": False, "isAbusive": False, "userId": "s9", "hostelId": "h1"},
]

def get_initial_data():
    return {
        "users": copy.deepcopy(INITIAL_USERS),
        "hostels": copy.deepcopy(INITIAL_HOSTELS),
        "complaints": copy.deepcopy(INITIAL_COMPLAINTS),
    }
