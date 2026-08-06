import datetime
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

def get_calendar_service():
    """Autentica na Google Calendar API usando o Refresh Token."""
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/calendar"]
    )

    if not creds.valid:
        creds.refresh(Request())

    return build("calendar", "v3", credentials=creds)

def create_calendar_event(title: str, start_time: str, end_time: str, description: str = "") -> str:
    """
    Cria um evento no Google Calendar.
    `start_time` e `end_time` devem estar no formato ISO (ex: '2026-07-31T15:00:00+01:00').
    """
    try:
        service = get_calendar_service()
        event = {
            'summary': title,
            'description': description,
            'start': {'dateTime': start_time, 'timeZone': 'Europe/Lisbon'},
            'end': {'dateTime': end_time, 'timeZone': 'Europe/Lisbon'},
        }
        
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        return f"Evento '{title}' agendado com sucesso no Google Calendar."
    except Exception as e:
        return f"Erro ao criar evento: {str(e)}"

def list_calendar_events(start_date: str, end_date: str) -> str:
    """
    Consulta eventos do Google Calendar entre `start_date` e `end_date` (formato ISO 'YYYY-MM-DDTHH:MM:SSZ').
    """
    try:
        service = get_calendar_service()
        events_result = service.events().list(
            calendarId='primary', 
            timeMin = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
            maxResults=5, # Não pedir 100 eventos de uma vez para não demorar
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        if not events:
            return "Nenhum evento encontrado para este período."
        
        output = "Eventos no Calendário:\n"
        for e in events:
            start = e['start'].get('dateTime', e['start'].get('date'))
            output += f"- {e.get('summary', 'Sem Título')} em {start}\n"
        return output
    except Exception as e:
        return f"Erro ao listar eventos: {str(e)}"
    
def apagar_evento_calendario(nome_do_evento: str) -> str:
    """
    Procura um evento no calendário pelo nome e apaga-o.
    """
    try:
        service = get_calendar_service()
        # 1. Procurar os próximos eventos para encontrar o ID
        # A forma moderna de ir buscar a hora UTC (precisa do timezone)
        agora = datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
        eventos_result = service.events().list(
            calendarId='primary', 
            timeMin=agora,
            maxResults=15, 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        eventos = eventos_result.get('items', [])
        
        if not eventos:
            return "Não tens eventos futuros marcados."

        # 2. Procurar uma correspondência no nome
        for evento in eventos:
            # Compara tudo em minúsculas para não falhar por causa de maiúsculas
            if nome_do_evento.lower() in evento.get('summary', '').lower():
                evento_id = evento['id']
                nome_real = evento.get('summary', '')
                
                # 3. Apagar o evento usando o ID
                service.events().delete(calendarId='primary', eventId=evento_id).execute()
                
                return f"Feito! O evento '{nome_real}' foi apagado da tua agenda com sucesso."
                
        return f"Não consegui encontrar nenhum evento com o nome '{nome_do_evento}' para apagar."
        
    except Exception as e:
        # AGORA VAMOS VER O ERRO NO TERMINAL!
        print("------- ERRO AO APAGAR NO CALENDÁRIO -------")
        print(e)
        print("--------------------------------------------")
        return f"Erro técnico ao apagar: {str(e)}"
    

# --- Lembra-te de usar o nome correto da tua variável 'service' aqui ---
# Se a tua variável se chama 'meu_calendario', troca 'service' por 'meu_calendario' abaixo.

def editar_evento_calendario(
    nome_atual: str,
    novo_titulo: str = None,
    nova_data_inicio: str = None,  # Formato 'YYYY-MM-DD'
    nova_hora_inicio: str = None,  # Formato 'HH:MM:SS'
    nova_data_fim: str = None,     # Formato 'YYYY-MM-DD'
    nova_hora_fim: str = None      # Formato 'HH:MM:SS'
) -> str:
    """
    Procura um evento pelo nome e atualiza as informações fornecidas.
    Se um campo não for fornecido (None), ele mantém a informação original.
    """
    try:
        service = get_calendar_service()
        # 1. ENCONTRAR O EVENTO (igual à função de apagar)
        # A forma moderna de ir buscar a hora UTC (precisa do timezone)
        agora = datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
        eventos_result = service.events().list(
            calendarId='primary',
            timeMin=agora,
            maxResults=20,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        eventos = eventos_result.get('items', [])
        evento_a_editar = None

        for evento in eventos:
            if nome_atual.lower() in evento.get('summary', '').lower():
                evento_a_editar = evento
                break

        if not evento_a_editar:
            return f"Não encontrei nenhum evento futuro com o nome '{nome_atual}'."

        evento_id = evento_a_editar['id']
        
        # 2. CONSTRUIR O CORPO DA ATUALIZAÇÃO (Patch Body)
        patch_body = {}

        if novo_titulo:
            patch_body['summary'] = novo_titulo

        # O segredo está aqui: ir buscar os horários originais do evento
        start_original = evento_a_editar.get('start', {})
        end_original = evento_a_editar.get('end', {})
        
        timezone = 'Europe/Lisbon'

        # TRATAR O INÍCIO
        if nova_data_inicio and nova_hora_inicio:
            patch_body['start'] = {
                'dateTime': f"{nova_data_inicio}T{nova_hora_inicio}",
                'timeZone': timezone
            }
        else:
            # Se não pediste para mudar o início, forçamos o antigo
            patch_body['start'] = start_original 

        # TRATAR O FIM
        if nova_data_fim and nova_hora_fim:
            patch_body['end'] = {
                'dateTime': f"{nova_data_fim}T{nova_hora_fim}",
                'timeZone': timezone
            }
        else:
            # Se não pediste para mudar o fim, forçamos o antigo
            patch_body['end'] = end_original

        if not novo_titulo and not nova_data_inicio and not nova_data_fim:
            return "Não forneceste nenhuma informação nova para atualizar o evento."

        # 3. ENVIAR AS ALTERAÇÕES (Usando patch para atualização parcial)
        evento_atualizado = service.events().patch(
            calendarId='primary',
            eventId=evento_id,
            body=patch_body
        ).execute()

        return f"Feito! O evento '{nome_atual}' foi atualizado com sucesso para '{evento_atualizado.get('summary')}'."

    except Exception as e:
        print(f"Erro técnico ao editar: {e}")
        return f"Ocorreu um erro ao tentar editar o evento: {str(e)}"