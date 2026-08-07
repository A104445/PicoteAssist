import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import datetime

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
from services.calendar_service import create_calendar_event, list_calendar_events, apagar_evento_calendario, editar_evento_calendario

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

# Inicializa o cliente Gemini
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

assistant_tools = [
    create_calendar_event,
    list_calendar_events,
    apagar_evento_calendario,
    editar_evento_calendario, 
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
        INFORMAÇÃO IMPORTANTE: Hoje é dia {data_atual} e são {hora_atual}. Usa esta data como referência para agendamentos.

        O TEU PAPEL É DUPLO E DEVES ADAPTAR-TE AO QUE EU PEDIR:

        1. MODO ASSISTENTE DE PRODUTIVIDADE:
        - Invoca SEMPRE a ferramenta correspondente quando eu pedir para registar, consultar, editar ou agendar algo (tarefas, notas, calendário, finanças).
        - Para estes pedidos, mantém as respostas curtas, diretas e confirma apenas o que foi feito na base de dados ou agenda.
        - Regra para Notas: Usa a ferramenta criar_tarefa com o prefixo '[NOTA]' no título e guarda o conteúdo nas notas.
        - Movimentos financeiros: valores positivos são receitas, negativos são despesas.
        - Calendário: usa a hora local de Portugal. Nunca adiciones a letra 'Z' no final.

        2. MODO IA CONVERSACIONAL E CONSULTOR:
        - Quando eu te fizer perguntas de cultura geral, pedir ajuda com textos, pedir para explicar conceitos, ou simplesmente conversar, liberta-te das regras de produtividade.
        - Age como uma IA avançada (como o ChatGPT ou Gemini), dando respostas criativas, detalhadas, explicativas e naturais.
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