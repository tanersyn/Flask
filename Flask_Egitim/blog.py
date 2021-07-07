from flask import Flask, render_template, flash, redirect, url_for, session, logging, request # render içine template vericez. Flask templateleri "templates" klasörünün içinde arıyor ve o klasör içindeki templatesi bulmayı sağlıyor
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt # bu bir modül ve içinde de fonksiyon var parolaları şifrelemeyi sağlıyor
from functools import wraps


# !!Kullanıcı Giriş Decorator'ı

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session: # Kullanıcı giriş yapmışssa
            return f(*args, **kwargs)
        else: # Oturum açılmamışssa yani session başlatılmamışssa anasayfa döndürmemiz gerek
            flash("Sayfayı Görüntülemek İçin Lütfen Giriş Yapın","warning")
            return redirect(url_for("login"))
    return decorated_function



# Kullanıcı Kayıt Formu
class RegisterForm(Form):
    name = StringField("İsim Soyisim", validators = [validators.Length(min = 4, max = 25)]) # validators = kısıtlamalar
    username = StringField("Kullanıcı Adı", validators = [validators.Length(min = 5, max = 35)])
    email = StringField("Email Adresi", validators = [validators.Email(message = "Lütfen Geçerli Email Adresi Giriniz")]) # validators = [validators.Email] email olup olmadığını sorgulayacak ve eğer değilse mesaj fırlatacak
    password = PasswordField("Parola", validators = [ # İki türlü parola yazılması lazım biri normal diğeri de doğru mu değil mi(confirm)
        validators.DataRequired(message = "Lütfen Parola Belirleyin"),
        validators.EqualTo(fieldname = "confirm", message = "Parolanız Uyuşmuyor") # İki taraftaki bilgiler eşit mi ona bakıyor
    ])
    confirm = PasswordField("Parola Doğrula")

class LoginForm(Form): # Wtf form
    username = StringField("Kullancı Adı")
    password = PasswordField("Parola")

app = Flask(__name__)
app.secret_key = "blog_" # Flash mesajlarının yayınlanması için kendimizin oluşturduğu bir secret_key ihtiyaç var

#--------------- MySQL İşlemleri-------------
app.config["MYSQL_HOST"] = "localhost" # Mysql localhostta çalışıyor sunucu kiralansaydı onun ismi verilecekti
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "blog_" # Mysql adı
app.config["MYSQL_CURSORCLASS"] = "DictCursor" # Flask ile MySql bağlantısı kurulmuş oldu. Flask bilgilerin nerde olduğunu bu sayede biliyor

mysql = MySQL(app)
#---------------------------------------------

@app.route("/")
def index():
    numbers = [1,2,3,4,5]

    articles = [
        {"id" : 1, "title" : "Deneme 1", "content" : "Deneme 1 İçerik"},
        {"id" : 2, "title" : "Deneme 2", "content" : "Deneme 2 İçerik"},
        {"id" : 3, "title" : "Deneme 3", "content" : "Deneme 3 İçerik"},
    ]

    return render_template("index.html", islem = 4, numbers = numbers, articles = articles)

@app.route("/about")
def about():
    return render_template("about.html")


# Makale Sayfası
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles" # Veri tabanındaki tüm makalelerin alınması
    result = cursor.execute(sorgu) # Veri tabanında makale var mı yok mu onun kontrolünü sağlamak için result değişkenine atanması

    if result > 0: # Makale var ise articles articles.html'e gönderiliyor. articles.html'de articles var mı yok mu kontrol edilmesi lazım(if)
        articles = cursor.fetchall() # Bir makale almak için fetchone birden fazla makale almak için fetchall(). Liste içinde sözlük olarak dönüyor
        return render_template("articles.html",articles = articles)
    else:
        return render_template("articles.html")



# !! Kullanıcı giriş yapmamış olsa dahi /dashboard yazıp makale ekle kısmına erişebiliyor bunu engellemek için flaskta decorator kullanılıyor.
# !! Decorator kullanıcının giriş yapıp yapmadığına göre erişim izin verecek(functool)

@app.route("/dashboard")
@login_required # Dashboard çalıştırılmadan önce decorater'a gidecek ve eğer session başlatılmışssa dashboard çalışacak ancak başlatılmamışssa redirect ile login sayfasına gidecek
def dashboard():
    # Hangi kullanıcı hangi makaleyi yazdıysa onun gösterilmesi
    cursor = mysql.connection.cursor()
    sorgu =  "Select * From articles where author =  %s" # Kullanıcıya göre(yazara göre)
    result = cursor.execute(sorgu,(session["username"],)) # session[username] %s'i karşılıyor

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else:
        return render_template("dashboard.html")
 
    return render_template("dashboard.html")

"""
@app.route("/article/<string:id>") # Dinamik url yapısı. article/1 veya article/100 id kaç ise ona gider
def id_goster(id):
    return "Article id :" + id
"""

