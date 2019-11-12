from tests.base import BaseTestCase

from app.extensions import db
from app.models import User, Photo, Comment, Tag, Role


class CLITestCase(BaseTestCase):

    def setUp(self):
        super(CLITestCase, self).setUp()
        db.drop_all()

    def test_initdb_command(self):
        result = self.runner.invoke(args=['initdb'])
        self.assertIn("Initialized database", result.output)

    def test_initdb_command_with_drop(self):
        result = self.runner.invoke(args=['initdb', '--drop'], input='y\n')  # \n is enter
        self.assertIn("This will delete the current database, continue?", result.output)
        self.assertIn("Dropped tables", result.output)

    def test_init_command(self):
        result = self.runner.invoke(args=['init'], input='y\n')  # \n is enter
        self.assertIn("Initializing the database..", result.output)
        self.assertIn("Initializing the permissions and roles", result.output)
        self.assertIn("Done", result.output)
        self.assertEqual(4, Role.query.count())

    def test_forge_command(self):
        # to be added
        pass

    def test_forge_command_with_count(self):
        result = self.runner.invoke(args=['forge', '--user', '5', '--follow', '10',
                                          '--photo', '10', '--tag', '10', '--collection', '10',
                                          '--comment', '10'])
        self.assertIn('Initializing the roles and permissions...', result.output)
        self.assertIn('Generating fake administrator', result.output)
        self.assertIn('Generating 5 fake users', result.output)
        self.assertEqual(6, User.query.count())

        self.assertIn('Generating 10 fake follows', result.output)

        self.assertIn('Generating 10 fake photos', result.output)
        self.assertEqual(10, Photo.query.count())

        self.assertIn('Generating 10 fake tags', result.output)
        self.assertEqual(10, Tag.query.count())

        self.assertIn('Generating 10 fake collections', result.output)

        self.assertIn('Generating 10 fake comments', result.output)
        self.assertEqual(10, Comment.query.count())
        
        self.assertIn('Done', result.output)