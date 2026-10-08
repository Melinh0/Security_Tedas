from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from . import encryption
from .models import AuditLog

User = get_user_model()


class BaseTestCase(TestCase):
    def setUp(self):
        super().setUp()
        cache.clear()


class EncryptionAtRestTests(BaseTestCase):
    def test_user_pii_is_encrypted_in_database(self):
        User.objects.create_user(username='alice', password='SenhaForte123',
                                 email='alice@example.com', role='user')

        raw = User.objects.filter(
            username_index=encryption.blind_index('alice')
        ).values('username', 'email', 'role').get()

        self.assertNotIn('alice', raw['username'])
        self.assertNotIn('alice@example.com', raw['email'])
        self.assertNotIn('user', raw['role'])
        self.assertTrue(raw['username'].startswith('gAAAAA'))

        user = User.objects.get(username_index=encryption.blind_index('alice'))
        self.assertEqual(user.get_username(), 'alice')
        self.assertEqual(user.email_plain, 'alice@example.com')
        self.assertEqual(user.role_plain, 'user')

    def test_wrong_key_cannot_decrypt(self):
        User.objects.create_user(username='bob', password='SenhaForte123')
        user = User.objects.get(username_index=encryption.blind_index('bob'))
        self.assertNotEqual(user.username, 'bob')

    def test_blind_index_lookup_and_login(self):
        User.objects.create_user(username='carol', password='SenhaForte123')
        client = APIClient()
        response = client.post(reverse('login'), {
            'username': 'carol', 'password': 'SenhaForte123',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.json())


class AuthFlowTests(BaseTestCase):
    def test_register_then_login(self):
        client = APIClient()
        response = client.post(reverse('register'), {
            'username': 'dave', 'password': 'SenhaForte123', 'role': 'user',
        }, format='json')
        self.assertEqual(response.status_code, 201)

        response = client.post(reverse('login'), {
            'username': 'dave', 'password': 'SenhaForte123',
        }, format='json')
        self.assertEqual(response.status_code, 200)

    def test_register_cannot_escalate_to_admin(self):
        client = APIClient()
        response = client.post(reverse('register'), {
            'username': 'mallory', 'password': 'SenhaForte123', 'role': 'admin',
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_weak_password_rejected(self):
        client = APIClient()
        response = client.post(reverse('register'), {
            'username': 'weak', 'password': '12345678',
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_invalid_login_creates_audit_log(self):
        client = APIClient()
        client.post(reverse('login'), {
            'username': 'ghost', 'password': 'SenhaForte123',
        }, format='json')
        log = AuditLog.objects.filter(action='LOGIN_FAILED').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.subject_plain, 'ghost')
        self.assertNotIn('ghost', log.subject_enc)


class RBACTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_user(username='root', password='SenhaForte123',
                                              role='admin')
        self.user = User.objects.create_user(username='member', password='SenhaForte123',
                                             role='user')
        self.public = User.objects.create_user(username='visitor', password='SenhaForte123',
                                               role='public')
        self.client = APIClient()

    def auth(self, user):
        response = self.client.post(reverse('login'), {
            'username': user.get_username(), 'password': 'SenhaForte123',
        }, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.json()["access"]}')

    def test_users_endpoint_requires_admin(self):
        self.auth(self.user)
        response = self.client.get(reverse('users'))
        self.assertEqual(response.status_code, 403)

        self.auth(self.admin)
        response = self.client.get(reverse('users'))
        self.assertEqual(response.status_code, 200)

    def test_reveal_requires_admin_and_is_audited(self):
        self.auth(self.user)
        response = self.client.get(reverse('reveal', args=[self.admin.pk]))
        self.assertEqual(response.status_code, 403)

        self.auth(self.admin)
        response = self.client.get(reverse('reveal', args=[self.user.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['username'], 'member')
        self.assertTrue(
            AuditLog.objects.filter(action='REVEAL_PII', user=self.admin).exists()
        )

    def test_visible_users_excludes_admin(self):
        self.auth(self.user)
        response = self.client.get(reverse('visible-users'))
        self.assertEqual(response.status_code, 200)
        usernames = [u['username'] for u in response.json()['results']]
        self.assertIn('member', usernames)
        self.assertIn('visitor', usernames)
        self.assertNotIn('root', usernames)

    def test_public_endpoint_requires_authentication(self):
        response = self.client.get(reverse('public'))
        self.assertEqual(response.status_code, 401)

    def test_audit_logs_endpoint_requires_admin(self):
        self.auth(self.user)
        response = self.client.get(reverse('audit-logs'))
        self.assertEqual(response.status_code, 403)

        self.auth(self.admin)
        response = self.client.get(reverse('audit-logs'))
        self.assertEqual(response.status_code, 200)


class AuditMiddlewareTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username='auditor', password='SenhaForte123')
        self.client = APIClient()

    def test_api_access_is_logged(self):
        response = self.client.post(reverse('login'), {
            'username': 'auditor', 'password': 'SenhaForte123',
        }, format='json')
        token = response.json()['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        self.client.get(reverse('me'))
        self.assertTrue(
            AuditLog.objects.filter(action='ACCESS', path='/api/me/').exists()
        )

    def test_denied_access_is_logged(self):
        self.client.get(reverse('audit-logs'))
        self.assertTrue(AuditLog.objects.filter(action='ACCESS_DENIED').exists())


class RateLimitTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def test_login_throttle(self):
        for _ in range(5):
            self.client.post(reverse('login'), {
                'username': 'nobody', 'password': 'SenhaForte123',
            }, format='json')
        response = self.client.post(reverse('login'), {
            'username': 'nobody', 'password': 'SenhaForte123',
        }, format='json')
        self.assertEqual(response.status_code, 429)


class UploadSanitizationTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username='uploader', password='SenhaForte123')
        self.client = APIClient()
        response = self.client.post(reverse('login'), {
            'username': 'uploader', 'password': 'SenhaForte123',
        }, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.json()["access"]}')

    @override_settings(MEDIA_ROOT='/tmp/test_media_securitytedas')
    def test_valid_image_upload(self):
        from PIL import Image
        buffer = BytesIO()
        Image.new('RGB', (10, 10), color='red').save(buffer, format='PNG')
        upload = SimpleUploadedFile('photo.png', buffer.getvalue(), content_type='image/png')
        response = self.client.post(reverse('upload-avatar'), {'avatar': upload})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()['avatar'].endswith('.png'))

    def test_rejects_non_image_payload(self):
        upload = SimpleUploadedFile('evil.png', b'#!/bin/sh\nrm -rf /',
                                    content_type='image/png')
        response = self.client.post(reverse('upload-avatar'), {'avatar': upload})
        self.assertEqual(response.status_code, 400)
