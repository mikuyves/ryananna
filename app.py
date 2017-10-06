# coding: utf-8

from datetime import datetime, timedelta
import json

from flask import Flask
from flask import render_template, request, session, redirect, url_for, flash
from flask_sockets import Sockets
from flask_mongoengine.pagination import Pagination

from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_moment import Moment
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from threading import Thread

import leancloud

from views.todos import todos_view
from search import update_item
from utils import obj_to_dict


app = Flask(__name__)
sockets = Sockets(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
app.config['SECRET_KEY'] = 'hard to guess string'
app.jinja_env.auto_reload = True


# 动态路由
app.register_blueprint(todos_view, url_prefix='/todos')


Spu = leancloud.Object.extend('Spu')
Sku = leancloud.Object.extend('Sku')
History = leancloud.Object.extend('History')


class UrlForm(FlaskForm):
    url = StringField('Enter the URL:', validators=[DataRequired()])
    submit = SubmitField('Submit')


class SearchForm(FlaskForm):
    keyword = StringField('Keyword', validators=[DataRequired()])
    submit = SubmitField('Search')


@app.route('/', methods=['GET', 'POST'])
def index():
    # Pagination.
    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('keyword')
    print(keyword)

    query = Spu.query.add_descending('createdAt')
    if keyword:
        query.contains('name', keyword)
    spu_all = query.find()

    pg = Pagination(spu_all, page, 20)

    # Get and arrange the item data to render.
    items = []
    for spu_obj in pg.items:
        spu = spu_obj.dump()
        sku_objs = Sku.query \
            .equal_to('spu', spu_obj) \
            .add_ascending('price').find()
        skus = [sku_obj.dump() for sku_obj in sku_objs]
        items.append({'spu': spu, 'skus': skus})

    # Search online.
    form = SearchForm()
    if form.validate_on_submit():
        input_keyword = form.keyword.data
        form.keyword.data = ''
        return redirect(url_for('index', keyword=input_keyword))

    return render_template('index.html',
                           form=form,
                           items=items,
                           pagination=pg,
                           current_time=datetime.utcnow())


@app.route('/latest', methods=['GET', 'POST'])
def latest():
    # Pagination.
    latest_spus = Spu.query \
        .greater_than_or_equal_to('createdAt', datetime.now() - timedelta(days=2))\
        .add_descending('createdAt')\
        .find()

    # Get and arrange the item data to render.
    items = []
    for spu_obj in latest_spus:
        spu = spu_obj.dump()
        sku_objs = Sku.query \
            .equal_to('spu', spu_obj) \
            .add_ascending('price').find()
        skus = [sku_obj.dump() for sku_obj in sku_objs]
        items.append({'spu': spu, 'skus': skus})

    # Search online.
    form = SearchForm()
    if form.validate_on_submit():
        input_keyword = form.keyword.data
        form.keyword.data = ''
        return redirect(url_for('index', keyword=input_keyword))

    return render_template('latest.html',
                           form=form,
                           items=items,
                           current_time=datetime.utcnow())


@app.route('/update30', methods=['GET', 'POST'])
def update30():
    # Pagination.
    latest_spus = Spu.query \
        .add_descending('updatedAt') \
        .limit(30)\
        .find()

    # Get and arrange the item data to render.
    items = []
    for spu_obj in latest_spus:
        spu = spu_obj.dump()
        sku_objs = Sku.query \
            .equal_to('spu', spu_obj) \
            .add_ascending('price').find()
        skus = [sku_obj.dump() for sku_obj in sku_objs]
        items.append({'spu': spu, 'skus': skus})

    # Search online.
    form = SearchForm()
    if form.validate_on_submit():
        input_keyword = form.keyword.data
        form.keyword.data = ''
        return redirect(url_for('index', keyword=input_keyword))

    return render_template('update30.html',
                           form=form,
                           items=items,
                           current_time=datetime.utcnow())


@app.route('/all', methods=['GET', 'POST'])
def all():
    # Pagination.
    latest_spus = Spu.query \
        .add_descending('createdAt') \
        .find()

    # Get and arrange the item data to render.
    items = []
    for spu_obj in latest_spus:
        spu = spu_obj.dump()
        sku_objs = Sku.query \
            .equal_to('spu', spu_obj) \
            .add_ascending('price').find()
        skus = [sku_obj.dump() for sku_obj in sku_objs]
        items.append({'spu': spu, 'skus': skus})

    # Search online.
    form = SearchForm()
    if form.validate_on_submit():
        input_keyword = form.keyword.data
        form.keyword.data = ''
        return redirect(url_for('index', keyword=input_keyword))

    return render_template('all.html',
                           form=form,
                           items=items,
                           current_time=datetime.utcnow())


@app.route('/commit', methods=['GET', 'POST'])
def commit():
    # Form to input the URL.
    url = None
    form = UrlForm()
    if form.validate_on_submit():
        url = form.url.data
        parse_new(url)
        form.url.data = ''
        return redirect(url_for('index'))

    return render_template('commit.html',
                           form=form)


@app.route('/sku/<asin>')
def sku(asin):
    sku_obj = Sku.query\
        .equal_to('asin', asin)\
        .include('spu')\
        .first()
    sku_objs = Sku.query\
        .equal_to('spu', sku_obj.get('spu'))\
        .add_ascending('price')\
        .find()

    sku = obj_to_dict(sku_obj)
    skus = [obj_to_dict(obj) for obj in sku_objs]

    return render_template('sku.html',
                           sku=sku,
                           skus=skus)

@app.route('/spu/<asin>')
def spu(asin):
    spu_obj = Spu.query \
        .equal_to('asin', asin) \
        .first()
    sku_objs  = Sku.query\
        .equal_to('spu', spu_obj)\
        .add_ascending('price')\
        .find()

    spu = obj_to_dict(spu_obj)
    skus = [obj_to_dict(obj) for obj in sku_objs]

    return render_template('spu.html',
                           spu=spu,
                           skus=skus)


@app.route('/time')
def time():
    return str(datetime.now())


@app.route('/item/<asin>')
def product(asin):
    query = Spu.query
    query.equal_to('asin', asin)
    spu = query.first()
    sku_objs = Sku.query\
        .equal_to('spu', spu)\
        .find()
    skus = [sku_obj.dump() for sku_obj in sku_objs]
    return json.dumps({'spu': spu, 'skus': skus})


@app.route('/delete/<asin>')
def delete_item(asin):
    '''asin:: Must be spu asin.'''
    spu = Spu.query.equal_to('asin', asin).first()
    spu_name = spu.get('name')
    skus = Sku.query.equal_to('spu', spu).find()
    # history_list = History.query.equal_to('sku', sku).find()
    objs = [spu] + skus
    leancloud.Object.destroy_all(objs)
    flash('{0} has been deleted.'.format(spu_name))
    return redirect(url_for('index'), 301)


@sockets.route('/echo')
def echo_socket(ws):
    while True:
        message = ws.receive()
        ws.send(message)


def async_parse_new(app, url, request):
    with app.app_context():
        # flash('Parsing item...')
        item = update_item(url)
        with app.test_request_context():
            flash('Ok! Parsed item: {}'.format(item.spu.get('name')))


def parse_new(url):
    thr = Thread(target=async_parse_new, args=[app, url, request])
    thr.start()
    return thr
