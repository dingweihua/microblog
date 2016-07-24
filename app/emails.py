from flask import render_template
from flask.ext.mail import Message
from flask import current_app

from app import app, mail
from decorators import async
from config import ADMINS

@async
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject=subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    send_async_email(current_app, msg)

def follower_notification(followed, follower):
    send_email('[microblog] %s is now following you!' % follower.name,
               ADMINS[0],
               [follower.email],
               render_template('users/follower_email.txt', user=followed, follower=follower),
               render_template('users/follower_email.html', user=followed, follower=follower))
