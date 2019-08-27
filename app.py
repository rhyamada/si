from flask import Flask, render_template, jsonify, Response, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects import postgresql
from flask_socketio import SocketIO, emit
import os

app = Flask(__name__)
app.config.update(SECRET_KEY='123456790',
    SQLALCHEMY_ECHO=True,
    SQLALCHEMY_DATABASE_URI=os.environ['DATABASE_URL'])
socketio = SocketIO(app)

db = SQLAlchemy(app)
class Doc(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    t = db.Column(db.String())
    d = db.Column(postgresql.JSON)

@app.route('/<string:t>',methods=['GET'])
def list(t):
    model = []
    for r in Doc.query.filter(Doc.t==t).limit(10):
        d = dict(r.d)
        d.update(id=r.id)
        model.append(d)
    return jsonify(model=model)

@app.route('/<string:t>',methods=['POST'])
def post(t):
    j = request.get_json()
    if not j:
        return dict(error='No data sent'),400
    m = j.get('model')
    if not m:
        return dict(error='No data sent'),400
    r = Doc.query.filter( Doc.t==t, Doc.id==m.get('id') ).first()
    if r:
        r.d = m
        Doc.query.session.commit()
        model = dict(r.d)
        model.update(id=r.id)
        return jsonify(model=model)
    r = Doc(t=t,d=m)
    Doc.query.session.add(r)
    Doc.query.session.commit()
    model = dict(r.d)
    model.update(id=r.id)
    if t=='tipo':
        send_menu()
        print('Broadcast!!!')
    return jsonify(model=model), 201

D = dict(texto='',numero=0,campos=[],icone='cog')
def padrao(c):    
    return c.get('d',D.get(c.get('t','texto'),'') )

@app.route('/<string:t>/<int:id>',methods=['GET'])
def by_id(t,id):
    if id == 0:
        T = Doc.query.filter( Doc.t=='tipo', Doc.d['tipo'].astext == t ).first()
        if not T:
            return dict(error='Not found'),404
        model = dict()
        for c in T.d['campos']:
            model[c['i']] = padrao(c)
        return jsonify(model=model)

    r = Doc.query.filter( Doc.t==t, Doc.id==id ).first()
    if not r:
        return dict(error='Not found'),404
    model = dict(r.d)
    model.update(id=r.id)
    return jsonify(model=model)

@app.route('/<string:t>/<string:n>',methods=['GET'])
def by_name(t,n):
    r = Doc.query.filter( Doc.t==t, Doc.d[t].astext == n).first()
    if not r:
        return dict(error='Not found'),404
    model = dict(r.d)
    model.update(id=r.id)
    return jsonify(model=model)

@app.route('/<string:t>/<int:id>',methods=['DELETE'])
def delete(t,id):
    r = Doc.query.filter( Doc.t==t, Doc.id==id ).first()
    if not r:
        return dict(error='Not Found'),404
    Doc.query.session.delete(r)
    Doc.query.session.commit()
    if t=='tipo':
        send_menu()
        print('Broadcast!!!')
    return '', 204

def send_menu():
    menu = []
    for t in Doc.query.filter(Doc.t=='tipo').order_by(Doc.d['ordem'].astext.cast(db.Integer)):
        menu.append(dict(t.d))
    socketio.emit('menu', menu)


@app.route('/menu')
def menu():
    menu = []
    for t in Doc.query.filter(Doc.t=='tipo').order_by(Doc.d['ordem'].astext.cast(db.Integer)):
        menu.append(dict(t.d))
    return jsonify(menu)

@socketio.on('connect')
def on_connect():
    send_menu()

@app.route('/')
def index():
    return render_template('index.html')

with app.app_context():
    db.drop_all()
    db.create_all()
    db.session.add(Doc(t='tipo',d=dict(
        tipo='tipo',icone='cog',ordem=1,campos=[
        dict(i='tipo',t='texto',d=''),
        dict(i='icone',t='texto',d='cog'),
        dict(i='ordem',t='numero',d=0),
        dict(i='campos',t='campos',d=[])]
        )))
    db.session.add(Doc(t='tipo',d=dict(
        tipo='cliente',icone='home',ordem=2,campos=[
        dict(i='nome',t='texto'),
        dict(i='cnpj',t='texto')]
        )))
    db.session.add(Doc(t='cliente',d=dict(
        nome='SERPRO',cnpj='0'
        )))
    db.session.add(Doc(t='tipo',d=dict(
        tipo='oferta',icone='cog',ordem=3,campos=[
        dict(i='nome',t='texto'),
        dict(i='condifguracao',t='texto')]
        )))
    db.session.add(Doc(t='tipo',d=dict(
        tipo='grupo',icone='edit',ordem=3,campos=[
        dict(i='nome',t='texto')]
        )))
    db.session.commit()

if __name__ == '__main__':
    socketio.run(app,host='0.0.0.0')
