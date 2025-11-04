from flask import Flask, render_template, url_for, redirect, session, g, Response, send_file, request, jsonify
from forms import *
from database import *
from werkzeug.security import generate_password_hash, check_password_hash
from flask_session import Session
from functools import wraps


app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_javascript_secret'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.teardown_appcontext(close_db)
Session(app)
init_db()

@app.before_request
def load_logged_in_user():
    g.user = session.get('user_id', None)


#Custom Decorator
def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.url))
        return view(*args,**kwargs)
    return wrapped_view


@app.route('/', methods=['GET', 'POST'])
def index_redirect():
    return redirect(url_for('index'))

@app.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html', title='Home')

@app.route('/login', methods=['GET', 'POST'])
def login():

    password_error=''
    username_error = ''
    form = LoginForm()

    if form.validate_on_submit():

        db = get_db()
        username = form.username.data
        entered_password = form.password.data

        user_details = db.execute('''SELECT *
                                     FROM users 
                                     WHERE username = ?''', (username,)).fetchone()
        
        if user_details:
            if check_password_hash(user_details[2], entered_password):

                password_error=''
                session['username'] = user_details['username']
                session['user_id'] = user_details['user_id']

                return redirect(url_for('game'))
            
            elif not check_password_hash(user_details[2], entered_password):
                password_error = 'Password is incorrect. '

        else:
            username_error = 'User does not exist. '

    return render_template('login.html',
                            form=form,
                            password_error = password_error,
                            title='Login',
                            username_error=username_error)

@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():

    success_message = ''
    username_error = ''

    form = SignUpForm()

    if form.validate_on_submit():

        username = form.username.data
        password = form.password.data

        db = get_db()
        existing_user = db.execute('''SELECT *
                                      FROM users
                                      WHERE username = ?''', (username,)).fetchone()

        if existing_user:
            if existing_user[1] == username:
                username_error = 'Username is taken, please try choose another one.'

        if not existing_user:
            hashed_password = generate_password_hash(password)
            db.execute('''INSERT INTO users(username, password)
             VALUES (?, ?)''', (username, hashed_password))
            db.commit()

            success_message = 'You have successfully signed up!'
            username_error = ''
        
    return render_template('sign_up.html',
                           form=form,
                           title='Sign Up',
                           success_message = success_message,
                           username_error=username_error)


@app.route('/game', methods=['GET', 'POST'])
@login_required
def game():
    return render_template('game.html')

@app.route('/leaderboard', methods=['GET', 'POST'])
@login_required
def leaderboard():

    db = get_db()

    leaderboard_scores = db.execute('''
        SELECT users.username, leaderboard_scores.score
        FROM leaderboard_scores
        JOIN users ON leaderboard_scores.user_id = users.user_id
        ORDER BY leaderboard_scores.score DESC''').fetchall()

    leaderboard_times = db.execute('''
        SELECT users.username, leaderboard_times.time
        FROM leaderboard_times
        JOIN users ON leaderboard_times.user_id = users.user_id
        ORDER BY leaderboard_times.time DESC''').fetchall()
    

    return render_template('leaderboard.html', title='Leaderboard', leaderboard_scores=leaderboard_scores, leaderboard_times=leaderboard_times)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    session.clear()  # Clears all session data
    return redirect(url_for('login'))

@app.route('/attributions', methods=['GET', 'POST'])
def attributions():
    return render_template('attributions.html')

# Code from lines 153-223 was written with help from the internet, links mentioned in attributions
@app.route('/api/submit_score', methods=['POST'])
@login_required
def submit_score():
    # Get the data from the AJAX request
    data = request.get_json()
    
    if not data or 'score' not in data:
        return jsonify({'success': False, 'error': 'Invalid data format'}), 400
    
    score = data['score']
    user_id = g.user  
    
    db = get_db()
    db.execute(
        'INSERT INTO leaderboard_scores (user_id, score) VALUES (?, ?)',
        (user_id, score)
    )
    db.commit()
    
    return jsonify({'success': True})

@app.route('/api/submit_time', methods=['POST'])
@login_required
def submit_time():
    # Get the data from the AJAX request
    data = request.get_json()
    
    if not data or 'time' not in data:
        return jsonify({'success': False, 'error': 'Invalid data format'}), 400
    
    time = data['time']
    user_id = g.user  
    
    # Store in database
    db = get_db()
    db.execute(
        'INSERT INTO leaderboard_times (user_id, time) VALUES (?, ?)',
        (user_id, time)
    )
    db.commit()
    
    return jsonify({'success': True})

@app.route('/api/get_leaderboard', methods=['GET'])
def get_leaderboard():
    db = get_db()
    
    scores = db.execute('''
        SELECT users.username, leaderboard_scores.score
        FROM leaderboard_scores
        JOIN users ON leaderboard_scores.user_id = users.user_id
        ORDER BY leaderboard_scores.score DESC
        
    ''').fetchall()
    
    times = db.execute('''
        SELECT users.username, leaderboard_times.time
        FROM leaderboard_times
        JOIN users ON leaderboard_times.user_id = users.user_id
        ORDER BY leaderboard_times.time DESC''').fetchall()
    
    # Convert SQL rows to dictionaries for JSON
    scores_list = [{'username': row['username'], 'score': row['score']} for row in scores]
    times_list = [{'username': row['username'], 'time': row['time']} for row in times]
    
    return jsonify({
        'scores': scores_list,
        'times': times_list
    })

