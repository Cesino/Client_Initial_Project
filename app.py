from flask import flash, Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import calendar
from datetime import datetime, timedelta
import bcrypt
import googlemaps
import os
from dotenv import find_dotenv, load_dotenv
import json
import ClothingLLM
from ollama import chat
import re
import WardrobeTrip as wt

app = Flask(__name__)
app.secret_key = "IDK"
load_dotenv(find_dotenv())
gmaps = googlemaps.Client(key=os.getenv("GOOGLE_API_KEY"))
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'CS-IA'

mysql = MySQL(app)

def dates_trips_dict(dates_trips):
    trip_dict = {}
    for location, sdate, edate in dates_trips:
        for day in range(sdate, edate + 1):
            trip_dict[day] = location
    return trip_dict

def reroute(request):
    if 'home' in request:
        return redirect(url_for('home'))
    elif 'calendar' in request:
        return redirect(url_for('cal'))
    elif 'clothing' in request:
        return redirect(url_for('clothing'))
    elif 'generator' in request:
        return redirect(url_for('generator'))
    elif 'settings' in request:
        return redirect(url_for('settings'))
    return redirect(url_for('home'))

def tripPossible(start_date, end_date, now_date):
    if (now_date + timedelta(days=16)).date() <= end_date or now_date.date() >= start_date:
        return False
    else:
        return True
def LLMReturn(prompt):
    items = prompt.split(';')
    print(items)
    if not items:
        return
    clothing_dict = {
        'underwear': ClothingLLM.Underwear_LLM,
        'shirt': ClothingLLM.Shirt_LLM,
        'bottoms': ClothingLLM.Bottoms_LLM,
        'jacket': ClothingLLM.Jacket_LLM,
        'suit': ClothingLLM.Suit_LLM,
        'sweater/cardigan': ClothingLLM.SweaterCardigan_LLM,
        'shoes': ClothingLLM.Shoes_LLM,
        'socks': ClothingLLM.Socks_LLM,
    }
    user_id = session['ID']
    cur = mysql.connection.cursor()
    cur.execute("SELECT user_items FROM users WHERE id = %s", (user_id,))
    result = cur.fetchone()
    if result[0]:
        user_items_json = json.loads(result[0])
    else:
        user_items_json = {}
    for item in items:
        response = chat(model='llama3.2:latest', messages=[
            {
            'role':'user',
            'content':f"Categorize the following clothing item and allocate it a name including the brand: {item}",
        }
        ],format=ClothingLLM.ClothingCategory.model_json_schema() ,options={'temperature': 0.1})
        match = re.search(r'"category": \s*"([^"]+)"', response['message']['content'])
        category = match.group(1)
        match = re.search(r'"name": \s*"([^"]+)"', response['message']['content'])
        name = match.group(1)
        response2 = chat(model='gemma:2b', messages=[
            {
                'role': 'user',
                'content': f"Classify the following clothing item based on the attributes: {item}",
            }
        ], format=clothing_dict[category].model_json_schema(), options={'temperature': 0.1})
        print(response2)
        try:
            subcategories_json = json.loads(response2['message']['content'])
        except json.JSONDecodeError:
            continue
        temp = name
        i = 1
        while True:
            if temp not in user_items_json:
                user_items_json[temp] = {
                    'category': category,
                    **subcategories_json
                }
                break
            else:
                i+=1
                temp = f"{temp} {i}"
        updated_json = json.dumps(user_items_json)
        cur.execute("UPDATE users SET user_items = %s WHERE id = %s", (updated_json, user_id))
        mysql.connection.commit()
    cur.close()

def ManualReturn(input):
    name = input['name']
    user_id = session['ID']
    cur = mysql.connection.cursor()
    cur.execute("SELECT user_items FROM users WHERE id = %s", (user_id,))
    result = cur.fetchone()
    if result[0]:
        user_items_json = json.loads(result[0])
    else:
        user_items_json = {}
    i = 1
    temp = name
    while True:
        if temp not in user_items_json:
            user_items_json[temp] = {
                **input
            }
            break
        else:
            i += 1
            temp = f"{temp} {i}"
    print(user_items_json)
    user_items_json[temp].pop("submit")
    updated_json = json.dumps(user_items_json)
    cur.execute("UPDATE users SET user_items = %s WHERE id = %s", (updated_json, user_id))
    mysql.connection.commit()
    cur.close()
    return

@app.route('/')
def default():
    return redirect(url_for('login'))

