from flask import Flask, render_template, jsonify, Response, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects import postgresql
import os

app = Flask(__name__)
app.config.update(SECRET_KEY='123456790',
    SQLALCHEMY_ECHO=True,
    SQLALCHEMY_DATABASE_URI=os.environ['DATABASE_URL'])

db = SQLAlchemy(app)
class Doc(db.Model):
    i = db.Column(db.Integer, primary_key=True)
    t = db.Column(db.String())
    d = db.Column(postgresql.JSON)

@app.route('/<string:t>',methods=['GET','POST'])
@app.route('/<string:t>/<int:i>',methods=['GET','POST'])
@app.route('/<string:t>/<string:n>',methods=['GET','POST'])
def all(t, i=None, n=None):
    r,j = None, request.get_json()
    if j and ('id' in j):
        i = j['id']
    if n:
        r = Doc.query.filter( Doc.t==t, Doc.d[t].astext == n).first()
    elif i:
        r = Doc.query.filter( Doc.t==t, Doc.id==i ).first()
    if r:
        if j:
            r.d = j
            Doc.query.session.commit()
        model = dict(r.d)
        model.update(id=r.i)
        return jsonify(model=model)
    else:
        model = []
        for r in Doc.query.filter(Doc.t==t).limit(10):
            d = dict(r.d)
            d.update(id=r.i)
            model.append(d)
        return jsonify(model=model)
    return '',404

@app.route('/menu')
def menu():
    menu = [
        dict(tipo='Home',icone='home')
    ]
    for t in Doc.query.filter(Doc.t=='Tipo').order_by(Doc.d['ordem'].astext.cast(db.Integer)):
        menu.append(dict(t.d))
    return jsonify(menu)

@app.route('/')
def index():
    return render_template('index.html')

with app.app_context():
    db.drop_all()
    db.create_all()
    db.session.add(Doc(t='Tipo',d=dict(
        tipo='Tipo',icone='cog',ordem=1,campos=[
        dict(i='tipo',t='texto'),
        dict(i='icone',t='texto'),
        dict(i='ordem',t='texto'),
        dict(i='campos',t='campos')]
        )))
    db.session.add(Doc(t='Tipo',d=dict(
        tipo='Cliente',icone='home',ordem=2,campos=[
        dict(i='nome',t='texto'),
        dict(i='cnpj',t='texto')]
        )))
    db.session.commit()

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=os.environ['PORT'])