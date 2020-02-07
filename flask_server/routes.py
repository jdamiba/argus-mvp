from flask import g, render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from flask_server import flask_server, db
from flask_server.forms import (
    LoginForm,
    RegistrationForm,
    PostForm,
    UpdateForm,
    ResetPWForm,
    EditProfileForm,
)
from flask_server.models import User, Post
from datetime import datetime
from functools import wraps

methods = ["GET", "POST"]


@flask_server.route("/")
def index():
    return redirect(url_for("discover"))


@flask_server.route("/discover")
def discover():
    page = request.args.get("page", 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, flask_server.config["POSTS_PER_PAGE"], False
    )
    next_url = url_for("discover", page=posts.next_num) if posts.has_next else None
    prev_url = url_for("discover", page=posts.prev_num) if posts.has_prev else None
    return render_template(
        "discover.html",
        title="Argus",
        posts=posts.items,
        next_url=next_url,
        prev_url=prev_url,
    )


@flask_server.route("/login", methods=methods)
def login():
    """ The controller to handle incoming GET and POST requests to the `/login` URL of the Flask web server.

    1. Checks to see if the user is already logged in. 
        a. If so, returns a response object that redirects the client to the '/index' route.
            - Results from a GET request from an authenticated user.

        b. If the user is not already logged in, makes the `LoginForm` (created using Flask-WTF) available to the `templates/login` view by passing it and the view as parameters to Flask's built-in `render_template()` function.
            - Results from a GET request from an unauthenticated user.

    2. If a correct username/pw combo is submitted, then an HTTP request is made to the remote SQL database to  query it for the user database object model with the current user's `username`.
        - This operation is safe because the databse enforces unique `usernames` upon registration. Also, the `login_user()` method uses the primary key `user_id` to actually log the user in- this operation simply retrieves the user object.
        - Results from a POST request to this route when the form is sumbitted.

    3. The user database object model is stored in a Python data structure and the controller makes it available to the Flask-Login method `login_user()` by passing it as a parameter to that method.
        a. The `login_user()` method populates Flask's [request context](https://flask.palletsprojects.com/en/1.1.x/reqcontext/) with the logged in user's database object model, which can then be accessed by this and other views and controllers./ to get information about the user.

        b. Flask automatically pushes a new request context (`ctx`) to the stack when handling each request. View functions, error handlers, and other functions that run during the request lifecycle will have access to the [request proxy](https://flask.palletsprojects.com/en/1.1.x/api/#flask.request), which points to the request object for the current request.

        c. Prior to a user logging in, `ctx.user` (an attribute of the request context) is an instance of the `AnonymousUserMixin` class.  After a user logs in, `ctx.user` is an instance of the User database object model defined using the Flask-SQLAlchemy extension in `flask_server/models`. 

        d. Sucessfully calling `login_user()` creates a session, as all subsequent requests will now have access to user's database object model. Without using sessions, the user would have to send authenticated requests each time they wanted to access a protected view instead of just once at log in.

    4. The user is redirected to the `index` view after sucessfully logging in.

    Parameters
    ----------
    param1 : string
        The first parameter is the URL being requested by the client.

    Returns
    -------
    str
        The login/signup page of the app, as generated by the `templates/login` Jinja2 template.
    """
    if current_user.is_authenticated:
        return redirect(url_for("feed"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("feed")
        return redirect(next_page)
    return render_template("login.html", title="Log In", form=form)


@flask_server.route("/feed")
@login_required
def feed():
    """ The controller to handle incoming GET requests to the root and `/index` URLs of the Flask web server.

    1. Uses the [`@login_required decorator`](https://flask-login.readthedocs.io/en/latest/#flask_login.login_required) imported from the [Flask-Login](https://flask-login.readthedocs.io/en/latest/) extension to ensure that the current user is logged-in  before responding with the actual view. 
        a. If the user is not logged in, the [LoginManager.unauthorized() callback function](https://flask-login.readthedocs.io/en/latest/#flask_login.LoginManager.unauthorized) is fired, which redirects the user to the `/login` controller.
            - Results from a GET request from an unauthenticated user.
            - This is equivalent to making the following the first commands run by the controller:
                ```
                if not current_user.is_authenticated:
                    return current_app.login_manager.unauthorized()
                ```

        b. If the user is logged in, then the controller retrieves their `user_id` from the current [request context](https://flask.palletsprojects.com/en/1.1.x/reqcontext/). 
            - [`Sessions`](https://flask.palletsprojects.com/en/1.1.x/api/?highlight=session#sessions) make it possible to persist data between requests (like the `user_id` of the user making requests),even though HTTP is a stateless protocol.
            - Results from a GET request from an authenticated user.

    2. Fetches the user's posts by making an HTTP request to the remote SQL database for all posts associated with their `user_id` (which is also the primary key of the Users table).

    3. Stores the user's posts in a Python data structure, and makes them available to the `templates/index` view by passing it and the view as parameters to Flask's built-in [`render_template()`](https://flask.palletsprojects.com/en/1.1.x/api/?highlight=render_template#flask.render_template) function.

    4. The `templates/index` view uses [Jinja2 HTML templating](https://jinja.palletsprojects.com/en/2.10.x/) to display:
        - A list of posts created by the logged-in user with links to create/update/delete.
        - Links to view the pitcher dashboard and logout of the app.

    Parameters
    ----------
    param1 : string
        The URL being requested by the client.

    Returns
    -------
    str
        The index page of the app, as generated by the `templates/index` Jinja2 template.
    """
    page = request.args.get("page", 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, flask_server.config["POSTS_PER_PAGE"], False
    )
    next_url = url_for("feed", page=posts.next_num) if posts.has_next else None
    prev_url = url_for("feed", page=posts.prev_num) if posts.has_prev else None
    return render_template(
        "feed.html",
        title="My Feed",
        posts=posts.items,
        next_url=next_url,
        prev_url=prev_url,
    )


@flask_server.route("/logout")
def logout():
    """ The controller to handle incoming GET requests to the `/logout` URL of the Flask web server.

    1. Terminates the current user's session and redirects to the `index` route. 
        - From now on, the request context user will be an instance of the `AnonymousUserMixin` class instead of an instance of a User database object model.

    Parameters
    ----------
    param1 : string
        The first parameter is the URL being requested by the client.

    Returns
    -------
    str
        The index page of the app, as generated by the `templates/index` Jinja2 template.
    """
    logout_user()
    flash("Logged out!")
    return redirect(url_for("discover"))


@flask_server.route("/create", methods=methods)
@login_required
def create_post():
    """ The controller to handle incoming GET and POST requests to the `/create` URL of the Flask web server.
    
    1. Makes the `PostForm()` created using Flask-WTF available to the `templates/create` view by passing the view and the form as parameters to Flask's built-in `render_template()` function.
        - Results from a GET request from an authenticated user.
    
    2. If data validation occurs, then an HTTP request is made to the remote SQL database requesting that a new row is inserted into the Posts table in the SQL database.
        - There is a `one-to-many relationship` between `Users` and `Posts` because the foreign key of every row in the Post table is a `user_id` of a row from the Users table. Each user can have many posts but each post has only one user.
    
    3. The user is redirected to the `index` view.
    
    Parameters
    ----------
    param1 : string
        The first parameter is the URL being requested by the client.
        
    Returns
    -------
    str
        The create page generated by the Jinja2 template.
    """
    form = PostForm()
    time = datetime.utcnow()
    if form.validate_on_submit():
        try:
            post = Post(user_id=current_user.id, url=form.url.data, body=form.body.data)
            db.session.add(post)
            db.session.commit()
            flash("Congratulations, you have successfully created a post!")
            return redirect(url_for("index"))
        except:
            flash("Sorry, there was an error creating your post!")
            return redirect(url_for("index"))
    return render_template("create.html", title="Create Post", form=form)


@flask_server.route("/delete/<int:id>")
@login_required
def delete(id):
    """ The controller to handle incoming GET requests to the `/delete` URL of the web server.
    
    1. Queries the SQL datatbase for the post with the specified `id`. 
    
    2. If the post was created by the logged-in user, then a row is deleted from the Posts table in the SQL database.
        
    4. The user is redirected to the `index` view. 
    
    Parameters
    ----------
    param1 : string
        The first parameter is the URL being requested by the client.
        
    Returns
    -------
    str
        The index page generated by the Jinja2 template.
    """
    post_to_delete = Post.query.get_or_404(id)
    if post_to_delete.user_id is not current_user.id:
        flash("Sorry, you are not authorized to delete that post!")
        return redirect(url_for("index"))
    try:
        db.session.delete(post_to_delete)
        db.session.commit()
        flash("Congratulations, you have successfully deleted a post!")
        return redirect(url_for("index"))
    except:
        flash("Sorry, there was an error deleting your post.")
        return redirect(url_for("index"))


@flask_server.route("/update/<int:id>", methods=methods)
def update(id):
    """ The controller to handle incoming GET and POST requests to the `/update` URL of the web server.
    
    1. Queries the SQL datatbase for the post with the specified `id`. 
    
    2. If the post was created by the logged-in user, then the controller makes the `UpdatePostForm` created using Flask-WTF available to the `templates/update` view by passing the view and the form as parameters to Flask's built-in `render_template()` function.
    
    3. If data validation occurs (i.e. post is acceptable), the row is updated in the Posts table in the SQL database. 
    
    3. The user is redirected to the `index` view.
    
    Parameters
    ----------
    param1 : string
        The first parameter is the URL being requested by the client.
        
    Returns
    -------
    str
        The update page, as generated by the `templates/update` Jinja2 template.
    """
    post_to_update = Post.query.get_or_404(id)
    if post_to_update.user_id is not current_user.id:
        flash("Sorry, you are not authorized to update that post!")
        return redirect(url_for("index"))
    form = UpdateForm()
    time = datetime.utcnow()
    if form.validate_on_submit():
        try:
            post_to_update.url = form.url.data
            post_to_update.body = form.body.data
            db.session.add(post_to_update)
            db.session.commit()
            flash("Congratulations, you have successfully updated a post!")
            return redirect(url_for("index"))
        except:
            flash("Sorry, there was an error updating your post!")
            return redirect(url_for("index"))
    return render_template(
        "update.html", title="Update Post", form=form, post=post_to_update
    )


@flask_server.route("/register", methods=methods)
def register():
    """ The controller to handle incoming GET and POST requests to the `/register` URL of the Flask web server.

    1. Checks to see if the user is already logged-in and authenticated. 
        a. If so, returns a response object that redirects the client to the '/index' route.
            - Results from a GET request from an authenticated user.

        b. If the user is not already logged-in and authenticated, makes the `RegistrationForm()` created using Flask-WTF available to the `templates/register` view by passing the view and the form as parameters to Flask's built-in `render_template()` function.
            - Results from a GET request from an unauthenticated user.

    2. If a valid username/pw/email combo is submitted, then an HTTP request is made to the remote SQL database requesting to insert a new row into the Users table. 

    4. The user is redirected to the `login` view. 

    Parameters
    ----------
    param1 : string
        The first parameter is the URL being requested by the client.

    Returns
    -------
    str
        The register page generated by the Jinja2 template.
    """
    if current_user.is_authenticated:
        return redirect(url_for("feed"))
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash("Congratulations, you are now a registered user!")
            return redirect(url_for("login"))
        except:
            flash("Sorry, there was an error registering your account!")
            return redirect(url_for("register"))
    return render_template("register.html", title="Register", form=form)


@flask_server.route("/reset-pw", methods=methods)
@login_required
def reset_pw():
    """ The controller to handle incoming GET and POST requests to the `/reset-pw` URL of the Flask web server.

    1. Checks to see if the user is already logged-in and authenticated. 
        a. If the user is already logged-in and authenticated, makes the `ResetPWForm()` created using Flask-WTF available to the `templates/reset-pw` view by passing the view and the form as parameters to Flask's built-in `render_template()` function.
            - Results from a GET request from an authenticated user.

        b. If the user is not already logged-in and authenticated, they are redirected to the `login` route.

    2. If a valid current_pw/new_pw combo is submitted, then an HTTP request is made to the remote SQL database requesting to update a row in the Users table. 

    4. The user is logged out and redirected to the `login` view. 

    Parameters
    ----------
    param1 : string
        The first parameter is the URL being requested by the client.

    Returns
    -------
    str
        The login page, as generated by the `templates/login` Jinja2 template.
    """
    form = ResetPWForm()
    if form.validate_on_submit():
        try:
            user = current_user
            user.set_password(form.new_password.data)
            db.session.add(user)
            db.session.commit()
            flash("Congratulations, you have updated your password!")
            logout_user()
            return redirect(url_for("login"))
        except:
            flash("Sorry, there was an error updating your password!")
            return redirect(url_for("reset-pw"))
    return render_template("reset-pw.html", title="Reset Password", form=form)


@flask_server.route("/user/<username>")
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get("page", 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, flask_server.config["POSTS_PER_PAGE"], False
    )
    next_url = (
        url_for(
            "user", title="User Profile", username=user.username, page=posts.next_num
        )
        if posts.has_next
        else None
    )
    prev_url = (
        url_for(
            "user", title="User Profile", username=user.username, page=posts.prev_num
        )
        if posts.has_prev
        else None
    )
    return render_template(
        "user.html",
        title="User Profile",
        user=user,
        posts=posts.items,
        next_url=next_url,
        prev_url=prev_url,
    )


@flask_server.route("/user/<username>/following")
@login_required
def following(username):
    user = User.query.filter_by(username=username).first_or_404()
    usernames = user.followed_users()
    return render_template(
        "following.html", title="Following", user=user, usernames=usernames
    )


@flask_server.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Your changes have been saved.")
        return redirect("/user/" + current_user.username)
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template("edit_profile.html", title="Edit Profile", form=form)


@flask_server.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()


@flask_server.route("/follow/<username>")
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash("User {} not found.".format(username))
        return redirect(url_for("feed"))
    if user == current_user:
        flash("You cannot follow yourself!")
        return redirect(url_for("user", username=username))
    current_user.follow(user)
    db.session.commit()
    flash("You are following {}!".format(username))
    return redirect(url_for("user", title="User Profile", username=username))


@flask_server.route("/unfollow/<username>")
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash("User {} not found.".format(username))
        return redirect(url_for("feed"))
    if user == current_user:
        flash("You cannot unfollow yourself!")
        return redirect(url_for("user", title="User Profile", username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash("You are not following {}.".format(username))
    return redirect(url_for("user", title="User Profile", username=username))
