#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Simple Bot to reply to Telegram messages
# This program is dedicated to the public domain under the CC0 license.
"""
This Bot uses the Updater class to handle the bot.
First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

from telegram import ReplyKeyboardMarkup, ParseMode, ChatAction, KeyboardButton
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          RegexHandler, ConversationHandler)
from datetime import datetime
from subprocess import check_output
from guess  import diagnostic

import logging

# Enable logging
logging.basicConfig(
format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
level=logging.INFO)

logger = logging.getLogger(__name__)

danger_cities = []

LISTENING_FOR_INPUT, SYMPTOMS_CHECKER, INFECTION_CHECKER = range(3)

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

def show_help(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
    text='Hi! Welcome to <b>Autism detector</b>. You probably have autism tbh.\n'
    "You can input the following commands: \n"
    "/help -- Displays this text \n"
    "/diagnose -- Starts the diagnose procedure \n"
    "/infection -- Submit a viral infection in you area \n"
    "/alerts -- Configure alerts for infections \n"
    "You can also either: \n"
    "- Send an [image]  -- Starts the diagnose procedure \n"
    "- Send a [location]  -- Starts the viral infection alert procedure",
    parse_mode=ParseMode.HTML)

    return LISTENING_FOR_INPUT

def input_received_diagnose(bot, update, user_data=""):
    update.message.reply_text("Send a photo or either describe your symptoms")
    return LISTENING_FOR_INPUT

def input_received_infection(bot, update, user_data=""):
    submit_keyboard = KeyboardButton(
        text="Submit your Location",
        request_location=True)

    custom_keyboard = [[submit_keyboard]]
    reply_markup = ReplyKeyboardMarkup(keyboard=custom_keyboard,
                                       one_time_keyboard=True)

    bot.send_message(chat_id=update.message.chat_id,
    text = "You can either write down your city or send " +
    "a live location to find out nearby infections",
    reply_markup=reply_markup)

    return INFECTION_CHECKER

def check_infection(bot, update, user_data=""):

    return LISTENING_FOR_INPUT

def infection_received(bot, update, user_data):
    bot.send_chat_action(chat_id=update.message.chat_id,
    action=ChatAction.FIND_LOCATION)

    location = update.message.location
    if (location):
        coords = (location.longitude, location.latitude)
        #tractar coords per convertir en area i guardar
    else:
        kek = 1
        #convertir nom de ciutat a coords, i de coords a area

    #store the area in the global array
    update.message.reply_text("Viral Infection submitted. Thank you!")

    return LISTENING_FOR_INPUT

def input_received(bot, update, user_data):
    if (update.message.photo):
        file_id = update.message.photo[-1].file_id
        photo_file = bot.get_file(file_id)
        filename = '%s - %s.jpg'%(update.message.from_user.username, str(update.message.date).replace(':', ''))
        filename = filename.replace(' ', '')
        photo_file.download(filename)
        user_data['filename'] = filename
        diagnose_on_course(bot, update, user_data)
    else:
        update.message.reply_text("I will cure u don't worry");

    return LISTENING_FOR_INPUT

def alerts_settings(bot, update, user_data):



def diagnose_on_course(bot, update, user_data):
    bot.send_chat_action(chat_id=update.message.chat_id,
    action=ChatAction.UPLOAD_PHOTO)
    show_diagnose(bot, update, user_data)
    #check response

def show_diagnose(bot, update, user_data):
    r = diagnostic(user_data['filename'])
    if len(r) == 1:
        update.message.reply_text("You have: " + r[0])
    else:
        update.message.reply_text(
        "You probably have " + r[0] + " or " + r[1] + "\n",
        "Answer a couple questions so we can diagnose you better: ")
        return SYMPTOMS_CHECKER

    return LISTENING_FOR_INPUT

def main():
    #Set TOKEN
    updater = Updater('468902066:AAEtfsuHosRJPKKk_VVrM87n7r3BegC3Yew')

    dispatcher = updater.dispatcher

    conversation_handler = ConversationHandler(
        entry_points=
            [CommandHandler('start', show_help)],

        states={
            LISTENING_FOR_INPUT: [MessageHandler(Filters.text | Filters.photo,
                                                 input_received,
                                                 pass_user_data=True)],

            INFECTION_CHECKER: [MessageHandler(Filters.text | Filters.location,
                                               infection_received,
                                               pass_user_data=True)],

        },

        fallbacks=[RegexHandler('^Done$', show_help, pass_user_data=True)]
    )

    help_handler = CommandHandler('help', show_help)
    diagnose_handler = CommandHandler('diagnose', input_received_diagnose)
    infection_handler = CommandHandler('infection', input_received_infection)
    alerts_handler = CommandHandler('alerts', alerts_settings)

    dispatcher.add_handler(conversation_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(diagnose_handler)
    dispatcher.add_handler(infection_handler)
    dispatcher.add_handler(alerts_handler)
    dispatcher.add_error_handler(error)
    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