@app.route('/change_password', methods=['POST'])
def change_password():
    pwd = request.form.get("new_password")
    rpwd = request.form.get("repeat_password")
    print(pwd, rpwd)
    if pwd == rpwd:
        user_id = session.get('ID')
        cur = mysql.connection.cursor()
        bytes = pwd.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_pwd = bcrypt.hashpw(bytes, salt)
        cur.execute("UPDATE users SET password = %s WHERE ID = %s", (hashed_pwd, user_id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('login'))
    else:
        return render_template('settings.html', error='Passwords do not match')


@app.route('/home')
def home():
    if 'ID' in session:
        user_id = session['ID']
        cur = mysql.connection.cursor()
        cur.execute(f"SELECT fname, lname FROM users WHERE ID='{user_id}'")
        fetchdata = cur.fetchall()
        cur.close()
        return render_template('home.html', data = fetchdata)
    else:
        return redirect(url_for('login'))

@app.route('/remove_item', methods=['POST', 'GET'])
def remove_item():
    print(request.form['item_name'])
    user_id = session['ID']
    item_name = request.form['item_name']
    cur = mysql.connection.cursor()
    cur.execute("SELECT user_items FROM users WHERE ID = %s", (user_id,))
    result = cur.fetchone()
    formatted_clothes = json.loads(result[0])
    for key in list(formatted_clothes.keys()):
        if formatted_clothes[key].get('name') == item_name:
            del formatted_clothes[key]
            break
    updated_items = json.dumps(formatted_clothes)
    cur = mysql.connection.cursor()
    cur.execute("UPDATE users SET user_items = %s WHERE id = %s", (updated_items, user_id))
    mysql.connection.commit()
    cur = mysql.connection.cursor()
    cur.execute("SELECT user_items FROM users WHERE id = %s", (user_id,))
    result = cur.fetchone()
    cur.execute("SELECT wardrobe_id, wardrobe_items FROM wardrobes WHERE user_id = %s", (user_id,))
    wardrobes = cur.fetchall()
    for wardrobe in wardrobes:
        wardrobe_id = wardrobe[0]  # Wardrobe ID
        wardrobe_items_json = wardrobe[1]  # JSON  string of items in this wardrobe
        wardrobe_items = json.loads(wardrobe_items_json)
        if item_name in wardrobe_items:
            wardrobe_items.pop(item_name)  # Remove the item
            updated_wardrobe_items_json = json.dumps(wardrobe_items)
            cur.execute("UPDATE wardrobes SET wardrobe_items = %s WHERE wardrobe_id = %s",
                        (updated_wardrobe_items_json, wardrobe_id))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('clothing'))

@app.route('/clothing', methods=['POST', 'GET'])
def clothing():
    if 'ID' in session:
        user_id=session['ID']
        cur = mysql.connection.cursor()
        cur.execute("SELECT user_items FROM users WHERE id = %s", (user_id,))
        result = cur.fetchone()
        cur.execute("SELECT trip_id FROM wardrobes WHERE user_id = %s", (user_id,))
        wardrobe_trips = cur.fetchall()
        trip_ids = [trip[0] for trip in wardrobe_trips]
        if trip_ids:
            # Fetch trips that match the trip_ids in wardrobe_trips
            cur.execute("SELECT * FROM trips WHERE user_id = %s AND trip_id IN %s", (user_id, tuple(trip_ids)))
            trips = cur.fetchall()
        else:
            trips = []
        cur.close()
        if result[0] is None:
            formatted_clothes = dict()
        else:
            formatted_clothes = json.loads(result[0])
        if request.method == 'POST':
            print("POSTED")
            print(request.form)
            if request.form.get("ai-name", ""):
                text = request.form.get("ai-name", "").strip()
                LLMReturn(text)
                cur = mysql.connection.cursor()
                cur.execute("SELECT user_items FROM users WHERE id = %s", (user_id,))
                result = cur.fetchone()
                formatted_clothes = json.loads(result[0])
                return render_template('clothing.html', clothes=formatted_clothes)
            else:
                if "close" in request.form:
                    return render_template('clothing.html', clothes=formatted_clothes)
                elif "submit" in request.form:
                    ManualReturn(request.form)
                    cur = mysql.connection.cursor()
                    cur.execute("SELECT user_items FROM users WHERE id = %s", (user_id,))
                    result = cur.fetchone()
                    cur.close()
        return render_template('clothing.html', clothes=formatted_clothes, trips=trips)
    else:
        return redirect(url_for('login'))

