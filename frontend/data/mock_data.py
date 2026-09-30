"""
SwachhLoop AI — Centralized Mock Data
=======================================
All prototype/demo data lives here for Phase 2.

Phase 3 integration:
    Replace these data structures by calling the real API through
    frontend/services/api_client.py. The shape of the data should
    remain compatible so pages need minimal changes.
"""

from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Demo Users (prototype authentication — Phase 3 replaces with real auth)
# ---------------------------------------------------------------------------

DEMO_USERS = [
    {
        "id": "u001",
        "name": "Arjun Nair",
        "email": "citizen@swachhloop.ai",
        "password": "demo123",
        "role": "citizen",
        "avatar_initials": "AN",
        "ward": "Ward 7 — Thrissur",
        "phone": "+91 98765 43210",
        "joined": "March 2025",
        "total_reports": 12,
        "resolved": 9,
    },
    {
        "id": "u002",
        "name": "Rajan Pillai",
        "email": "cleaner@swachhloop.ai",
        "password": "demo123",
        "role": "cleaner",
        "avatar_initials": "RP",
        "ward": "Zone B — Thrissur",
        "phone": "+91 87654 32109",
        "joined": "January 2025",
        "employee_id": "CLN-042",
        "tasks_completed": 87,
    },
    {
        "id": "u003",
        "name": "Priya Menon",
        "email": "staff@swachhloop.ai",
        "password": "demo123",
        "role": "municipal_staff",
        "avatar_initials": "PM",
        "department": "Waste Management — Thrissur Corporation",
        "phone": "+91 76543 21098",
        "joined": "August 2024",
        "employee_id": "STAFF-011",
    },
    {
        "id": "u004",
        "name": "Dr. Suresh Kumar",
        "email": "admin@swachhloop.ai",
        "password": "demo123",
        "role": "admin",
        "avatar_initials": "SK",
        "department": "IT & System Administration",
        "phone": "+91 65432 10987",
        "joined": "June 2024",
        "employee_id": "ADMIN-001",
    },
]

# ---------------------------------------------------------------------------
# Mock Complaints
# ---------------------------------------------------------------------------

