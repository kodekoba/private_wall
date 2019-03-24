from flask import Flask, render_template, request, redirect, session, flash
import re
NAME_REGEX = re.compile(r'^[a-zA-Z]+$')
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
# SECUREPW_REGEX = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')    # min 8 char, 1 upper, 1 lower, 1 num, 1 special char
# SECUREPW_REGEX = re.compile('^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$')     # minimum 8 char, 1 letter, 1 number
from flask_bcrypt import Bcrypt        
from mysqlconn import connectToMySQL
app = Flask(__name__)
app.secret_key = "YEEEEEEEEEEEEEEE"
bcrypt = Bcrypt(app)

@app.route("/")   
def index():
    # if not "userid" in session.keys():
    #     session["userid"] = False
    if not "loggedout" in session.keys():
        session["loggedout"] = False
    if session["loggedout"] == True:
        flash("You have been successfully logged out.", "logout")
    session["loggedout"] = False
    # session.pop("userid") # stops the issue that arises from an old session being still active, makes you effectively log out if you see this page
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    is_valid = True
    if len(request.form["fname"]) == 0:
        is_valid = False
        flash("This is a required field", "fname")
    elif len(request.form["fname"]) < 2:
        is_valid = False
        flash("First name must be at least 2 characters", "fname")
    elif not NAME_REGEX.match(request.form["fname"]):
        is_valid = False
        flash("First name must contain only letters", "fname")
    if len(request.form["lname"]) == 0:
        is_valid = False
        flash("This is a required field", "lname")
    elif len(request.form["lname"]) < 2:
        is_valid = False
        flash("Last name must be at least 2 characters", "lname")
    elif not NAME_REGEX.match(request.form["lname"]):
        is_valid = False
        flash("Last name must contain only letters", "lname")
    if len(request.form["email"]) == 0:
        is_valid = False
        flash("This is a required field", "email")
    elif not EMAIL_REGEX.match(request.form["email"]):
        is_valid = False
        flash("Invalid email address!!", "email")
    if len(request.form["pass"]) == 0:
        is_valid = False
        flash("This is a required field", "pass")
    elif len(request.form["pass"]) < 8:
        is_valid = False
        flash("Password must be at least 8 characters!!", "pass")
    if request.form["pass2"] != request.form["pass"]:
        is_valid = False
        flash("Passwords must match!!", "pass2")
    if is_valid:
        print("Got Post Info")
        print(request.form)
        session["first"] = request.form["fname"]      # store first name in session if we need to call on it
        session["justregistered"] = True              # store a check that someone had just registered if we want to send a special msg
        pw_hashed = bcrypt.generate_password_hash(request.form['pass']) 
        print(pw_hashed)
        mysql = connectToMySQL("privatewall")
        query = "INSERT INTO users (first_name, last_name, email, pw_hashed) VALUES (%(fn)s, %(ln)s, %(em)s, %(pw)s);"
        # put the pw_hash in our data dictionary, NOT the password the user provided
        data = { 
            "fn" : request.form["fname"],
            "ln" : request.form["lname"],
            "em" : request.form["email"],
            "pw" : pw_hashed 
        }
        session["userid"] = mysql.query_db(query, data)
        # mysql.query_db(query, data)
        return redirect("/wall")
    else:
        return redirect("/")

@app.route("/login", methods=["POST"])
def login():
    if len(request.form["loginemail"]) == 0:
        flash("This is a required field", "logemail")
    if len(request.form["loginpass"]) == 0:
        flash("This is a required field", "logpass")
    mysql = connectToMySQL("privatewall")
    query = "SELECT * FROM users WHERE email = %(em)s;"
    data = { "em" : request.form["loginemail"] }
    result = mysql.query_db(query, data)
    if len(result) > 0:
        if bcrypt.check_password_hash(result[0]['pw_hashed'], request.form['loginpass']):
            session["userid"] = result[0]["user_id"]
            session["first"] = result[0]["first_name"]
            print(session["first"])
            return redirect('/wall')
    flash("You could not be logged in", "loginfail")
    return redirect("/")

@app.route("/wall")
def walldolf():
    if not "userid" in session.keys():  
        session["userid"] = False
        return redirect("/")
    if not "first" in session.keys():
        session["first"] = False
    mysql = connectToMySQL("privatewall")   # dbquery for showing list of users you can send messages to
    query = "SELECT * FROM users WHERE user_id != %(id)s ORDER BY first_name;"
    data = { "id": session["userid"] }
    userlist = mysql.query_db(query,data)
    
    mysql2 = connectToMySQL("privatewall")  # dbquery for showing messages sent to that user
    # query2 = "SELECT * FROM messages JOIN users ON users.user_id = messages.user_sender_id WHERE user_recipient_id = %(id)s;"
    query2 = "SELECT *, TIMESTAMPDIFF(HOUR, messages.created_at, NOW()) as timesince FROM messages JOIN users ON users.user_id = messages.user_sender_id WHERE user_recipient_id = %(id)s;"
    data2 = { "id": session["userid"] }
    readposts = mysql2.query_db(query2,data2)

    mysql3 = connectToMySQL("privatewall")   # dbquery for showing how many msgs you received
    query3 = "SELECT user_recipient_id, IFNULL(count(*), 0) AS count FROM messages LEFT JOIN users ON users.user_id = messages.user_sender_id WHERE user_recipient_id = %(id)s;"
    data3 = { "id": session["userid"] }
    number_of_msgs = mysql3.query_db(query3,data3)

    mysql4 = connectToMySQL("privatewall")   # dbquery for showing how many msgs you sent
    query4 = "SELECT user_sender_id, IFNULL(count(*), 0) AS count FROM messages LEFT JOIN users ON users.user_id = messages.user_sender_id WHERE user_sender_id = %(id)s;"
    data4 = { "id": session["userid"] }
    num_msgs = mysql4.query_db(query4,data4)

    return render_template("wall.html", fn = session["first"], user_list = userlist, posts = readposts, msgs4u = number_of_msgs, msgs_from_u = num_msgs)

@app.route("/wallpost", methods=["POST"])
def postmsg():
    mysql = connectToMySQL("privatewall")
    query = "INSERT INTO messages (msg, user_sender_id, user_recipient_id) VALUES (%(ms)s, %(us)s, %(ur)s);"
    data = { 
        "ms" : request.form["form_message"],
        "us" : session["userid"],
        "ur" : request.form["recip_id"]
    }
    mysql.query_db(query, data)
    return redirect("/wall")

@app.route("/delete/<id>")  # WANT TO CREATE A HASH FOR THE MOST SECURITY
def delete_user(id):
    mysql = connectToMySQL("privatewall")
    query = "DELETE FROM messages WHERE message_id = %(id)s"
    # ^ "...WHERE ... AND user_recipient_id = %(us)s"
    data = { "id": id }
    # ^ "us" : session["userid"]
    mysql.query_db(query,data)
    return redirect("/wall")

@app.route("/logout")
def delcookies():
    session.clear()
    session["loggedout"] = True
    # session.clear()		    # clears all keys
    # session.pop('key_name')	# clears a specific key
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)