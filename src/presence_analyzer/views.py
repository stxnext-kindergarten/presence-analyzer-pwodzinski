# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar
import logging
import locale
from flask import redirect, abort
from flask.ext.mako import MakoTemplates, render_template
from mako.exceptions import TopLevelLookupException

from presence_analyzer.main import app
from presence_analyzer.utils import (
    jsonify,
    get_data,
    mean,
    group_by_weekday,
    total_group_by_weekday,
    group_by_start_end,
    parse_xml
)

mako = MakoTemplates(app)

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


@app.route('/')
def mainpage():
    """
    Redirects to front page.
    """
    return redirect('/presence_weekday')


@app.route('/<template>')
def viewer(template):
    """
    Redirects to template.
    """
    sites = {
        'mean_time_weekday': 'Presence mean time',
        'presence_weekday': 'Presence by weekday',
        'presence_start_end': 'Presence start-end',
        'presence_total_hour': 'User hours vs total hours'
    }

    try:
        return render_template(template+'.html', selected=template, base=sites)
    except TopLevelLookupException:
        abort(404)


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    data = get_data()
    return [
        {'user_id': i, 'name': 'User {0}'.format(str(i))}
        for i in data.keys()
    ]


@app.route('/api/v2/users', methods=['GET'])
@jsonify
def users_view2():
    """
    Users listing for dropdown.
    """
    locale.setlocale(locale.LC_COLLATE, "")
    data = parse_xml()
    values = [
        {
            'user_id': user_id,
            'name': data[user_id]['name'],
            'avatar': data[user_id]['avatar']
        }
        for user_id in data.keys()
    ]
    values.sort(key=lambda x: x['name'], cmp=locale.strcoll)

    return values


@app.route('/api/v1/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def mean_time_weekday_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], mean(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    return result


@app.route('/api/v1/presence_weekday/<int:user_id>', methods=['GET'])
@jsonify
def presence_weekday_view(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], sum(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    result.insert(0, ('Weekday', 'Presence (s)'))
    return result


@app.route('/api/v2/total_hour/<int:user_id>', methods=['GET'])
@jsonify
def presence_total_hour(user_id):
    """
    Returns user daily time and total daily time of all users.
    """
    data = get_data()

    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    get_total_hours = total_group_by_weekday(data)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (
            calendar.day_abbr[weekday],
            float("%0.2f" % (float(sum(intervals)) / 3600)),
            float("%0.2f" % (float(get_total_hours[weekday]) / 3600))
        )
        for weekday, intervals in enumerate(weekdays)
    ]

    result.insert(0, ('Weekday', 'User hours', 'Total hours'))
    return result


@app.route('/api/v1/mean_time_start_end/<int:user_id>', methods=['GET'])
@jsonify
def presence_start_end_view(user_id):
    """
    Returns total time of given user grouped by start end.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_start_end(data[user_id])

    result = [
        (
            calendar.day_abbr[key],
            mean(weekdays[key][0]),
            mean(weekdays[key][1])
        )
        for key in weekdays
    ]

    return result
