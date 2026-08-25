import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import datetime
from fastapi import Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
import requests

# Forçar a procura do .env na pasta raiz ou na pasta atual
load_dotenv(dotenv_path="../../.env") # Tenta ler da raiz
load_dotenv() # Tenta ler da pasta api (caso falhe o de cima)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# ESTA É A LINHA MÁGICA PARA O NOSSO TESTE
print(f"-> CHAVE CARREGADA NO PYTHON: {GEMINI_API_KEY}")

from google import genai
from google.genai import types
from services.supabase_service import (
    add_task, list_tasks, add_note, list_notes, add_transaction, get_financial_summary
)
from services.calendar_service import create_calendar_event, list_calendar_events, apagar_evento_calendario, editar_evento_calendario, criar_evento_recorrente

from services.tasks_service import ler_tarefas, ler_notas, criar_tarefa, editar_tarefa, concluir_tarefa, apagar_tarefa, limpar_tarefas_concluidas

app = FastAPI(title="Picote Assist API")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# Permite que o Vite (porta 5173) se ligue à API sem bloqueios de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURAÇÕES GOOGLE OAUTH ---
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/tasks',
    'https://www.googleapis.com/auth/userinfo.profile'
]
CLIENT_SECRETS_FILE = "credentials.json"

# Vai buscar o URL da Nuvem. Se não existir no .env, assume o localhost para testares no PC.
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
# ----------------------------------

# Inicializa o cliente Gemini
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

assistant_tools = [
    create_calendar_event,
    list_calendar_events,
    apagar_evento_calendario,
    editar_evento_calendario, 
    criar_evento_recorrente,
    ler_tarefas,
    ler_notas,
    criar_tarefa,
    editar_tarefa,
    concluir_tarefa,
    apagar_tarefa,
    limpar_tarefas_concluidas,
    add_task,
    list_tasks,
    add_note,
    list_notes,
    add_transaction,
    get_financial_summary
]

