import math
import dateutil.parser
import datetime
import time
import os
import logging
import rds_config
import sys
import pymysql

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

rds_host  = rds_config.db_endpoint
name = rds_config.db_username
password = rds_config.db_password
db_name = rds_config.db_name

try:
    conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
except:
    logger.error("ERROR: Unexpected error: Could not connect to MySQL instance.")
    sys.exit()

logger.info("SUCCESS: Connection to RDS MySQL instance succeeded")
""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """


def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


""" --- Helper Functions --- """


def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')


def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False

""" --- Functions that control the bot's behavior --- """

def get_package_price(package_name):
    prices = {'gold': 32000, 'premium': 52000, 'trail': 5000}
    return prices[package_name.lower()]


def validate_package_details(package_name):
    package_names = ['gold', 'premium', 'trail']
    if package_name is not None and package_name.lower() not in package_names:
        return build_validation_result(False,
                                       'PACKAGE_NAME',
                                       'We do not have {}, would you like a different type of package?  Our most popular package is trail'.format(package_name))

    return build_validation_result(True, None, None)

""" --- Functions that control the bot's behavior --- """
def package_overview(intent_request):
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'we have gold, premium and trail package'})

def package_details(intent_request):
    package_name = get_slots(intent_request)["PACKAGE_NAME"]
    slots = get_slots(intent_request)

    validation_result = validate_package_details(package_name)

    if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                              intent_request['currentIntent']['name'],
                              slots,
                              validation_result['violatedSlot'],
                              validation_result['message'])

    price = get_package_price(package_name)

    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': '{} will cost {}. Thanks for visiting us. Bye'.format(package_name,price)})

""" ---Distribution status intent """

def distribution_status(intent_request):
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'within 5 to 7 days of paid out date, you will get the cash'})


    # return 'Added {} items from RDS MySQL table'.format(emp_name)

""" ---Distribution send form intent function """
def validate_send_distribution_form(distr_type):
    distr_type_list = ['inservice', 'hardship', 'termination']
    str_distr_types=', '.join(str(x) for x in distr_type_list)
    if distr_type is not None and distr_type.lower() not in distr_type_list:
        return build_validation_result(False,
                                       'Distr_Type',
                                       'We do not have {} distibution type for now, we have {} distribution\n'.format(distr_type,str_distr_types))

    return build_validation_result(True, None, None)



def send_distribution_form(intent_request):
    distr_type = get_slots(intent_request)["Distr_Type"]
    slots = get_slots(intent_request)

    validation_result = validate_send_distribution_form(distr_type)

    if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                              intent_request['currentIntent']['name'],
                              slots,
                              validation_result['violatedSlot'],
                              validation_result['message'])  

    form_url = ''
    if distr_type == 'inservice':
        form_url = 'https://drive.google.com/open?id=18C-21BgREbpBDHXMocuyxid44j_GXVG0A8ykAXumjqg'
    elif  distr_type == 'hardship':
        form_url = 'https://drive.google.com/open?id=11ugYWLyFmza5HLU80dR93wGCB-5z6xi2ygvLFxymPcU'
    elif  distr_type == 'termination':
        form_url = 'https://drive.google.com/open?id=1xysHuqpQbTrCRS3CxoC0FO8Zu4ZGqn8msEXll1lbCGs'
    else:
        form_url = distr_type+ ' No Url Found'

    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'Here is the form link \n\n {} \n\n'.format(form_url)})



def get_person_account_balance(first_name,last_name,dob):
    sql_query = "select AccountBalance from rkstatement_personhistory  where FIRSTNAM='{}' and LASTNAM='{}' and DOB='{}'  limit 1;".format(first_name,last_name,dob)
    logger.info(sql_query)
    with conn.cursor() as cur:        
        cur.execute(sql_query)
        for row in cur:
            logger.info('test log'+ str(row[0])+' USD')
            return str(row[0])+' USD'

    return 'Sorry we are unable to find you in our system. Thank you.'

def SSNAccountBal(intent_request):
    logger.info(slots["Birth_Date"])
    slot_list=get_slots(intent_request)
    first_name=slot_list["First_Name"]
    last_name=slot_list["Last_Name"]
    dob=slot_list["Birth_Date"]

    bal_info=get_person_account_balance(first_name,last_name,dob)
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'Your current account balance is {}'.format(bal_info)})


def get_person_loan_balance(first_name,last_name,dob):
    sql_query="select AccountBalance from rkstatement_personhistory   where FIRSTNAM='{}' and LASTNAM='{}' and DOB='{}'  limit 1;".format(first_name,last_name,dob)
    with conn.cursor() as cur:        
        cur.execute(sql_query)
        for row in cur:
            logger.info('test log'+ str(row[0])+' USD')
            return str(row[0])+' USD'

    return 'Sorry we are unable to find you in our system. Thank you.'

def SSNLoanBal(intent_request):
    slot_list=get_slots(intent_request)
    first_name=slot_list["First_Name"]
    last_name=slot_list["Last_Name"]
    dob=slot_list["Birth_Date"]

    bal_info=get_person_loan_balance(first_name,last_name,dob)
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'Your current loan balance is {}'.format(bal_info)})



""" --- Intents --- """


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'PackageOverview':
        return package_overview(intent_request)
    if intent_name == 'PackageDetails':
        return package_details(intent_request)
    if intent_name == 'DistributionStatus':
        return distribution_status(intent_request)
    if intent_name == 'SendDistributionForm':
        return send_distribution_form(intent_request)
    if intent_name == 'SSNLoanBal':
        return SSNLoanBal(intent_request)
    if intent_name == 'SSNAccountBal':
        return SSNAccountBal(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """

def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)