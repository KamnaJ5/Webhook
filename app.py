from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3, os, uuid
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'civic_secret_2024'

UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB_PATH = 'civic.db'

# ─── Priority Scoring ───────────────────────────────────────────────
CATEGORY_WEIGHT = {
    'Road Damage':      5,
    'Flooding / Drain': 5,
    'Power Outage':     4,
    'Water Leakage':    4,
    'Garbage Overflow': 3,
    'Broken Streetlight': 3,
    'Other':            2,
}
SEVERITY_WEIGHT = {'High': 3, 'Medium': 2, 'Low': 1}

def calc_priority(category, severity, location, conn):
    base = CATEGORY_WEIGHT.get(category, 2) + SEVERITY_WEIGHT.get(severity, 1)
    # recurrence bonus: same category in same location
    cur = conn.execute(
        "SELECT COUNT(*) FROM issues WHERE category=? AND location LIKE ?",
        (category, f"%{location.split(',')[0].strip()[:20]}%")
    )
    recurrence = cur.fetchone()[0]
    score = base + min(recurrence, 5)   # cap bonus at 5
    if score >= 10:   label = 'Critical'
    elif score >= 7:  label = 'High'
    elif score >= 5:  label = 'Medium'
    else:             label = 'Low'
    return score, label

# ─── DB helpers ─────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS issues (
        id          TEXT PRIMARY KEY,
        name        TEXT NOT NULL,
        phone       TEXT,
        category    TEXT NOT NULL,
        severity    TEXT NOT NULL,
        description TEXT NOT NULL,
        location    TEXT NOT NULL,
        photo       TEXT,
        status      TEXT DEFAULT 'Pending',
        priority_score INTEGER DEFAULT 0,
        priority_label TEXT DEFAULT 'Low',
        assigned_to TEXT,
        admin_notes TEXT,
        created_at  TEXT NOT NULL,
        updated_at  TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

