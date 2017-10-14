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

from telegram import ReplyKeyboardMarkup, ParseMode
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          RegexHandler, ConversationHandler)
from datetime import datetime
from subprocess import check_output

import logging

# Enable logging
logging.basicConfig(
format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
level=logging.INFO)

logger = logging.getLogger(__name__)

LISTENING_FOR_INPUT, DIAGNOSE_STARTED, DIAGNOSE_FINISHED = range(3)

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

def show_help(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
    text='Hi! Welcome to <b>Autism detector</b>. You probably have autism tbh.\n'
    "You can input the following commands: \n"
    "/help -- Displays this text \n"
    "/diagnose -- Starts the diagnose procedure \n"
    "/infection -- Starts the viral infection alert procedure \n"
    "You can also either: \n"
    "- Send an [image]  -- Starts the diagnose procedure \n"
    "- Send a [location]  -- Starts the viral infection alert procedure",
    parse_mode=ParseMode.HTML)

    return LISTENING_FOR_INPUT

def input_received_diagnose(bot, update, user_data):
    update.message.reply_text("Send a photo or either describe your symptoms")
    return LISTENING_FOR_INPUT

def input_received_infection(bot, update, user_data):
    update.message.reply_text("You can either write down your city or send " +
    "a live location to find out nearby infections")
    return LISTENING_FOR_INPUT

def input_received(bot, update, user_data):
    if (update.message.photo):
        file_id = update.message.photo[-1].file_id
        photo_file = bot.get_file(file_id)
        filename = '%s - %s.jpg'%(update.message.from_user.username, str(update.message.date).replace(':', ''))
        filename = filename.replace(' ', '')
        photo_file.download(filename)
        print(check_output('python guess.py ' + filename, shell=True))
    elif (update.message.location):

    else:
        update.message.reply_text("I will cure u don't worry");
    return DIAGNOSE_STARTED

def diagnose_on_course(bot, update, user_data):
    bot.send_chat_action(chat_id=update.message.chat_id,
    action="Asking the doctor...")

    #check response

def main():
    #Set TOKEN
    updater = Updater('468902066:AAEtfsuHosRJPKKk_VVrM87n7r3BegC3Yew')

    dispatcher = updater.dispatcher

    conversation_handler = ConversationHandler(
        entry_points=
            [CommandHandler('start', show_help)],

        states={
            LISTENING_FOR_INPUT: [MessageHandler(Filters.text | Filters.photo | Filters.location,
                                                 input_received,
                                                 pass_user_data=True)],

            DIAGNOSE_STARTED: [MessageHandler(Filters.text,
                                              diagnose_on_course,
                                              pass_user_data=True)],
            ]
        },

        fallbacks=[RegexHandler('^Done$', show_help, pass_user_data=True)]
    )

    help_handler = CommandHandler('help', show_help)
    diagnose_handler = CommandHandler('diagnose', input_received_diagnose)
    infection_handler = CommandHandler('infection', input_received_infection)

    dispatcher.add_handler(conversation_handler);
    dispatcher.add_handler(help_handler);
    dispatcher.add_handler(diagnose_handler);
    dispatcher.add_error_handler(error);
    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
