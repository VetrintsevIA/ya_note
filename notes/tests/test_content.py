from django.test import TestCase
from django.urls import reverse
from notes.models import Note
from notes.forms import NoteForm
from django.contrib.auth import get_user_model

User = get_user_model()


class TestNotesContent(TestCase):
    """Тесты для проверки содержимого страниц приложения заметок."""

    @classmethod
    def setUpTestData(cls):
        """Установка данные для тестов создание пользователей."""
        cls.user1 = User.objects.create_user(username="User1",
                                             password="password1")
        cls.user2 = User.objects.create_user(username="User2",
                                             password="password2")

        cls.note1_user1 = Note.objects.create(
            title="Заметка 1 пользователя 1",
            text="Текст заметки 1", slug="note1-user1", author=cls.user1
        )
        cls.note2_user1 = Note.objects.create(
            title="Заметка 2 пользователя 1",
            text="Текст заметки 2", slug="note2-user1", author=cls.user1
        )
        cls.note1_user2 = Note.objects.create(
            title="Заметка 1 пользователя 2",
            text="Текст заметки 3", slug="note1-user2", author=cls.user2
        )

        cls.notes_list_url = reverse("notes:list")
        cls.add_note_url = reverse("notes:add")
        cls.edit_note_url = reverse("notes:edit",
                                    kwargs={"slug": cls.note1_user1.slug})

    def test_note_in_object_list(self):
        """Проверяем, что заметка передаётся на страницу со списком заметок."""
        self.client.force_login(self.user1)
        response = self.client.get(self.notes_list_url)
        object_list = response.context["object_list"]
        self.assertIn(self.note1_user1, object_list)
        self.assertIn(self.note2_user1, object_list)

    def test_note_exclusion_from_other_user(self):
        """Проверяем, что в список заметок одного пользователя\
            не попадают заметки другого."""
        self.client.force_login(self.user1)
        response = self.client.get(self.notes_list_url)
        object_list = response.context["object_list"]
        self.assertNotIn(self.note1_user2, object_list)

    def test_form_in_add_note_page(self):
        """Проверяем, что на странице добавления заметки передаётся форма."""
        self.client.force_login(self.user1)
        response = self.client.get(self.add_note_url)
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], NoteForm)

    def test_form_in_edit_note_page(self):
        """Проверяем, что на странице редактирования\
            заметки передаётся форма."""
        self.client.force_login(self.user1)
        response = self.client.get(self.edit_note_url)
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], NoteForm)
