from tests.base import BaseTestCase

from app.extensions import db
from app.models import User, Photo, Comment, Tag, Role, Follow, Collect


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

    # def test_forge_command(self):
    def test_forge_zero(self):
        result = self.runner.invoke(args=['forge', '--user', '0', '--follow', '0',
                                          '--photo', '0', '--tag', '0', '--collection', '0',
                                          '--comment', '0'])
        # db.create_all()
        self.assertIn("Initializing the roles and permissions...", result.output)
        self.assertIn("Done", result.output)

        # Role.init_role()
        self.assertEqual(4, Role.query.count())
        self.assertEqual("Locked", Role.query.filter_by(name="Locked").first().name)
        self.assertEqual("User", Role.query.filter_by(name="User").first().name)
        self.assertEqual("Moderator", Role.query.filter_by(name="Moderator").first().name)
        self.assertEqual("Administrator", Role.query.filter_by(name="Administrator").first().name)

        #         click.echo("Generating fake administrator")
        self.assertIn("Generating fake administrator", result.output)
        #         fake_admin()
        self.assertEqual(6, User.query.count())

    def test_forge_user(self):
        result = self.runner.invoke(args=['forge', '--follow', '0',
                                          '--photo', '0', '--tag', '0', '--collection', '0',
                                          '--comment', '0'])
        #         click.echo("Generating %s fake users" % user)
        self.assertIn('Generating 10 fake users', result.output)
        #     @click.option('--user', default=10, help='Quantity of users, default is 10')
        #         fake_user(user)
        self.assertEqual(10+6, User.query.count())

    def test_forge_user_follow(self):
        result = self.runner.invoke(args=['forge',
                                          '--photo', '0', '--tag', '0', '--collection', '0',
                                          '--comment', '0'])

        #         click.echo("Generating %s fake follows" % follow)
        self.assertIn("Generating 30 fake follows", result.output)
        #     @click.option("--follow", default=30, help="Quantity of follows, default is 30")
        #         fake_follow(follow)
        self.assertEqual(30+16, Follow.query.count())

    def test_forge_tag(self):
        result = self.runner.invoke(args=['forge', '--user', '0', '--follow', '0',
                                          '--photo', '0', '--collection', '0',
                                          '--comment', '0'])

        #         click.echo("Generating %s fake tags" % tag)
        self.assertIn('Generating 20 fake tags', result.output)
        #     @click.option('--tag', default=20, help="Quantity of photos, default is 20")
        #         fake_tag(tag)
        self.assertLessEqual(20, Tag.query.count())
        self.assertGreaterEqual(0, Tag.query.count())

    def test_forge_photo(self):
        result = self.runner.invoke(args=['forge', '--user', '0', '--follow', '0',
                                          '--collection', '0',
                                          '--comment', '0'])
        #         click.echo("Generating %s fake photos" % photo)
        self.assertIn('Generating 30 fake photos', result.output)
        #     @click.option('--photo', default=30, help="Quantity of photos, default is 30")
        #         fake_photo(photo)
        self.assertEqual(30, Photo.query.count())

    def test_forge_comment(self):
        result = self.runner.invoke(args=['forge', '--user', '0', '--follow', '0',
                                          '--collection', '0'])
        #         click.echo("Generating %s fake comments" % comment)
        self.assertIn('Generating 100 fake comments', result.output)
        #     @click.option('--comment', default=100, help='Quantity of photos, default is 100')
        #         fake_comment(comment)
        self.assertEqual(100, Comment.query.count())

    def test_forge_collection(self):
        result = self.runner.invoke(args=['forge', '--follow', '0',
                                          '--comment', '0'])

        #         click.echo("Generating %s fake collections" % collection)
        self.assertIn('Generating 50 fake collections', result.output)
        #     @click.option('--collection', default=50, help="Quantity of collections, default is 50")
        #         fake_collect(collection)
        self.assertEqual(50, Collect.query.count())

        #         click.echo("Done")
        self.assertIn('Done', result.output)

    def test_forge_command_with_count(self):
        result = self.runner.invoke(args=['forge', '--user', '5', '--follow', '10',
                                          '--photo', '10', '--tag', '10', '--collection', '10',
                                          '--comment', '10'])
        self.assertIn('Initializing the roles and permissions...', result.output)
        self.assertIn('Generating fake administrator', result.output)
        self.assertIn('Generating 5 fake users', result.output)
        self.assertEqual(6+5, User.query.count())

        self.assertIn('Generating 10 fake follows', result.output)
        self.assertEqual(6+5+10, Follow.query.count())

        self.assertIn('Generating 10 fake photos', result.output)
        self.assertEqual(10, Photo.query.count())

        self.assertIn('Generating 10 fake tags', result.output)
        self.assertEqual(10, Tag.query.count())

        self.assertIn('Generating 10 fake collections', result.output)
        self.assertEqual(10, Collect.query.count())

        self.assertIn('Generating 10 fake comments', result.output)
        self.assertEqual(10, Comment.query.count())

        self.assertIn('Done', result.output)