MOCK_COMPLAINTS = [
    {
        "id": "CMP-2024-0891",
        "citizen_id": "u001",
        "citizen_name": "Arjun Nair",
        "title": "Illegal Dumping Near Gandhi Park",
        "description": "Large pile of construction debris and plastic waste dumped near the park entrance. The waste is blocking the footpath and causing a health hazard.",
        "waste_type": "Construction & Plastic Mix",
        "location": "Gandhi Park Entrance, Ward 7, Thrissur",
        "lat": 10.5273,
        "lon": 76.2144,
        "priority": "CRITICAL",
        "status": "CLEANING",
        "reported_at": "2026-09-18 09:15",
        "image_url": None,
        "ai_confidence": 94,
        "ai_reason": "Large accumulation detected near a frequently used public area. Multiple waste categories identified.",
        "assigned_cleaner": "Rajan Pillai",
        "assigned_at": "2026-09-18 11:30",
        "timeline": [
            {"step": "SUBMITTED", "done": True, "time": "Sep 18, 09:15 AM"},
            {"step": "VALIDATED", "done": True, "time": "Sep 18, 10:00 AM"},
            {"step": "ASSIGNED", "done": True, "time": "Sep 18, 11:30 AM"},
            {"step": "CLEANING", "done": True, "time": "Sep 19, 08:00 AM"},
            {"step": "VERIFICATION", "done": False, "time": None},
            {"step": "RESOLVED", "done": False, "time": None},
        ],
    },
    {
        "id": "CMP-2024-0885",
        "citizen_id": "u001",
        "citizen_name": "Arjun Nair",
        "title": "Overflowing Waste Bin on MG Road",
        "description": "The municipal bin near the bus stop is overflowing and waste is spilling onto the road. Strong smell is causing inconvenience.",
        "waste_type": "Mixed Municipal Waste",
        "location": "MG Road Bus Stop, Ward 7, Thrissur",
        "lat": 10.5198,
        "lon": 76.2195,
        "priority": "HIGH",
        "status": "RESOLVED",
        "reported_at": "2026-09-15 14:20",
        "image_url": None,
        "ai_confidence": 88,
        "ai_reason": "Overflowing bin identified with spill detected on adjacent area.",
        "assigned_cleaner": "Rajan Pillai",
        "assigned_at": "2026-09-15 16:00",
        "resolved_at": "2026-09-16 10:30",
        "resolution_time": "20 hours",
        "timeline": [
            {"step": "SUBMITTED", "done": True, "time": "Sep 15, 02:20 PM"},
            {"step": "VALIDATED", "done": True, "time": "Sep 15, 03:00 PM"},
            {"step": "ASSIGNED", "done": True, "time": "Sep 15, 04:00 PM"},
            {"step": "CLEANING", "done": True, "time": "Sep 16, 08:00 AM"},
            {"step": "VERIFICATION", "done": True, "time": "Sep 16, 10:00 AM"},
            {"step": "RESOLVED", "done": True, "time": "Sep 16, 10:30 AM"},
        ],
    },
    {
        "id": "CMP-2024-0879",
        "citizen_id": "u001",
        "citizen_name": "Arjun Nair",
        "title": "Plastic Waste Near School Gate",
        "description": "Plastic bags and food wrappers scattered near the school entrance.",
        "waste_type": "Plastic Waste",
        "location": "St. Thomas School Gate, Ward 7",
        "lat": 10.5312,
        "lon": 76.2088,
        "priority": "MEDIUM",
        "status": "VALIDATED",
        "reported_at": "2026-09-20 08:45",
        "image_url": None,
        "ai_confidence": 91,
        "ai_reason": "Plastic waste accumulation detected near a school zone.",
        "assigned_cleaner": None,
        "timeline": [
            {"step": "SUBMITTED", "done": True, "time": "Sep 20, 08:45 AM"},
            {"step": "VALIDATED", "done": True, "time": "Sep 20, 10:00 AM"},
            {"step": "ASSIGNED", "done": False, "time": None},
            {"step": "CLEANING", "done": False, "time": None},
            {"step": "VERIFICATION", "done": False, "time": None},
            {"step": "RESOLVED", "done": False, "time": None},
        ],
    },
    {
        "id": "CMP-2024-0871",
        "citizen_id": "u005",
        "citizen_name": "Meena Thomas",
        "title": "Medical Waste Disposal Issue",
        "description": "Improperly disposed biomedical waste found near the drainage.",
        "waste_type": "Biomedical Waste",
        "location": "Near Community Health Centre, Ward 5",
        "lat": 10.5350,
        "lon": 76.2200,
        "priority": "CRITICAL",
        "status": "ASSIGNED",
        "reported_at": "2026-09-19 11:00",
        "image_url": None,
        "ai_confidence": 96,
        "ai_reason": "Biomedical waste detected — high-risk category. Requires immediate attention.",
        "assigned_cleaner": "Vijayan K.",
        "timeline": [
            {"step": "SUBMITTED", "done": True, "time": "Sep 19, 11:00 AM"},
            {"step": "VALIDATED", "done": True, "time": "Sep 19, 11:30 AM"},
            {"step": "ASSIGNED", "done": True, "time": "Sep 19, 12:00 PM"},
            {"step": "CLEANING", "done": False, "time": None},
            {"step": "VERIFICATION", "done": False, "time": None},
            {"step": "RESOLVED", "done": False, "time": None},
        ],
    },
    {
        "id": "CMP-2024-0868",
        "citizen_id": "u006",
        "citizen_name": "Rajesh Varma",
        "title": "Open Burning of Waste",
        "description": "Residents burning plastic and household waste in an open area near the canal.",
        "waste_type": "Mixed — Open Burning",
        "location": "Canal Road, Ward 9",
        "lat": 10.5140,
        "lon": 76.2310,
        "priority": "HIGH",
        "status": "SUBMITTED",
        "reported_at": "2026-09-20 07:30",
        "image_url": None,
        "ai_confidence": 85,
        "ai_reason": "Smoke pattern and waste scatter detected indicating active burning activity.",
        "assigned_cleaner": None,
        "timeline": [
            {"step": "SUBMITTED", "done": True, "time": "Sep 20, 07:30 AM"},
            {"step": "VALIDATED", "done": False, "time": None},
            {"step": "ASSIGNED", "done": False, "time": None},
            {"step": "CLEANING", "done": False, "time": None},
            {"step": "VERIFICATION", "done": False, "time": None},
            {"step": "RESOLVED", "done": False, "time": None},
        ],
    },
]

