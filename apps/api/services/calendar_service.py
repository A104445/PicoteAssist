import datetime
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from state import current_google_token

def get_calendar_service():
    """Autentica na Google Calendar API usando o token em memória (Stateless)."""
    # 1. Vai buscar o token do utilizador isolado neste pedido
    token_do_user = current_google_token.get()
    
    if not token_do_user:
        raise Exception("Autenticação necessária. Clica no botão 'Conectar Google' primeiro.")
        
    # 2. Constrói as credenciais diretamente a partir do .env e do token recebido
    creds = Credentials(
        token=None,
        refresh_token=token_do_user,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ.get("GOOGLE_CLIENT_ID"),
        client_secret=os.environ.get("GOOGLE_CLIENT_SECRET")
    )
    
    # 3. Devolve o serviço construído para o calendário
    return build("calendar", "v3", credentials=creds)

def create_calendar_event(title: str, start_time: str, end_time: str, description: str = "", todo_o_dia: bool = False) -> str:
    """
    Cria um evento no Google Calendar.
    `start_time` e `end_time` devem estar no formato ISO (ex: '2026-07-31T15:00:00+01:00').
    """
    try:
        service = get_calendar_service()
        
        event = {
            'summary': title,
            'description': description,
        }
        
        # --- NOVA LÓGICA DE NOTIFICAÇÕES ---
        # Palavras que não queremos que o telemóvel apite
        palavras_silenciosas = ['almoço', 'jantar', 'lanche', 'pequeno-almoço', 'dormir', 'sono', 'refeição', 'pequeno almoço']
        
        if any(p in title.lower() for p in palavras_silenciosas):
            # Desativa o alarme padrão e não coloca nenhum
            event['reminders'] = {
                'useDefault': False,
                'overrides': []
            }
        else:
            # Desativa o padrão de 30 mins e coloca o teu de 15 mins
            event['reminders'] = {
                'useDefault': False,
                'overrides': [{'method': 'popup', 'minutes': 15}]
            }
        
        if todo_o_dia:
            # Extrai apenas a parte da data (YYYY-MM-DD) cortando a string ISO
            data_inicio = start_time[:10]
            
            # A Google exige que a data de fim seja o dia SEGUINTE
            inicio_obj = datetime.datetime.strptime(data_inicio, "%Y-%m-%d")
            fim_obj = inicio_obj + datetime.timedelta(days=1)
            data_fim_final = fim_obj.strftime("%Y-%m-%d")
            
            event['start'] = {'date': data_inicio}
            event['end'] = {'date': data_fim_final}
        else:
            event['start'] = {'dateTime': start_time, 'timeZone': 'Europe/Lisbon'}
            event['end'] = {'dateTime': end_time, 'timeZone': 'Europe/Lisbon'}
            
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
        
        # Prevenção: a Google exige que o formato termine em 'Z' (UTC). 
        # Se o modelo do Gemini se esquecer, o Python acrescenta:
        if not start_date.endswith('Z'): start_date += 'Z'
        if not end_date.endswith('Z'): end_date += 'Z'
        
        events_result = service.events().list(
            calendarId='primary', 
            timeMin=start_date,  # <-- Agora olha para o início do dia!
            timeMax=end_date,    # <-- E para de olhar no fim do dia!
            maxResults=30, 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        if not events:
            return "Nenhum evento encontrado para este período."
            
        output = "Eventos no Calendário:\n"
        for e in events:
            start = e['start'].get('dateTime', e['start'].get('date'))
            desc = e.get('description', 'Sem descrição atual.')
            output += f"- {e.get('summary', 'Sem Título')} em {start} | Descrição: {desc}\n"
        return output
    except Exception as e:
        return f"Erro ao listar eventos: {str(e)}"
    
def apagar_evento_calendario(nome_do_evento: str) -> str:
    """
    Procura um evento no calendário pelo nome e apaga-o.
    """
    try:
        service = get_calendar_service()
        
        # 1. Procurar os eventos (recuando 7 dias para apanhar lixo e testes antigos)
        passado = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)).isoformat().replace('+00:00', 'Z')
        
        eventos_result = service.events().list(
            calendarId='primary', 
            timeMin=passado,
            maxResults=100,  # Aumentámos a margem
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        eventos = eventos_result.get('items', [])
        
        if not eventos:
            return "Não tens eventos recentes marcados."
            
        # 2. Procurar uma correspondência (lendo de trás para a frente para apagar o mais recente)
        for evento in reversed(eventos):
            if nome_do_evento.lower() in evento.get('summary', '').lower():
                evento_id = evento['id']
                nome_real = evento.get('summary', '')
                
                # 3. Apagar o evento usando o ID
                service.events().delete(calendarId='primary', eventId=evento_id).execute()
                
                return f"Feito! O evento '{nome_real}' foi apagado da tua agenda com sucesso."
                
        return f"Não consegui encontrar nenhum evento com o nome '{nome_do_evento}' para apagar."
        
    except Exception as e:
        print("------- ERRO AO APAGAR NO CALENDÁRIO -------")
        print(e)
        return f"Erro técnico ao apagar: {str(e)}"
    
# --- Lembra-te de usar o nome correto da tua variável 'service' aqui ---
# Se a tua variável se chama 'meu_calendario', troca 'service' por 'meu_calendario' abaixo.

def editar_evento_calendario(
    nome_atual: str,
    novo_titulo: str = None,
    nova_data_inicio: str = None,  # Formato 'YYYY-MM-DD'
    nova_hora_inicio: str = None,  # Formato 'HH:MM:SS'
    nova_data_fim: str = None,     # Formato 'YYYY-MM-DD'
    nova_hora_fim: str = None,      # Formato 'HH:MM:SS'
    nova_descricao: str = None,
    editar_serie: bool = False   
) -> str:
    """
    Procura um evento pelo nome e atualiza as informações fornecidas.
    Se um campo não for fornecido (None), ele mantém a informação original.
    """
    try:
        service = get_calendar_service()
        
        # 1. ENCONTRAR O EVENTO (Visão de 24h)
        ontem = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)).isoformat().replace('+00:00', 'Z')
        
        eventos_result = service.events().list(
            calendarId='primary',
            timeMin=ontem,
            maxResults=100,  # <-- Aumentámos para 100 para não cortar o final do dia!
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        eventos = eventos_result.get('items', [])
        evento_a_editar = None
        
        # MAGIA AQUI: Ler a lista de trás para a frente (reversed) para apanhar o evento mais recente!
        for evento in reversed(eventos):
            if nome_atual.lower() in evento.get('summary', '').lower():
                evento_a_editar = evento
                break
                
        if not evento_a_editar:
            return f"Não encontrei nenhum evento com o nome '{nome_atual}' nas últimas 24 horas."
            
        evento_id = evento_a_editar['id']
        
        if editar_serie and 'recurringEventId' in evento_a_editar:
            evento_id = evento_a_editar['recurringEventId']
            
        # 2. CONSTRUIR O CORPO DA ATUALIZAÇÃO (Patch Body)
        patch_body = {}

        if novo_titulo:
            patch_body['summary'] = novo_titulo
            
        if nova_descricao:
            patch_body['description'] = nova_descricao
            
        start_original = evento_a_editar.get('start', {})
        end_original = evento_a_editar.get('end', {})
        timezone = 'Europe/Lisbon'

        # O segredo está aqui: ir buscar os horários originais do evento
        start_original = evento_a_editar.get('start', {})
        end_original = evento_a_editar.get('end', {})
        
        timezone = 'Europe/Lisbon'

        # TRATAR O INÍCIO
        if nova_hora_inicio:
            # Se ele mandar só a hora, aproveitamos a data que o evento já tinha
            data_inicio_segura = nova_data_inicio if nova_data_inicio else start_original.get('dateTime', '')[:10]
            
            # Se por acaso estiver vazio (fallback de segurança para hoje)
            if not data_inicio_segura: 
                data_inicio_segura = datetime.datetime.now().strftime("%Y-%m-%d")
                
            patch_body['start'] = {
                'dateTime': f"{data_inicio_segura}T{nova_hora_inicio}",
                'timeZone': timezone
            }
        else:
            # Se não pediste para mudar o início, forçamos o antigo
            patch_body['start'] = start_original

        # TRATAR O FIM
        if nova_hora_fim:
            # Se ele mandar só a hora, aproveitamos a data que o evento já tinha
            data_fim_segura = nova_data_fim if nova_data_fim else end_original.get('dateTime', '')[:10]
            
            # Se por acaso estiver vazio (fallback de segurança para hoje)
            if not data_fim_segura: 
                data_fim_segura = datetime.datetime.now().strftime("%Y-%m-%d")
                
            patch_body['end'] = {
                'dateTime': f"{data_fim_segura}T{nova_hora_fim}",
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
    
def criar_evento_recorrente(
    titulo: str,
    data_primeiro_evento: str,  # Formato 'YYYY-MM-DD'
    hora_inicio: str,           # Formato 'HH:MM:SS'
    hora_fim: str,              # Formato 'HH:MM:SS'
    dias_semana: str,           # Formato 'MO,TU,WE,TH,FR,SA,SU'
    data_limite: str            # Formato 'YYYYMMDD' (Ex: 20270131 para fim de janeiro)
) -> str:
    """
    Cria um evento semanal recorrente no calendário (ideal para horários de aulas ou rotinas).
    """
    try:
        service = get_calendar_service()
        
        # Garante que as horas têm segundos (o Gemini às vezes manda só HH:MM)
        if len(hora_inicio) == 5: hora_inicio += ":00"
        if len(hora_fim) == 5: hora_fim += ":00"
        
        start_datetime = f"{data_primeiro_evento}T{hora_inicio}"
        end_datetime = f"{data_primeiro_evento}T{hora_fim}"
        
        # AQUI ESTÁ A MAGIA: Removemos os hifens automaticamente no Python!
        data_limite_limpa = data_limite.replace("-", "")
        until_format = f"{data_limite_limpa}T235959Z"
        
        rrule = f"RRULE:FREQ=WEEKLY;BYDAY={dias_semana};UNTIL={until_format}"
        
        evento = {
            'summary': titulo,
            'start': {
                'dateTime': start_datetime,
                'timeZone': 'Europe/Lisbon',
            },
            'end': {
                'dateTime': end_datetime,
                'timeZone': 'Europe/Lisbon',
            },
            'recurrence': [
                rrule
            ]
        }
        
        evento_criado = service.events().insert(calendarId='primary', body=evento).execute()
        return f"Evento recorrente '{titulo}' criado com sucesso! (ID: {evento_criado.get('id')})"
        
    except Exception as e:
        return f"Erro ao criar evento recorrente: {str(e)}"
    
import datetime

def cancelar_evento_calendario(
    nome_evento: str, 
    data_alvo: str = None, 
    parar_recorrencia: bool = False
) -> str:
    """
    Cancela uma ocorrência específica ou termina uma série recorrente a partir de hoje.
    """
    try:
        service = get_calendar_service()
        agora = datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
        
        eventos_result = service.events().list(
            calendarId='primary',
            timeMin=agora,
            maxResults=50,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        eventos = eventos_result.get('items', [])
        evento_alvo = None
        
        for evento in eventos:
            if nome_evento.lower() in evento.get('summary', '').lower():
                if data_alvo:
                    # Verifica se a data especificada está no início do evento
                    start = evento['start'].get('dateTime', evento['start'].get('date'))
                    if data_alvo in start:
                        evento_alvo = evento
                        break
                else:
                    evento_alvo = evento
                    break
                    
        if not evento_alvo:
            return f"Não encontrei o evento '{nome_evento}'."
            
        evento_id = evento_alvo['id']
        
        # CENÁRIO 1: Cancelar APENAS o evento deste dia
        if not parar_recorrencia:
            service.events().delete(calendarId='primary', eventId=evento_id).execute()
            return f"A ocorrência do evento '{nome_evento}' foi cancelada com sucesso."
            
        # CENÁRIO 2: Terminar a série a partir de hoje (preservando o histórico passado)
        elif parar_recorrencia and 'recurringEventId' in evento_alvo:
            master_id = evento_alvo['recurringEventId']
            master_event = service.events().get(calendarId='primary', eventId=master_id).execute()
            
            # Formato UTC que a Google exige para o limite do RRULE
            hoje_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT235959Z")
            
            novas_regras = []
            for regra in master_event.get('recurrence', []):
                if 'RRULE' in regra:
                    partes = [p for p in regra.replace('RRULE:', '').split(';') if not p.startswith('UNTIL')]
                    partes.append(f"UNTIL={hoje_str}")
                    novas_regras.append(f"RRULE:{';'.join(partes)}")
                else:
                    novas_regras.append(regra)
                    
            master_event['recurrence'] = novas_regras
            service.events().update(calendarId='primary', eventId=master_id, body=master_event).execute()
            return f"A série '{nome_evento}' foi cancelada a partir de hoje. O histórico passado foi mantido."
            
        else:
            # Se pediram para parar a recorrência mas o evento é único, apagamos normalmente
            service.events().delete(calendarId='primary', eventId=evento_id).execute()
            return f"O evento '{nome_evento}' não era recorrente, mas foi apagado com sucesso."
            
    except Exception as e:
        return f"Erro ao cancelar evento: {str(e)}"