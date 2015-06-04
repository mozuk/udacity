from app import app, login_session, db_session
from database_setup import Category, CategoryItem, local_storage
from flask import render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import asc, desc
from sqlalchemy_imageattach.entity import store_context
from app.user import getUserInfo
from app.category_item import *
from flask import Response


# Helper function to return an XML response
def xml_response(data, status_code=200):
    from dicttoxml import dicttoxml

    data = dicttoxml(data)

    res = Response(data, mimetype='text/xml')
    res.status_code = status_code

    return res


# Helper function to get data for xml and json catalog dumpers
def get_category_data():
    categories = db_session.query(Category).all()
    json_dict_list = [r.serialize for r in categories]
    for index, data in enumerate(json_dict_list):
        items = db_session.query(CategoryItem) \
            .filter_by(category_id=json_dict_list[index]['id']).all()
        json_dict_list[index]['category_items'] = [i.serialize for i in items]
    return json_dict_list


# Show the whole catalog in json
@app.route('/catalog/json')
def catalog_json():
    return jsonify(categories=get_category_data())


# Show the whole catalog in xml
@app.route('/catalog/xml')
def catalog_xml():
    return xml_response(get_category_data())


# Show all categories
@app.route('/')
def show_categories():
    categories = db_session.query(Category).order_by(asc(Category.name))
    items = db_session.query(CategoryItem).order_by(desc(CategoryItem.added))
    if 'username' in login_session:
        username = login_session["username"]
    else:
        username = None
    return render_template('categories.html', categories=categories,
                           items=items,
                           username=username)


# Create a new category
@app.route('/category/new/', methods=['GET', 'POST'])
def new_category():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        new = Category(name=request.form['name'],
                       user_id=login_session['user_id'])
        db_session.add(new)
        user = getUserInfo(login_session['user_id'])
        flash('New Category %s Successfully Created by %s' %
              (new.name, user.name))
        db_session.commit()
        return redirect(url_for('show_categories',
                                username=login_session["username"],
                                categories=db_session.
                                    query(Category).order_by(asc(Category.name))))
    else:
        return render_template('new_category.html',
                               username=login_session["username"],
                               categories=db_session.
                                    query(Category).order_by(asc(Category.name)))


# Edit a category
@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
def edit_category(category_id):
    if 'username' not in login_session:
        return redirect('/login')

    edited = db_session.query(
        Category).filter_by(id=category_id).one()

    if request.method == 'POST':
        if request.form['name']:
            edited.name = request.form['name']
            flash('%s Category Successfully Edited ' % edited.name)
            return redirect(url_for('show_categories',
                                    username=login_session["username"],
                                    categories=db_session.
                                    query(Category).order_by(asc(Category.name))))
    else:
        return render_template('edit_category.html',
                               category=edited,
                               username=login_session["username"],
                               categories=db_session.
                                    query(Category).order_by(asc(Category.name)))


# Delete a category
@app.route('/category/<int:category_id>/delete/', methods=['GET', 'POST'])
def delete_category(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    delete_me = db_session.query(
        Category).filter_by(id=category_id).one()
    if delete_me.user_id != login_session['user_id']:
        return """<script>function myFunction() {
            alert('You are not authorized to edit this category.
            Please create your own category in order to edit.');
            } </script><body onload='myFunction()''>"""
    if request.method == 'POST':
        db_session.delete(delete_me)
        flash('%s Successfully Deleted' % delete_me.name)
        db_session.commit()
        return redirect(url_for('show_categories',
                                category_id=category_id,
                                username=login_session["username"],
                                categories=db_session.
                                    query(Category).order_by(asc(Category.name))))
    else:
        return render_template('delete_category.html',
                               category=delete_me,
                               username=login_session["username"],
                               categories=db_session.
                                    query(Category).order_by(asc(Category.name)))


# Show a category items catalog
@app.route('/category/<int:category_id>/')
@app.route('/category/<int:category_id>/items/')
def show_items(category_id):
    if 'username' in login_session:
        username = login_session["username"]
    else:
        username = None
    category = db_session.query(Category).filter_by(id=category_id).one()
    items = db_session.query(CategoryItem).filter_by(
        category_id=category_id).all()
    with store_context(local_storage):
        if username is not None and \
                category.user_id == login_session['user_id']:
            return render_template('owner_items.html',
                                   items=items,
                                   category=category,
                                   username=username,
                                   categories=db_session.
                                    query(Category).order_by(asc(Category.name)))
        else:
            return render_template('items.html',
                                   items=items,
                                   category=category,
                                   username=username,
                                   categories=db_session.
                                    query(Category).order_by(asc(Category.name)))


# JSON APIs to view items Information
@app.route('/category/<int:category_id>/items/json')
def show_items_json(category_id):
    # check that category exists
    db_session.query(Category).filter_by(id=category_id).one()
    items = db_session.query(CategoryItem).filter_by(
        category_id=category_id).all()
    return jsonify(items=[i.serialize for i in items])
