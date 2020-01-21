from flask import Flask, redirect, render_template, request, session, flash
from mysqlconnection import connectToMySQL    # import the function that will return an instance of a connection
import re
from flask_bcrypt import Bcrypt        

app = Flask(__name__)
app.secret_key = 'HeyYo!' 
bcrypt = Bcrypt(app)    

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$') 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add', methods=['POST'])
def adduser():
    # validate
    is_valid = True
    if len(request.form['fn']) < 1:
        is_valid = False
        flash('First Name is required')
    if len(request.form['ln']) < 1:
        is_valid = False
        flash('Last Name is required')
    if len(request.form['em']) < 1:
        is_valid = False
        flash('Email address is required')
    if not EMAIL_REGEX.match(request.form['em']):
        is_valid = False
        flash("Invalid email address!")
    if len(request.form['pw']) < 5:
        is_valid = False
        flash('Password must be at least 5 characters')
    if request.form['pw'] != request.form['pwc']:
        is_valid = False
        flash('Passwords must match.')

    # add to database
    if is_valid:
        db = connectToMySQL('thoughts')
        validate_email_query = 'SELECT id FROM users WHERE email=%(email)s;'
        form_data = {
        'email': request.form['em']
        }
        existing_users = db.query_db(validate_email_query, form_data)
        if existing_users:
            flash("Email already in use")
            is_valid = False

    if is_valid:
        pwhash = bcrypt.generate_password_hash(request.form['pw'])
        mysql = connectToMySQL('thoughts')
        query = 'INSERT INTO users (firstname, lastname, pw, email, modified_at) VALUES (%(fn)s, %(ln)s, %(pw)s, %(em)s, NOW())'
        data = {
            "fn": request.form['fn'],
            "ln": request.form['ln'],
            "pw": pwhash,
            "em": request.form['em']
        }
        new_id = mysql.query_db(query, data)
        flash('Added!')
    return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    # validate
    is_valid = True
    if len(request.form['em']) < 1:
        is_valid = False
        flash('Email address is required')
    if not EMAIL_REGEX.match(request.form['em']):    # test whether a field matches the pattern
        is_valid = False
        flash("Invalid email address!")
    if len(request.form['pw']) < 5:
        is_valid = False
        flash('Password must be at least 5 characters')
    # login and store in session
    if is_valid:
        mysql = connectToMySQL('thoughts')
        query = 'SELECT * FROM users WHERE email = %(em)s'
        data = {"em": request.form['em']}
        result = mysql.query_db(query, data)
        if result:
            if bcrypt.check_password_hash(result[0]['pw'], request.form['pw']):
                session['userid'] = result[0]['id']
                return redirect('/thoughts')
        # flash an error message and redirect back to a safe route
        flash("You could not be logged in")
        return redirect('/')

@app.route('/thoughts')
def dashboard():
    if 'userid' not in session:
        return redirect('/')
    mysql = connectToMySQL('thoughts')
    query = 'SELECT * FROM users WHERE id = %(id)s'
    data = {"id": session['userid']}
    user = mysql.query_db(query, data)
    user = user[0]
    mysql = connectToMySQL('thoughts')
    query = "SELECT thoughts.userid, thoughts.id as thought_id, users.firstname, thoughts.content, thoughts.created_at, COUNT(thoughts.id) as times_liked FROM likes RIGHT JOIN thoughts ON thoughts.id = likes.thoughtid JOIN users ON thoughts.userid = users.id  GROUP BY thoughts.id ORDER BY times_liked DESC"
    thoughts = mysql.query_db(query)
    if thoughts == False:
        thoughts == []
    return render_template('dashboard.html', user = user, thoughts=thoughts)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/thoughts/create', methods=['POST'])
def createthought():
    if 'userid' not in session:
        return redirect('/')
    is_valid = True
    if len(request.form['thought']) > 255:
        flash('Thoughts must be between 5 and 255 characters')
        is_valid = False
    if len(request.form['thought']) < 5:
        flash('Thoughts must be between 5 and 255 characters')
        is_valid = False
    if is_valid:
        mysql = connectToMySQL('thoughts')
        query = 'INSERT INTO thoughts (content, userid) VALUES (%(content)s, %(userid)s)'
        data = {
            "content": request.form['thought'],
            "userid": session['userid']
            }
        newthought = mysql.query_db(query, data)
        if newthought:
            flash('Thought added!')
    return redirect('/thoughts')