# ---------------------------------------------------------------------------
# Mock Tasks (for Cleaner dashboard)
# ---------------------------------------------------------------------------

MOCK_TASKS = [
    {
        "id": "TSK-0421",
        "complaint_id": "CMP-2024-0891",
        "title": "Clean Illegal Dumping — Gandhi Park",
        "waste_type": "Construction & Plastic Mix",
        "location": "Gandhi Park Entrance, Ward 7",
        "lat": 10.5273,
        "lon": 76.2144,
        "priority": "CRITICAL",
        "distance": "1.2 km",
        "estimated_time": "45 min",
        "reported_at": "Sep 18, 09:15 AM",
        "assigned_at": "Sep 18, 11:30 AM",
        "status": "IN_PROGRESS",
        "description": "Large pile of construction debris and plastic waste. Requires heavy-duty equipment.",
        "image_url": None,
    },
    {
        "id": "TSK-0420",
        "complaint_id": "CMP-2024-0871",
        "title": "Biomedical Waste Removal — Ward 5",
        "waste_type": "Biomedical Waste",
        "location": "Near Community Health Centre, Ward 5",
        "lat": 10.5350,
        "lon": 76.2200,
        "priority": "CRITICAL",
        "distance": "3.5 km",
        "estimated_time": "60 min",
        "reported_at": "Sep 19, 11:00 AM",
        "assigned_at": "Sep 19, 12:00 PM",
        "status": "PENDING",
        "description": "Biomedical waste near drainage. Use full protective equipment.",
        "image_url": None,
    },
    {
        "id": "TSK-0418",
        "complaint_id": "CMP-2024-0879",
        "title": "Plastic Waste — School Zone",
        "waste_type": "Plastic Waste",
        "location": "St. Thomas School Gate, Ward 7",
        "lat": 10.5312,
        "lon": 76.2088,
        "priority": "MEDIUM",
        "distance": "0.8 km",
        "estimated_time": "20 min",
        "reported_at": "Sep 20, 08:45 AM",
        "assigned_at": "Sep 20, 11:00 AM",
        "status": "PENDING",
        "description": "Plastic bags and food wrappers. Standard cleanup required.",
        "image_url": None,
    },
    {
        "id": "TSK-0415",
        "complaint_id": "CMP-2024-0861",
        "title": "Drain Blockage — Residency Road",
        "waste_type": "Organic & Plastic Mix",
        "location": "Residency Road Drain, Ward 7",
        "lat": 10.5220,
        "lon": 76.2160,
        "priority": "HIGH",
        "distance": "2.1 km",
        "estimated_time": "35 min",
        "reported_at": "Sep 17, 15:00 PM",
        "assigned_at": "Sep 17, 17:00 PM",
        "status": "COMPLETED",
        "description": "Drain blockage cleared. Cleanup verified.",
        "image_url": None,
    },
]

# ---------------------------------------------------------------------------
# Mock Notifications
# ---------------------------------------------------------------------------

