from flask import Flask, render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps



class registerform(Form):
    name=StringField("İsim Soyisim..",validators= [validators.Length(min=5,max=20)])
    username=StringField("Takma Ad..",validators= [validators.Length(min=5,max=20)])
    email=StringField("E-MAİL",validators= [validators.Email(message = "Geçerli bir mail giriniz...")])
    Password = PasswordField("Şifre..",validators= [validators.DataRequired(message= "Boş bırakamazsınız.."),validators.EqualTo(fieldname = "confirm", message= "Şifreleriniz uyuşmuyor...")])
    confirm = PasswordField("Şifre Tekrar",validators= [validators.DataRequired(message= "Boş bırakılamaz...")])

class girisForm(Form):
    username=StringField("Takma Ad",validators= [validators.Length(min=5,max=20),validators.DataRequired(message= "Boş bırakamazsınız..")])
    Password = PasswordField("Şifre",validators= [validators.DataRequired(message= "Boş bırakamazsınız..")])


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logid_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Kontrol Paneli sadece üyeler için.","danger")
            return redirect(url_for("index5"))
    return decorated_function

app = Flask(__name__)
app.secret_key= "ybblog"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "ybblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

@app.route("/")
def index():
    numara = (1,2,3,4,5)

    return render_template("navbar.html",number = numara)

@app.route("/hakkımızda")
def index1():
    return render_template("hakkımızda.html")

@app.route("/makale")
def index2():
    cursor= mysql.connection.cursor()
    sorgu="Select * from article"

    result= cursor.execute(sorgu)
    if result>0:
        articles=cursor.fetchall()
        return render_template("makale.html",articles=articles)
    else:
        return render_template("makale.html")


@app.route("/article/<int:id>/comment", methods=["GET","POST"])
@login_required
def index21(id):
    if request.method=="GET":
        return redirect(url_for("index2"))
    else:
        yorum= request.form.get("articlecomment")
        cursor= mysql.connection.cursor()
        sorgu="INSERT into comment(makaleid,yorum,nameyorum) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(id,yorum,session["username"]))
        mysql.connection.commit()


        sorgu2= "Select * from article where id= %s"
        result= cursor.execute(sorgu2,(id,))
        if result>0:
            article=cursor.fetchone()
            sorgu2= "Select * from comment where makaleid=%s"
            cursor.execute(sorgu2,(id,))
            comments=cursor.fetchall()
            flash("Yorumunuz Yapılmıştır","success")
            return render_template("article.html", article=article, comments=comments)
        else:
            return render_template("article.html")


@app.route("/giris",methods= ["GET","POST"])
def index4():
    form = registerform(request.form)
    if request.method=="POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.Password.data)
        sayac= 0
        cursor = mysql.connection.cursor()

        sorgu2="Select * from kullanıcı where username=%s"
        result= cursor.execute(sorgu2,(username,))
        sorgu3="Select * from kullanıcı where email=%s"
        result1= cursor.execute(sorgu3,(email,))
        if result != 0:
            sayac +=1
        
        if result1 != 0:
            sayac += 1

        if sayac == 0:
            sorgu= "Insert into kullanıcı(name,email,username,password) Values(%s,%s,%s,%s)"
            cursor.execute(sorgu,(name,email,username,password))
            mysql.connection.commit()
            cursor.close()

            flash("Basarı ile kayıt olundu..","success")

            return redirect(url_for("index5"))
        elif sayac ==1:
            flash("Maalesef kullanıcı ismi alınmış veya email ile hesap alınmış.", "danger")
            return redirect(url_for("index4"))

        else:
            flash("Maalesef kullanıcı ismi alınmış ve email ile hesap alınmış.", "danger")
            return redirect(url_for("index4"))
    else:
        return render_template("giris.html", form=form)

@app.route("/login",methods = ["GET","POST"])
def index5():
    form= girisForm(request.form)
    if request.method=="POST":
        username = form.username.data
        password = form.Password.data
        
        cursor = mysql.connection.cursor()

        sorgu= "Select * from kullanıcı where username= %s"

        kullanıcı= cursor.execute(sorgu,(username,))
        if kullanıcı>0:
            data= cursor.fetchone()
            realPassword= data["password"]
            realid=data["id"]
            if sha256_crypt.verify(password,realPassword):
                flash("Giriş Yapıldı.","success")

                session["logid_in"]= True
                session["username"]=username
                session["id"]=realid

                return redirect(url_for("index"))
            else:
                flash("Şifre Yanlış.","danger")
                return redirect(url_for("index5"))
        else:
            flash("Kullanıcı yok.","danger")
            return redirect(url_for("index5"))

    else:
        return render_template("login.html",form = form)