# ─── Citizen Routes ──────────────────────────────────────────────────
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/report', methods=['GET', 'POST'])
def report():
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        phone    = request.form.get('phone', '').strip()
        category = request.form.get('category', '')
        severity = request.form.get('severity', '')
        desc     = request.form.get('description', '').strip()
        location = request.form.get('location', '').strip()

        if not all([name, category, severity, desc, location]):
            flash('Please fill all required fields.', 'error')
            return render_template('report.html')

        # Photo upload
        photo_filename = None
        file = request.files.get('photo')
        if file and file.filename:
            ext = file.filename.rsplit('.', 1)[-1].lower()
            if ext in ALLOWED_EXTENSIONS:
                photo_filename = f"{uuid.uuid4().hex}.{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))

        issue_id = 'CIV' + uuid.uuid4().hex[:8].upper()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = get_db()
        score, label = calc_priority(category, severity, location, conn)
        conn.execute(
            '''INSERT INTO issues
               (id,name,phone,category,severity,description,location,photo,
                status,priority_score,priority_label,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (issue_id, name, phone, category, severity, desc, location,
             photo_filename, 'Pending', score, label, now, now)
        )
        conn.commit()
        conn.close()

        flash(f'Issue reported! Your tracking ID: {issue_id}', 'success')
        return redirect(url_for('track', issue_id=issue_id))

    return render_template('report.html')

@app.route('/track')
def track():
    issue_id = request.args.get('issue_id', '').strip().upper()
    issue = None
    if issue_id:
        conn = get_db()
        issue = conn.execute('SELECT * FROM issues WHERE id=?', (issue_id,)).fetchone()
        conn.close()
        if not issue:
            flash('No issue found with that ID.', 'error')
    return render_template('track.html', issue=issue, issue_id=issue_id)

# ─── Authority Routes ────────────────────────────────────────────────
@app.route('/admin')
def admin():
    conn = get_db()
    status_filter   = request.args.get('status', '')
    category_filter = request.args.get('category', '')
    priority_filter = request.args.get('priority', '')

    query = 'SELECT * FROM issues WHERE 1=1'
    params = []
    if status_filter:
        query += ' AND status=?'; params.append(status_filter)
    if category_filter:
        query += ' AND category=?'; params.append(category_filter)
    if priority_filter:
        query += ' AND priority_label=?'; params.append(priority_filter)
    query += ' ORDER BY priority_score DESC, created_at DESC'

    issues = conn.execute(query, params).fetchall()

    # stats for top bar
    stats = {
        'total':    conn.execute('SELECT COUNT(*) FROM issues').fetchone()[0],
        'pending':  conn.execute("SELECT COUNT(*) FROM issues WHERE status='Pending'").fetchone()[0],
        'progress': conn.execute("SELECT COUNT(*) FROM issues WHERE status='In Progress'").fetchone()[0],
        'resolved': conn.execute("SELECT COUNT(*) FROM issues WHERE status='Resolved'").fetchone()[0],
    }
    conn.close()
    return render_template('admin.html', issues=issues, stats=stats,
                           status_filter=status_filter,
                           category_filter=category_filter,
                           priority_filter=priority_filter)

@app.route('/admin/issue/<issue_id>', methods=['GET', 'POST'])
def admin_issue(issue_id):
    conn = get_db()
    if request.method == 'POST':
        status      = request.form.get('status')
        assigned_to = request.form.get('assigned_to', '').strip()
        admin_notes = request.form.get('admin_notes', '').strip()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute(
            'UPDATE issues SET status=?,assigned_to=?,admin_notes=?,updated_at=? WHERE id=?',
            (status, assigned_to, admin_notes, now, issue_id)
        )
        conn.commit()
        flash('Issue updated successfully.', 'success')
        return redirect(url_for('admin_issue', issue_id=issue_id))

    issue = conn.execute('SELECT * FROM issues WHERE id=?', (issue_id,)).fetchone()
    conn.close()
    if not issue:
        flash('Issue not found.', 'error')
        return redirect(url_for('admin'))
    return render_template('issue_detail.html', issue=issue)

@app.route('/analytics')
def analytics():
    conn = get_db()
    # Category breakdown
    cat_data = conn.execute(
        "SELECT category, COUNT(*) as cnt FROM issues GROUP BY category ORDER BY cnt DESC"
    ).fetchall()
    # Status breakdown
    status_data = conn.execute(
        "SELECT status, COUNT(*) as cnt FROM issues GROUP BY status"
    ).fetchall()
    # Priority breakdown
    priority_data = conn.execute(
        "SELECT priority_label, COUNT(*) as cnt FROM issues GROUP BY priority_label ORDER BY priority_score DESC"
    ).fetchall()
    # Top locations
    location_data = conn.execute(
        "SELECT location, COUNT(*) as cnt FROM issues GROUP BY location ORDER BY cnt DESC LIMIT 5"
    ).fetchall()
    # Recent trend (last 7 days by date)
    trend_data = conn.execute(
        """SELECT substr(created_at,1,10) as day, COUNT(*) as cnt
           FROM issues GROUP BY day ORDER BY day DESC LIMIT 7"""
    ).fetchall()
    conn.close()
    return render_template('analytics.html',
                           cat_data=cat_data,
                           status_data=status_data,
                           priority_data=priority_data,
                           location_data=location_data,
                           trend_data=trend_data)

def seed_db():
    """Seed sample data for demo/presentation if DB is empty."""
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM issues').fetchone()[0]
    if count > 0:
        conn.close()
        return
    samples = [
        ('CIV0000001','Amit Sharma','9876543210','Road Damage','High',
         'Large pothole on main road near bus stop causing accidents',
         'MG Road, near City Bus Stop, Ward 5','Pending'),
        ('CIV0000002','Priya Nair','9845001234','Garbage Overflow','Medium',
         'Garbage bin overflowing for 3 days, causing health hazard',
         'Gandhi Nagar, Sector 12','Pending'),
        ('CIV0000003','Rajan Mehta','','Flooding / Drain','High',
         'Blocked drain causing water logging after every rain',
         'MG Road, Ward 5','In Progress'),
        ('CIV0000004','Sunita Rao','9123456780','Broken Streetlight','Low',
         'Streetlight not working for 2 weeks, area is dark at night',
         'Park Street, Sector 8','In Progress'),
        ('CIV0000005','Vikram Singh','9012345678','Water Leakage','High',
         'Water pipe burst near junction, wasting municipal water',
         'Civil Lines, Junction Point','Resolved'),
    ]
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for s in samples:
        score, label = calc_priority(s[3], s[4], s[6], conn)
        conn.execute(
            '''INSERT OR IGNORE INTO issues
               (id,name,phone,category,severity,description,location,
                status,priority_score,priority_label,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
            (*s, score, label, now, now)
        )
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    seed_db()
    app.run(host='0.0.0.0',debug=True,port='3000')