MOCK_NOTIFICATIONS = {
    "citizen": [
        {
            "id": "n001",
            "type": "success",
            "title": "Complaint Resolved",
            "message": "Your complaint CMP-2024-0885 (MG Road Waste Bin) has been resolved.",
            "time": "Sep 16, 10:30 AM",
            "read": False,
        },
        {
            "id": "n002",
            "type": "info",
            "title": "Cleaner Assigned",
            "message": "Rajan Pillai has been assigned to your complaint CMP-2024-0891.",
            "time": "Sep 18, 11:30 AM",
            "read": False,
        },
        {
            "id": "n003",
            "type": "info",
            "title": "Complaint Validated",
            "message": "Your complaint CMP-2024-0879 has been validated by municipal staff.",
            "time": "Sep 20, 10:00 AM",
            "read": True,
        },
        {
            "id": "n004",
            "type": "info",
            "title": "Report Submitted",
            "message": "Your waste report CMP-2024-0879 has been submitted successfully.",
            "time": "Sep 20, 08:45 AM",
            "read": True,
        },
    ],
    "cleaner": [
        {
            "id": "n101",
            "type": "warning",
            "title": "New Critical Task",
            "message": "A CRITICAL task has been assigned: Biomedical Waste — Ward 5.",
            "time": "Sep 19, 12:00 PM",
            "read": False,
        },
        {
            "id": "n102",
            "type": "info",
            "title": "Route Updated",
            "message": "Your task route for today has been optimized. Check My Tasks.",
            "time": "Sep 20, 07:30 AM",
            "read": False,
        },
        {
            "id": "n103",
            "type": "success",
            "title": "Task Verified",
            "message": "Task TSK-0415 (Drain Blockage) has been verified and marked resolved.",
            "time": "Sep 17, 18:00 PM",
            "read": True,
        },
    ],
    "municipal_staff": [
        {
            "id": "n201",
            "type": "warning",
            "title": "Escalation Alert",
            "message": "CMP-2024-0868 (Open Burning) has not been validated for 12 hours.",
            "time": "Sep 20, 12:00 PM",
            "read": False,
        },
        {
            "id": "n202",
            "type": "error",
            "title": "Critical Complaint",
            "message": "New CRITICAL complaint: Medical Waste — Ward 5. Immediate action required.",
            "time": "Sep 19, 11:00 AM",
            "read": False,
        },
        {
            "id": "n203",
            "type": "success",
            "title": "Complaint Resolved",
            "message": "CMP-2024-0885 has been resolved in 20 hours. Within SLA.",
            "time": "Sep 16, 10:30 AM",
            "read": True,
        },
    ],
    "admin": [
        {
            "id": "n301",
            "type": "info",
            "title": "System Health OK",
            "message": "All backend services are operational. Last check: 5 min ago.",
            "time": "Sep 20, 12:20 PM",
            "read": False,
        },
        {
            "id": "n302",
            "type": "warning",
            "title": "New User Registration",
            "message": "3 new user accounts pending approval from Ward 9.",
            "time": "Sep 20, 09:00 AM",
            "read": True,
        },
    ],
}

# ---------------------------------------------------------------------------
# Mock Map Markers
# ---------------------------------------------------------------------------

MOCK_MAP_MARKERS = [
    {
        "id": "m001",
        "lat": 10.5273,
        "lon": 76.2144,
        "type": "CRITICAL",
        "label": "Gandhi Park Dumping",
        "complaint_id": "CMP-2024-0891",
    },
    {
        "id": "m002",
        "lat": 10.5350,
        "lon": 76.2200,
        "type": "CRITICAL",
        "label": "Biomedical Waste",
        "complaint_id": "CMP-2024-0871",
    },
    {
        "id": "m003",
        "lat": 10.5312,
        "lon": 76.2088,
        "type": "MEDIUM",
        "label": "School Zone Plastic",
        "complaint_id": "CMP-2024-0879",
    },
    {
        "id": "m004",
        "lat": 10.5140,
        "lon": 76.2310,
        "type": "HIGH",
        "label": "Open Burning",
        "complaint_id": "CMP-2024-0868",
    },
    {
        "id": "m005",
        "lat": 10.5198,
        "lon": 76.2195,
        "type": "RESOLVED",
        "label": "MG Road Bin (Resolved)",
        "complaint_id": "CMP-2024-0885",
    },
]

# ---------------------------------------------------------------------------
# Mock Awareness Content
# ---------------------------------------------------------------------------

