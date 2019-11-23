from flask import jsonify

from flask import Blueprint, redirect, request, url_for, flash
from flask_login import (current_user, login_required)
from sqlalchemy import and_

from monolith.database import db, Reaction, ReactionCatalogue, Counter

reactions = Blueprint('reactions', __name__)


@reactions.route('/reactions/story_id', methods=['GET'])
def _get_reactions(story_id):

    all_reactions = Reaction.query.filter(Reaction.story_id == story_id).order_by(Reaction.reaction_type_id).all()

    return jsonify(all_reactions)


@reactions.route('/reactions/counters/story_id', methods=['GET'])
def _get_counters(story_id):

    all_counter = Counter.query.filter(Counter.story_id == story_id).order_by(Reaction.reaction_type_id).all()

    return jsonify(all_counter)


@reactions.route('/reactions/new', methods=['POST'])
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
    return

@reactions.route('/reactions/react', methods=['POST'])
@login_required
def _reaction():
    story_id = request.args['story_id']
    reaction_caption = request.args['reaction_caption']

    # Retrieve all reactions with a specific user_id ad story_id
    old_reaction = Reaction.query.filter(and_(Reaction.reactor_id == current_user.id,
                                              Reaction.story_id == story_id,
                                              Reaction.marked != 2)).first()

    # Retrieve the id of the reaction
    reaction_type_id = ReactionCatalogue.query.filter_by(reaction_caption=reaction_caption).first().reaction_id

    # Retrieve if present the user's last reaction about the same story
    if old_reaction is None:
        new_reaction = Reaction()
        new_reaction.reactor_id = current_user.id
        new_reaction.story_id = story_id
        new_reaction.reaction_type_id = reaction_type_id
        new_reaction.marked = 0
        db.session.add(new_reaction)
    else:
        if old_reaction.reaction_type_id == reaction_type_id:
            reaction = Reaction.query.filter_by(reactor_id=current_user.id, story_id=story_id).first()

            if reaction.marked == 0:
                Reaction.query.filter_by(reactor_id=current_user.id, story_id=story_id).delete()

            db.session.commit()
            flash('Reaction successfully deleted!')
            return redirect(url_for('stories._stories'))
        else:

            if old_reaction.marked == 0:
                old_reaction.reaction_type_id = reaction_type_id
            elif old_reaction.marked == 1:
                old_reaction.marked = 2
                new_reaction = Reaction()
                new_reaction.reactor_id = current_user.id
                new_reaction.story_id = story_id
                new_reaction.marked = 0
                new_reaction.reaction_type_id = reaction_type_id
                db.session.add(new_reaction)
    db.session.commit()

    return redirect(url_for('stories._stories'))
