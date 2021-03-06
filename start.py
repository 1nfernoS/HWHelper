"""
This is initial module. Here we take request and handle it.
Also there is basic checking of structure to avoid unauthorized requests
Of course, it isn't secure, but it will not fall after bad request
(c) Misden a.k.a. 1nfernos, 2021
"""
from traceback import format_exc
from json import JSONDecodeError
from flask import Flask, request, json, make_response
import flask

from db.users import get_msg, update_msg, get_user, reg_user, set_role

import settings

from commands import cmd
from commands import start as commands
from payloads import start as payload
from forwards import parse as forwards

import after_response
import vk_api

# -+ distribution
# + targets
# keyboards
# squads
# battle results
# Remind before battle
# Customize texts
# chats are 2000000000+

app = Flask(__name__)
after_response.AfterResponse(app)

# TODO:
#   0.Structure
#       0.1. Module of management fraction
#   2.Distribution
#       + 2.1 Distribution by forwarding
#       2.2 Distribution by reaction on bot msgs
#       2.3 Distribution in messages or/and on wall
#       + 2.3.1 If possible, use existing app
#       2.4 Notification before battle
#       2.5 Statistics from battle to squads chats
#   3.Api
#       + 3.1 Changing token
#       +- 3.2 Keyboard with targets
#       + 3.2.1 Keyboard with targets in command chat
#       +- 3.3 Access to LoS (Leader of Squad)
#       +- 3.3.1 Changing LoS
#   //5.Settings
#       +- 5.1 Customize Notifications
#       +- 5.2 Enabling distribution
#       + 5.3 Access control
#       + 5.4 Commands for parse
#       5.4.1 Customize presets
#   6.QoL
#       6.1 Pinned message in chats
#       6.2 Profile message
#       +- 6.3 Employee list
#   7.Keyboards


@app.route('/')
def index():
    return '<h2>HWHelper Bot, use VK bot instead this</h2>'


@app.route('/', methods=['POST'])
def handler():
    """
    Start point for pre-processing request from vk
    :return: response('ok', 200) / confirmation token
    """
    try:
        r = request.data
        data = json.loads(str(r))
    except JSONDecodeError:
        return make_response("No data provided", 400)

    # confirmation don't send any other data
    try:
        type_msg = data['type']
    except KeyError:
        return make_response("Wrong data provided", 400)
    except TypeError:
        return make_response("Wrong data provided", 400)

    if type_msg == 'confirmation':
        return settings.confirmation_token

    try:
        obj_msg = data['object']
        group_id = data['group_id']
    except KeyError:
        return make_response("Wrong data provided", 400)

    if group_id != settings.group_id:
        return make_response("Error: only bot have access", 403)

    if type_msg == 'message_new':
        data_msg = obj_msg['message']
        message(data_msg)

    return make_response('ok', 200)


@app.errorhandler(500)
def internal_error(*args):
    """
    Send in errors chat info about exception and continue working
    Something like except: pass
    :return: response('ok', 200)
    """
    vk_api.send(settings.errors_chat, str(format_exc(-5)))
    return make_response('ok', 200)


def message(msg):
    """
    Main processing with message
    :param msg: dict, message object from vk [object][message]
    :return: None
    """

    time = int(msg['date'])
    text = str(msg['text'])
    chat = int(msg['peer_id'])
    user = int(msg['from_id'])

    if user > 0:
        pl = 'payload' in msg.keys()
        fwd = len(msg['fwd_messages']) != 0
        com = text.startswith('/')
        if user != chat:
            if pl or com:
                pass
            else:
                return
        else:
            if pl or com or fwd:
                pass
            else:
                return
        try:
            get_user(user)
        except ValueError:
            reg_user(user, time - 1)
            if user == settings.creator:
                set_role(user, 0)
                vk_api.send(user, "You became a creator")

        if time == get_msg(user):
            vk_api.send(chat, "2fast4me")
            return
        else:
            update_msg(user, time)
    else:
        return

    # keyboards
    if pl:
        pl = json.loads(msg['payload'])
        payload(msg, pl)
        return

    # forwards
    if fwd and text == '':
        forward = msg['fwd_messages']
        forwards(msg, forward)
        return

    # commands
    if com:
        command = msg['text'].split()
        command[0] = command[0].replace('/', '')
        if command[0] in cmd():
            commands(msg, command[0])
        else:
            vk_api.send(chat, '\"/' + str(command[0]) + '\" not in list')
        return
    return


if __name__ == '__main__':
    app.run()
