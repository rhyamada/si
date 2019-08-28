from flask import Flask, render_template, jsonify, Response, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects import postgresql
from flask_socketio import SocketIO, emit
from sqlalchemy import event
import os

import eventlet
eventlet.monkey_patch()

app = Flask(__name__)
app.config.update(SECRET_KEY='123456790',SQLALCHEMY_ECHO=True,SQLALCHEMY_DATABASE_URI=os.environ['DATABASE_URL'])
socketio = SocketIO(app,message_queue=os.environ['REDIS_URL'])
db = SQLAlchemy(app)

class Doc(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    t = db.Column(db.String())
    d = db.Column(postgresql.JSON)

def send_menu():
    menu = []
    for t in Doc.query.filter(Doc.t=='tipo').order_by(Doc.d['ordem'].astext.cast(db.Integer)):
        menu.append(dict(t.d))
    socketio.emit('menu', menu)

def change(action,doc):
    if doc.t=='tipo':
        send_menu()
    socketio.emit(action,doc.d, namespace=doc.t)

@event.listens_for(Doc, 'after_update')
def _after_update(mapper, connection, doc):
    change('update',doc)

@event.listens_for(Doc, 'after_insert')
def _after_insert(mapper, connection, doc):
    change('insert',doc)

@event.listens_for(Doc, 'after_delete')
def _after_delete(mapper, connection, doc):
    change('delete',doc)

def resp(doc):
    model = dict(doc.d)
    model.update(id=doc.id)
    return jsonify(model=model)

@app.route('/<string:t>',methods=['GET'])
def list(t):
    model = []
    g = request.args.get
    for r in Doc.query.filter(Doc.t==t).limit(g('_size',20)):
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
        return resp(r)
    r = Doc(t=t,d=m)
    Doc.query.session.add(r)
    Doc.query.session.commit()
    return resp(r)

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
    return resp(r)

@app.route('/<string:t>/<string:n>',methods=['GET'])
def by_name(t,n):
    r = Doc.query.filter( Doc.t==t, Doc.d[t].astext == n).first()
    if not r:
        return dict(error='Not found'),404
    return resp(r)

@app.route('/<string:t>/<int:id>',methods=['DELETE'])
def delete(t,id):
    r = Doc.query.filter( Doc.t==t, Doc.id==id ).first()
    if not r:
        return dict(error='Not Found'),404
    Doc.query.session.delete(r)
    Doc.query.session.commit()
    return '', 204

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
    db.session.commit()

if __name__ == "__main__":
    socketio.run(app,host='0.0.0.0',port=os.environ['PORT'])