# Kayıt Ol
# Bir sayfaya ulaştığımızda bu GET request yapmış oluyoruz ve server bunu anlıyor ve bize o sayfanın html içeriğini döndürüyor. Biz herhangi bir formu sumbit ettiğimizde oluşan http request türüne de POST request diyoruz. Eğer biz bir fonksiyon çalıştıracaksak bunun GET mi yoksa POST request mi yapıldığını anlamamız gerekiyor. Bunuda dahil ettiğimiz request ile anlayabiliriz.
@app.route("/register", methods = ["GET","POST"]) # İki türlü request tipine de alabilir o yüzden ikisini de yazıyoruz.
def register():

    form = RegisterForm(request.form) # Oluşturduğumuz registerformdan bir object oluşturuyoruz.
                                      # Bizim sayfamıza hem get req. hem post req. yapılıyor. POST req yapıldığında içindeki verileri almak için bu yüzden "request.form" kullanıldı
    if request.method == "POST" and form.validate() : # yani kayıt ol butonuna basma olayı. form.validate() formda bir sıkıntı yoksa True dönecek anlamında
        # Eğer method post ise ve formda herhangi bir sıkıntı yoksa(örneğin şifreler uyuşmuşssa veya mail doğru tipteyse gibi) artık formdaki bilgileri alıp mysql'e bağlanıp orada bir sql sorgusu gerçekleştireceğiz. Bizim mysqlde user adlı tablo var ama içi boş durumda şuan
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data) # formdan alınan bilgileri şifreleyerek kaydetmek istiyoruz

        # Buradan sonra artık mysqle bağlanması gerekiyor
        cursor = mysql.connection.cursor() # cursor; veritabanı üzerinde işlem yapmamızı sağlayan bir yapı. Bu yapıyı kullanarak sql surgularını çalıştırabiliyoruz.
        sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password)) # Tek elemanlı ise (name,) olur. "," koymassak bir demet olarak algolamıyor
        mysql.connection.commit() # Veri tabanında herhangi bir değişiklik yapılmyacaksa, sadece veritabınında bilgi çelicekse commit işlemi yapılması gerekmiyor. Ama veritabında herhngi bir silme veya güncelleme vs yapıldıysa mutlaka commit edilmeli
        cursor.close() 

        # Kayıt işlemi gerçekleştikten sonra kullanıcıya bir feedback vermemiz gerek.Flash messages kullanıyoruz
        flash("Başarıyla Kayıt Oldunuz",category = "success")

        return redirect(url_for("login")) # redirect belirli bir sayfaya git demek
                                          # normalde sayfaya git diyoruz ama url_for sayesinde gitmek istediğimiz fonskiyonu yazarak gidiyoruz
                                          # Kayıt olduktan sonra login sayfasına git olarak değiştirdik sonradan
    else:   
        return  render_template("register.html", form = form) # register.html kısmında formu göstermek için form  = form yazdık(yazdığımız formu register.html'e göndermek istiyoruz anlamında)

# Login İşlemleri
@app.route("/login",methods = ["GET","POST"])
def login():

    form = LoginForm(request.form)

    if request.method == "POST": # Post işlemi ise formdaki bilgileri alacağız ve sonrasında veritabanında sorgulamaya çalışacağız
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()
        sorgu = "Select *From users where username = %s" # Kullanıcıya göre alıyoruz. Fakat kullanıcı olmazssa result 0 gelebilir. Bunu da kontrol etmemiz gerekir
        result = cursor.execute(sorgu,(username,)) # Kullanıcı varsa 0'dan büyük olacak olmazsada kullanıcı 0 olacak
        
        if result > 0 :
            # app.config["MYSQL_CURSORCLASS"] = "DictCursor" yazdığımızdan dolayi bilgiler bize demet şeklinde geliyor
            data = cursor.fetchone() # Kullanıcının bütün bilgileri almış olduk. Sözlük üzerinden gezinildiği gibi gezinilebilir
            # Girilen parolayla gerçek parolanın karşılaştırılması gerek
            real_password = data["password"] # Bizim datada password kısmı vardı onu aldığımızı söylüyoruz
            if sha256_crypt.verify(password_entered,real_password): # İki parolanın aynı olup olmadığını karşılaştıyor. Eğer parola true dönerse başarıyla giriş yapılmıştır demektir
                flash("Başarıyla Giriş Yaptınız","success")
                
                # Başarıyla giriş yapıldıktan sonra session kontrolü yapılması gerek
                session["logged_in"] = True
                session["username"] = username # Giriş yapan kullanıcının usernameni kullanıyoruz

                return redirect(url_for("index")) # Giriş yaptıktan sonra anasayfaya geri döndürüyoruz
            else: # Parola yanlış girilmişsse
                flash("Parolanızı Yanlış Girdiniz","warning")
                return redirect(url_for("login")) # Yanlış parola girildiğinde giriş yap kısmına döndürüyoruz tekrardan

        else:
            flash("Böyle bir kullanıcı bulunmuyor.","danger")
            return redirect(url_for("login"))

    return render_template("login.html", form = form)

