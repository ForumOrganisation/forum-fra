# coding=utf-8

import json
import os
import requests
import datetime
from deepdiff import DeepDiff

from flask import abort, redirect, render_template, request, send_from_directory, url_for, make_response, send_file, session
from flask_login import current_user, login_required, login_user, logout_user
from login import validate_login
from storage import Company, get_company, set_company, get_db

from forum import app, GridFS, log
from gridfs.errors import NoFile
from mailing import send_mail
from bson.objectid import ObjectId


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return redirect('https://www.forumorg.org/', code=301)


# Admin
@app.route('/dashboard')
@app.route('/dashboard/<page>')
@login_required
def dashboard(page=None):
    company = None
    if current_user.id == 'admin':
        if request.args.get('id'):
            session['company_id'] = request.args.get('id')
        if not session.get('company_id'):
            return redirect('/admin')
        company = get_db().companies.find_one({'id': session['company_id']}, {'_id': 0})
    if not page or page == 'accueil':
        return render_template('dashboard/dashboard.html', company=company)
    return render_template('dashboard/sections/{}.html'.format(page), company=company)


@app.route('/connexion', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        remember_me = 'remember_me' in request.form
        company_id = request.form.get('id', None)
        password = request.form.get('password', None)
        company = get_company(company_id)
        # checking stuff out
        if not company_id or not password:
            return render_template('login.html', error="blank_fields")
        if not company:
            return render_template('login.html', error="no_company_found")
        if not validate_login(company['password'], password):
            return render_template('login.html', error="wrong_password")
        # all is good
        company = Company(id=company_id, password=password)
        print('connected_as: {}'.format(company_id))
        login_user(company, remember=remember_me)
        if company_id == "admin":
            return redirect('/admin')
        else:
            return redirect(request.args.get('next') or url_for('dashboard'))
    return render_template('login.html')


@app.route('/js_log', methods=["POST"])
def js_log():
    print('js_log', request.form.to_dict())
    return 'success'


@app.route('/deconnexion')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/update_company', methods=["POST"])
@login_required
def update_company():
    page = request.form.get('page')
    if current_user.data.get(page) and current_user.id != 'admin':
        return "error"
    else:
        company = request.form.get('company')
        company = json.loads(company)
        old_company = get_db().companies.find_one({'id': company['id']}, {'_id': 0})
        set_company(company['id'], company)
        send_event(old_company, company, page)
        return "success"


def send_event(old_company, company, page):
    zone, company_id = company.get('zone'), company.get('name')
    dt = datetime.datetime.now().strftime('%A %H:%M:%S')
    try:
        diff = DeepDiff(old_company, company, ignore_order=True, verbose_level=2).json
    except Exception as e:
        diff = {'error': e}

    try:
        root = json.loads(diff)
        if root.get('dictionary_item_added'):
            root = root.get('dictionary_item_added')
            if 'furnitures' in root.keys()[0]:
                equipement = root.values()[0]
                furniture = root.keys()[0].split('[')[3].replace(']', '').replace('\'', '')
                diff = u'Passage de 0 à {} unités pour {}'.format(equipement, furniture)
            if 'catering' in root.keys()[0]:
                repas = root.values()[0]
                day = 'Mercredi' if 'wed' in root.keys()[0] else 'Jeudi'
                diff = u'Passage de 0 à {} repas pour le {}'.format(repas, day)

        if root.get('iterable_item_added'):
            root = root.get('iterable_item_added')
            if 'persons' in root.keys()[0]:
                badge = root.values()[0]
                diff = u'Ajout de {}    {}    {}'.format(badge.get('name'), badge.get('function'), badge.get('days'))
            if 'transports' in root.keys()[0]:
                transport = root.values()[0]
                diff = u'De {} vers {} à {} ({}, Nb: {})'.format(transport.get('departure_place'),
                                                                 transport.get('arrival_place'), transport.get('departure_time'), transport.get('phone'), transport.get('nb_persons'))
                if transport.get('comment'):
                    diff += u' Commentaire: {}'.format(transport.get('comment'))

        if root.get('values_changed'):
            root = root.get('values_changed')
            if 'catering' in root.keys()[0]:
                repas = root.values()[0]
                day = 'Mercredi' if 'wed' in root.keys()[0] else 'Jeudi'
                diff = u'Passage de {} à {} repas pour le {}'.format(repas.get('old_value'), repas.get('new_value'), day)
            if 'furnitures' in root.keys()[0]:
                equipement = root.values()[0]
                furniture = root.keys()[0].split('[')[3].replace(']', '').replace('\'', '')
                diff = u'Passage de {} à {} unités pour {}'.format(equipement.get('old_value'), equipement.get('new_value'), furniture)
    except Exception as e:
        pass
    log(diff)
    if diff:
        log('lol')
        get_db().stream.insert({'delivered': False, 'validated': False, 'section': page,
                                'zone': zone, 'created_on': dt, 'company': company_id, 'diff': diff})


@app.route('/get_resume/<oid>')
def get_resume(oid):
    try:
        file = GridFS.get(ObjectId(oid))
        response = make_response(file.read())
        response.mimetype = file.content_type
        return response
    except NoFile:
        abort(404)


@app.route('/validate_section', methods=["POST"])
@login_required
def validate_section():
    page = request.form.get('page')
    if not current_user.data.get(page):
        get_db().companies.update_one({'id': current_user.id}, {'$set': {page: True}})
        return "success"
    else:
        return "error"


@app.route('/update_banner', methods=["POST"])
@login_required
def update_banner():
    if not current_user.data.get('equipement'):
        company_id = request.form.get('pk')
        banner = request.form.get('value')

        company = get_company(company_id)
        company['banner'] = banner
        set_company(company['id'], company)
        return "success"
    else:
        abort(500)


@app.route('/add_job', methods=["POST"])
@login_required
def add_job():
    job = request.form.get('job')
    job = json.loads(job)
    get_db().jobs.insert_one(job)
    return "success"


@app.route('/remove_job', methods=["POST"])
@login_required
def remove_job():
    job_id = request.form.get('id')
    get_db().jobs.delete_one({'_id': ObjectId(job_id)})
    return "success"


@app.route('/identicon', methods=["GET"])
@login_required
def identicon():
    from binascii import hexlify
    from identicon import render_identicon
    from io import BytesIO
    text = request.args.get('text', 'EMPTY')
    code = int(hexlify(text), 16)
    size = 25
    img = render_identicon(code, size)
    stream = BytesIO()
    img.save(stream, format='png')
    stream.seek(0)
    return send_file(
        stream,
        mimetype='image/png'
    )


# VITRINE
# start of app
@app.route('/', methods=["GET"])
@app.route('/<page>', methods=["GET"])
def index(page=None):
    if page == 'presse':
        return render_template('press.html'.format(page))
    return render_template('index.html')


@app.route('/send_request', methods=["GET"])
def send_request():
    # Params
    email = request.args.get('email')
    contact_name = request.args.get('nom_complet')
    company_name = request.args.get('nom')
    telephone = request.args.get('tel')
    captcha = request.args.get('captcha')

    # ReCaptcha
    base_url = 'https://www.google.com/recaptcha/api/siteverify'
    secret = os.environ.get('RECAPTCHA_SECRET_KEY')
    res = requests.post(base_url, data={'response': captcha, 'secret': secret}).json()

    # Sending mail...
    if res.get('success'):
        return send_mail(email, contact_name, company_name, telephone)
    else:
        abort(500)


# INDEXING
@app.route('/robots.txt')
@app.route('/sitemap.xml')
@app.route('/favicon.ico')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])
