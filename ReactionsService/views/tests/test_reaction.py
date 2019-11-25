import datetime
import json

import flask_testing

from ReactionsService.app import create_app
from ReactionsService.database import db, Reaction
from ReactionsService.urls import TEST_DB


class TestReaction(flask_testing.TestCase):
    app = None

    def create_app(self):
        global app
        app = create_app(database=TEST_DB)
        return app

    # def setUp(self) -> None:
    #     with app.app_context():

    def assertDescription(self, reply, expected_description):
        body = json.loads(str(reply.data, 'utf8'))
        self.assertEqual(body['description'], expected_description)

    def test_reaction(self):
        len_to_be_deleted_reactions = len(Reaction.query.filter(Reaction.story_id == '1',
                                                                Reaction.reactor_id == 1,
                                                                Reaction.marked == 2).all())

        data = {
            'story_id': 1,
            'current_user': 1,
            'reaction_caption': 'like',
        }
        self.client.post('/react', json=data)

        unmarked_reactions = Reaction.query.filter(Reaction.story_id == '1',
                                                   Reaction.reactor_id == 1,
                                                   Reaction.marked == 0).all()

        self.assertEqual(len(unmarked_reactions), 1)
        self.assertEqual(unmarked_reactions[0].reaction_type_id, 1)

        data = {
            'story_id': 1,
            'current_user': 1,
            'reaction_caption': 'like',
        }

        self.client.post('/react', json=data)
        #self.assert_message_flashed('Reaction successfully deleted! (Updating ... )')

        data = {
            'story_id': 1,
            'current_user': 1,
            'reaction_caption': 'dislike',
        }

        self.client.post('/react', json=data)
        unmarked_reactions = Reaction.query.filter(Reaction.story_id == '1', Reaction.marked == 0).all()
        self.assertEqual(unmarked_reactions[0].reaction_type_id, 2)
        self.assertEqual(len(unmarked_reactions), 1)

        Reaction.query.filter(Reaction.story_id == '1', Reaction.marked == 0).first().marked = 1
        db.session.commit()

        data = {
            'story_id': 1,
            'current_user': 1,
            'reaction_caption': 'like',
        }

        self.client.post('/react', json=data)
        unmarked_reactions = Reaction.query.filter(Reaction.story_id == '1',
                                                   Reaction.reactor_id == 1,
                                                   Reaction.marked == 0).all()

        marked_reactions = Reaction.query.filter(Reaction.story_id == '1',
                                                 Reaction.reactor_id == 1,
                                                 Reaction.marked == 1).all()

        to_be_deleted_reactions = Reaction.query.filter(Reaction.story_id == '1',
                                                        Reaction.reactor_id == 1,
                                                        Reaction.marked == 2).all()

        self.assertEqual(len(unmarked_reactions), 1)
        self.assertEqual(len(marked_reactions), 0)
        self.assertEqual(len(to_be_deleted_reactions), len_to_be_deleted_reactions + 1)

    def test_reaction_1(self):
        data = {
            'story_id': 1,
            'current_user': 1,
            'reaction_caption': 'like',
        }

        self.client.post('/react', json=data)

        data = {
            'story_id': 1,
            'current_user': 1,
            'reaction_caption': 'dislike',
        }

        self.client.post('/react', json=data)

        unmarked_reactions = Reaction.query.filter(Reaction.story_id == '1',
                                                   Reaction.reactor_id == 1,
                                                   Reaction.marked == 0).all()

        self.assertEqual(len(unmarked_reactions), 1)
        self.assertEqual(unmarked_reactions[0].reaction_type_id, 2)

        Reaction.query.filter(Reaction.story_id == '1', Reaction.reactor_id == 1,
                              Reaction.marked == 0).first().marked = 1
        db.session.commit()

        data = {
            'story_id': 1,
            'current_user': 1,
            'reaction_caption': 'dislike',
        }

        self.client.post('/react', json=data)
        self.assertEqual(Reaction.query.filter(Reaction.story_id == '1', Reaction.reactor_id == 1).first().marked, 2)


    def test_get_reactions(self):
        data = {
            'story_id': 1,
            'current_user': 1,
            'reaction_caption': 'like',
        }

        self.client.post('/react', json=data)
        reply = self.client.get('/reactions/1')

        body = json.loads(reply.get_data(as_text=True))
        expected_body = [{"id":1, "reactor_id":1, "story_id":1, "reaction_type_id":2, "marked":0}]
        self.assertEqual(expected_body, body)



    #def test_get_counters(self):
    #def test_initialize_new_story(self):
