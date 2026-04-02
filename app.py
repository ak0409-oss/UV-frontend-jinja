import os, time, datetime, sys
from functools import wraps
from flask import (Flask, render_template, redirect, url_for,
                   request, session, flash)
from authlib.integrations.flask_client import OAuth

sys.path.insert(0, os.path.dirname(__file__))
from data.mock_data import get_initial_data, BAD_WORDS

# ── App setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "univoice-dev-secret-change-me")

# Allow plain-http OAuth callbacks in local development only
if os.environ.get("FLASK_ENV") != "production":
    os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

# ── Google OAuth ──────────────────────────────────────────────────────────────
oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    # Google's discovery document — authlib fetches all endpoints automatically
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile",
        "prompt": "select_account",   # always show account picker
    },
)

# ── In-memory data store ───────────────────────────────────────────────────────
_store = get_initial_data()

ROLE_ROUTES = {
    "admin":   "/admin",
    "student": "/student",
    "warden":  "/warden",
    "mentor":  "/mentor",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def find(collection, id_):
    return next((x for x in _store[collection] if x["id"] == id_), None)


def find_by_email(email):
    return next((u for u in _store["users"] if u["email"] == email), None)


def get_current_user():
    uid = session.get("user_id")
    return find("users", uid) if uid else None


def _set_session(user, picture=None):
    """Populate session after successful authentication."""
    session["user_id"]      = user["id"]
    session["user_role"]    = user["role"]
    session["user_name"]    = user["name"]
    session["user_picture"] = picture or ""


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get("user_role") not in roles:
                flash("Unauthorised access.", "error")
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        return decorated
    return decorator


def inject_user(template, **kwargs):
    return render_template(
        template,
        current_user=get_current_user(),
        user_picture=session.get("user_picture", ""),
        **kwargs,
    )


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(ROLE_ROUTES.get(session.get("user_role"), "/login"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    # Redirect already-logged-in users straight to their dashboard
    if "user_id" in session:
        return redirect(ROLE_ROUTES.get(session.get("user_role"), "/"))

    oauth_enabled = bool(
        os.environ.get("GOOGLE_CLIENT_ID") and
        os.environ.get("GOOGLE_CLIENT_SECRET")
    )

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = next(
            (u for u in _store["users"]
             if u["email"].lower() == email and u.get("password") == password),
            None,
        )
        if user:
            _set_session(user)
            flash(f"Welcome, {user['name']}!", "success")
            return redirect(ROLE_ROUTES[user["role"]])
        flash("Invalid email or password.", "error")

    return render_template("login.html", oauth_enabled=oauth_enabled)


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("login"))


# ── Google OAuth routes ───────────────────────────────────────────────────────

@app.route("/auth/google")
def google_login():
    """Kick off the Google OAuth2 flow."""
    if not (os.environ.get("GOOGLE_CLIENT_ID") and os.environ.get("GOOGLE_CLIENT_SECRET")):
        flash("Google Sign-In is not configured on this server.", "error")
        return redirect(url_for("login"))

    redirect_uri = url_for("google_callback", _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route("/auth/google/callback")
def google_callback():
    """Handle the redirect back from Google."""
    try:
        token    = google.authorize_access_token()
        userinfo = token.get("userinfo") or google.userinfo()
    except Exception as exc:
        flash(f"Google authentication failed: {exc}", "error")
        return redirect(url_for("login"))

    email   = (userinfo.get("email") or "").strip().lower()
    name    = userinfo.get("name", "")
    picture = userinfo.get("picture", "")

    if not email:
        flash("Could not retrieve your email address from Google.", "error")
        return redirect(url_for("login"))

    # Match Google email against registered users
    user = find_by_email(email)
    if user:
        _set_session(user, picture=picture)
        flash(f"Welcome, {user['name']}! (signed in via Google)", "success")
        return redirect(ROLE_ROUTES[user["role"]])

    # Email not in the system — show a helpful error
    flash(
        f"No UniVoice account found for {email}. "
        "Ask your administrator to register your email first, "
        "then try again.",
        "error",
    )
    return redirect(url_for("login"))


# ── Admin ─────────────────────────────────────────────────────────────────────

@app.route("/admin")
@login_required
@role_required("admin")
def admin_dashboard():
    return inject_user("admin/dashboard.html")


@app.route("/admin/hostels", methods=["GET", "POST"])
@login_required
@role_required("admin")
def admin_hostels():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "create":
            _store["hostels"].append({
                "id":         f"h{int(time.time())}",
                "name":       request.form["name"],
                "gender":     request.form["gender"],
                "totalRooms": int(request.form.get("totalRooms", 50)),
            })
            flash("Hostel created successfully.", "success")
        elif action == "delete":
            hid = request.form["hostel_id"]
            _store["hostels"] = [h for h in _store["hostels"] if h["id"] != hid]
            for u in _store["users"]:
                if u.get("hostelId") == hid:
                    u["hostelId"] = None
            flash("Hostel deleted.", "success")
        return redirect(url_for("admin_hostels"))
    return inject_user("admin/hostels.html", hostels=_store["hostels"])


@app.route("/admin/wardens", methods=["GET", "POST"])
@login_required
@role_required("admin")
def admin_wardens():
    wardens = [u for u in _store["users"] if u["role"] == "warden"]
    if request.method == "POST":
        action = request.form.get("action")
        if action == "create":
            _store["users"].append({
                "id":       f"w{int(time.time())}",
                "email":    request.form["email"],
                "name":     request.form["name"],
                "password": request.form["password"],
                "role":     "warden",
                "hostelId": request.form.get("hostelId") or None,
            })
            flash("Warden created.", "success")
        elif action == "delete":
            uid = request.form["user_id"]
            _store["users"] = [u for u in _store["users"] if u["id"] != uid]
            flash("Warden deleted.", "success")
        return redirect(url_for("admin_wardens"))
    hostel_map = {h["id"]: h["name"] for h in _store["hostels"]}
    return inject_user("admin/wardens.html", wardens=wardens,
                       hostels=_store["hostels"], hostel_map=hostel_map)


@app.route("/admin/mentors", methods=["GET", "POST"])
@login_required
@role_required("admin")
def admin_mentors():
    mentors = [u for u in _store["users"] if u["role"] == "mentor"]
    if request.method == "POST":
        action = request.form.get("action")
        if action == "create":
            _store["users"].append({
                "id":       f"m{int(time.time())}",
                "email":    request.form["email"],
                "name":     request.form["name"],
                "password": request.form["password"],
                "role":     "mentor",
            })
            flash("Mentor created.", "success")
        elif action == "delete":
            uid = request.form["user_id"]
            _store["users"] = [u for u in _store["users"] if u["id"] != uid]
            flash("Mentor deleted.", "success")
        return redirect(url_for("admin_mentors"))
    return inject_user("admin/mentors.html", mentors=mentors)


@app.route("/admin/students", methods=["GET", "POST"])
@login_required
@role_required("admin")
def admin_students():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "create":
            _store["users"].append({
                "id":         f"s{int(time.time())}",
                "email":      request.form["email"],
                "name":       request.form["name"],
                "password":   request.form["password"],
                "role":       "student",
                "hostelId":   request.form.get("hostelId")   or None,
                "mentorId":   request.form.get("mentorId")   or None,
                "roomNumber": request.form.get("roomNumber") or None,
            })
            flash("Student created.", "success")
        elif action == "delete":
            uid = request.form["user_id"]
            _store["users"] = [u for u in _store["users"] if u["id"] != uid]
            flash("Student deleted.", "success")
        return redirect(url_for("admin_students"))
    sel_hostel = request.args.get("hostel", "")
    students   = [u for u in _store["users"] if u["role"] == "student"
                  and (not sel_hostel or u.get("hostelId") == sel_hostel)]
    mentors    = [u for u in _store["users"] if u["role"] == "mentor"]
    mentor_map = {m["id"]: m["name"] for m in mentors}
    return inject_user("admin/students.html", students=students,
                       hostels=_store["hostels"], mentors=mentors,
                       mentor_map=mentor_map, sel_hostel=sel_hostel)


@app.route("/admin/edit-user/<uid>", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_user(uid):
    user = find("users", uid)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        user["name"]     = request.form["name"]
        user["email"]    = request.form["email"]
        user["hostelId"] = request.form.get("hostelId") or None
        user["mentorId"] = request.form.get("mentorId") or None
        flash("User updated.", "success")
        return redirect(url_for("admin_dashboard"))
    mentors = [u for u in _store["users"] if u["role"] == "mentor"]
    return inject_user("admin/edit_user.html", user=user,
                       hostels=_store["hostels"], mentors=mentors)


@app.route("/admin/student/<uid>")
@login_required
@role_required("admin")
def student_profile(uid):
    student = find("users", uid)
    if not student:
        flash("Student not found.", "error")
        return redirect(url_for("admin_students"))
    hostel        = find("hostels", student.get("hostelId")) if student.get("hostelId") else None
    mentor        = find("users",   student.get("mentorId")) if student.get("mentorId") else None
    all_complaints = [c for c in _store["complaints"] if c["userId"] == uid]
    flagged       = [c for c in all_complaints if c.get("isAbusive")]
    history       = [c for c in all_complaints if not c.get("isAbusive")]
    return inject_user("admin/student_profile.html", student=student,
                       hostel=hostel, mentor=mentor, flagged=flagged, history=history)


@app.route("/admin/complaints", methods=["GET", "POST"])
@login_required
@role_required("admin")
def admin_complaints():
    if request.method == "POST":
        cid = request.form["complaint_id"]
        _store["complaints"] = [c for c in _store["complaints"] if c["id"] != cid]
        flash("Complaint deleted.", "success")
        return redirect(url_for("admin_complaints"))
    sel_hostel = request.args.get("hostel", "")
    sel_status = request.args.get("status", "pending")
    filtered   = [c for c in _store["complaints"]
                  if c["status"] == sel_status
                  and (not sel_hostel or c.get("hostelId") == sel_hostel)]
    user_map   = {u["id"]: u for u in _store["users"]}
    counts     = {
        s: len([c for c in _store["complaints"]
                if c["status"] == s
                and (not sel_hostel or c.get("hostelId") == sel_hostel)])
        for s in ("pending", "in_progress", "resolved", "rejected", "flagged")
    }
    return inject_user("admin/complaints.html", complaints=filtered,
                       hostels=_store["hostels"], user_map=user_map,
                       sel_hostel=sel_hostel, sel_status=sel_status, counts=counts)


# ── Student ───────────────────────────────────────────────────────────────────

@app.route("/student", methods=["GET", "POST"])
@login_required
@role_required("student")
def student_dashboard():
    current_user = get_current_user()
    if request.method == "POST":
        heading     = request.form.get("heading", "")
        description = request.form.get("description", "")
        text        = f"{heading} {description}".lower()
        is_abusive  = any(w in text for w in BAD_WORDS)
        _store["complaints"].append({
            "id":          f"c{int(time.time())}",
            "heading":     heading,
            "description": description,
            "category":    request.form.get("category", "others"),
            "createdAt":   datetime.date.today().isoformat(),
            "status":      "flagged" if is_abusive else "pending",
            "isUrgent":    False,
            "isAbusive":   is_abusive,
            "userId":      current_user["id"],
            "hostelId":    current_user.get("hostelId", ""),
        })
        flash(
            "Complaint flagged for abusive content." if is_abusive
            else "Complaint filed successfully.",
            "warning" if is_abusive else "success",
        )
        return redirect(url_for("student_dashboard"))
    my_complaints = [c for c in _store["complaints"] if c["userId"] == current_user["id"]]
    hostel        = find("hostels", current_user.get("hostelId")) if current_user.get("hostelId") else None
    categories    = ["electric", "toilet", "wifi", "mess", "personal", "others"]
    return inject_user("student_dashboard.html", my_complaints=my_complaints,
                       hostel=hostel, categories=categories)


# ── Warden ────────────────────────────────────────────────────────────────────

@app.route("/warden", methods=["GET", "POST"])
@login_required
@role_required("warden")
def warden_dashboard():
    current_user = get_current_user()
    if request.method == "POST":
        cid     = request.form["complaint_id"]
        action  = request.form["action"]
        comment = request.form.get("comment", "").strip()
        c = find("complaints", cid)
        if c:
            c["status"] = action
            if comment:
                c["wardenComment"] = comment
            if action == "resolved":
                c["resolvedAt"] = datetime.date.today().isoformat()
        flash(f"Complaint marked as {action}.", "success")
        return redirect(url_for("warden_dashboard"))
    hid              = current_user.get("hostelId")
    hostel_complaints = [c for c in _store["complaints"] if c.get("hostelId") == hid]
    user_map         = {u["id"]: u for u in _store["users"]}
    hostel           = find("hostels", hid) if hid else None
    urgent      = [c for c in hostel_complaints if c.get("isUrgent")    and c["status"] not in ("resolved","rejected")]
    pending     = [c for c in hostel_complaints if c["status"] == "pending"     and not c.get("isUrgent")]
    in_progress = [c for c in hostel_complaints if c["status"] == "in_progress" and not c.get("isUrgent")]
    completed   = [c for c in hostel_complaints if c["status"] in ("resolved","rejected")]
    archived    = [c for c in hostel_complaints if c["status"] == "flagged"]
    return inject_user("warden_dashboard.html", hostel=hostel, user_map=user_map,
                       urgent=urgent, pending=pending, in_progress=in_progress,
                       completed=completed, archived=archived)


# ── Mentor ────────────────────────────────────────────────────────────────────

@app.route("/mentor", methods=["GET", "POST"])
@login_required
@role_required("mentor")
def mentor_dashboard():
    current_user = get_current_user()
    if request.method == "POST":
        cid = request.form["complaint_id"]
        c   = find("complaints", cid)
        if c:
            comment   = request.form.get("comment", "").strip()
            is_urgent = request.form.get("is_urgent") == "1"
            if comment:
                c["mentorComment"] = comment
            c["isUrgent"] = is_urgent
        flash("Complaint updated.", "success")
        return redirect(url_for("mentor_dashboard"))
    mentee_ids       = [u["id"] for u in _store["users"] if u.get("mentorId") == current_user["id"]]
    mentee_complaints = [c for c in _store["complaints"] if c["userId"] in mentee_ids]
    user_map         = {u["id"]: u for u in _store["users"]}
    return inject_user("mentor_dashboard.html",
                       mentee_complaints=mentee_complaints, user_map=user_map)


# ── Error handlers ────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template("not_found.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("not_found.html"), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
