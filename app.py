from flask import Flask, render_template, session, url_for,redirect,request,flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from sqlalchemy.sql import func


db=SQLAlchemy()
DB_NAME="database.db"

app=Flask(__name__)
app.secret_key="secret"
app.config['SQLALCHEMY_DATABASE_URI']=f'sqlite:///{DB_NAME}'
db.init_app(app)
        

class User(db.Model,UserMixin):
    id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(100),unique=True)
    email=db.Column(db.String(100))
    password=db.Column(db.String(100))
    posts=db.relationship('Post',backref='author',lazy=True)
    profile_pic=db.Column(db.Text,nullable=True)


class Post(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(100))
    text=db.Column(db.String(1000))
    date_posted=db.Column(db.DateTime(timezone=True), default=func.now())
    username=db.Column(db.String(100),db.ForeignKey('user.username'))
    post_pic=db.Column(db.Text,nullable=True)
    

class Follow(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    follower=db.Column(db.String(100),db.ForeignKey('user.username'))
    following=db.Column(db.String(100),db.ForeignKey('user.username'))


if not os.path.exists('website/' + DB_NAME):
    with app.app_context():
        db.create_all()

@app.route('/follow/<string:username>',methods=['POST','GET'])
def follow(username):
    if request.method=='POST':
        if 'username' not in session:
            flash("Please login to continue")
            return redirect(url_for('login'))
        else:
            if username==session['username']:
                flash("You cannot follow yourself")
                return redirect(url_for('search'))
            else:
                if Follow.query.filter_by(follower=session['username'],following=username).first():
                    flash("You are already following this user")
                    return redirect(url_for('search'))
                else:
                    follow=Follow(follower=session['username'],following=username)
                    db.session.add(follow)
                    db.session.commit()
                    flash("Followed successfully")
                    return redirect(url_for('search'))
    else:
        flash("Invalid request")
        return redirect(url_for('search'))


@app.route('/unfollow/<string:username>',methods=['POST','GET'])
def unfollow(username):
    if 'username' not in session:
        flash("Please login to continue")
        return redirect(url_for('login'))
    else:
        if username==session['username']:
            flash("You cannot unfollow yourself")
            return redirect(url_for('search'))
        else:
            if Follow.query.filter_by(follower=session['username'],following=username).first():
                follow=Follow.query.filter_by(follower=session['username'],following=username).first()
                db.session.delete(follow)
                db.session.commit()
                flash("Unfollowed successfully")
                return redirect(url_for('search'))
            else:
                flash("You are not following this user")
                return redirect(url_for('search'))

@app.route('/delete/<int:id>',methods=['POST','GET'])
def delete(id):
    if 'username' not in session:
        flash("Please login to continue")
        return redirect(url_for('login'))
    else:
        post=Post.query.filter_by(id=id).first()
        if post.author.username==session['username']:
            db.session.delete(post)
            db.session.commit()
            flash("Post deleted successfully")
            return redirect(url_for('home'))
        else:
            flash("You cannot delete this post")
            return redirect(url_for('home'))

@app.route('/editpost/<int:id>',methods=['POST','GET'])
def editpost(id):
    if 'username' not in session:
        flash("Please login to continue")
        return redirect(url_for('login'))
    else:
        post=Post.query.filter_by(id=id).first()
        if post.username==session['username']:
            if request.method=='POST':
                post.title=request.form['title2']
                post.text=request.form['text2']
                post.date_posted=func.now()
                
                db.session.commit()
                flash("Post updated successfully")
                return redirect(url_for('home'))
            else:
                return render_template('editpost.html',post=post)
        else:
            flash("You cannot edit this post")
            return redirect(url_for('home'))

@app.route('/deleteaccount',methods=['POST','GET'])
def deleteaccount():
    if 'username' not in session:
        flash("Please login to continue")
        return redirect(url_for('login'))
    else:
        user=User.query.filter_by(username=session['username']).first()
        posts=Post.query.filter_by(username=session['username']).all()
        for post in posts:
            db.session.delete(post)
        follows=Follow.query.filter_by(follower=session['username']).all()
        for follow in follows:
            db.session.delete(follow)
        follows=Follow.query.filter_by(following=session['username']).all()
        for follow in follows:
            db.session.delete(follow)
        db.session.delete(user)
        db.session.commit()
        flash("Account deleted successfully")
        return redirect(url_for('logout'))

@app.route('/editprofile',methods=['POST','GET'])
def editprofile():
    if 'username' not in session:
        flash("Please login to continue")
        return redirect(url_for('login'))
    else:      
        user=User.query.filter_by(username=session['username']).first()
        if request.method=='POST':
            user.email=request.form['email']
            user.password=request.form['password']
            if request.files['profile_pic'].filename!='':
                user.profile_pic=request.files['profile_pic'].read()
            db.session.commit()
            flash("Profile updated successfully")
            return redirect(url_for('home'))
        else:
            return render_template('editprofile.html',user=user)


@app.route('/login',methods=['POST',"GET"])
def login():
    if request.method=='POST':
        uname=request.form['username']
        passw=request.form['password']
        user=User.query.filter_by(username=uname).first()
        if user:
            if user.password==passw:
                session['username']=uname
                flash("Logged in successfully")
                return redirect(url_for('home'))
            else:
                flash("Invalid username or password")
                return redirect(url_for('login'))
        else:
            flash("Username do not exist")
            return redirect(url_for('login'))
    else:
        if 'username' in session:
            flash("Already logged in")
            return redirect(url_for('home'))
        else:
            return render_template('login.html')

@app.route('/register',methods=['POST','GET'])
def register():
    if request.method=='POST':
        if "username" in session:
            return redirect(url_for('home'))
        else:
            uname=request.form['username1']
            email=request.form['email1']
            passw=request.form['password1']
            profile_pic=request.files['profile_pic']

          
            new_user=User(username=uname,email=email,password=passw,profile_pic=profile_pic.read())
            if User.query.filter_by(username=uname).first():
                flash("Username already exists")
                return redirect(url_for('register'))
            db.session.add(new_user)
            db.session.commit()
           

            flash("Registered successfully")
            return redirect(url_for('login'))
    else:
        if 'username' in session:
            flash("Already logged in")
            return redirect(url_for('home'))
        else:
            return render_template('register.html')

@app.route('/')
def home():
    if "username" not in session:
        flash("Please login to continue")
        return redirect(url_for('login'))
    else:
        posts=Post.query.filter_by(username=session['username']).all()
        posts.sort(key=lambda x: x.date_posted, reverse=True)
        for post in posts:
            if post.post_pic:
                with open('static/post_pics/'+str(post.id)+'.png','wb+') as f:
                    f.write(post.post_pic)
                    f.close()
    
        return render_template('home.html',uname=session['username'],posts=posts)

@app.route('/profile',methods=['POST','GET'])
def profile():
    if "username" not in session:
        flash("Please login to continue")
        return redirect(url_for('login'))
    else:
        current_user=session['username']
        followers=Follow.query.filter_by(following=current_user).all()
        following=Follow.query.filter_by(follower=current_user).all()
        posts=Post.query.filter_by(username=current_user).all()
        followers_len=len(followers)
        following_len=len(following)
        posts_len=len(posts)
        posts.reverse()
        uname=User.query.filter_by(username=current_user).first()

        flagimg=False

        for post in posts:
            if post.post_pic:
                with open('static/post_pics/'+str(post.id)+'.png','wb+') as f:
                    f.write(post.post_pic)
                f.close()
        if uname.profile_pic:

            img=open('static/profile_pics/profile.png','wb+')
            img.write(uname.profile_pic)
            img.close()

            flagimg=True

        return render_template('profile.html',uname=uname,followers_count=followers_len,following_count=following_len,posts_count=posts_len,followers=followers,followings=following,posts=posts,flagimg=flagimg)

@app.route('/viewprofile/<string:username>',methods=['POST','GET'])
def viewprofile(username):
    if "username" not in session:
        flash("Please login to continue")
        return redirect(url_for('login'))
    else:
        current_user=session['username']

        person=User.query.filter_by(username=username).first()
        if not person:
            flash("User do not exist")
            return redirect(url_for('search'))

        followers=Follow.query.filter_by(following=username).all()
        following=Follow.query.filter_by(follower=username).all()
        posts=Post.query.filter_by(username=username).all()
        followers_len=len(followers)
        following_len=len(following)
        posts_len=len(posts)
        posts.reverse()
        followerlist=[]
        for follower in followers:
            followerlist.append(follower.follower)
        if current_user in followerlist:
            flag1=True
        else:
            flag1=False
        flagimg=False
        if person.profile_pic:
            img=open('static/profile_pics/profile.png','wb+')
            img.write(person.profile_pic)
            img.close()
            flagimg=True
        
        for post in posts:
            if post.post_pic:
                with open('static/post_pics/'+str(post.id)+'.png','wb+') as f:
                    f.write(post.post_pic)
                    f.close()
        

        uname=User.query.filter_by(username=username).first()
        return render_template('profile.html',uname=uname,followers_count=followers_len,following_count=following_len,posts_count=posts_len,followers=followers,followings=following,posts=posts,flag=True,flag1=flag1,flagimg=flagimg)

@app.route('/search',methods=['POST','GET'])
def search():
    if request.method=='POST':
        if 'username' not in session:
            flash("Please login to continue")
            return redirect(url_for('login'))
        else:
            search=request.form['search']
            return redirect(url_for('searchresult',search=search))
            
           
    else:
        if 'username' not in session:
            flash("Please login to continue")
            return redirect(url_for('login'))
        else:
            return render_template('search.html')

@app.route('/searchresult/<search>',methods=['POST','GET'])
def searchresult(search):
    if 'username' not in session:
        flash("Please login to continue")
        return redirect(url_for('login'))
    else:
        users=User.query.filter(User.username.like('%'+search+'%') , User.username!=session['username']).all()
        current_user=session['username']
        following=[]
        for user in users:
            if Follow.query.filter_by(follower=current_user,following=user.username).first():
                following.append(user.username)
        return render_template('searchresult.html',users=users,current_user=current_user,following=following)
    

@app.route('/logout')
def logout():
    if 'username' in session:
        session.pop('username',None)
        flash("Logged out successfully")
    else:
        flash("Already logged out")
    return redirect(url_for('login'))
    
@app.route('/myfeed')
def myfeed():
    if 'username' not in session:
        flash("Please login to continue")
        return redirect(url_for('login'))
    else:
        current_user=session['username']
        following=Follow.query.filter_by(follower=current_user).all()
        posts=[]
        for user in following:
            posts+=Post.query.filter_by(username=user.following).all()
        posts.sort(key=lambda x:x.date_posted,reverse=True)
        for post in posts:
            if post.post_pic:
                with open('static/post_pics/'+str(post.id)+'.png','wb+') as f:
                    f.write(post.post_pic)
                    f.close()

        return render_template('myfeed.html',posts=posts)

@app.route('/addpost',methods=['POST','GET'])
def addpost():
    if request.method=='POST':
        if 'username' not in session:
            flash("Please login to continue")
            return redirect(url_for('login'))
        else:
            title=request.form['title']
            text=request.form['text']
            post_img=request.files['post_img']
            new_post=Post(title=title,text=text,username=session['username'],post_pic=post_img.read())
            db.session.add(new_post)
            db.session.commit()
            flash("Post added successfully")
            return redirect(url_for('home'))
    else:
        if 'username' not in session:
            flash("Please login to continue")
            return redirect(url_for('login'))
        else:
            return render_template('addpost.html')

@app.errorhandler(404)
def pagenotfound(e):
	return render_template("error404.html"),404

if __name__=="__main__":
    app.run()