@app.route('/thought/<thought_id>/add_like', methods=['POST', 'GET'])
def addlike(thought_id):
    if 'userid' not in session:
        return redirect('/')
    mysql = connectToMySQL('thoughts')
    query = 'Select * from likes where thoughtid = %(thoughtid)s AND userid = %(userid)s'
    data = {
        "thoughtid": thought_id,
        "userid": session['userid']
        }
    oldlike = mysql.query_db(query, data)
    if oldlike:
        flash('You already Liked this')
        return redirect('/thought/{}/detail'.format(thought_id))
    mysql = connectToMySQL('thoughts')
    query = 'INSERT INTO likes (thoughtid, userid) VALUES (%(thoughtid)s, %(userid)s)'
    data = {
        "thoughtid": thought_id,
        "userid": session['userid']
        }
    newlike = mysql.query_db(query, data)
    if newlike:
        flash('liked')
    return redirect('/thought/{}/detail'.format(thought_id))

@app.route('/thought/<thought_id>/unlike', methods=['GET'])
def unlike(thought_id):
    if 'userid' not in session:
        return redirect('/')
    mysql = connectToMySQL('thoughts')
    query = 'Select * from likes where thoughtid = %(thoughtid)s AND userid = %(userid)s'
    data = {
        "thoughtid": thought_id,
        "userid": session['userid']
        }
    oldlike = mysql.query_db(query, data)
    if oldlike:
        mysql = connectToMySQL('thoughts')
        query = 'DELETE FROM likes WHERE thoughtid=%(thoughtid)s AND userid=%(userid)s'
        data = {
            "thoughtid": thought_id,
            "userid": session['userid']
            }
        unlike = mysql.query_db(query, data)
        flash('Unliked')
    else:
        flash('You do not already like this thought.')
    return redirect('/thought/{}/detail'.format(thought_id))


@app.route('/thought/<thought_id>/detail', methods=['GET'])
def detail(thought_id):
    if 'userid' not in session:
        return redirect('/')
    mysql = connectToMySQL('thoughts')
    query = '''SELECT 
                thoughts.id, 
                users.firstname, 
                users.lastname, 
                users.id as 'uid',
                thoughts.content, 
                thoughts.created_at, 
                thoughts.userid 
            FROM users join thoughts on thoughts.userid = users.id   
            WHERE thoughts.id = %(thoughtid)s'''
    data = {"thoughtid": thought_id}
    thought = mysql.query_db(query, data)
    thought = thought[0]

    mysql = connectToMySQL('thoughts')
    query = '''SELECT 
                    users.firstname, 
                    users.lastname
                FROM likes join users on users.id = likes.userid   
                WHERE likes.thoughtid =%(thoughtid)s and users.id !=%(userid)s
                
                UNION

                SELECT 
                    users.firstname, 
                    users.lastname
            FROM likes join users on users.id = likes.userid   
            WHERE likes.thoughtid =%(thoughtid)s and users.id =%(userid)s
 '''
    data = {"thoughtid": thought_id, "userid": session['userid']}
    likes = mysql.query_db(query, data)

    mysql = connectToMySQL('thoughts')
    query = "SELECT * FROM likes WHERE userid = %(user_id)s"
    data = {
        'user_id': session['userid']
    }
    liked_thoughts = []
    lk = mysql.query_db(query, data)
    for l in lk:
        liked_thoughts.append(l['thoughtid'])

    if thought['id'] in liked_thoughts:
        thought['already_liked'] = True
    else:
        thought['already_liked'] = False
    print(thought)

    return render_template ('/detail.html', thought=thought, likes=likes)


@app.route('/thought/<thought_id>/delete', methods=['GET'])
def thoughtdelete(thought_id):
    if 'userid' not in session:
        return redirect('/')
    mysql = connectToMySQL('thoughts')
    query = 'DELETE FROM thoughts where id = %(thoughtid)s'
    data = {
        "thoughtid": thought_id
        }
    deletethought = mysql.query_db(query, data)
    flash('deleted')
    return redirect('/thoughts')

@app.route('/', defaults={'path': ''})

@app.route('/<path:path>')
def catch_all(path):
    return 'Sorry! No response. Try again.'

if __name__=="__main__":    
    app.run(debug=True)     