# Detay Sayfası
@app.route("/article/<string:id>") # Dinamik url yapısı. article/1 veya article/100 id kaç ise ona gider    
def article(id):
    # id'e göre veritabanında sorgu yapılması gerek
    cursor = mysql.connection.cursor()
    sorgu = "Select * from articles where id = %s" # Makale başındaki id'e göre
    result = cursor.execute(sorgu,(id,)) 

    if result > 0:
        article = cursor.fetchone() # id primary key olduğundan hangisi ise 1 eleman seçilmesi
        return render_template("article.html",article = article)
    else:
        return render_template("article.html")


# Logout İşlemleri
@app.route("/logout")
def logout():
    
    session.clear() # Çıkış yaptığımız anda oturumun kapanması gerek
    return redirect(url_for("index")) 

# Makale Ekleme
@app.route("/addarticle", methods = ["GET","POST"])
def addarticle():

    form = ArticleForm(request.form)

    # Makalelerin veritabanına eklenmesi
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()
        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content)) # session["username"] = oturumu açan kişi yazar 
        mysql.connection.commit()
        cursor.close()

        flash("Makale Başarıyla Eklendi","success")
        return redirect(url_for("dashboard")) # Makale eklendikten sonra makale ekle sayfasına tekrardan dönüş


    return render_template("addarticle.html", form = form)


# Makale Silme
# Makale silerken dikkat edilmesi gerekenler; Öncelikle giriş yapılması lazım silmek için.Bir diğer noktada başkasının makalesi silinmemesi gerek kullanıcı yalnızca kendi makalesini silebilir(decorator kullanılacak)
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * from articles where author = %s and id = %s"
    result = cursor.execute(sorgu,(session["username"],id)) # author yerine session[username] 

    if result > 0 : # Hem makale bize ait hemde makale varsa 

        sorgu2 = "Delete from articles where id = %s" # Varsa silinmesi gerek
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))

    else:

        flash("Böyle Bir Makale Yok Veya Bu İşleme Yetkiniz Yok","danger")
        return redirect(url_for("index"))


# Makale Güncelleme
@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required
def update(id):
    # request tipine farklı durumlar içerecek
    if request.method == "GET":
        
        cursor = mysql.connection.cursor()
        sorgu = "Select * from articles where id = %s and author = %s" # 4 durum var; makalenin olmama durumu, makalenin olup kullanıcının olmama durumu
        result = cursor.execute(sorgu,(id,session["username"]))

        if result == 0: # Makale olup kullanıcının olmama veya makalenin hiç olmama durumu
            flash("Böyle Bir Makale Yok Veya Bu İşleme Yetkiniz Yok","danger")
            return redirect(url_for("index"))
        else: # Makale var demektir makalenin aricle alınması
            article = cursor.fetchone() # Makalenşn tüm bilgileri(author,id vs)hepsi elimizde
            # Sonrasında form oluşturup formda göstermek gerek
            form = ArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form = form)
    
    else: # Post request kısmı

        form = ArticleForm(request.form)
        
        newTitle = form.title.data
        newContent = form.content.data

        sorgu2 = "Update articles Set title = %s,content = %s where id = %s"

        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()

        flash("Makale Başarıyla Güncellendi","info")
        return redirect(url_for("dashboard"))


# Makale Form(Wtf Form)
class ArticleForm(Form):
    title = StringField("Makale Başlığı", validators = [validators.Length(min = 5, max = 100)])
    content = TextAreaField("Makale İçeriği", validators = [validators.Length(min = 10)])

# Arama Url
@app.route("/search",methods = ["GET","POST"])
def search():
    # Sadece post requeste izin verilmesi gerek. Yani search butonuna basılmadan url girerek gidilmesin
    if request.method == "GET":
        return redirect(url_for("index"))
    else: # (Ara butonuna basılarak arama yapılmışssa)
        
        keyword = request.form.get("keyword") # arama kısmına yazılan kelimenin alınması gerek keyword değişkeni ile aldık
        cursor = mysql.connection.cursor()
        sorgu = "Select * from articles where title like '%" + keyword +  "%'" # Kelimeyi bu sorgu ile alıyoruz
        result = cursor.execute(sorgu)

        if result == 0: # Aranan kelimeye uygun bir makale yok demektir
            flash("Aranan Kelimeye Uygun Makale Bulunamadı","warning")
            return redirect(url_for("articles"))
        else:
            # Aranan kelimeye uygun tüm kelimeleri alıp render edilip html sayfasına gönderilmesi
            articles = cursor.fetchall()
            return render_template("articles.html",articles = articles)

if __name__ == "__main__":
    app.run(debug=True)