class ChatRequest(BaseModel):
    message: str
    history: list = []

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        data_atual = datetime.datetime.now().strftime("%d de %B de %Y")
        hora_atual = datetime.datetime.now().strftime("%H:%M")

        # system_instruction = f"""És o Picote Assist, o meu assistente pessoal.
        # INFORMAÇÃO IMPORTANTE: Hoje é dia {data_atual} e são {hora_atual}. Usa sempre esta data como referência para 'hoje', 'amanhã', 'próxima semana', etc.
        # Regras de atuação:
        # 1. Invoca SEMPRE a ferramenta correspondente quando o utilizador pedir para registar, consultar ou agendar algo.
        # 2. Mantém as tuas respostas finais concisas, amigáveis e focadas na confirmação do que foi feito.
        # 3. Para movimentos financeiros: valores positivos são faturação/receitas e negativos são despesas/gastos.
        # Atenção: Ao criares eventos no calendário, usa sempre a hora local de Portugal. Nunca adiciones a letra 'Z' no final da string de data/hora.
        # Regra para Notas: Sempre que eu te pedir para guardar uma nota, ideia ou apontamento, usa a ferramenta criar_tarefa com o prefixo '[NOTA]' no título e guarda o conteúdo no campo das notas.
        # Se eu quiser saber quais são as minhas tarefas pendentes, usa a ferramenta ler_tarefas.
        # Se eu quiser ler, consultar ou saber quais são as minhas notas guardadas, usa a ferramenta ler_notas.
        # Se eu te pedir para limpar ou apagar as tarefas concluídas/terminadas, usa a ferramenta limpar_tarefas_concluidas.
        # """
        
        system_instruction = f"""És o Picote Assist, o meu assistente pessoal e de inteligência artificial.
        INFORMAÇÃO IMPORTANTE: Hoje é dia {data_atual} e são {hora_atual}. Usa sempre esta data como referência.

        O TEU PAPEL É TRIPLO E DEVES ADAPTAR-TE AO QUE EU PEDIR:

        1. MODO ASSISTENTE DE PRODUTIVIDADE:
        - Invoca SEMPRE a ferramenta correspondente quando eu pedir para registar, consultar ou agendar algo.
        - Mantém as tuas respostas concisas e foca-te na confirmação do que foi feito.
        - Para movimentos financeiros: valores positivos são receitas, negativos são despesas.
        - Ao criares eventos no calendário, usa a hora local de Portugal. Nunca adiciones a letra 'Z' no final.
        - Regra para Notas: Usa a ferramenta criar_tarefa com o prefixo '[NOTA]' no título e guarda o conteúdo nas notas.
        - MODO FECHO DO DIA (VOU DORMIR / BOA NOITE):
            Quando eu disser "Vou dormir" ou "Boa noite":
            1. Usa list_calendar_events para leres todos os eventos do dia de hoje.
            2. Calcula OBRIGATORIAMENTE a soma total de Calorias, Proteína, Hidratos e Lípidos das refeições de hoje (não aceites resumir apenas a calorias).
            3. Usa create_calendar_event para criar o evento "Resumo do Dia". O `start_time` tem de ser EXATAMENTE no minuto atual, e o `end_time` tem de ser EXATAMENTE 10 minutos depois. Na "description", escreve o relatório estruturado:
                - Total Calorias: X kcal
                - Proteína: X g
                - Hidratos: X g
                - Lípidos: X g
            4. Usa novamente create_calendar_event para criar o evento "Dormir". O `start_time` deste evento tem de ser EXATAMENTE 11 minutos após a hora atual (ou seja, 1 minuto após o fim do Resumo, para os blocos não colarem). O `end_time` deve ser 8 horas para a frente.
            5. Despede-te com o balanço diário e deseja-me uma boa noite.
        - MODO ARRANQUE DO DIA (ACORDEI / BOM DIA):
            Quando eu disser "Bom dia" ou "Acordei":
            1. Usa editar_evento_calendario para encontrares o evento "Dormir" da noite anterior e altera apenas a `nova_hora_fim` (e data, se passou da meia-noite) para a hora exata atual.
            2. Usa list_calendar_events para leres a minha agenda para hoje.
            3. Usa ler_tarefas para leres as minhas pendências.
            4. Dá-me os bons dias de forma enérgica e faz-me um resumo amigável do dia, cruzando as tarefas com os meus tempos livres.
            
        2. MODO IA CONVERSACIONAL E CONSULTOR:
        - Quando eu te fizer perguntas de cultura geral, pedir ajuda com textos, explicações, ou simplesmente conversar, liberta-te das regras de produtividade.
        - Age como uma IA avançada (como o ChatGPT), dando respostas criativas, detalhadas, formatadas em Markdown e naturais.

        3. MODO NUTRICIONISTA E REGISTO DINÂMICO:
        - INICIAR REFEIÇÃO/SONO: Quando eu disser que vou começar a comer ou dormir, cria o evento no calendário a começar AGORA (deixa o fim em aberto ou para daqui a 1 hora).
        - TERMINAR: Quando eu disser que acabei, procura esse evento de hoje e usa o editar_evento_calendario para mudar a HORA DE FIM para AGORA.
        - ESTIMATIVAS: Calcula as Calorias e Macros usando a regra dos temperos (+1 c. de sopa de azeite por defeito).
        - ACRESCENTAR COMIDA (MUITO IMPORTANTE): Se eu te disser que "comi mais X" numa refeição, NÃO apagues o que lá está! PRIMEIRO, pesquisa o evento para leres a descrição atual. SEGUNDO, acrescenta o novo alimento à lista, soma os macros novos aos antigos, e só depois edita o evento com os TOTAIS atualizados.
        - MODO NUTRICIONISTA (REGISTAR COMIDA):
            Sempre que eu te disser o que comi e tu usares a ferramenta editar_evento_calendario para registar a refeição, é OBRIGATÓRIO escreveres na `nova_descricao` os valores com quebras de linha reais e no seguinte formato:
            Prato: [O que eu comi]
            - Calorias: X kcal
            - Proteína: X g
            - Hidratos: X g
            - Lípidos: X g
        - CORREÇÃO DE REFEIÇÕES (EDITAR COMIDA):
            Quando eu quiser alterar ou corrigir uma refeição que já registei (ex: "edita o jantar"):
            1. Calcula imediatamente os macros desta nova refeição.
            2. Usa OBRIGATORIAMENTE a ferramenta editar_evento_calendario.
            3. Usa o nome da refeição no campo `nome_atual` (ex: "Jantar").
            4. No campo `nova_descricao`, substitui os dados antigos escrevendo a nova informação OBRIGATORIAMENTE neste formato:
            Prato: [O que eu comi]
            - Calorias: X kcal
            - Proteína: X g
            - Hidratos: X g
            - Lípidos: X g
            
        4. MODO GESTÃO DE HORÁRIOS (AULAS E ROTINAS):
        - Quando eu te der o meu horário de aulas ou rotinas fixas, usa a ferramenta criar_evento_recorrente.
        - Faz a tradução automática dos dias para o formato do Google: MO (Segunda), TU (Terça), WE (Quarta), TH (Quinta), FR (Sexta). Se a aula for à Segunda e Quarta, envia 'MO,WE'.
        - O parâmetro data_limite dita quando o evento para de se repetir. Se for relativo a aulas de um semestre, assume automaticamente o fim do semestre atual (Janeiro ou Junho), a menos que eu indique outra data.
        - CANCELAMENTOS: Se eu pedir para cancelar ou apagar um evento de um dia específico, usa a ferramenta cancelar_evento_calendario com a data_alvo e parar_recorrencia=False. Se eu disser que já não vou mais a uma atividade (cancelar de vez), usa a ferramenta com parar_recorrencia=True.
        - EDIÇÕES DE ROTINAS: Tens 3 formas de lidar com alterações:
          1. ALTERAR SÓ UM DIA: Se o evento atrasou só hoje, usa editar_evento_calendario com editar_serie=False.
          2. CORRIGIR O PASSADO: Se eu disser que me enganei desde o início e quero corrigir a série toda (passado e futuro), usa editar_evento_calendario com editar_serie=True.
          3. MUDAR A PARTIR DE HOJE (MUITO IMPORTANTE): Se o horário mudou definitivamente, mas eu quero preservar o meu histórico passado, tens de executar DUAS ferramentas em sequência:
             - 1º: Usa cancelar_evento_calendario com parar_recorrencia=True para terminar a série antiga a partir de hoje.
             - 2º: Usa criar_evento_recorrente para criar a nova série com o novo horário e os novos dias.
        - EVENTOS DE DIA INTEIRO: Quando eu te pedir para marcar um evento de dia inteiro (ex: feriados, aniversários, datas limite), usa a ferramenta create_calendar_event com todo_o_dia=True.
        """

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=assistant_tools,
            temperature=0.2
        )

        chat_history = []
        for item in req.history:
            chat_history.append(
                types.Content(
                    role=item.get("role"),
                    parts=[types.Part.from_text(text=item.get("text", ""))]
                )
            )

        try:
            print(f"1. A iniciar chat com o modelo...")
            chat = client.chats.create(model="gemini-3.1-flash-lite", config=config, history=chat_history)
            
            print(f"2. A enviar mensagem para o Gemini: {req.message}")
            response = chat.send_message(req.message)
            
            print("3. Resposta recebida com sucesso!")
            return {"response": response.text}
        except Exception as e:
            print(f"ERRO FATAL: {str(e)}") # Isto vai cuspir o erro real no terminal!
            raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        print(f"Erro na API: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
# Guarda o estado de segurança entre o login e o callback
oauth_state = {}

@app.get("/api/google/login")
def login_google():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=f'{BACKEND_URL}/api/google/callback' 
    )
    
    # A Google agora exige que guardemos o "state" e o "code_verifier" (PKCE)
    auth_url, state = flow.authorization_url(prompt='consent', access_type='offline')
    
    # Guardamos os dados de segurança na nossa variável de memória
    oauth_state['state'] = state
    oauth_state['code_verifier'] = flow.code_verifier
    
    return RedirectResponse(auth_url)


