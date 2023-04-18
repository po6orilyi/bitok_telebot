import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes, MessageHandler, ApplicationBuilder, CommandHandler

from api_connector import ApiConnector
from config import BOT_TOKEN, GROUP_ID, callback_delay_seconds, webhook_port, webhook_url
from utils import get_webtransaction_message_text, get_webtransaction_id_from_callback_string, \
    unpack_webtransaction_data, WebtransactionStatus, get_card_number

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Create ApiConnector object
api_connector = ApiConnector()

async def msg_handler(update, context):
    if update.effective_user.id == 1111111 and update.effective_user.username == 'WebhookMessageSender':
        msg_data = update.message.text
        webt_id, _, webt_card_number, webt_bank, webt_sum, webt_currency, webt_status, webt_user, _, _ = \
            unpack_webtransaction_data(msg_data)

        keyboard = [
            [
                InlineKeyboardButton("В процесі", callback_data=f'accept_order_{webt_id}'),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = get_webtransaction_message_text(webt_id=webt_id, webt_card_number=webt_card_number, webt_bank=webt_bank,
                                               webt_sum=webt_sum, webt_currency=webt_currency, hide_card_number=True)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup)


async def accept_order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    webtrsaction_id = get_webtransaction_id_from_callback_string(query.data)

    # 1. Update transaction info:
    success_update = api_connector.update_transaction_info(transaction_id=webtrsaction_id,
                                            Status=WebtransactionStatus.PROCESS, User=update.effective_user.username)
    # 2. Get new info about transaction:
    if success_update:
        transaction_data = api_connector.get_transaction_info(transaction_id=webtrsaction_id)

        webt_id, _, webt_card_number, webt_bank, webt_sum, webt_currency, webt_status, webt_user, _, _ = \
            unpack_webtransaction_data(transaction_data)

        keyboard = [
            [
                InlineKeyboardButton("В процесі ✅", callback_data='order_processing_callback'),
            ],
            [
                InlineKeyboardButton("Завершити", callback_data=f'finalize_order_{webtrsaction_id}'),
                InlineKeyboardButton("Відхилити", callback_data=f'cancel_order_{webtrsaction_id}'),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = get_webtransaction_message_text(webt_id=webt_id, webt_card_number=webt_card_number, webt_bank=webt_bank,
                                               webt_sum=webt_sum, webt_currency=webt_currency, webt_status='В процесі',
                                               webt_user=webt_user)
        await query.edit_message_text(
            text=text, reply_markup=reply_markup
        )
    else:
        text = f'@{update.effective_user.username}\nНе вдалося змінити статус заявки #{webtrsaction_id} на ' \
               f'"{WebtransactionStatus.PROCESS}". Спробуйте ще'
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


async def cancel_order(context: ContextTypes.DEFAULT_TYPE):
    context_data = context.job.data
    webtrsaction_id = get_webtransaction_id_from_callback_string(context.job.name)
    query = context_data.get('query')
    transaction_data = context_data.get('transaction_data')

    webt_id, webt_user, webt_card_number = transaction_data[0], transaction_data[7], transaction_data[2]

    success_update = api_connector.update_transaction_info(transaction_id=webtrsaction_id,
                                                           Status=WebtransactionStatus.CANCELED,
                                                           Card=get_card_number(card_number=webt_card_number,
                                                                                hide_number=True)
                                                           )
    if success_update:
        updated_transaction_data = api_connector.get_transaction_info(transaction_id=webtrsaction_id)
        webt_id, _, webt_card_number, webt_bank, webt_sum, webt_currency, webt_status, webt_user, _, _ = \
            unpack_webtransaction_data(updated_transaction_data)
        if webt_status == WebtransactionStatus.CANCELED:
            text = get_webtransaction_message_text(webt_id=webt_id, webt_card_number=webt_card_number,
                                                   webt_bank=webt_bank, webt_sum=webt_sum,
                                                   webt_currency=webt_currency, webt_user=webt_user,
                                                   webt_status='Відхилено ❌')
            await query.edit_message_text(text=text)
    else:
        text = f'@{update.effective_user.username}\nНе вдалося змінити статус заявки #{webtrsaction_id} на ' \
               f'"{WebtransactionStatus.CANCELED}". Спробуйте ще'
        await context.bot.send_message(chat_id=context.job.chat_id, text=text)


async def order_processing_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()


async def finalize_order(context: ContextTypes.DEFAULT_TYPE):
    context_data = context.job.data
    webtrsaction_id = get_webtransaction_id_from_callback_string(context.job.name)
    query = context_data.get('query')
    transaction_data = context_data.get('transaction_data')
    webt_id, webt_user, webt_card_number = transaction_data[0], transaction_data[7], transaction_data[2]

    success_update = api_connector.update_transaction_info(transaction_id=webtrsaction_id,
                                                           Status=WebtransactionStatus.SUCCESS,
                                                           Card=get_card_number(card_number=webt_card_number,
                                                                                hide_number=True)
                                                           )
    if success_update:
        updated_transaction_data = api_connector.get_transaction_info(transaction_id=webtrsaction_id)
        webt_id, _, webt_card_number, webt_bank, webt_sum, webt_currency, webt_status, webt_user, _, _ = \
            unpack_webtransaction_data(updated_transaction_data)
        if webt_status == WebtransactionStatus.SUCCESS:
            text = get_webtransaction_message_text(webt_id=webt_id, webt_card_number=webt_card_number,
                                                   webt_bank=webt_bank, webt_sum=webt_sum,
                                                   webt_currency=webt_currency, webt_user=webt_user,
                                                   webt_status='Завершено✅')
            await query.edit_message_text(text=text)
    else:
        text = f'@{update.effective_user.username}\nНе вдалося змінити статус заявки #{webtrsaction_id} на ' \
               f'"{WebtransactionStatus.SUCCESS}". Спробуйте ще'
        await context.bot.send_message(chat_id=context.job.chat_id, text=text)


async def order_action_callback_delayed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    webtrsaction_id = get_webtransaction_id_from_callback_string(query.data)
    transaction_data = api_connector.get_transaction_info(transaction_id=webtrsaction_id)
    transaction_data = unpack_webtransaction_data(transaction_data)
    webt_id, webt_user = transaction_data[0], transaction_data[7]

    if webt_user == update.effective_user.username and webt_id == webtrsaction_id:

        settings = {
            'cancel_order': {'callback_func': cancel_order, 'text': 'ВІДХИЛЕНО'},
            'finalize_order': {'callback_func': finalize_order, 'text': 'ЗАВЕРШЕНО'}
        }

        action_signature = 'cancel_order' if 'cancel_order' in query.data else 'finalize_order'

        context.job_queue.run_once(settings[action_signature]['callback_func'], callback_delay_seconds,
                                   data={'query': query, 'transaction_data': transaction_data},
                                   name=query.data, chat_id=update.effective_chat.id, user_id=update.effective_user.id)

        text = query.message.text + '\n\n' + f'<b>Транзакцію буде {settings[action_signature]["text"]} через ' \
                                             f'{callback_delay_seconds} секунд</b>'
        keyboard = [
            [
                InlineKeyboardButton("Відмінити дію ↩",
                                     callback_data=f'undo_last_action-{action_signature}_{webtrsaction_id}'),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=text, reply_markup=reply_markup, parse_mode='HTML'
        )
    else:
        print('WRONG USER PRESSED | ' * 50)

async def undo_last_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    job_name = query.data.split('-')[-1]
    jobs_to_be_canceled = context.job_queue.get_jobs_by_name(job_name)

    jobs_belong_to_the_user_called_this_callback = True
    # Cancel jobs
    for job in jobs_to_be_canceled:
        if job.user_id == update.effective_user.id:
            job.schedule_removal()
        else:
            jobs_belong_to_the_user_called_this_callback = False
            print('WRONG USER PRESSED | '*50)
            break

    if jobs_belong_to_the_user_called_this_callback:
        await accept_order_callback(update, context)



if __name__ == '__main__':
    os.environ['TELEGRAM_GROUP_ID'] = str(GROUP_ID)

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(MessageHandler(None, msg_handler))
    application.add_handler(CallbackQueryHandler(accept_order_callback, pattern=r'accept_order_\d*'))
    application.add_handler(CallbackQueryHandler(order_processing_callback, pattern=r'order_processing_\d*'))
    application.add_handler(CallbackQueryHandler(order_action_callback_delayed, pattern=r'(finalize|cancel)_order_\d*'))
    application.add_handler(CallbackQueryHandler(undo_last_action_callback,
                                                 pattern=r'undo_last_action-(finalize|cancel)_order_\d*'))

    application.run_webhook(
    listen='0.0.0.0',
    port=webhook_port,
    url_path='webtransaction',
    key='./ssl-keys/private.key',
    cert='./ssl-keys/cert.pem',
    webhook_url=webhook_url,
)
