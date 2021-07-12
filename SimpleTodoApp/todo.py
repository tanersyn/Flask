from flask import Flask,render_template,redirect,url_for,request
from flask_sqlalchemy import SQLAlchemy

# Veritabanı ile ORM birleştirilmesi
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/taner/Desktop/TodoApp/todo.db' # Veri tabanının bulunduğu kısım
db = SQLAlchemy(app)

@app.route("/")
def index():
    
    todos = Todo.query.all() # Eklenen todoların özellikleri sözlük halinde tutuluyor Liste halinde dönüyor
    return render_template("index.html", todos = todos)

@app.route("/add",methods = ["POST"])
def addTodo():

    title = request.form.get("title") # Form kısmında name=title olan kısımdan bilgiler geleceğinden formdan bilgilerin alınması
    newTodo = Todo(title = title, complete = False) # Classtan yeni bir obje oluşturulması. id otomatik oluşturulacak, complete kısmı ise yeni bir todo eklendi fakat tamamlanmamış bir todo olduğundan false olarak başalatılması
    db.session.add(newTodo) # newTodo database eklenmesi
    db.session.commit()

    return redirect(url_for("index")) # Veri tabanına todo eklendikten sonra tekrar anasayfaya dönülmesi

@app.route("/complete/<string:id>")
def completeTodo(id):

    todo = Todo.query.filter_by(id = id).first() # id'e göre verilerin alınması sorgusu
    
    """if todo.complete == True:
        todo.complete = False
    else:
        todo.complete = True"""
    todo.complete = not todo.complete

    db.session.commit()

    return redirect(url_for("index"))

@app.route("/delete/<string:id>")
def deleteTodo(id):

    todo = Todo.query.filter_by(id = id).first()
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for("index"))


class Todo(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    complete = db.Column(db.Boolean) # Her bir todo ekleneip eklenmediğinin ölçülmesi(1 veya 0 değeri alacak)

if __name__ == "__main__":

    db.create_all() # Yukarıda class şeklinde yazılan todo veritabanına tablo olarak eklenmesi
    app.run(debug=True)