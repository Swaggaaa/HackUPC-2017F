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

treatments = {'cavity' : """- Fluoride treatments: If your cavity just started, a fluoride treatment may help restore your tooth's enamel and can sometimes reverse a cavity in the very early stages.
- Fillings (restorations): fillings are the main treatment option when decay has progressed beyond the earliest stage. They are made of various materials.
- Tooth extractions: Some teeth become so severely decayed that they can't be restored and must be removed. Having a tooth pulled can leave a gap that allows your other teeth to shift. If possible, consider getting a bridge or a dental implant to replace the missing tooth.""",

'cataract' : """Risk of cataracts can be increased by:
- inherited genetic disorders
- diabetes
- smoking
- long-term use of steroids
- obesity
- previous eye surgeries
- drinking excessive amounts of alcohol.

If you experience any changes in your vision, make an appointment for an eye exam.""",

'conjunctivitis' : """Conjunctivitis can be caused by exposure to something for which you have an allergy,
and also by exposure to someone infected of viral/bacterial conjunctivitis.
Usage of extended-wear contact lenses is a risk factor as well.

You will be advised to stop wearing contact lenses if you wear them.
Disinfect hard lenses overnight before you reuse them.
Your doctor could prescribe some type of eyedrops if your conjunctivitis is caused from an allergy.""",

'sty' : """Styes are often caused by bacteria infection.
To avoid this, you should not:

- Touch your eyes with unwashed hands
- Insert your contact lenses without correctly disinfecting them
- Leave on eye makeup overnight

Your doctor could prescribe you antibiotic eyedrops or a topical antibiotic cream.
In severe cases, these antibiotics may come in tablet or pill form."""}


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