@app.route('/create_wardrobe', methods=['POST', 'GET'])
def create_wardrobe():
    user_id = session['ID']
    trip_id = request.form.get("trip_id")
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        cur.execute(f" SELECT user_items FROM users WHERE ID = %s", (user_id,))
        clothes = json.loads(cur.fetchone()[0])
        cur.execute(f" SELECT * FROM trips WHERE trip_id = %s", (trip_id,))
        trip = cur.fetchone()
        new_wardrobe_trip = wt.WardrobeTrip(trip[0], trip[2], trip[3], trip[4], trip[5], trip[6], trip[7], wt.categorization_clothings(clothes))
        new_wardrobe = wt.createWardrobe(new_wardrobe_trip)
        new_dict = dict()
        for cloth in new_wardrobe:
            new_dict[cloth] = clothes[cloth]
        new_json = json.dumps(new_dict)
        cur.execute(f"INSERT INTO wardrobes (user_id, trip_id, wardrobe_items) VALUES (%s, %s, %s)", (user_id, trip_id, new_json))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('generator'))


@app.route('/calendar', methods=['POST','GET'])
def cal():
    if 'current_date' in session:
        current_date = session['current_date']
    else:
        current_date = datetime.now()
        session['current_date'] = current_date

    if 'ID' in session:
        cur = mysql.connection.cursor()
        cur.execute(f" SELECT * FROM trips WHERE user_id = %s", (session['ID'],))
        trips = cur.fetchall()
        cur.close()
        month = current_date.month
        year = current_date.year
        cal = calendar.Calendar(firstweekday=6)
        month_days = cal.monthdayscalendar(year, month)
        month_name = current_date.strftime('%B')
        if request.method == 'POST':
            direction = request.form.get('direction')
            if direction == 'next':
                if month == 12:
                    current_date = current_date.replace(year=current_date.year+1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month+1)
            elif direction == 'prev':
                if month == 1:
                    current_date = current_date.replace(year=current_date.year - 1, month=12)
                else:
                    current_date = current_date.replace(month=current_date.month-1)
            session['current_date'] = current_date
            month = current_date.month
            year = current_date.year
            month_name = current_date.strftime('%B')
            month_days = cal.monthdayscalendar(year, month)
        removing_trips = [(trip[0],trip[2], trip[3], trip[4]) for trip in trips]
        filtered_trips = [trip for trip in trips if (trip[3].month == current_date.month and trip[3].year == current_date.year) or (trip[4].month == current_date.month and trip[4].year == current_date.year)]
        dates_trips = [(var[2], 1 if var[3].month < current_date.month else var[3].day, 31 if var[4].month > current_date.month else var[4].day) for var in filtered_trips]
        return render_template('calendar.html', month_days=month_days, month_name=month_name, year=year, trips=dates_trips_dict(dates_trips), trip_removing = removing_trips)
    else:
        return redirect(url_for('login'))

@app.route('/new_trip', methods=['POST', 'GET'])
def new_trip():
    dest = request.form.get('destination')
    dest_inf = gmaps.geocode(dest)
    sdate = request.form.get('start_date')
    edate = request.form.get('end_date')
    if not dest_inf or sdate > edate:
        if not dest_inf:
            flash("Invalid destination. Please enter a valid location.", "error")
        if sdate > edate:
            flash("Start date later than End date. Please enter valid dates.", "error")
        return redirect(url_for('cal'))
    sport = request.form.get('sport_occasion')
    formal = request.form.get('formal_occasion')
    casual = request.form.get('casual_occasion')
    location = dest_inf[0]['geometry']['location']
    corrected_destination = dest_inf[0]['formatted_address']
    lat, lng = location['lat'], location['lng']
    uid = session['ID']
    cur = mysql.connection.cursor()
    cur.execute("SELECT start_date, end_date FROM trips WHERE user_id = %s", (uid,))
    existing_trips = cur.fetchall()
    print(sdate, edate)
    for trip in existing_trips:
        ex_start = trip[0].strftime('%Y-%m-%d')
        ex_end = trip[1].strftime('%Y-%m-%d')
        if (sdate <= ex_end and edate >= ex_start):
            flash("The trip dates overlap with an existing trip. Please choose different dates.", "error")
            return redirect(url_for('cal'))
    if (not (sport.isdigit() and formal.isdigit() and casual.isdigit())):
        flash("The occasion dates format are not correct.", "error")
        return redirect(url_for('cal'))
    occasion_string = f"{casual}%{formal}%{sport}"
    cur.execute(f"INSERT INTO trips (user_id, destination, start_date, end_date, trip_type, latitude, longitude) VALUES (%s, %s, %s, %s, %s, %s, %s)",(uid ,corrected_destination, sdate, edate, occasion_string, lat, lng))
    mysql.connection.commit()
    cur.close()
    flash("Trip added successfully!", "success")
    return redirect(url_for('cal'))

