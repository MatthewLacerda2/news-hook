import logging
from typing import Dict

logger = logging.getLogger(__name__)

def t(key: str, language_code: str = None) -> str:
    """
    Get translation for key and language code.
    If language_code is 'pt' and exists, return Portuguese.
    Otherwise, return English.
    """
    translations = {
        'en': {
            "alert.create.prompt_required": "Please provide a prompt after /create",
            "alert.create.already_exists": "That Alert is already active",
            "alert.create.processing": "Ok, let me see . . . . .",
            "alert.create.validation_failed": "I'm sorry, I cannot create an alert for that\n\n<b>Reason:</b> {reason}",
            "alert.create.success": "Got it! Alert created!\nWill be active until <b>{expire_date}</b>\n\n<b>{keywords}</b>",
            "alert.cancel.id_required": "Please provide an alert ID after <b>/cancel</b>",
            "alert.cancel.not_found": "That alert does not exist.",
            "alert.cancel.success": "Alert cancelled!",
            "alert.list.no_alerts": "There are no active alerts.",
            "alert.list.item": "<b>Alert</b>: {prompt}\n<b>Expires At: {expire_date}</b>\n<b>Id</b>: {alert_id}\n\n",
            "help.message": "Use:\n\n<b>/create &lt;prompt&gt;: to create an alert</b>\n<b>/cancel &lt;alert_id&gt;: to cancel the alert</b>\n<b>/list</b>: To list all active alerts\n\nExample: <b>/create</b> Inform me if the price of BTC is below $30,000.",
            "help.unknown_command": "Unknown command. {help_message}",
            "error.request_too_brief": "Your request is too brief.",
            "error.no_message": "No message found in update",
            "error.no_text": "No text found in message",
            "error.no_user_id": "No user ID found in message"
        },
        'pt': {
            "alert.create.prompt_required": "Por favor, forneça um prompt após /create",
            "alert.create.already_exists": "Esse Alerta já está ativo",
            "alert.create.processing": "Ok, deixe-me ver . . . . .",
            "alert.create.validation_failed": "Desculpe, não posso criar um alerta para isso\n\n<b>Motivo:</b> {reason}",
            "alert.create.success": "Pronto! Alerta criado!\nEstará ativo até <b>{expire_date}</b>\n\n<b>{keywords}</b>",
            "alert.cancel.id_required": "Por favor, forneça um ID de alerta após <b>/cancel</b>",
            "alert.cancel.not_found": "Esse alerta não existe.",
            "alert.cancel.success": "Alerta cancelado!",
            "alert.list.no_alerts": "Não há alertas ativos.",
            "alert.list.item": "<b>Alerta</b>: {prompt}\n<b>Expira em: {expire_date}</b>\n<b>Id</b>: {alert_id}\n\n",
            "help.message": "Use:\n\n<b>/create &lt;prompt&gt;: para criar um alerta</b>\n<b>/cancel &lt;alert_id&gt;: para cancelar o alerta</b>\n<b>/list</b>: Para listar todos os alertas ativos\n\nExemplo: <b>/create</b> Informe-me se o preço do BTC estiver abaixo de $30.000.",
            "help.unknown_command": "Comando desconhecido. {help_message}",
            "error.request_too_brief": "Sua solicitação é muito breve.",
            "error.no_message": "Nenhuma mensagem encontrada na atualização",
            "error.no_text": "Nenhum texto encontrado na mensagem",
            "error.no_user_id": "Nenhum ID de usuário encontrado na mensagem"
        }
    }
    
    # Try the given language code first, fallback to 'en'
    target_lang = language_code if language_code in translations else 'en'
    return translations[target_lang].get(key, key)