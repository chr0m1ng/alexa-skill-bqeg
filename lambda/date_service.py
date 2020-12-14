from pytz import timezone
from datetime import datetime
import requests

def delta_to_time(tdelta):
    time = {'days': tdelta.days}
    time['hours'], rem = divmod(tdelta.seconds, 3600)
    time['minutes'], time['seconds'] = divmod(rem, 60)
    return time

def get_user_datetime(handler_input):
    # get device id
    sys_object = handler_input.request_envelope.context.system
    device_id = sys_object.device.device_id
    
    # get Alexa Settings API information
    api_endpoint = sys_object.api_endpoint
    api_access_token = sys_object.api_access_token
    
    # construct systems api timezone url
    url = f'{api_endpoint}/v2/devices/{device_id}/settings/System.timeZone'
    headers = {'Authorization': f'Bearer {api_access_token}'}
    
    res = requests.get(url, headers=headers)
    res = res.json()
    return datetime.now(timezone(res))

def hour_diff(handler_input, initial, final=None):
    initial = datetime.fromisoformat(initial)
    if final is None:
        final = get_user_datetime(handler_input).replace(tzinfo=None)
    else:
        final = datetime.fromisoformat(final)
    return final - initial