@app.route('/generator')
def generator():
    if 'ID' in session:
        uid = session['ID']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM trips WHERE user_id = %s", (uid,))
        existing_trips = cur.fetchall()
        cur.execute("SELECT * FROM wardrobes WHERE user_id = %s", (uid,))
        wardrobes = cur.fetchall()
        cur.execute("SELECT user_items FROM users WHERE ID = %s", (uid,))
        user_items = cur.fetchone()
        valid_trips = []
        for trip in existing_trips:
            if tripPossible(trip[3], trip[4], datetime.now()):
                valid_trips.append(trip)
        print(wardrobes)
        print(user_items)
        print(existing_trips)
        return render_template('generator.html', trips=valid_trips, wardrobes=wardrobes, user_items=user_items, existing_trips=existing_trips)
    else:
        return redirect(url_for('login'))

@app.route('/settings')
def settings():
    if 'ID' in session:
        return render_template('settings.html')
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['loginEmail']
        pwd = request.form['loginPwd']
        cur = mysql.connection.cursor()
        cur.execute(f"select ID, email, password from users where email = %s",(email,))
        user = cur.fetchone()
        cur.close()
        if user and bcrypt.checkpw(pwd.encode('utf-8'), user[2].encode('utf-8')):
            session['ID'] = user[0]
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']
        pwd = request.form['password']
        rpwd = request.form['rpassword']
        if pwd == rpwd:
            cur = mysql.connection.cursor()
            bytes = pwd.encode('utf-8')
            salt = bcrypt.gensalt()
            hashed_pwd = bcrypt.hashpw(bytes, salt)
            cur.execute(f"INSERT INTO users (fname, lname, email, password) VALUES (%s, %s, %s, %s)", (fname, lname, email, hashed_pwd))
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('login'))
        else:
            return render_template('register.html', error='Passwords do not match')
    return render_template('register.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('ID', None)
    return redirect(url_for('login'))

@app.route('/calendar_done', methods=['POST'])
def calendar_done():
    if 'calendar' not in request.form:
        session.pop('current_date', None)
        return reroute(request.form)
    else:
        return redirect(url_for('cal'))

@app.route('/remove_item_wardrobe', methods=['POST'])
def remove_item_wardrobe():
    item_remove = request.form.get("item_name").split(',')[0]
    trip_id = request.form.get("item_name").split(',')[1]
    cur = mysql.connection.cursor()
    print(trip_id)
    cur.execute(f"SELECT wardrobe_items FROM wardrobes WHERE trip_id=%s", (trip_id,))
    result = cur.fetchone()
    print(result)
    wardrobe_items_json = result[0]
    wardrobe_items = json.loads(wardrobe_items_json)
    if item_remove in wardrobe_items:
        wardrobe_items.pop(item_remove)
        updated_items_json = json.dumps(wardrobe_items)

        cur.execute("UPDATE wardrobes SET wardrobe_items=%s WHERE trip_id=%s", (updated_items_json, trip_id))
        mysql.connection.commit()

        flash(f"Item '{item_remove}' has been removed from your wardrobe.", "success")
    else:
        flash(f"Item '{item_remove}' not found in the wardrobe.", "error")
    cur.close()
    return redirect(url_for('generator'))

@app.route('/add-to-trip-wardrobe', methods=['POST'])
def add_to_trip_wardrobe():
    user_id = session['ID']
    item_add = request.form.get('item_id')
    trip_add = request.form.get('trip')
    cur = mysql.connection.cursor()
    cur.execute(f"SELECT wardrobe_items FROM wardrobes WHERE user_id =%s AND trip_id=%s", (user_id, trip_add))
    wardrobe_items_json = cur.fetchone()[0]
    wardrobe_items = json.loads(wardrobe_items_json)
    cur.execute(f"SELECT user_items FROM users WHERE ID =%s", (user_id,))
    user_items_json = cur.fetchone()[0]
    user_items = json.loads(user_items_json)
    cur.close()
    if item_add in wardrobe_items:
        flash('This item is already in the wardrobe for this trip.', 'warning')
        return redirect(url_for('clothing'))
    wardrobe_items[item_add] = user_items[item_add]
    wardrobe_items_json = json.dumps(wardrobe_items)
    cur = mysql.connection.cursor()
    cur.execute("UPDATE wardrobes SET wardrobe_items = %s WHERE user_id = %s AND trip_id = %s",
                (wardrobe_items_json, user_id, trip_add))
    mysql.connection.commit()  # Commit the changes to the database
    cur.close()
    flash('Item successfully added to the wardrobe for the trip.', 'success')  # Flash a success message
    return redirect(url_for('clothing'))


@app.route('/remove_trip', methods=['POST'])
def remove_trip():
    cur = mysql.connection.cursor()
    rtrip = request.form['trip_id']
    ruser = session['ID']
    cur.execute(f"DELETE FROM trips WHERE user_id =%s AND trip_id=%s", (ruser, rtrip))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('cal'))
@app.route('/rerouting', methods=['POST'])
def rerouting():
    return reroute(request.form)

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
