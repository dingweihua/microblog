# -*- coding: utf-8 -*-

from datetime import datetime
from flask import Blueprint, request, render_template, flash, g, session, redirect, url_for
from werkzeug import check_password_hash, generate_password_hash
from flask.ext.babel import gettext

from app import db, babel
from app.emails import follower_notification
from app.users.forms import RegisterForm, LoginForm, EditForm, PostForm, SearchForm
from app.users.models import User, Post
from app.users.decorators import requires_login
from config import POSTS_PER_PAGE, MAX_SEARCH_RESULTS, LANGUAGES


mod = Blueprint('users', __name__, url_prefix='/users')


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(LANGUAGES.keys())


@mod.route('/<name>/', methods=['GET', 'POST'])
@mod.route('/<name>/<int:page>/', methods=['GET', 'POST'])
@requires_login
def home(name, page=1):
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, timestamp=datetime.utcnow(), author=g.user)
        db.session.add(post)
        db.session.commit()
        flash(gettext('Your post is live now!'))
        redirect(url_for('users.home', name=name, page=page))
    user = User.query.filter_by(name=name).first()
    posts = user.followed_posts().paginate(page, POSTS_PER_PAGE, False) if user else []
    if user:
        return render_template('users/profile.html', user=user, form=form, posts=posts)
    else:
        return render_template('404.html')


@mod.before_request
def before_request():
    """
    pull user's profile from the database before every request are treated
    """
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])
        if g.user:
            g.user.last_seen = datetime.utcnow()
            db.session.add(g.user)
            db.session.commit()
            g.search_form = SearchForm()
    g.locale = get_locale()


@mod.route('/login/', methods=['GET', 'POST'])
def login():
    """
    Login form
    """
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('users.home', name=g.user.name))
    form = LoginForm()
    # make sure data are valid, but doesn't validate password is right
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # we use werkzeug to validate user's password
        if user and check_password_hash(user.password, form.password.data):
            # the session can't be modified as it's signed, 
            # it's a safe place to store the user id
            session['user_id'] = user.id
            flash(gettext('Welcome %(user_name)s', user_name=user.name))
            return redirect(url_for('users.home', name=user.name))
        flash(gettext('Wrong email or password'))
    return render_template("users/login.html", form=form)


@mod.route('/register/', methods=['GET', 'POST'])
def register():
    """
    Registration Form
    """
    form = RegisterForm()
    if form.validate_on_submit():
        # get the unique name
        form.name.data = User.make_valid_name(form.name.data)
        form.name.data = User.make_unique_name(form.name.data)
        # create an user instance not yet stored in the database
        user = User(name=form.name.data, email=form.email.data, \
            password=generate_password_hash(form.password.data))
        # Insert the record in our database and commit it
        db.session.add(user)
        db.session.commit()
        # make the user follow himself/herself
        db.session.add(user.follow(user))
        db.session.commit(user)
       
        # Log the user in, as he now has an id
        session['user_id'] = user.id
       
        # flash will display a message to the user
        flash(gettext('Thanks for registering'))
        # redirect user to the 'home' method of the user module.
        return redirect(url_for('users.home', name=user.name))
    return render_template("users/register.html", form=form)


@mod.route('/logout/')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('users.login'))


@mod.route('/search/', methods=['POST'])
@requires_login
def search():
    if not g.search_form.validate_on_submit():
        return redirect(url_for('users.home', name=g.user.name))
    return redirect(url_for('users.search_results', query=g.search_form.search.data))


@mod.route('/search_results/<query>')
@requires_login
def search_results(query):
    results = Post.query.whoosh_search(query, MAX_SEARCH_RESULTS).all()
    return render_template('search_results.html', query=query, results=results)


@mod.route('/edit/', methods=['GET', 'POST'])
@requires_login
def edit():
    form = EditForm(g.user.name)
    if form.validate_on_submit():
        g.user.name = form.name.data
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()
        flash(gettext('Your changes have been saved.'))
        return redirect(url_for('users.home', name=g.user.name))
    else:
        form.name.data = g.user.name
        form.about_me.data = g.user.about_me
    return render_template('users/edit.html', form=form)


@mod.route('/follow/<name>')
@requires_login
def follow(name):
    user = User.query.filter_by(name=name).first()
    if not user:
        flash(gettext('User %(name)s not found.', name=name))
        return redirect(url_for('users.home', name=user.name))
    if user == g.user:
        flash(gettext('You can\'t follow yourself.'))
        return redirect(url_for('users.home', name=user.name))
    u = g.user.follow(user)
    if u is None:
        flash(gettext('Cannot follow %(name)s.', name=name))
        return redirect(url_for('users.home', name=user.name))
    db.session.add(u)
    db.session.commit()
    flash(gettext('You are now following %(name)s.', name=name))
    follower_notification(user, g.user)
    return redirect(url_for('users.home', name=user.name))


@mod.route('/unfollow/<name>')
@requires_login
def unfollow(name):
    user = User.query.filter_by(name=name).first()
    if not user:
        flash(gettext('User %(name)s not found.', name=name))
        return redirect(url_for('users.home', name=user.name))
    if user == g.user:
        flash(gettext('You can\'t unfollow yourself.'))
        return redirect(url_for('users.home', name=user.name))
    u = g.user.unfollow(user)
    if u is None:
        flash(gettext('Cannot unfollow %(name)s.', name=name))
        return redirect(url_for('users.home', name=user.name))
    db.session.add(u)
    db.session.commit()
    flash(gettext('You have stopped following %(name)s.', name=name))
    return redirect(url_for('users.home', name=user.name))
