import json
import os
import csv

from flask import Response, flash, stream_with_context, redirect
from flask_admin.babel import gettext
from flask_admin.base import expose
from flask_admin.contrib.pymongo import ModelView
from flask_admin.contrib.pymongo.filters import BasePyMongoFilter, FilterEqual
from flask_admin.helpers import get_redirect_target
from flask_admin.form import rules
from flask_login import current_user
from werkzeug import secure_filename
from wtforms import fields, form, validators
from export import log, generate_vals


SECTIONS = ['equipement', 'transport', 'restauration', 'badges', 'programme',
            'name', 'acompte',
            'emplacement', 'duration', 'equiped', 'banner', 'size']


def get_sections():
    fn = os.path.join(os.path.dirname(__file__), 'sections.json')
    with open(fn) as file:
        return json.load(file)


class CompanyForm(form.Form):
    # Basic
    id = fields.StringField('Identifiant', validators=[validators.Required(), validators.Length(min=3, max=30)], render_kw={"placeholder": "Ex. LOREAL"})
    password = fields.StringField('Mot de passe', validators=[validators.Required(), validators.Length(min=3, max=30)], render_kw={"placeholder": "Ex. motdepasse"})
    name = fields.StringField('Nom complet', render_kw={"placeholder": "Ex. L'Oreal"})
    acompte = fields.SelectField('Acompte paye?', choices=[('non', 'non'), ('oui', 'oui')])
    # Equipement
    emplacement = fields.StringField('Emplacement', render_kw={"placeholder": "Ex. F13"})
    size = fields.SelectField('Surface', choices=[(9, '9 m2'), (12, '12 m2'), (18, '18 m2'), (36, '36 m2')], coerce=int)
    duration = fields.SelectField('Jours de presence', choices=[(1, '1 jour'), (2, '2 jours')], coerce=int)
    equiped = fields.SelectField('Equipe?', choices=[('non', 'non'), ('oui', 'oui')])
    # Dashboard
    equipement = fields.SelectField('Valider Equipement', choices=[('non', 'non'), ('oui', 'oui')])
    restauration = fields.SelectField('Valider Restauration', choices=[('non', 'non'), ('oui', 'oui')])
    badges = fields.SelectField('Valider Badges', choices=[('non', 'non'), ('oui', 'oui')])
    transport = fields.SelectField('Valider Transports', choices=[('non', 'non'), ('oui', 'oui')])
    programme = fields.SelectField('Valider Programme', choices=[('non', 'non'), ('oui', 'oui')])


class CompanyView(ModelView):
    form = CompanyForm
    column_list = ['id'] + SECTIONS[:5]
    export_types = SECTIONS[:4]
    form_rules = [
        rules.FieldSet(('id', 'password', 'name'), 'Profil'),
        rules.FieldSet(('equipement', 'restauration', 'badges',
                        'programme', 'transport'), 'Avancement'),
        rules.FieldSet(('acompte',), 'Finances'),
        rules.FieldSet(('size', 'duration', 'equiped', 'emplacement'), 'Finances'),
    ]

    can_export = True
    can_delete = True
    create_modal = False
    edit_modal = False

    column_searchable_list = ['id']

    def __init__(self, *args, **kwargs):
        super(CompanyView, self).__init__(*args, **kwargs)
        self.static_folder = 'static'
        self.endpoint = 'admin'
        self.name = 'Entreprises'
        self.sections = get_sections()

    def is_accessible(self):
        return current_user.get_id() == 'admin' and current_user.is_authenticated

    def _on_model_change(self, form, model, is_created):
        if is_created:
            model['sections'] = self.sections

    @expose('/export/<export_type>/')
    def export(self, export_type):
        return_url = get_redirect_target() or self.get_url('.index_view')

        if not self.can_export or (export_type not in self.export_types):
            flash(gettext('Permission denied.'), 'error')
            return redirect(return_url)

        if export_type == 'csv':
            return self._export_csv(return_url)
        else:
            return self._export_fields(export_type, return_url)

    def _export_fields(self, export_type, return_url):
        count, data = self._export_data()

        # Dummy object for csv creation
        class Echo(object):

            def write(self, value):
                return value

        writer = csv.writer(Echo())
        data = [r for r in data if r['id'] != 'admin']
        gen_vals = generate_vals(writer, export_type, data)
        filename = self.get_export_name(export_type='csv')
        disposition = 'attachment;filename=%s' % (
            secure_filename(filename.replace(self.name, export_type)),)
        return Response(
            stream_with_context(gen_vals),
            headers={'Content-Disposition': disposition},
            mimetype='text/csv'
        )


class UserForm(form.Form):
    id = fields.StringField(
        'Email', render_kw={"placeholder": "Ex. yokoya@live.com"})
    password = fields.PasswordField('Mot de passe', validators=[validators.Required(
    ), validators.Length(min=5, max=30)], render_kw={"placeholder": "Ex. 123456"})


class FilterRegister(FilterEqual, BasePyMongoFilter):
    def apply(self, query, value):
        query.append({'events.{}.registered'.format(value): True})
        return query

    def operation(self):
        return "evenement"


class UserView(ModelView):
    column_list = ['id', 'events', 'confirmed_on', 'registered_on']
    column_labels = dict(id='Email')
    export_types = ['csv']
    can_export = True
    can_delete = True
    can_view_details = True
    form = UserForm
    column_export_list = ['id', 'registered_on', 'confirmed_on', 'events', 'profile']
    column_filters = (FilterRegister(column='events', name='participants', options=(('styf', 'styf'), ('joi', 'joi'))),)

    def __init__(self, *args, **kwargs):
        super(UserView, self).__init__(*args, **kwargs)
        self.name = 'Utilisateurs'


class EventForm(form.Form):
    name = fields.StringField('Nom')
    type = fields.StringField('Type')
    quota = fields.IntegerField('Quota')
    places_left = fields.IntegerField('Places restantes')


class EventView(ModelView):
    column_list = ['name', 'type', 'quota', 'places_left']
    column_labels = dict(id='Email')
    export_types = ['csv']
    can_export = True
    can_delete = True
    form = EventForm

    def __init__(self, *args, **kwargs):
        super(EventView, self).__init__(*args, **kwargs)
        self.name = 'Journee Objectif Ingenieur'