@app.get("/api/google/callback")
def google_callback(request: Request):
    # Lemos o state que a Google enviou de volta no link
    state = request.query_params.get("state")
    
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state,  # Passamos o state para validar a segurança
        redirect_uri=f'{BACKEND_URL}/api/google/callback'
    )
    
    # Injetamos o "código secreto" original que guardámos no login
    flow.code_verifier = oauth_state.get('code_verifier')
    
    # O Render/Vercel usam HTTPS, forçamos essa conversão por segurança
    authorization_response = str(request.url).replace("http://", "https://") if "localhost" not in BACKEND_URL else str(request.url)
    
    # Agora sim, a Google vai aceitar o pedido!
    flow.fetch_token(authorization_response=authorization_response) 
    credentials = flow.credentials
    
    with open('token.json', 'w') as token_file:
        token_file.write(credentials.to_json())
        
    try:
        # Pede à Google a foto de perfil usando a chave que acabámos de gerar
        resposta_perfil = requests.get(
            "https://www.googleapis.com/oauth2/v1/userinfo?alt=json",
            headers={"Authorization": f"Bearer {credentials.token}"}
        )
        foto_url = resposta_perfil.json().get("picture", "")
    except Exception as e:
        print(f"Erro ao buscar foto: {e}")
        foto_url = ""
        
    print("-> TOKEN E FOTO GUARDADOS COM SUCESSO!")
    
    # Redireciona de volta para o teu Vue, passando o link da foto escondido no URL
    url_destino = f"{FRONTEND_URL}?avatar={foto_url}" if foto_url else FRONTEND_URL
    return RedirectResponse(url_destino)