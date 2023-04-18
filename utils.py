class WebtransactionStatus:
    DEFAULT = 'waiting'
    PROCESS = 'process'
    CANCELED = 'canceled'
    SUCCESS = 'success'



def get_webtransaction_message_text(
        webt_id: int,
        webt_card_number: str,
        webt_bank: str,
        webt_sum: float,
        webt_currency: str,
        webt_status: str = None,
        webt_user: str = None,
        hide_card_number: bool = False
) -> str:

    card_number = get_card_number(webt_card_number, hide_card_number)
    result_str = ''
    result_str += f'Карта: {card_number}\n'
    result_str += f'Сума: {webt_sum}\n'
    result_str += f'Валюта: {webt_currency}\n'
    result_str += f'Банк: {webt_bank}\n'
    result_str += f'id: {webt_id}\n'
    result_str += f'Статус: {webt_status if webt_user else "Нова заявка"}\n'
    result_str += f'Оператор: {"@"+webt_user if webt_user else "-"}'
    return result_str

def get_card_number(card_number: str, hide_number: bool) -> str:
    card_number_ = card_number.replace('-', '').replace(' ', '')
    if hide_number:
        card_number_ = f'{card_number_[:4]}****{card_number_[12:]}'
    return card_number_

def get_webtransaction_id_from_callback_string(callback_string: str) -> int:
    webtrsaction_id = callback_string.split('_')[-1]
    return int(webtrsaction_id)


def unpack_webtransaction_data(webtransaction_data: dict) -> tuple:
    webt_id = webtransaction_data.get('Id')
    webt_account_id = webtransaction_data.get('AccountId')
    webt_card_number = webtransaction_data.get('Card')
    webt_bank = webtransaction_data.get('Bank')
    webt_sum = webtransaction_data.get('Summ')
    webt_currency = webtransaction_data.get('Currency')
    webt_status = webtransaction_data.get('Status')
    webt_user = webtransaction_data.get('User')
    webt_date_create = webtransaction_data.get('DateCreate')
    webt_date_update = webtransaction_data.get('DateUpdate')
    return (
        webt_id,
        webt_account_id,
        webt_card_number,
        webt_bank,
        webt_sum,
        webt_currency,
        webt_status,
        webt_user,
        webt_date_create,
        webt_date_update
    )