MOCK_AWARENESS_CONTENT = [
    {
        "id": "aw001",
        "category": "Waste Segregation",
        "title": "How to Segregate Waste at Home",
        "title_ml": "വീട്ടിൽ മാലിന്യം വേർതിരിക്കുന്നതെങ്ങനെ",
        "summary": "Proper segregation of wet, dry, and hazardous waste is the first step in responsible waste management.",
        "summary_ml": "നനഞ്ഞ, ഉണങ്ങിയ, അപകടകരമായ മാലിന്യം വേർതിരിക്കൽ ഉത്തരവാദിത്തമുള്ള മാലിന്യ സംസ്കരണത്തിന്റെ ആദ്യ പടിയാണ്.",
        "content": [
            "🟢 Green Bin (Wet Waste): Food scraps, vegetable peels, fruit waste, garden waste.",
            "🔵 Blue Bin (Dry Waste): Paper, cardboard, plastic bottles, glass, metal cans.",
            "🔴 Red Bin (Hazardous): Batteries, medicines, e-waste, paint, chemicals.",
            "Never mix wet and dry waste — this is the most important rule.",
            "Compost your wet waste if possible to reduce landfill contribution.",
        ],
        "icon": "🗂️",
        "color": "#2e7d32",
        "featured": True,
    },
    {
        "id": "aw002",
        "category": "Plastic Reduction",
        "title": "Reducing Single-Use Plastic",
        "title_ml": "ഒറ്റത്തവണ ഉപയോഗ പ്ലാസ്റ്റിക് കുറയ്ക്കൽ",
        "summary": "Single-use plastics are the largest contributor to waste in Kerala. Simple changes can make a huge difference.",
        "summary_ml": "കേരളത്തിലെ ഏറ്റവും വലിയ മാലിന്യ ഉറവിടം ഒറ്റത്തവണ ഉപയോഗ പ്ലാസ്റ്റിക്കാണ്.",
        "content": [
            "Carry reusable cloth bags when shopping.",
            "Use a steel or glass water bottle instead of plastic bottles.",
            "Avoid plastic straws — use bamboo or steel alternatives.",
            "Buy in bulk to reduce individual plastic packaging.",
            "Kerala has banned many single-use plastics — know the law.",
        ],
        "icon": "♻️",
        "color": "#1565c0",
        "featured": True,
    },
    {
        "id": "aw003",
        "category": "Composting",
        "title": "Home Composting Guide",
        "title_ml": "വീട്ടിൽ കമ്പോസ്റ്റ് ഉണ്ടാക്കൽ",
        "summary": "Turn your kitchen waste into rich compost. It's easier than you think and helps your garden too.",
        "summary_ml": "നിങ്ങളുടെ അടുക്കള മാലിന്യം ഉപയോഗപ്രദമായ കമ്പോസ്റ്റ് ആക്കി മാറ്റൂ.",
        "content": [
            "Start with a compost bin or pit in your backyard.",
            "Add kitchen scraps: vegetable peels, fruit waste, eggshells.",
            "Layer with dry leaves or garden waste to balance moisture.",
            "Turn the pile every week for proper aeration.",
            "Ready in 6-8 weeks — use as fertilizer for your garden.",
        ],
        "icon": "🌱",
        "color": "#2e7d32",
        "featured": False,
    },
    {
        "id": "aw004",
        "category": "Local Guidelines",
        "title": "Thrissur Corporation Waste Rules",
        "title_ml": "തൃശ്ശൂർ കോർപ്പറേഷൻ മാലിന്യ നിയമങ്ങൾ",
        "summary": "Know the local waste disposal rules to avoid penalties and contribute to a cleaner Thrissur.",
        "summary_ml": "ശിക്ഷ ഒഴിവാക്കാനും ശുദ്ധമായ തൃശ്ശൂർ ഉണ്ടാക്കാനും പ്രാദേശിക മാലിന്യ നിയമങ്ങൾ അറിയൂ.",
        "content": [
            "Waste must be segregated before collection — mandatory.",
            "Bulk generators (>10 kg/day) must process waste on-site.",
            "Burning waste is prohibited — fines apply.",
            "Construction waste must be disposed at designated sites.",
            "Report violations using the SwachhLoop AI app.",
        ],
        "icon": "📋",
        "color": "#6a0572",
        "featured": False,
    },
    {
        "id": "aw005",
        "category": "E-Waste",
        "title": "Electronic Waste Disposal",
        "title_ml": "ഇലക്ട്രോണിക് മാലിന്യ സംസ്കരണം",
        "summary": "Old phones, batteries, and electronics contain hazardous materials — never throw them in regular bins.",
        "summary_ml": "പഴയ ഫോണുകളും ബാറ്ററികളും ഇലക്ട്രോണിക്സുകളും അപകടകരമായ വസ്തുക്കൾ ഉള്ളതാണ്.",
        "content": [
            "Never dispose e-waste in regular dustbins.",
            "Take old phones, laptops, and batteries to certified collection centers.",
            "Many electronics stores accept old devices for recycling.",
            "Thrissur Corporation has e-waste collection drives quarterly.",
            "Check the SwachhLoop awareness section for upcoming drives.",
        ],
        "icon": "💻",
        "color": "#e65100",
        "featured": False,
    },
]

# ---------------------------------------------------------------------------
# Admin User Management Data
# ---------------------------------------------------------------------------

