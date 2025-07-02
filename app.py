# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_cors import CORS
import os
import pytz

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///church.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)



# モデル定義
class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)

    room = db.relationship('Room', backref=db.backref('reservations', lazy=True))

@app.route('/')
def index():
    rooms = Room.query.all()
    print("rooms:", rooms)  # ← 追加
    return render_template('index.html', rooms=rooms)


@app.route('/events/<int:room_id>')
def get_events(room_id):
    reservations = Reservation.query.filter_by(room_id=room_id).all()
    events = [
        {
            'id': r.id,
            'title': r.title,
            'start': r.start.isoformat(),
            'end': r.end.isoformat()
        } for r in reservations
    ]
    return jsonify(events)

@app.route("/reserve", methods=["POST"])
def reserve():
    data = request.get_json()
    jst = pytz.timezone('Asia/Tokyo')
    new_reservation = Reservation(
        title=data["title"],
        start=datetime.fromisoformat(data["start"]).astimezone(jst),
        end=datetime.fromisoformat(data["end"]).astimezone(jst),
        room_id=data["room_id"]
    )
    db.session.add(new_reservation)
    db.session.commit()
    return jsonify({"status": "success"})

@app.route("/update/<int:event_id>", methods=["PUT"])
def update_event(event_id):
    data = request.get_json()
    jst = pytz.timezone('Asia/Tokyo')
    event = Reservation.query.get(event_id)
    if event:
        event.title = data["title"]
        event.start = datetime.fromisoformat(data["start"]).astimezone(jst)
        event.end = datetime.fromisoformat(data["end"]).astimezone(jst)
        db.session.commit()
        return jsonify({"status": "success"})
    return jsonify({"status": "fail"}), 404

@app.route('/delete/<int:event_id>', methods=['DELETE'])
def delete_reservation(event_id):
    reservation = Reservation.query.get(event_id)
    if reservation:
        db.session.delete(reservation)
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': '予約が見つかりませんでした'})


@app.route('/rooms', methods=['GET', 'POST'])
def manage_rooms():
    if request.method == 'POST':
        name = request.form['name']
        if name:
            db.session.add(Room(name=name))
            db.session.commit()
    rooms = Room.query.all()
    return render_template('rooms.html', rooms=rooms)

@app.route('/rooms/delete/<int:room_id>', methods=['POST'])
def delete_room(room_id):
    room = Room.query.get(room_id)
    if room and not room.reservations:  # 予約がある部屋は削除できない
        db.session.delete(room)
        db.session.commit()
    return redirect(url_for('manage_rooms'))

@app.route('/rooms/edit/<int:room_id>', methods=['POST'])
def edit_room(room_id):
    room = Room.query.get(room_id)
    new_name = request.form['name']
    if room and new_name:
        room.name = new_name
        db.session.commit()
    return redirect(url_for('manage_rooms'))

@app.route('/update_batch', methods=['PUT'])
def update_batch():
    data = request.get_json()
    updates = data.get('updates', [])

    for item in updates:
        reservation = Reservation.query.get(item['id'])
        if reservation:
            reservation.title = item['title']
            reservation.start = datetime.fromisoformat(item['start'])
            reservation.end = datetime.fromisoformat(item['end'])
        else:
            print(f"❌ ID {item['id']} の予約が見つかりません")

    db.session.commit()
    return jsonify({"status": "success"})


if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        if Room.query.count() == 0:
            db.session.add(Room(name="母子室"))
            db.session.add(Room(name="礼拝堂"))
            db.session.add(Room(name="学生会室"))
            db.session.add(Room(name="和室"))
            db.session.add(Room(name="牧師室"))
            db.session.add(Room(name="食堂"))
            db.session.add(Room(name="キッチン"))
            db.session.add(Room(name="小礼拝堂"))
            db.session.add(Room(name="ゲスト室"))
            db.session.add(Room(name="1階会議室"))
            db.session.add(Room(name="シャワー"))
            db.session.commit()
            print("✅ 初期部屋データを追加しました")
        else:
            print("⚠️ 初期部屋データはすでに存在します")
            
        
    app.run(debug=True, host='0.0.0.0', port=5000)
