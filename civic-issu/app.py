from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
from werkzeug.utils import secure_filename
import os
import config

app = Flask(__name__)
app.secret_key = "secret123"
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Home
@app.route('/')
def index():
    return render_template('index.html')

# User Registration
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = config.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name,email,password) VALUES (%s,%s,%s)", 
                       (name,email,password))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Registration successful! Please login.", "success")
        return redirect('/login')
    return render_template('register.html')

# User Login
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = config.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email,password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['name'] = user['name']
            return redirect('/dashboard')
        else:
            flash("Invalid credentials", "danger")
    return render_template('login.html')

# User Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    conn = config.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM reports WHERE user_id=%s", (session['user_id'],))
    reports = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('dashboard.html', reports=reports)




# Report Issue
# @app.route('/report', methods=['GET','POST'])
# def report():
#     if 'user_id' not in session:
#         return redirect('/login')
#     if request.method == 'POST':
#         title = request.form['title']
#         description = request.form['description']
#         category = request.form['category']
#         location = request.form['location']
#         file = request.files['image']

#         filename = None
#         if file:
#             filename = secure_filename(file.filename)
#             file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

#         conn = config.get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("INSERT INTO reports (user_id,title,description,category,image,location) VALUES (%s,%s,%s,%s,%s,%s)",
#                        (session['user_id'],title,description,category,filename,location))
#         conn.commit()
#         cursor.close()
#         conn.close()
#         flash("Report submitted successfully!", "success")
#         return redirect('/dashboard')
#     return render_template('report_issue.html')






# Report Issue
@app.route('/report', methods=['GET','POST'])
def report():
    if 'user_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        location = request.form['location']
        latitude = request.form['latitude']
        longitude = request.form['longitude']
        file = request.files['image']

        filename = None
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        conn = config.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reports (user_id,title,description,category,image,location,latitude,longitude) 
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (session['user_id'],title,description,category,filename,location,latitude,longitude))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Report submitted successfully!", "success")
        return redirect('/dashboard')
    return render_template('report_issue.html')

# Admin Login
@app.route('/admin', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = config.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin WHERE username=%s AND password=%s", (username,password))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()

        if admin:
            session['admin'] = True
            return redirect('/admin/dashboard')
        else:
            flash("Invalid admin credentials", "danger")
    return render_template('admin_login.html')

# Admin Dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect('/admin')
    conn = config.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT reports.*, users.name FROM reports JOIN users ON reports.user_id=users.id")
    reports = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin_dashboard.html', reports=reports)

# Update Status
@app.route('/admin/update/<int:report_id>/<status>')
def update_status(report_id, status):
    if 'admin' not in session:
        return redirect('/admin')
    conn = config.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE reports SET status=%s WHERE id=%s", (status,report_id))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/admin/dashboard')
# next
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))   # for users

@app.route('/admin_logout')
def admin_logout():
    session.clear()
    return redirect(url_for('index'))   # for admin



# @app.route('/map')
# def map_view():
#     conn = config.get_db_connection()
#     cursor = conn.cursor(dictionary=True)
#     cursor.execute("SELECT id, title, description, status, latitude, longitude FROM reports WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
#     reports = cursor.fetchall()
#     cursor.close()
#     conn.close()

#     # Convert lat/lng to float (important for JS)
#     for r in reports:
#         r['latitude'] = float(r['latitude'])
#         r['longitude'] = float(r['longitude'])

#     return render_template('map.html', reports=reports)

@app.route('/map')
def map_view():
    conn = config.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, title, description, status, latitude, longitude 
        FROM reports
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    """)
    reports = cursor.fetchall()
    cursor.close()
    conn.close()

    cleaned_reports = []
    for r in reports:
        try:
            lat = float(r['latitude']) if r['latitude'] not in (None, '') else None
            lng = float(r['longitude']) if r['longitude'] not in (None, '') else None
            if lat is not None and lng is not None:
                r['latitude'] = lat
                r['longitude'] = lng
                cleaned_reports.append(r)
        except ValueError:
            # skip invalid entries
            continue

    return render_template('map.html', reports=cleaned_reports)
if __name__ == '__main__':
    # app.run(debug=True)
    app.run(debug=True, port=8000)
    