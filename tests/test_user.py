from flask import url_for

from app.models import User
from .base import BaseTestCase


class UserTestCase(BaseTestCase):

    def test_index_page(self):