@app.route("/logout")
def index6():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def index7():
    cursor= mysql.connection.cursor()
    sorgu="Select * from article where author=%s"

    response= cursor.execute(sorgu,(session["username"],))
    if response > 0:
        article=cursor.fetchall()
        return render_template("dashboard.html",article=article)
    else:
        return render_template("dashboard.html")


@app.route("/addarticle", methods= ["GET","POST"])
@login_required
def index8():
    form=addarticleform(request.form)
    if request.method == "POST" and form.validate():
        title= form.title.data
        icerik= form.icerik.data

        cursor= mysql.connection.cursor()

        sorgu="Insert into article(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(sorgu,(title,session["username"],icerik))

        mysql.connection.commit()

        cursor.close()

        flash("Basarı ile eklendi.","success")
        return redirect(url_for("index7"))
    return render_template("addarticle.html",form=form)

@app.route("/article/<string:id>")
def index9(id):
    cursor= mysql.connection.cursor()
    sorgu= "Select * from article where id= %s"

    result= cursor.execute(sorgu,(id,))

    if result>0:
        article=cursor.fetchone()
        sorgu2= "Select * from comment where makaleid=%s"
        cursor.execute(sorgu2,(id,))
        comments=cursor.fetchall()
        return render_template("article.html", article=article, comments=comments)
    else:
        return render_template("article.html")

@app.route("/delete/<string:id>")
@login_required
def index10(id):
    cursor= mysql.connection.cursor()

    sorgu= "Select * from article where author=%s and id=%s"

    result= cursor.execute(sorgu,(session["username"], id))

    if result>0:
        sorgu2="Delete from article where id=%s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        flash("Başarı ile silindi.", "success")
        return redirect(url_for("index7"))
    
    else:
        flash("Makale bulunamadı veya silmeye yetkiniz yok...","warning")
        return redirect(url_for("index"))


@app.route("/search", methods=["GET","POST"])
def index12():
    if request.method=="GET":
       return redirect(url_for("index"))
    else :
        cursor= mysql.connection.cursor()

        aranan= request.form.get("keyword")

        sorgu="Select * from article where title like '%"+aranan+"%'"

        result= cursor.execute(sorgu)

        if result == 0:
            flash("Makale bulunamadı...","info")
            return redirect(url_for("index2"))
        else:
            articles=cursor.fetchall()
            return render_template("makale.html", articles=articles)

@app.route("/deneme/<string:id>")
@login_required
def index13(id):
    cursor= mysql.connection.cursor()
    sorgu= ("INSERT INTO favori(makaleid,kullanıcıname) VALUES(%s,%s)")

    cursor.execute(sorgu,(id,session["username"]))
    cursor.connection.commit()

    return redirect(url_for("index2"))

@app.route("/deneme/<string:id>/article")
@login_required
def index25(id):
    cursor= mysql.connection.cursor()
    sorgu= ("INSERT INTO favori(makaleid,kullanıcıname) VALUES(%s,%s)")

    cursor.execute(sorgu,(id,session["username"]))
    cursor.connection.commit()

    return redirect(url_for("index9", id= id))

@app.route("/dashboard/<string:nameyorum>")
def index23(nameyorum):
    cursor= mysql.connection.cursor()
    sorgu="Select * from kullanıcı where username=%s"
    cursor.execute(sorgu,(nameyorum,))
    profilSahibi=cursor.fetchall()
    sorgu2= "Select * from article where author=%s"
    cursor.execute(sorgu2,(nameyorum,))
    article= cursor.fetchall()
    return render_template("profil.html", profilSahibi= profilSahibi, article= article)


@app.route("/friends/<string:author>")
@login_required
def index24(author):
    cursor=mysql.connection.cursor()
    sorgu="INSERT into arkadasliste(kullanıcıName,eklenenName) VALUES(%s,%s)"
    sorgu2="Select * from article where author=%s"

    cursor.execute(sorgu2,(author,))
    result=cursor.fetchone()

    cursor.execute(sorgu,(session["username"], author))
    mysql.connection.commit()
    bilgi= result["id"]
    return redirect(url_for("index9", id=bilgi))

