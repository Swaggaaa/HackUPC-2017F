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

from telegram             import ReplyKeyboardMarkup, ParseMode, ChatAction, KeyboardButton
from telegram.ext         import (Updater, CommandHandler, MessageHandler, Filters,
                          RegexHandler, ConversationHandler)
from datetime             import datetime
from subprocess           import check_output
from guess                import diagnostic
from hospital_recommender import (near_specialist, city_exists, get_city_name,
                          get_city_location)

import logging

# Enable logging
logging.basicConfig(
format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
level=logging.INFO)

logger = logging.getLogger(__name__)

danger_cities = []
alert_users_cities = {}
LISTENING_FOR_INPUT, SYMPTOMS_CHECKER, INFECTION_CHECKER, ASK_NEAR, HOSPITAL_CHECKER, ALERTS_MODIFIER, ALERTS_LOCATION_ENABLE, ALERTS_LOCATION_DISABLE = range(8)

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

def display_menu_location(bot, update, to_what):
    submit_keyboard = KeyboardButton(
                        text="Submit your Location",
                        request_location=True)

    custom_keyboard = [[submit_keyboard]]
    reply_markup = ReplyKeyboardMarkup(keyboard=custom_keyboard,
                                    one_time_keyboard=True)

    bot.send_message(chat_id=update.message.chat_id,
                     text = "You can either write down your city or send " +
                     "a live location " + to_what,
                     reply_markup=reply_markup)


def input_received_diagnose(bot, update, user_data=""):
    update.message.reply_text("Send a photo or either describe your symptoms")
    return LISTENING_FOR_INPUT

def input_received_infection(bot, update, user_data=""):
    display_menu_location(bot, update, "to submit the infection for that place")
    return INFECTION_CHECKER

def infection_received(bot, update, user_data):
    bot.send_chat_action(chat_id=update.message.chat_id,
    action=ChatAction.FIND_LOCATION)

    location = update.message.location
    city_name = ""

    if (location):
        city_name = get_city_name(
            lat=location.latitude,
            lng=location.longitude
        )
    else:
        city_name = update.message.text
        if(not city_exists(update.message.text)):
            update.message.reply_text("City not found. Please try again")
            return INFECTION_CHECKER

    if (not city_name in danger_cities):
        danger_cities.append(city_name)
        update.message.reply_text("Viral Infection submitted for " + city_name +
                                  ". Thank you!"
                                 )
        for chat_id in alert_users_cities[city_name]:
            bot.send_message(chat_id=chat_id,
                             text="<b>NEW INFECTION</b> IN <b>" +
                                   city_name + "</b>",
                             parse_mode=ParseMode.HTML
                            )
    else:
        update.message.reply_text("A Viral Infection already exists for " +
                                   city_name + "."
                                 )


    return LISTENING_FOR_INPUT

def input_received(bot, update, user_data):
    file_id = update.message.photo[-1].file_id
    photo_file = bot.get_file(file_id)
    filename = '%s - %s.jpg'%(update.message.from_user.username, str(update.message.date).replace(':', ''))
    filename = filename.replace(' ', '')
    photo_file.download(filename)
    user_data['filename'] = filename
    healthy = not diagnose_on_course(bot, update, user_data)
    #update.message.reply_text("Do you want to find a medical center nearby?")
    if (not healthy):
        custom_keyboard = [['YES','NO']]
        reply_markup = ReplyKeyboardMarkup(keyboard=custom_keyboard,
                                          one_time_keyboard=True)
        bot.send_message(chat_id=update.message.chat_id,
                         text="Do you want to find a medical center nearby?",
                         reply_markup=reply_markup)

        return ASK_NEAR

    return LISTENING_FOR_INPUT

def input_received_alerts(bot, update, user_data=""):
    custom_keyboard = [['Enable','Disable']]
    reply_markup = ReplyKeyboardMarkup(keyboard=custom_keyboard,
                                       one_time_keyboard=True)
    bot.send_message(chat_id=update.message.chat_id,
                     text="Do you want to set up alerts for Viral " \
                          "Infections in your area?",
                     reply_markup=reply_markup)
    return ALERTS_MODIFIER

def alerts_settings(bot, update, user_data):
    display_menu_location(bot,
                          update,
                          "to enable or disable alerts for that city")
    if (update.message.text == 'Enable'):
        return ALERTS_LOCATION_ENABLE

    return ALERTS_LOCATION_DISABLE

def alerts_location_enable(bot, update, user_data):
    if (update.message.text and not city_exists(update.message.text)):
        update.message.reply_text("Invalid city. Rewrite it or send it again")
        return ALERTS_LOCATION_ENABLE

    city_name = get_city_name(lgt=update.message.location.longitude,
                              lat=update.message.location.latitude) if update.message.location else update.message.text
    if (city_name in alert_users_cities):
        if (update.message.chat_id in alert_users_cities[city_name]):
            update.message.reply_text("You are already receiving updates for " +
            "that location")
            return LISTENING_FOR_INPUT

        alert_users_cities[city_name].append(update.message.chat_id)
    else:
        alert_users_cities[city_name] = [update.message.chat_id]

    update.message.reply_text("Alerts enabled for user %s in city %s" %(
                                update.message.from_user.username, city_name
                                ))
    return LISTENING_FOR_INPUT

