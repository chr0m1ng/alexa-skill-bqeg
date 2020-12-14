from date_service import get_user_datetime, hour_diff, delta_to_time
from functools import reduce
from base64 import b64encode
import requests

TANGERINO_BASE_URL = 'https://app.tangerino.com.br/Tangerino/ws'

def get_user_auth(user_id, emp):
    encoded_part = b64encode(f'{user_id}:{emp}'.encode('ascii')).decode('ascii')
    return f'Basic {encoded_part}'

def get_user_summary(user_id, emp):
    authorization = get_user_auth(user_id, emp)
    headers = {
        'authorization': authorization,
        'funcionarioId': str(user_id)
    }
    res = requests.get(f'{TANGERINO_BASE_URL}/funcionarioWS/sumario/{user_id}', headers=headers)
    return res.json()

def punch_in(user_id, emp, pin, date):
    authorization = get_user_auth(user_id, emp)
    headers = {
        'authorization': authorization,
        'empregador': emp,
        'funcionarioId': str(user_id),
        'pin': pin,
        'username': str(user_id)
    }
    body = {
        'horaInicio': date.strftime('%d/%m/%Y %H:%M:%S'),
        'deviceId': None,
        'online': 'true',
        'codigoEmpregador': emp,
        'pin': pin,
        'horaFim': '',
        'tipo': 'WEB',
        'foto': '',
        'intervalo': '',
        'validFingerprint': False,
        'versao': 'registra-ponto-fingerprint',
        'plataforma': 'WEB',
        'funcionarioid': user_id,
        'idAtividade': 6,
        'latitude': None,
        'longitude': None
    }
    res = requests.post(f'{TANGERINO_BASE_URL}/pontoWS/ponto/sincronizacaoPontos/1.2', headers=headers, json=body)
    res = res.json()
    return res['mensagemDetalhada']

def allow_device(emp, pin):
    requests.post(f'{TANGERINO_BASE_URL}/autorizaDipositivoWS/verifica/web/empregador/{emp}/pin/{pin}', json={'deviceId': None})

def get_user_info(emp, pin):
    res = requests.get(f'{TANGERINO_BASE_URL}/fingerprintWS/funcionario/empregador/{emp}/pin/{pin}')
    return res.json()

def get_user_id(emp, pin):
    user = get_user_info(emp, pin)
    return user['funcionario']['id']

def punch_tangerino(handler_input, emp, pin):
    tang_id = get_user_id(emp, pin)
    allow_device(emp, pin)
    current_dt = get_user_datetime(handler_input)
    return punch_in(tang_id, emp, pin, current_dt)

def calculate_punchs(handler_input, punchs):
    punch_deltas = []
    for punch in punchs:
        init = punch['dataEntrada']
        final = punch['dataSaida'] if 'dataSaida' in punch else None
        punch_deltas.append(hour_diff(handler_input, init, final))
    return punch_deltas

def is_working(today_punchs):
    return 'dataSaida' not in today_punchs[-1]

def get_working_hours(handler_input, emp, pin):
    tang_id = get_user_id(emp, pin)
    user_summary = get_user_summary(tang_id, emp)
    today_punchs = user_summary['hoje']['marcacoes']
    punch_deltas = calculate_punchs(handler_input, today_punchs)
    return { **delta_to_time(reduce(lambda x, y: x + y, punch_deltas)), 'is_working': is_working(today_punchs) }
