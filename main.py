from telegram.ext import Updater
from telegram.ext import CommandHandler, ConversationHandler, CallbackQueryHandler
import random
import logging
import json
import os.path
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def save_stats_to_file(stats_to_save):
    """Save stats to JSON."""
    with open('data.json', 'w+') as fp:
        json.dump(stats_to_save, fp)


def read_from_file():
    """Read stats from JSON."""
    if os.path.isfile('data.json'):
        with open('data.json', 'r') as fp_open:
            return json.load(fp_open)
    else:
        save_stats_to_file(dict())
        return dict()


current_list = read_from_file()

GAME_LIST = {1: "Stone", 2: "Scissors", 3: "Paper"}

def start(update, context):
    """/start command to start the game."""
    context.bot.send_message(chat_id=update.effective_chat.id, text="Let's play")
    new_user = update.message.from_user.username

    if new_user not in current_list.keys():
        current_list[new_user] = {'win': 0, 'fail': 0, 'draw': 0}
        save_stats_to_file(current_list)
    game(update, context)
    return 0


def game(update, context):
    """Offer the user three options for an answer."""
    keyboard = [[InlineKeyboardButton("Stone", callback_data='1'),
                 InlineKeyboardButton("Scissors", callback_data='2'),
                 InlineKeyboardButton("Paper", callback_data='3')]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Make your choice", reply_markup=reply_markup)
    return 0


def answer_choice(answer_text, x):
    """Returns a string with the user's answer and the secret symbol."""
    return GAME_LIST[int(answer_text)] + ' vs ' + GAME_LIST[x]


def answer_stats(user):
    """Returns a string with the user's stats."""
    return 'W: ' + str(current_list[user]['win']) \
           + ' F: ' + str(current_list[user]['fail']) \
           + ' D: ' + str(current_list[user]['draw'])


def button(update, context):
    """
    Get the user's choice and determine the result of the round.
    Display the result of the round, the user's answer and the secret symbol.
    Display short user's stats.
    Again offer the user three options for an answer.
    """

    answer = update.callback_query
    answer_text = "{}".format(answer.data)
    user = "{}".format(answer.from_user.username)

    x = random.randint(1, 3)

    logger.info("Secret symbol: " + GAME_LIST[x])
    logger.info("User's choise: " + GAME_LIST[int(answer_text)])

    delta = x - int(answer_text)
    if delta == 0:
        current_list[user]['draw'] += 1
        save_stats_to_file(current_list)
        context.bot.send_message(chat_id=update.effective_chat.id, text='Draw ' + answer_choice(answer_text, x))
        context.bot.send_message(chat_id=update.effective_chat.id, text=answer_stats(user))
        return game(update, context)
    elif delta in (1, -2):
        current_list[user]['win'] += 1
        save_stats_to_file(current_list)
        context.bot.send_message(chat_id=update.effective_chat.id, text='You win! ' + answer_choice(answer_text, x))
        context.bot.send_message(chat_id=update.effective_chat.id, text=answer_stats(user))
        return game(update, context)
    elif delta in (2, -1):
        current_list[user]['fail'] += 1
        save_stats_to_file(current_list)
        context.bot.send_message(chat_id=update.effective_chat.id, text='Fail :( ' + answer_choice(answer_text, x))
        context.bot.send_message(chat_id=update.effective_chat.id, text=answer_stats(user))
        return game(update, context)


def cancel(update, context):
    """Exit the game."""
    textm = 'Exit game'
    context.bot.send_message(chat_id=update.effective_chat.id, text=textm)
    return ConversationHandler.END


def reset(update, context):
    """Delete user's stats."""
    textm = 'Deleted'
    user = update.message.from_user.username
    current_list[user] = {'win': 0, 'fail': 0, 'draw': 0}
    save_stats_to_file(current_list)
    context.bot.send_message(chat_id=update.effective_chat.id, text=textm)
    return ConversationHandler.END


def show_record(update, context):
    """Display general statistics for all users."""
    list = read_from_file()
    if list:
        list_sorted = sorted(list, key=lambda x: (list[x]['win'], -list[x]['fail']), reverse=True)
        textm = ""
        for i in range(len(list_sorted)):
            k = str(i+1) + '. ' + list_sorted[i] + ': ' + answer_stats(list_sorted[i]) + '\n'
            textm += k
        context.bot.send_message(chat_id=update.effective_chat.id, text=textm)
    else:
        textm = "No stats, press '/start'"
        context.bot.send_message(chat_id=update.effective_chat.id, text=textm)

def result(update, context):
    """Display general statistics for current user."""
    user = update.message.from_user.username

    current_list = read_from_file()

    try:
        textm = user + '\n' + 'Wins: ' + str(current_list[user]['win']) + '\n' +\
                'Fails: ' + str(current_list[user]['fail']) + '\n' + 'Draws: ' +\
                str(current_list[user]['draw'])
        context.bot.send_message(chat_id=update.effective_chat.id, text=textm)

    except KeyError:
        textm = "No stats for you, press '/start'"
        context.bot.send_message(chat_id=update.effective_chat.id, text=textm)

def main():
    updater = Updater(token='PUT_YOUR_TOKEN_HERE', use_context=True)
    dispatcher = updater.dispatcher

    reset_handler = CommandHandler('reset', reset)
    dispatcher.add_handler(reset_handler)

    result_handler = CommandHandler('result', result)
    dispatcher.add_handler(result_handler)

    show_record_handler = CommandHandler('records', show_record)
    dispatcher.add_handler(show_record_handler)

    updater.start_polling()  # To start the bot

    conv_handler = ConversationHandler(
        allow_reentry=True,
        entry_points=[CommandHandler('start', start)],
        states={
            0: [CallbackQueryHandler(button)],
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('reset', reset)]
    )
    dispatcher.add_handler(conv_handler)

if __name__ == '__main__':
    main()