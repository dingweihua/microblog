import os
import unittest
from datetime import datetime, timedelta

from config import _basedir
from app import app, db
from app.users.models import User, Post

class UserTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(_basedir, 'test.db')
        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_make_unique_name(self):
        user = User(name='john', email='john@sugarlady.com')
        db.session.add(user)
        db.session.commit()
        name = User.make_unique_name('john')
        self.assertEqual(name, 'john2')
        # use the new name
        user = User(name=name, email='john2@sugarlady.com')
        db.session.add(user)
        db.session.commit()
        new_name = User.make_unique_name('john')
        self.assertEqual(new_name, 'john3')

    def test_follow(self):
        user1 = User(name='mark', email='mark@sugarlady.com')
        user2 = User(name='rudy', email='rudy@sugarlady.com')
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()

        self.assertEqual(user1.is_following(user2), False)
        self.assertEqual(user1.unfollow(user2), None)
        user1 = user1.follow(user2)
        db.session.add(user1)
        db.session.commit()
        # user1 has already followed user2
        self.assertEqual(user1.follow(user2), None)
        self.assertEqual(user1.followed.count(), 1)
        self.assertEqual(user1.followed.first().name, 'rudy')
        self.assertEqual(user2.followers.count(), 1)
        self.assertEqual(user2.followers.first().name, 'mark')

        user1 = user1.unfollow(user2)
        db.session.add(user1)
        db.session.commit()
        self.assertEqual(user1.unfollow(user2), None)
        self.assertEqual(user1.is_following(user2), False)
        self.assertEqual(user1.followed.count(), 0)
        self.assertEqual(user2.followers.count(), 0)

    def test_followed_posts(self):
        # create 4 users
        user1 = User(name='mark', email='mark@sugarlady.com')
        user2 = User(name='rudy', email='rudy@sugarlady.com')
        user3 = User(name='jack', email='jack@sugarlady.com')
        user4 = User(name='william', email='william@sugarlady.com')
        db.session.add(user1)
        db.session.add(user2)
        db.session.add(user3)
        db.session.add(user4)

        # create 4 posts
        utcnow = datetime.utcnow()
        post1 = Post(body='post from mark', author=user1, timestamp=utcnow + timedelta(seconds=1))
        post2 = Post(body='post from rudy', author=user2, timestamp=utcnow + timedelta(seconds=2))
        post3 = Post(body='post from jack', author=user3, timestamp=utcnow + timedelta(seconds=3))
        post4 = Post(body='post from william', author=user4, timestamp=utcnow + timedelta(seconds=4))
        db.session.add(post1)
        db.session.add(post2)
        db.session.add(post3)
        db.session.add(post4)
        db.session.commit()

        # setup the followers
        user1 = user1.follow(user2)
        user2 = user2.follow(user3)
        user2 = user2.follow(user4)
        user3 = user3.follow(user1)
        user3 = user3.follow(user3)
        user4 = user4.follow(user1)
        user4 = user4.follow(user3)
        user4 = user4.follow(user4)
        db.session.add(user1)
        db.session.add(user2)
        db.session.add(user3)
        db.session.add(user4)
        db.session.commit()

        f1 = user1.followed_posts()
        f2 = user2.followed_posts()
        f3 = user3.followed_posts()
        f4 = user4.followed_posts()
        self.assertEqual(f1.count(), 1)
        self.assertEqual(f2.count(), 2)
        self.assertEqual(f3.count(), 2)
        self.assertEqual(f4.count(), 3)
        self.assertEqual(f1.all(), [post2])
        self.assertEqual(f2.all(), [post4, post3])
        self.assertEqual(f3.all(), [post3, post1])
        self.assertEqual(f4.all(), [post4, post3, post1])


if __name__ == '__main__':
    unittest.main()
