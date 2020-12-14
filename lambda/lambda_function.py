# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging
import ask_sdk_core.utils as ask_utils

from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model.dialog import ElicitSlotDirective
from ask_sdk_model import Response, DialogState
from tangerino_service import punch_tangerino, get_working_hours
from db_service import get_db_adapter
from utils import get_slot_canonical_name

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

HELP_TEXT = 'Você pode me pedir para bater ponto, calcular as horas trabalhadas ou cadastrar o código do empregador e pin do funcionário. O que deseja?'
FINISHED_LOGIN_TEXT = 'Quer bater o ponto ou consultar as horas trabalhas? é só me perguntar "quantas horas trabalhei?" ou "bater o ponto"'
ASK_PIN_TEXT = 'Para me contar qual é o seu pin, basta dizer: "Meu pin é 1234"'
ASK_EMP_TEXT = 'Para me contar qual é o seu código, basta dizer: "Meu código de empregado é A12BC"'

ERROR_TEXT = lambda action: f'Desculpe, não foi possível {action}, tente novamente'

EMP_KEY = 'emp_code'
PIN_KEY = 'pin_code'

def get_user_credentials(handler_input):
    attrs = handler_input.attributes_manager.persistent_attributes
    emp_code = attrs[EMP_KEY] if EMP_KEY in attrs else None
    pin_code = attrs[PIN_KEY] if PIN_KEY in attrs else None
    handler_input.attributes_manager.session_attributes[EMP_KEY] = emp_code
    handler_input.attributes_manager.session_attributes[PIN_KEY] = pin_code
    return emp_code, pin_code

def try_action_with_user(handler_input, action):
    emp, pin = get_user_credentials(handler_input)
    ask = None
    if emp is None:
        ask = ASK_EMP_TEXT
        speak = f'Você precisa me falar o seu código de empregador primeiro. {ask}'
    elif pin is None:
        ask = ASK_PIN_TEXT
        speak = f'Você precisa me falar o seu pin primeiro. {ask}'
    else:
        speak = action(handler_input, emp, pin)
    return speak, ask

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        session_attr = handler_input.attributes_manager.session_attributes
        speak_output = f'Bem vindo ao bate que eu gósto. {HELP_TEXT}'

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(HELP_TEXT)
                .response
        )
    
class PunchInIntentHandler(AbstractRequestHandler):
    """Handler for Punch In Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("PunchInIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        speak = ERROR_TEXT('dropar a caneta')
        ask = None
        try:
            speak, ask = try_action_with_user(handler_input, punch_tangerino)
        except Exception as ex:
            logger.error(ex)

        output = handler_input.response_builder.speak(speak)
        if ask is not None:
            output.ask(ask)
        return output.response

class CurrentWorkingHourIntentHandler(AbstractRequestHandler):
    """Handler for Current Working Hour Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("CurrentWorkingHourIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        speak = ERROR_TEXT('calcular suas horas trabalhadas')
        ask = None

        try:
            working_hours, ask = try_action_with_user(handler_input, get_working_hours)
            if ask is None:
                if working_hours['is_working']:
                    current_status = 'está trabalhando'
                    ask = 'Caso queira bater o ponto basta pedir'
                else:
                    current_status = 'trabalhou'

                speak = f'Você {current_status} por {working_hours["hours"]} horas e {working_hours["minutes"]} minutos. '

                if working_hours['hours'] >= 8 and working_hours['is_working']:
                    speak += 'Já passou das 8 horas trabalhadas, está na hora de parar'
            else:
                speak = working_hours
        except Exception as ex:
            logger.error(ex)
        
        output = handler_input.response_builder.speak(speak)
        if ask is not None:
            output.ask(ask)

        return output.response

class EmpCodeIntentHandler(AbstractRequestHandler):
    """Handler for Emp Code Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("EmpCodeIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        res = ERROR_TEXT('salvar seu código de empregador')
        
        try:
            emp_code = get_slot_canonical_name(handler_input, EMP_KEY)
            attr = handler_input.attributes_manager.persistent_attributes
            attr[EMP_KEY] = emp_code
            handler_input.attributes_manager.session_attributes = attr
            handler_input.attributes_manager.save_persistent_attributes()
            
            reprompt = ASK_PIN_TEXT if PIN_KEY not in attr else FINISHED_LOGIN_TEXT
            res = f'Salvei o seu código de empregador como {emp_code}, da próxima vez você não vai precisar me informar. {reprompt}'
            
        except Exception as ex:
            logger.error(ex)
        
        return (
            handler_input.response_builder
                .speak(res)
                .ask(reprompt)
                .response
        )

class PinCodeIntentHandler(AbstractRequestHandler):
    """Handler for Pin Code Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("PinCodeIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        res = ERROR_TEXT('salvar seu pin')
        
        try:
            pin_code = handler_input.request_envelope.request.intent.slots[PIN_KEY].value
            attr = handler_input.attributes_manager.persistent_attributes
            attr[PIN_KEY] = pin_code
            handler_input.attributes_manager.session_attributes = attr
            handler_input.attributes_manager.save_persistent_attributes()
            
            reprompt = ASK_EMP_TEXT if EMP_KEY not in attr else FINISHED_LOGIN_TEXT
            res = f'Salvei o seu pin como {pin_code}, da próxima vez você não vai precisar me informar. {reprompt}'
            
        except Exception as ex:
            logger.error(ex)
        
        return (
            handler_input.response_builder
                .speak(res)
                .ask(reprompt)
                .response
        )


class EraseDataIntentHandler(AbstractRequestHandler):
    """Handler for Erase Data Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("EraseDataIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        res = ERROR_TEXT('apagar seus dados')
        
        try:
            pin_code = handler_input.request_envelope.request.intent.slots[PIN_KEY].value
            attr = handler_input.attributes_manager.persistent_attributes
            if PIN_KEY in attr:
                del attr[PIN_KEY]
            if EMP_KEY in attr:
                del attr[EMP_KEY]

            handler_input.attributes_manager.session_attributes = attr
            handler_input.attributes_manager.delete_persistent_attributes()
            
            res = 'Deletei todos os seus dados, da próxima vez você vai precisar me informar. Adeus'
            
        except Exception as ex:
            logger.error(ex)
        
        return (
            handler_input.response_builder
                .speak(res)
                .response
        )

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        return (
            handler_input.response_builder
                .speak(HELP_TEXT)
                .ask(HELP_TEXT)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Adeus!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "Você ativou " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = ERROR_TEXT('executar esta ação')

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = CustomSkillBuilder(persistence_adapter=get_db_adapter())

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(PunchInIntentHandler())
sb.add_request_handler(CurrentWorkingHourIntentHandler())
sb.add_request_handler(EmpCodeIntentHandler())
sb.add_request_handler(PinCodeIntentHandler())
sb.add_request_handler(EraseDataIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()