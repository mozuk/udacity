from app import app, login_session, db_session
from sqlalchemy_imageattach.entity import store_context
from flask import redirect, request, render_template, url_for, flash, jsonify
from database_setup import Category, CategoryItem, local_storage
from app.category import *


# Create a new item
@app.route('/category/<int:category_id>/item/new/',
           methods=['GET', 'POST'])
def new_item(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    category = db_session.query(Category).filter_by(id=category_id).one()
    all_categories = db_session.query(Category).order_by(asc(Category.name))
    if request.method == 'POST':
        try:
                photo = request.files.get('photo')
                new_item = CategoryItem(name=request.form['name'],
                                        description=request.
                                        form['description'],
                                        category_id=category_id)
                with store_context(local_storage):
                    new_item.picture.from_file(photo)
                    new_item.picture.generate_thumbnail(width=300)
                    db_session.add(new_item)
                    db_session.commit()
        except:
            flash("Item creation failed")
            return redirect(url_for('show_items',
                                    category_id=category_id,
                                    categories=all_categories))
        flash('New %s Item Successfully Created' % (new_item.name))
        return redirect(url_for('show_items',
                                category_id=category_id,
                                categories=all_categories))
    else:
        return render_template('new_item.html',
                               category_id=category_id,
                               categories=all_categories)


# Edit an item
@app.route('/category/<int:category_id>/item/<int:item_id>/edit',
           methods=['GET', 'POST'])
def edit_item(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    edited_item = db_session.query(CategoryItem).filter_by(id=item_id).one()
    # confirm category exists
    db_session.query(Category).filter_by(id=category_id).one()
    print edited_item.category.name
    if request.method == 'POST':
        if request.form['name']:
            edited_item.name = request.form['name']
        if request.form['description']:
            edited_item.description = request.form['description']
        if request.form['category']:
            edited_item.category = db_session.query(Category).filter_by(
                id=request.form['category']).one()
            print edited_item.category.name
        photo = request.files.get('photo')
        if photo:
            with store_context(local_storage):
                    edited_item.picture.from_file(photo)
                    edited_item.picture.generate_thumbnail(width=300)
                    db_session.add(edited_item)
                    db_session.commit()
        else:
            db_session.add(edited_item)
            db_session.commit()
        flash('Item Successfully Edited')
        return redirect(url_for('show_items',
                                category_id=category_id))
    else:
        all_categories = db_session.query(Category).order_by(asc(Category.name))
        return render_template('edit_item.html',
                               category_id=category_id,
                               item_id=item_id,
                               item=edited_item,
                               categories=all_categories)


# Delete an item
@app.route('/category/<int:category_id>/item/<int:item_id>/delete',
           methods=['GET', 'POST'])
def delete_item(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    db_session.query(Category).filter_by(id=category_id).one()
    delete_me = db_session.query(CategoryItem).filter_by(id=item_id).one()
    all_categories = db_session.query(Category).order_by(asc(Category.name))
    if request.method == 'POST':
        with store_context(local_storage):
            db_session.delete(delete_me)
            db_session.commit()
            flash('item Item Successfully Deleted')
            return redirect(url_for('show_items',
                                    category_id=category_id,
                                    categories=all_categories))
    else:
        return render_template('delete_item.html', item=delete_me)


# json dump of item
@app.route('/category/<int:category_id>/item/<int:item_id>/json')
def item_json(category_id, item_id):
    # confirm item exists
    item = db_session.query(CategoryItem).filter_by(id=item_id).one()
    return jsonify(item=item.serialize)


# display single item view
@app.route('/category/<int:category_id>/item/<int:item_id>')
def single_item(category_id, item_id):
    # confirm item exists
    item = db_session.query(CategoryItem).filter_by(id=item_id).one()
    category = db_session.query(Category).filter_by(id=category_id).one()
    with store_context(local_storage):
        return render_template('single_item.html',
                               category_id=category_id,
                               item=item,
                               categories=db_session.
                               query(Category).order_by(asc(Category.name)),
                               username=login_session['username'])
