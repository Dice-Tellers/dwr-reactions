import os

from flask import jsonify
import json

from flask import  request, jsonify
from flakon import SwaggerBlueprint
from sqlalchemy import and_

from ReactionsService.database import db, Reaction, ReactionCatalogue, Counter

YML = os.path.join(os.path.dirname(__file__), '..', 'static', 'api_reactions.yaml')
reactions = SwaggerBlueprint('reactions', '__name__', swagger_spec=YML)


@reactions.operation("getReactions")
def _get_reactions(story_id):
    all_reactions = Reaction.query.filter(Reaction.story_id == story_id).order_by(Reaction.reaction_type_id).all()

    return jsonify(all_reactions)


@reactions.operation("getCounters")
def _get_counters(story_id):
    all_counter = Counter.query.filter(Counter.story_id == story_id).order_by(Reaction.reaction_type_id).all()

    return jsonify(all_counter)

@reactions.operation("delete")
def _delete_cascade():
    story_id = request.args['story_id']

    reactions_to_delete = Reaction.query.filter(Reaction.story_id == story_id).all()
    counters_to_delete = Counter.query.filter(Counter.story_id == story_id).all()
    reactions_to_delete.delete()
    counters_to_delete.delete()
    db.session.commit()

    return jsonify(description="Deletion has been successful")

@reactions.operation("newStory")
def _initialize_new_story():
    story_id = request.args['story_id']

    all_reactions = list(db.engine.execute("SELECT reaction_id FROM reaction_catalogue ORDER BY reaction_id"))

    for reaction in all_reactions:
        new_counter = Counter()
        new_counter.reaction_type_id = reaction.id
        new_counter.story_id = story_id
        new_counter.counter = 0
        db.session.add(new_counter)

    db.session.submit()
    return jsonify(description="Counter successfully created")


@reactions.operation("react")
def _reaction():
    story_id = request.json['story_id']
    current_user = request.json['current_user']
    reaction_caption = request.json['reaction_caption']

    # Retrieve all reactions with a specific user_id ad story_id
    old_reaction = Reaction.query.filter(and_(Reaction.reactor_id == current_user,
                                              Reaction.story_id == story_id,
                                              Reaction.marked != 2)).first()

    # Retrieve the id of the reaction
    reaction_type_id = ReactionCatalogue.query.filter_by(reaction_caption=reaction_caption).first().reaction_id

    # Retrieve if present the user's last reaction about the same story
    if old_reaction is None:
        new_reaction = Reaction()
        new_reaction.reactor_id = current_user
        new_reaction.story_id = story_id
        new_reaction.reaction_type_id = reaction_type_id
        new_reaction.marked = 0
        db.session.add(new_reaction)
    else:
        if old_reaction.reaction_type_id == reaction_type_id:
            reaction = Reaction.query.filter_by(reactor_id=current_user, story_id=story_id).first()

            if reaction.marked == 0:
                Reaction.query.filter_by(reactor_id=current_user, story_id=story_id).delete()

            if reaction.marked == 1:
                reaction.marked = 2

            db.session.commit()
            return jsonify(description="Reaction successfully deleted")
        else:

            if old_reaction.marked == 0:
                old_reaction.reaction_type_id = reaction_type_id
            elif old_reaction.marked == 1:
                old_reaction.marked = 2
                new_reaction = Reaction()
                new_reaction.reactor_id = current_user
                new_reaction.story_id = story_id
                new_reaction.marked = 0
                new_reaction.reaction_type_id = reaction_type_id
                db.session.add(new_reaction)
    db.session.commit()

    return jsonify(description="Reaction successfully added")


@reactions.operation("stats")
def _reaction_stats():
    story_id = 1
    all_reactions = db.engine.execute(
        "SELECT reaction_caption FROM reaction_catalogue ORDER BY reaction_caption").fetchall()
    query = "SELECT reaction_caption, counter FROM counter c, reaction_catalogue r WHERE " \
            "reaction_type_id = reaction_id AND story_id = " + str(story_id) + " ORDER BY reaction_caption "
    story_reactions = db.engine.execute(query).fetchall()
    num_reactions = ReactionCatalogue.query.count()
    num_story_reactions = Counter.query.filter_by(story_id=story_id).join(ReactionCatalogue).count()

    # Reactions dictionary of tuples (Reaction, Counter)
    reactions_list = {}

    # Set 0 all counters for all reactions
    for r in all_reactions:
        reactions_list.update({r.reaction_caption: 0})

    # Generate tuples (reaction, counter)
    if num_reactions != 0 and num_story_reactions != 0:
        # Update all counter with correct value
        for existing_r in story_reactions:
            reactions_list.update({existing_r.reaction_caption: existing_r.counter})

    return json.dumps(dict(reactions_list))