def alerts_location_disable(bot, update, user_data):
    if (update.message.text and not city_exists(update.message.text)):
        update.message.reply_text("Invalid city. Rewrite it or send it again")
        return ALERTS_LOCATION_DISABLE

    city_name = get_city_name(lgt=update.message.location.longitude,
                              lat=update.message.location.latitude) if update.message.location else update.message.text
    if (not city_name in alert_users_cities or
    not update.message.chat_id in alert_users_cities[city_name]):
        update.message.reply_text("You are already not receiving updates for " +
        "that location")
        return LISTENING_FOR_INPUT

    alert_users_cities[city_name].remove(update.message.chat_id)
    update.message.reply_text("You have been removed from " + city_name)

    return LISTENING_FOR_INPUT


def near_hospitals(bot, update, user_data):
    if update.message.text == 'YES':
        display_menu_location(bot, update, "to find out nearby medical centres")
        return HOSPITAL_CHECKER
    else:
        update.message.reply_text(
            "Thank you!"
        )
        return LISTENING_FOR_INPUT

def locate_hospital(bot, update, user_data):
    bot.send_chat_action(chat_id=update.message.chat_id,
    action=ChatAction.FIND_LOCATION)
    location = update.message.location if update.message.location else \
               get_city_location(update.message.text)

    near_hospitals = near_specialist(lat=location.latitude,
                                     lng=location.longitude,
                                     )

    update.message.reply_text("Here are some places, where you can go: ")
    for near_hospital in near_hospitals:
        update.message.reply_text(near_hospital['name'])
        bot.sendLocation(chat_id=update.message.chat_id,
                         latitude=float(near_hospital['location']['lat']),
                         longitude=float(near_hospital['location']['lng'])
                        )

    return LISTENING_FOR_INPUT

def diagnose_on_course(bot, update, user_data):
    bot.send_chat_action(chat_id=update.message.chat_id,
    action=ChatAction.UPLOAD_PHOTO)
    return show_diagnose(bot, update, user_data)
    #check response

def show_diagnose(bot, update, user_data):
    r, chart_filename = diagnostic(user_data['filename'])

    if len(r) == 1:
        if r[0] == "perfect smile" or r[0] == "good eye":
            update.message.reply_text("Congratulations! You are <b>Healthy</b>",
                                    parse_mode=ParseMode.HTML)
            return False

        update.message.reply_text("You have been diagnosed with <b>" + r[0] +
                                  "</b>.",
                                  parse_mode='HTML')

        f = open(chart_filename, 'rb')
        bot.send_photo(chat_id=update.message.chat_id,
                       photo=f)
    else:
        update.message.reply_text(
        "You probably have " + r[0] + " or " + r[1] + "\n"
        )

    return True

def main():
    #Set TOKEN
    updater = Updater('468902066:AAEtfsuHosRJPKKk_VVrM87n7r3BegC3Yew')

    dispatcher = updater.dispatcher


    conversation_handler = ConversationHandler(
        entry_points=
            [CommandHandler('start', show_help)],


        states={
            LISTENING_FOR_INPUT: [MessageHandler(Filters.photo,
                                                 input_received,
                                                 pass_user_data=True)],

            INFECTION_CHECKER: [MessageHandler(Filters.text | Filters.location,
                                               infection_received,
                                               pass_user_data=True)],

            ASK_NEAR: [RegexHandler('^(YES|NO)$',
                                    near_hospitals,
                                    pass_user_data=True),
                      ],

            HOSPITAL_CHECKER: [MessageHandler(Filters.text | Filters.location,
                                               locate_hospital,
                                               pass_user_data=True)],

            ALERTS_MODIFIER: [RegexHandler('^(Enable|Disable)$',
                                            alerts_settings,
                                            pass_user_data=True),
                             ],

            ALERTS_LOCATION_ENABLE: [MessageHandler(Filters.text | Filters.location,
                                             alerts_location_enable,
                                             pass_user_data=True),
                              ],

            ALERTS_LOCATION_DISABLE: [MessageHandler(Filters.text | Filters.location,
                                                      alerts_location_disable,
                                                      pass_user_data=True),
                              ],

        },

        fallbacks=[RegexHandler('^Done$', show_help, pass_user_data=True),
                    CommandHandler('help', show_help),
                    CommandHandler('diagnose', input_received_diagnose),
                    CommandHandler('infection', input_received_infection),
                    CommandHandler('alerts', input_received_alerts)]
    )

    dispatcher.add_error_handler(error)
    dispatcher.add_handler(conversation_handler)
    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
