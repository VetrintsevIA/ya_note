from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):
    """Тесты для проверки путей."""

    @classmethod
    def setUpTestData(cls):
        """Создание пользователей."""
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        cls.note = Note.objects.create(
            title='Тестовая заметка',
            text='Текст заметки',
            slug='test-note',
            author=cls.author
        )

    def test_pages_availability_anonymous(self):
        """Проверка доступности маршрутов для анонимного пользователя."""
        urls = (
            ('notes:home', None),
            ('notes:detail', {'slug': self.note.slug}),
        )
        for name, kwargs in urls:
            with self.subTest(name=name):
                url = reverse(name, kwargs=kwargs)
                response = self.client.get(url)
                if name == 'notes:detail':
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_authenticated(self):
        """Проверка доступности страниц для авторизованного пользователя."""
        self.client.force_login(self.author)
        urls = (
            ('notes:home', None),
            ('notes:add', None),
            ('notes:edit', {'slug': self.note.slug}),
            ('notes:delete', {'slug': self.note.slug}),
            ('notes:list', None),
            ('notes:success', None),
        )
        for name, kwargs in urls:
            with self.subTest(name=name):
                url = reverse(name, kwargs=kwargs)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_restrict_edit_delete_for_non_author(self):
        """Проверка ограничения доступа к редак-ю и удалению для не автора."""
        self.client.force_login(self.reader)
        urls = (
            ('notes:edit', {'slug': self.note.slug}),
            ('notes:delete', {'slug': self.note.slug}),
        )
        for name, kwargs in urls:
            with self.subTest(name=name):
                url = reverse(name, kwargs=kwargs)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_redirect_for_anonymous(self):
        """Проверка редиректа для анон-го пользователя на страницы логина."""
        login_url = reverse('users:login')
        urls = (
            ('notes:add', None),
            ('notes:edit', {'slug': self.note.slug}),
            ('notes:delete', {'slug': self.note.slug}),
            ('notes:list', None),
        )
        for name, kwargs in urls:
            with self.subTest(name=name):
                url = reverse(name, kwargs=kwargs)
                expected_redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, expected_redirect_url)