MOCK_USERS_ADMIN = [
    {"id": "u001", "name": "Arjun Nair", "email": "citizen@swachhloop.ai", "role": "Citizen", "ward": "Ward 7", "status": "Active", "joined": "Mar 2025"},
    {"id": "u002", "name": "Rajan Pillai", "email": "cleaner@swachhloop.ai", "role": "Cleaner", "ward": "Zone B", "status": "Active", "joined": "Jan 2025"},
    {"id": "u003", "name": "Priya Menon", "email": "staff@swachhloop.ai", "role": "Municipal Staff", "ward": "All", "status": "Active", "joined": "Aug 2024"},
    {"id": "u004", "name": "Dr. Suresh Kumar", "email": "admin@swachhloop.ai", "role": "Admin", "ward": "All", "status": "Active", "joined": "Jun 2024"},
    {"id": "u005", "name": "Meena Thomas", "email": "meena.t@ward5.in", "role": "Citizen", "ward": "Ward 5", "status": "Active", "joined": "Sep 2025"},
    {"id": "u006", "name": "Rajesh Varma", "email": "rajesh.v@ward9.in", "role": "Citizen", "ward": "Ward 9", "status": "Active", "joined": "Sep 2025"},
    {"id": "u007", "name": "Vijayan K.", "email": "vijayan.k@corp.in", "role": "Cleaner", "ward": "Zone A", "status": "Active", "joined": "Feb 2025"},
    {"id": "u008", "name": "Latha S.", "email": "latha.s@corp.in", "role": "Cleaner", "ward": "Zone C", "status": "Inactive", "joined": "Apr 2025"},
]

# ---------------------------------------------------------------------------
# System Health (Demo — Phase 3 replaces with real health checks)
# ---------------------------------------------------------------------------

MOCK_SYSTEM_HEALTH = [
    {"service": "Backend API", "status": "Online", "latency": "12ms", "uptime": "99.8%", "icon": "🟢"},
    {"service": "Database", "status": "Online", "latency": "8ms", "uptime": "99.9%", "icon": "🟢"},
    {"service": "AI Services", "status": "Stub (Phase 3)", "latency": "—", "uptime": "—", "icon": "🟡"},
    {"service": "RAG Pipeline", "status": "Stub (Phase 3)", "latency": "—", "uptime": "—", "icon": "🟡"},
    {"service": "Route Optimizer", "status": "Stub (Phase 4)", "latency": "—", "uptime": "—", "icon": "🟡"},
]

# ---------------------------------------------------------------------------
# Dashboard Stats (Municipal Staff)
# ---------------------------------------------------------------------------

MUNICIPAL_STATS = {
    "total_complaints": 42,
    "pending": 8,
    "validated": 6,
    "assigned": 11,
    "cleaning": 7,
    "verification": 4,
    "resolved": 128,
    "escalated": 3,
    "avg_resolution_hours": 18.4,
    "cleaners_available": 5,
    "cleaners_on_task": 8,
}

# ---------------------------------------------------------------------------
# Audit Log (Admin)
# ---------------------------------------------------------------------------

MOCK_AUDIT_LOG = [
    {"time": "Sep 20, 12:15 PM", "user": "Priya Menon (Staff)", "action": "Validated complaint CMP-2024-0879", "type": "VALIDATE"},
    {"time": "Sep 20, 11:00 AM", "user": "Priya Menon (Staff)", "action": "Assigned TSK-0418 to Rajan Pillai", "type": "ASSIGN"},
    {"time": "Sep 20, 08:45 AM", "user": "Arjun Nair (Citizen)", "action": "Submitted complaint CMP-2024-0879", "type": "SUBMIT"},
    {"time": "Sep 19, 12:00 PM", "user": "Priya Menon (Staff)", "action": "Assigned TSK-0420 to Vijayan K.", "type": "ASSIGN"},
    {"time": "Sep 19, 11:30 AM", "user": "System (Auto)", "action": "Validated CMP-2024-0871 — AI confidence 96%", "type": "AI"},
    {"time": "Sep 18, 11:30 AM", "user": "Priya Menon (Staff)", "action": "Assigned TSK-0421 to Rajan Pillai", "type": "ASSIGN"},
    {"time": "Sep 16, 10:30 AM", "user": "System (Auto)", "action": "Marked CMP-2024-0885 as RESOLVED", "type": "RESOLVE"},
    {"time": "Sep 15, 03:00 PM", "user": "System (Auto)", "action": "Validated CMP-2024-0885 — AI confidence 88%", "type": "AI"},
]