@app.route("/friends")
@login_required
def index27():
    return render_template("friends.html")

@app.route("/friends/<string:author>/profil")
@login_required
def index26(author):
    cursor=mysql.connection.cursor()
    sorgu="INSERT into arkadasliste(kullanıcıName,eklenenName) VALUES(%s,%s)"
    sorgu2="Select * from article where author=%s"

    cursor.execute(sorgu2,(author,))
    result=cursor.fetchone()

    cursor.execute(sorgu,(session["username"], author))
    mysql.connection.commit()
    return redirect(url_for("index23", nameyorum= author))


@app.route("/article/<string:id>/<int:id1>")
@login_required
def index22(id,id1):
    cursor= mysql.connection.cursor()
    sorgu3= ("INSERT INTO commentlike(makaleid,kullanıcıname,likecommentid) VALUES(%s,%s,%s)")
    cursor.execute(sorgu3,(id,session["username"],id1))

    sorgu= "Select * from article where id= %s"

    result= cursor.execute(sorgu,(id,))

    if result>0:
        article=cursor.fetchone()
        sorgu2= "Select * from comment where makaleid=%s"
        cursor.execute(sorgu2,(id,))
        comments=cursor.fetchall()
        cursor.connection.commit()
        return render_template("article.html", article=article, comments=comments)
    else:
        return render_template("article.html")


@app.route("/deneme", methods=["GET","POST"])
@login_required
def index14():
    if request.method=="GET":
        return render_template("deneme.html")

    else:
        yorum= request.form.get("comment")
        cursor= mysql.connection.cursor()
        sorgu= "INSERT into comment(makaleid,yorum,nameyorum) VALUES(%s,%s,%s)"

        cursor.execute(sorgu,(5,yorum,session["username"]))
        return redirect(url_for("index1"))



@app.route("/edit/<string:id>",methods= ["GET","POST"])
@login_required
def index11(id):
    if request.method == "GET":
        cursor=mysql.connection.cursor()
        sorgu="Select * from article where id=%s and author=%s"
        result= cursor.execute(sorgu,(id,session["username"]))

        if result==0:
            flash("Makale bulunamadı veya düzeltmeye yetkiniz yok.","info")
            return redirect(url_for("index"))
        else:
            form=addarticleform()
            article= cursor.fetchone()
            
            form.title.data= article["title"]
            form.icerik.data= article["content"]
            return render_template("update.html",form=form)

    else:
        form= addarticleform(request.form)
        cursor= mysql.connection.cursor()
        sorgu2="Update article set title=%s, content=%s where id=%s"

        yeniTitle= form.title.data
        yeniicerik= form.icerik.data

        cursor.execute(sorgu2,(yeniTitle,yeniicerik,id))

        mysql.connection.commit()

        flash("Başarı ile güncellendi", "success")
        return redirect(url_for("index7"))


@app.route("/begenilen")
@login_required
def index15():
    cursor= mysql.connection.cursor()
    sorgu="SELECT DISTINCT makaleid FROM favori where kullanıcıname=%s"
    cursor.execute(sorgu,(session["username"],))
    articll=cursor.fetchall()
    liste=list()
    for i in articll:
        sorgu2="Select * From article where id=%s"
        cursor.execute(sorgu2,(i["makaleid"],))
        liste.append(cursor.fetchall())
    articl=liste
    return render_template("begenilen.html", liste= liste)

@app.route("/fav-delete/<string:id>")
@login_required
def index16(id):
    cursor= mysql.connection.cursor()

    sorgu= "Delete from favori where makaleid=%s"
    cursor.execute(sorgu,(id,))
    mysql.connection.commit()
    flash("Başarı ile silindi","success")
    return redirect(url_for("index15"))



   
    


class addarticleform(Form):
    title=StringField("Başlık", validators=[validators.Length(min=5, max=100)])
    icerik=TextAreaField("Metin", validators=[validators.Length(min=10), validators.DataRequired(message="Boş bırakılamaz")])

if __name__ == "__main__":
    app.run(debug=True)