def show_help(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
    text='Hi! Welcome to <b>First AId</b>.\n'
    "You can input the following commands: \n"
    "/help -- Displays this text \n"
    "/diagnose -- Starts the diagnose procedure \n"
    "/infection -- Submit a viral infection in you area \n"
    "/alerts -- Configure alerts for infections \n",
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
    update.message.reply_text("Send a photo so I can assist you.")
    return LISTENING_FOR_INPUT

def input_received_infection(bot, update, user_data=""):
    display_menu_location(bot, update, "to submit the infection for that place.")
    return INFECTION_CHECKER

def infection_received(bot, update, user_data):
    bot.send_chat_action(chat_id=update.message.chat_id,
    action=ChatAction.FIND_LOCATION)

    location = update.message.location
    city_name = ""

    if (location):
        city_name = get_city_name(
            lat=location.latitude,
            lgt=location.longitude
        )
    else:
        city_name = update.message.text

        if not city_exists(update.message.text):
            update.message.reply_text("City not found. Please try again.")
            return INFECTION_CHECKER


    if (not city_name in danger_cities):
        danger_cities.append(city_name)
        update.message.reply_text("Viral Infection submitted for " + city_name +
                                  ". Thank you!"
                                 )

        if not city_name in alert_users_cities:
            return LISTENING_FOR_INPUT

        for chat_id in alert_users_cities[city_name]:
            bot.send_message(chat_id=chat_id,
                             text="<b>NEW INFECTION</b> IN <b>" +
                                   city_name + "</b>.",
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
    filename = '%s - %s.jpg'%(update.message.from_user.first_name, str(update.message.date).replace(':', ''))
    filename = filename.replace(' ', '')
    photo_file.download(filename)
    user_data['filename'] = filename
    healthy = not diagnose_on_course(bot, update, user_data)
    #update.message.reply_text("Do you want to find a medical center nearby?")
    if (not healthy):
        custom_keyboard = [['Yes','No']]
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
                          "to enable or disable alerts for that city.")
    if (update.message.text == 'Enable'):
        return ALERTS_LOCATION_ENABLE

    return ALERTS_LOCATION_DISABLE

def alerts_location_enable(bot, update, user_data):
    if (update.message.text and not city_exists(update.message.text)):
        update.message.reply_text("Invalid city. Rewrite it or send it again.")
        return ALERTS_LOCATION_ENABLE

    city_name = get_city_name(lgt=update.message.location.longitude,
                              lat=update.message.location.latitude) if update.message.location else update.message.text
    if (city_name in alert_users_cities):
        if (update.message.chat_id in alert_users_cities[city_name]):
            update.message.reply_text("You are already receiving updates for " +
            "that location.")
            return LISTENING_FOR_INPUT

        alert_users_cities[city_name].append(update.message.chat_id)
    else:
        alert_users_cities[city_name] = [update.message.chat_id]

    update.message.reply_text("Alerts enabled for user %s in city %s." %(
                                update.message.from_user.first_name, city_name
                                ))
    if city_name in danger_cities:
        bot.send_message(chat_id=update.message.chat_id,
                         text="<b>EXISTING INFECTION</b> IN <b>" +
                               city_name + "</b>.",
                         parse_mode=ParseMode.HTML
                        )
    return LISTENING_FOR_INPUT

def alerts_location_disable(bot, update, user_data):
    if (update.message.text and not city_exists(update.message.text)):
        update.message.reply_text("Invalid city. Rewrite it or send it again.")
        return ALERTS_LOCATION_DISABLE

    city_name = get_city_name(lgt=update.message.location.longitude,
                              lat=update.message.location.latitude) if update.message.location else update.message.text
    if (not city_name in alert_users_cities or \
    not update.message.chat_id in alert_users_cities[city_name]):
        update.message.reply_text("You are already not receiving updates for " +
        "that location.")
        return LISTENING_FOR_INPUT

    alert_users_cities[city_name].remove(update.message.chat_id)
    update.message.reply_text("You have been removed from " + city_name + ".")

    return LISTENING_FOR_INPUT


def near_hospitals(bot, update, user_data):
    if update.message.text == 'Yes':
        display_menu_location(bot, update, "to find out nearby medical centres.")
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

    r = [i.replace(' ', '') for i in r]
    if len(r) == 1:
        if r[0] == "perfectsmile" or r[0] == "goodeye":
            update.message.reply_text("Congratulations! You are <b>Healthy</b>.",
                                    parse_mode=ParseMode.HTML)
            return False

        update.message.reply_text("You have been diagnosed with <b>" + r[0] +
                                  "</b>.",
                                  parse_mode=ParseMode.HTML
        )

        update.message.reply_text("The suggested treatment for %s is:\n%s" %(r[0], treatments[r[0]]))
    else:
        if r[0] == "perfectsmile" or r[0] == "goodeye" or \
        r[1] == "perfectsmile" or r[1] == "goodeye":
            if (r[0] == "perfectsmile" and r[1] == "goodeye") or \
            r[1] == "perfectsmile" and r[1] == "goodeye":
                update.message.reply_text("Congratulations! You are <b>Healthy</b>.",
                                        parse_mode=ParseMode.HTML
                )
                return True

            bad_thing = ""
            if r[0] == "perfectsmile" or r[0] == "goodeye":
                bad_thing = r[1]
            else:
                bad_thing = r[0]

            update.message.reply_text("You are either <b>Healthy</b> or " +
                                      "have <b>" + bad_thing + "</b>",
                                      parse_mode=ParseMode.HTML
            )

        else:
            update.message.reply_text(
            "You probably have <b>" + r[0] + "</b> or <b>" + r[1] + "</b>.",
            parse_mode=ParseMode.HTML
            )


    f = open(chart_filename, 'rb')
    update.message.reply_text("Our diagnose has an accuracy of: ")
    bot.send_photo(chat_id=update.message.chat_id,
                   photo=f)

    return True

def main():
    #Set TOKEN
    updater = Updater('417439438:AAHmj9RPgHYYEqXOdhahMTZEkBeBNeVN6T0')

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

            ASK_NEAR: [RegexHandler('^(Yes|No)$',
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
