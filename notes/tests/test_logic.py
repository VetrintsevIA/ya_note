from http import HTTPStatus
from django.test import Client, TestCase
from django.urls import reverse
from notes.models import Note
from django.contrib.auth import get_user_model
from pytils.translit import slugify

User = get_user_model()


class TestNoteCreation(TestCase):
    """Тесты для создания заметок."""

    @classmethod
    def setUpTestData(cls):
        """Создание пользователя."""
        cls.user = User.objects.create_user(username="User",
                                            password="password")
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.add_note_url = reverse("notes:add")
        cls.form_data = {"title": "Новая заметка", "text": "Текст заметки"}

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        response = self.client.post(self.add_note_url, data=self.form_data)
        login_url = reverse('users:login')
        expected_redirect = f"{login_url}?next={self.add_note_url}"
        self.assertRedirects(response, expected_redirect)
        self.assertEqual(Note.objects.count(), 0)

    def test_user_can_create_note(self):
        """Залогиненный пользователь может создать заметку."""
        response = self.auth_client.post(self.add_note_url,
                                         data=self.form_data)
        self.assertEqual(Note.objects.count(), 1)
        note = Note.objects.get()
        self.assertEqual(note.title, self.form_data["title"])
        self.assertEqual(note.text, self.form_data["text"])
        self.assertEqual(note.author, self.user)
        self.assertRedirects(response, reverse("notes:success"))

    def test_cant_create_note_with_duplicate_slug(self):
        """Невозможно создать две заметки с одинаковым slug."""
        Note.objects.create(
            title="Уникальная заметка",
            text="Текст",
            slug="unique-slug",
            author=self.user,
        )
        duplicate_slug_data = {"title": "Заметка 2",
                               "text": "Текст", "slug": "unique-slug"}
        response = self.auth_client.post(self.add_note_url,
                                         data=duplicate_slug_data)
        self.assertEqual(Note.objects.count(), 1)
        # Проверяем наличие ошибки в списке ошибок формы
        errors = response.context["form"].errors["slug"]
        self.assertIn("unique-slug - такой slug уже существует", errors[0])

    def test_slug_generated_if_not_provided(self):
        """Если slug не указан, он формируется автоматически."""
        self.auth_client.post(self.add_note_url, data=self.form_data)
        note = Note.objects.get()
        expected_slug = slugify(self.form_data["title"])[:100]
        self.assertEqual(note.slug, expected_slug)


class TestNoteEditDelete(TestCase):
    """Тесты для редактирования и удаления заметок."""

    @classmethod
    def setUpTestData(cls):
        """Создание двух пользователей."""
        cls.author = User.objects.create_user(username="Author",
                                              password="password1")
        cls.reader = User.objects.create_user(username="Reader",
                                              password="password2")

        cls.note = Note.objects.create(
            title="Заметка автора", text="Текст заметки", slug="author-note",
            author=cls.author
        )

        cls.edit_url = reverse("notes:edit", kwargs={"slug": cls.note.slug})
        cls.delete_url = reverse("notes:delete",
                                 kwargs={"slug": cls.note.slug})
        cls.notes_list_url = reverse("notes:list")

        cls.form_data = {"title": "Обновлённая заметка",
                         "text": "Обновлённый текст"}

    def setUp(self):
        """Настраиваем клиентов для авторизованных пользователей."""
        self.author_client = Client()
        self.author_client.force_login(self.author)

        self.reader_client = Client()
        self.reader_client.force_login(self.reader)

    def test_author_can_edit_note(self):
        """Автор может редактировать свою заметку."""
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, reverse("notes:success"))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.form_data["title"])
        self.assertEqual(self.note.text, self.form_data["text"])

    def test_reader_cant_edit_note(self):
        """Читатель не может редактировать чужую заметку."""
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertNotEqual(self.note.title, self.form_data["title"])
        self.assertNotEqual(self.note.text, self.form_data["text"])

    def test_author_can_delete_note(self):
        """Автор может удалить свою заметку."""
        response = self.author_client.post(self.delete_url)
        self.assertRedirects(response, reverse("notes:success"))
        self.assertEqual(Note.objects.count(), 0)

    def test_reader_cant_delete_note(self):
        """Читатель не может удалить чужую заметку."""
        response = self.reader_client.post(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)
