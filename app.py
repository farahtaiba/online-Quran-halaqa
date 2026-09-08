from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from pathlib import Path
from datetime import datetime
import os, secrets

BASE = Path(__file__).resolve().parent
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + str(BASE / 'halaqa.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = str(BASE / 'static' / 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
db = SQLAlchemy(app)

ALLOWED = {'pdf','jpg','jpeg','png'}

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False)
    phone = db.Column(db.String(30), default='')
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='student', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=False)
    level = db.Column(db.String(80), default='All Levels')
    icon = db.Column(db.String(20), default='◈')
    active = db.Column(db.Boolean, default=True)

class Worksheet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, default='')
    filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    worksheet_id = db.Column(db.Integer, db.ForeignKey('worksheet.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(30), default='Submitted')
    feedback = db.Column(db.Text, default='')
    corrected_filename = db.Column(db.String(255), default='')
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    worksheet = db.relationship('Worksheet', backref='submissions')
    student = db.relationship('User', backref='submissions')

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Ayah(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    arabic = db.Column(db.Text, nullable=False)
    english = db.Column(db.Text, nullable=False)
    urdu = db.Column(db.Text, nullable=False)
    surah = db.Column(db.String(120), nullable=False)
    reference = db.Column(db.String(30), nullable=False)
    active = db.Column(db.Boolean, default=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

def teacher_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get('role') != 'teacher':
            flash('Teacher access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

def save_upload(file, prefix):
    if not file or not file.filename or not allowed_file(file.filename):
        return None
    ext = file.filename.rsplit('.',1)[1].lower()
    name = secure_filename(f'{prefix}_{datetime.utcnow().strftime("%Y%m%d%H%M%S%f")}.{ext}')
    file.save(Path(app.config['UPLOAD_FOLDER']) / name)
    return name

@app.context_processor
def inject_globals():
    return {'year': datetime.now().year}

@app.route('/')
def home():
    ayah = Ayah.query.filter_by(active=True).order_by(Ayah.id.desc()).first()
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(3).all()
    courses = Course.query.filter_by(active=True).all()
    return render_template('index.html', ayah=ayah, announcements=announcements, courses=courses)

@app.route('/about')
def about(): return render_template('about.html')
@app.route('/courses')
def courses(): return render_template('courses.html', courses=Course.query.filter_by(active=True).all())
@app.route('/schedule')
def schedule(): return render_template('schedule.html')

@app.route('/contact', methods=['GET','POST'])
def contact():
    if request.method == 'POST':
        flash('JazakAllahu khairan. Your message has been received.', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name','').strip(); email = request.form.get('email','').strip().lower()
        phone = request.form.get('phone','').strip(); password = request.form.get('password','')
        if not name or not email or len(password) < 8:
            flash('Please provide your name, valid email and a password of at least 8 characters.', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('An account with this email already exists.', 'danger'); return redirect(url_for('register'))
        db.session.add(User(name=name,email=email,phone=phone,password=generate_password_hash(password),role='student'))
        db.session.commit(); flash('Account created successfully. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email=request.form.get('email','').strip().lower(); password=request.form.get('password','')
        user=User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password,password):
            session.clear(); session.update(user_id=user.id,name=user.name,role=user.role)
            return redirect(url_for('teacher_dashboard' if user.role=='teacher' else 'student_dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('home'))

@app.route('/student')
@login_required
def student_dashboard():
    if session.get('role') == 'teacher': return redirect(url_for('teacher_dashboard'))
    user=User.query.get_or_404(session['user_id'])
    worksheets=Worksheet.query.order_by(Worksheet.created_at.desc()).all()
    submissions=Submission.query.filter_by(student_id=user.id).order_by(Submission.submitted_at.desc()).all()
    announcements=Announcement.query.order_by(Announcement.created_at.desc()).limit(5).all()
    return render_template('student_dashboard.html', user=user, worksheets=worksheets, submissions=submissions, announcements=announcements)

@app.route('/student/profile', methods=['POST'])
@login_required
def student_profile():
    user=User.query.get_or_404(session['user_id'])
    user.name=request.form.get('name','').strip() or user.name; user.phone=request.form.get('phone','').strip()
    db.session.commit(); session['name']=user.name; flash('Profile updated.', 'success')
    return redirect(url_for('student_dashboard'))

@app.route('/worksheet/<int:wid>/download')
@login_required
def worksheet_download(wid):
    w=Worksheet.query.get_or_404(wid); return send_from_directory(app.config['UPLOAD_FOLDER'], w.filename, as_attachment=True)

@app.route('/worksheet/<int:wid>/submit', methods=['POST'])
@login_required
def submit_worksheet(wid):
    if session.get('role')=='teacher': return redirect(url_for('teacher_dashboard'))
    w=Worksheet.query.get_or_404(wid); file=request.files.get('file'); filename=save_upload(file,f'student_{session["user_id"]}')
    if not filename:
        flash('Upload a PDF, JPG, JPEG or PNG file.', 'danger'); return redirect(url_for('student_dashboard'))
    db.session.add(Submission(worksheet_id=w.id,student_id=session['user_id'],filename=filename,status='Submitted'))
    db.session.commit(); flash('Worksheet submitted successfully.', 'success'); return redirect(url_for('student_dashboard'))

@app.route('/submission/<int:sid>/file')
@login_required
def submission_file(sid):
    s=Submission.query.get_or_404(sid)
    if s.student_id != session['user_id'] and session.get('role')!='teacher': abort(403)
    return send_from_directory(app.config['UPLOAD_FOLDER'], s.filename, as_attachment=True)

@app.route('/submission/<int:sid>/corrected')
@login_required
def corrected_file(sid):
    s=Submission.query.get_or_404(sid)
    if s.student_id != session['user_id'] and session.get('role')!='teacher': abort(403)
    if not s.corrected_filename: flash('No corrected file is available yet.','warning'); return redirect(url_for('student_dashboard'))
    return send_from_directory(app.config['UPLOAD_FOLDER'], s.corrected_filename, as_attachment=True)

@app.route('/teacher')
@teacher_required
def teacher_dashboard():
    students=User.query.filter_by(role='student').order_by(User.created_at.desc()).all()
    worksheets=Worksheet.query.order_by(Worksheet.created_at.desc()).all()
    submissions=Submission.query.order_by(Submission.submitted_at.desc()).all()
    courses=Course.query.order_by(Course.id).all(); announcements=Announcement.query.order_by(Announcement.created_at.desc()).all()
    ayahs=Ayah.query.order_by(Ayah.id.desc()).all()
    return render_template('teacher_dashboard.html',students=students,worksheets=worksheets,submissions=submissions,courses=courses,announcements=announcements,ayahs=ayahs)

@app.route('/teacher/worksheet', methods=['POST'])
@teacher_required
def upload_worksheet():
    filename=save_upload(request.files.get('file'),'worksheet')
    title=request.form.get('title','').strip(); description=request.form.get('description','').strip()
    if not filename or not title:
        flash('Add a title and a valid PDF/JPG/JPEG/PNG file.','danger'); return redirect(url_for('teacher_dashboard'))
    db.session.add(Worksheet(title=title,description=description,filename=filename)); db.session.commit()
    flash('Worksheet published.','success'); return redirect(url_for('teacher_dashboard'))

@app.route('/teacher/submission/<int:sid>', methods=['POST'])
@teacher_required
def review_submission(sid):
    s=Submission.query.get_or_404(sid); s.status=request.form.get('status','Checked'); s.feedback=request.form.get('feedback','').strip(); s.reviewed_at=datetime.utcnow()
    corrected=save_upload(request.files.get('corrected'),f'corrected_{sid}')
    if corrected: s.corrected_filename=corrected
    db.session.commit(); flash('Submission review saved.','success'); return redirect(url_for('teacher_dashboard'))

@app.route('/teacher/student/<int:uid>/delete', methods=['POST'])
@teacher_required
def delete_student(uid):
    u=User.query.get_or_404(uid)
    if u.role=='teacher': abort(403)
    for s in Submission.query.filter_by(student_id=u.id).all(): db.session.delete(s)
    db.session.delete(u); db.session.commit(); flash('Student removed.','success'); return redirect(url_for('teacher_dashboard'))

@app.route('/teacher/course', methods=['POST'])
@teacher_required
def add_course():
    title=request.form.get('title','').strip(); desc=request.form.get('description','').strip(); level=request.form.get('level','All Levels').strip(); icon=request.form.get('icon','◈').strip()
    if title and desc: db.session.add(Course(title=title,description=desc,level=level,icon=icon)); db.session.commit(); flash('Course added.','success')
    return redirect(url_for('teacher_dashboard'))

@app.route('/teacher/course/<int:cid>/toggle', methods=['POST'])
@teacher_required
def toggle_course(cid):
    c=Course.query.get_or_404(cid); c.active=not c.active; db.session.commit(); return redirect(url_for('teacher_dashboard'))

@app.route('/teacher/announcement', methods=['POST'])
@teacher_required
def add_announcement():
    title=request.form.get('title','').strip(); body=request.form.get('body','').strip()
    if title and body: db.session.add(Announcement(title=title,body=body)); db.session.commit(); flash('Announcement posted.','success')
    return redirect(url_for('teacher_dashboard'))

@app.route('/teacher/ayah', methods=['POST'])
@teacher_required
def add_ayah():
    arabic=request.form.get('arabic','').strip(); english=request.form.get('english','').strip(); urdu=request.form.get('urdu','').strip(); surah=request.form.get('surah','').strip(); reference=request.form.get('reference','').strip()
    if all([arabic,english,urdu,surah,reference]):
        Ayah.query.update({Ayah.active:False}); db.session.add(Ayah(arabic=arabic,english=english,urdu=urdu,surah=surah,reference=reference,active=True)); db.session.commit(); flash('Ayah of the Day updated.','success')
    else: flash('Please complete all Ayah fields.','danger')
    return redirect(url_for('teacher_dashboard'))

@app.errorhandler(413)
def too_large(e):
    flash('File is too large. Maximum size is 10 MB.','danger'); return redirect(request.referrer or url_for('home'))


def seed():
    db.create_all()
    if not User.query.filter_by(email='teacher@halaqa.local').first():
        db.session.add(User(name='Bilal Ahmad Ganie',email='teacher@halaqa.local',password=generate_password_hash('ChangeMe123!'),role='teacher'))
    if Course.query.count()==0:
        data=[
        ('Qur’an with Tajweed','Improve pronunciation, recitation and Tajweed through structured lessons.','Beginner → Advanced','☾'),
        ('Arabic Grammar','Build a strong foundation in Arabic grammar with weekly practice.','Basic → Advanced','ع'),
        ('Tafsir','Explore the meanings and lessons of selected Qur’anic passages.','Intermediate','✦'),
        ('Islamic Counselling','Faith-centered guidance for everyday challenges and personal growth.','All Levels','♡'),
        ('Moral & Character Development','Develop beautiful character through Islamic teachings and practical habits.','All Levels','◇')]
        for x in data: db.session.add(Course(title=x[0],description=x[1],level=x[2],icon=x[3]))
    if Ayah.query.count()==0:
        db.session.add(Ayah(arabic='رَّبِّ زِدْنِي عِلْمًا',english='My Lord, increase me in knowledge.',urdu='اے میرے رب! میرے علم میں اضافہ فرما۔',surah='Surah Taha',reference='20:114',active=True))
    if Announcement.query.count()==0:
        db.session.add(Announcement(title='Welcome to the Halaqa',body='May this learning journey bring benefit, consistency and a deeper connection with the Qur’an.'))
    db.session.commit()

with app.app_context(): seed()

if __name__=='__main__': app.run(debug=True)
