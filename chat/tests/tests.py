from django.test import TestCase, Client
from ..models import Message, ChatRoom, Profile
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from .. import views

User = get_user_model()


class BanTestCase(TestCase):
    def setUp(self):
        banned_user = User.objects.create(username='banned_user', password='goodpassword')
        self.factory = RequestFactory()

    def test_profile_created(self):
        url = '/register'
        form_data = {
            'username': 'some_user',
            'password': 'goodpassword',
            'password2': 'goodpassword'
        }
        request = self.factory.post(url, data=form_data)
        self.setup_request(request)
        request.user = AnonymousUser()

        response = views.register_view(request)
        user = User.objects.get(username='some_user')
        self.assertEqual(user.username, 'some_user')
