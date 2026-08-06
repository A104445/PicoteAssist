import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

def get_tasks_service():
    """Autentica na Google Tasks API usando o Refresh Token."""
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/tasks"] # O scope mudou para o Tasks
    )

    if not creds.valid:
        creds.refresh(Request())

    return build("tasks", "v1", credentials=creds)

def ler_tarefas() -> str:
    """
    Lê as tarefas pendentes da lista principal do Google Tasks.
    Filtra e oculta automaticamente as que contêm a etiqueta '[NOTA]'.
    """
    try:
        service = get_tasks_service()
        # showCompleted=False para não trazer as tarefas já concluídas
        resultados = service.tasks().list(tasklist='@default', showCompleted=False).execute()
        tarefas = resultados.get('items', [])
        
        if not tarefas:
            return "A tua lista de tarefas está vazia. Tudo limpo!"
            
        texto_resposta = "Aqui estão as tuas tarefas pendentes:\n"
        tarefas_encontradas = 0
        
        for tarefa in tarefas:
            titulo = tarefa.get('title', '')
            # Apenas adiciona à resposta se não for uma nota
            if '[nota]' not in titulo.lower():
                texto_resposta += f"- {titulo}\n"
                tarefas_encontradas += 1
                
        if tarefas_encontradas == 0:
            return "Não tens tarefas pendentes na lista (apenas notas guardadas)."
            
        return texto_resposta
    except Exception as e:
        print("------- ERRO AO LER TAREFAS -------")
        print(e)
        print("-----------------------------------")
        return f"Erro técnico ao aceder às tarefas: {str(e)}"
    
def ler_notas() -> str:
    """
    Lê todas as notas guardadas (tarefas que contêm a etiqueta '[NOTA]').
    Mostra o título da nota e o seu conteúdo (descrição).
    """
    try:
        service = get_tasks_service()
        # showCompleted=False para mostrar apenas as notas ativas
        resultados = service.tasks().list(tasklist='@default', showCompleted=False).execute()
        tarefas = resultados.get('items', [])
        
        texto_resposta = "Aqui estão as tuas notas guardadas:\n\n"
        notas_encontradas = 0
        
        for tarefa in tarefas:
            titulo = tarefa.get('title', '')
            
            # Filtra APENAS as que têm [nota] no título
            if '[nota]' in titulo.lower():
                notas_encontradas += 1
                descricao = tarefa.get('notes', 'Sem conteúdo.')
                
                # Limpa o prefixo [NOTA] para ficar mais bonito na leitura
                titulo_limpo = titulo.lower().replace('[nota]', '').strip().title()
                
                texto_resposta += f"📌 {titulo_limpo}\nConteúdo: {descricao}\n\n"
                
        if notas_encontradas == 0:
            return "Não tens nenhuma nota guardada neste momento."
            
        return texto_resposta
        
    except Exception as e:
        print("------- ERRO AO LER NOTAS -------")
        print(e)
        print("---------------------------------")
        return f"Erro técnico ao aceder às notas: {str(e)}"

def criar_tarefa(titulo: str, notas: str = None) -> str:
    """
    Cria uma nova tarefa no Google Tasks.
    Pode ter apenas um título, ou um título e notas adicionais.
    """
    try:
        print(f"\n[DEBUG] 🕵️ O PICOTE DECIDIU CHAMAR: CRIAR TAREFA -> Título: {titulo}")
        service = get_tasks_service()
        corpo_tarefa = {'title': titulo}
        
        if notas:
            corpo_tarefa['notes'] = notas
            
        resultado = service.tasks().insert(tasklist='@default', body=corpo_tarefa).execute()
        return f"Feito! A tarefa '{resultado['title']}' foi adicionada à tua lista."
        
    except Exception as e:
        print("------- ERRO AO CRIAR TAREFA -------")
        print(e)
        print("------------------------------------")
        return f"Erro técnico ao criar a tarefa: {str(e)}"
    
def editar_tarefa(
    nome_atual: str,
    novo_titulo: str = None,
    novas_notas: str = None,
    nova_data: str = None # Formato 'YYYY-MM-DD'
) -> str:
    """
    Procura uma tarefa pelo nome e edita-a. 
    Acrescenta novas notas sem apagar as antigas. (Não utiliza horas).
    """
    try:
        print(f"\n[DEBUG] 🕵️ EDITAR TAREFA -> Procurou: '{nome_atual}' | Novo Titulo: {novo_titulo} | Nova Data: {nova_data}")
        
        service = get_tasks_service()
        
        # 1. Procurar a tarefa
        resultados = service.tasks().list(tasklist='@default').execute()
        tarefas = resultados.get('items', [])
        
        tarefa_a_editar = None
        for tarefa in tarefas:
            if nome_atual.lower() in tarefa.get('title', '').lower():
                tarefa_a_editar = tarefa
                break
                
        if not tarefa_a_editar:
            return f"Não encontrei nenhuma tarefa com o nome '{nome_atual}'."
            
        tarefa_id = tarefa_a_editar['id']
        notas_existentes = tarefa_a_editar.get('notes', '')
        
        # 2. Preparar as alterações
        patch_body = {}
        
        if novo_titulo:
            patch_body['title'] = novo_titulo
            
        # --- A LÓGICA DAS NOTAS (Sem horas) ---
        notas_finais = notas_existentes
        
        if novas_notas:
            if notas_existentes:
                # Se já tem texto, dá uns parágrafos e acrescenta a nova informação
                notas_finais = f"{notas_existentes}\n\n[Atualização]: {novas_notas}"
            else:
                # Se estava vazio, mete só a informação nova
                notas_finais = novas_notas
                
        # Tratar a data
        if nova_data:
            patch_body['due'] = f"{nova_data}T00:00:00.000Z"
                    
        # Só atualiza as notas se houver mudanças reais
        if notas_finais != notas_existentes:
            patch_body['notes'] = notas_finais

        if not patch_body:
            return "Não forneceste nenhuma informação nova para atualizar a tarefa."

        # 3. Enviar a atualização
        resultado = service.tasks().patch(
            tasklist='@default', 
            task=tarefa_id, 
            body=patch_body
        ).execute()
        
        return f"Feito! A tarefa '{nome_atual}' foi atualizada com sucesso sem perder dados."
        
    except Exception as e:
        print("------- ERRO AO EDITAR TAREFA -------")
        print(e)
        print("-------------------------------------")
        return f"Erro técnico ao editar a tarefa: {str(e)}"

def concluir_tarefa(nome_tarefa: str) -> str:
    """
    Procura uma tarefa pelo nome e marca-a como concluída.
    """
    try:
        service = get_tasks_service()
        resultados = service.tasks().list(tasklist='@default').execute()
        tarefas = resultados.get('items', [])
        
        for tarefa in tarefas:
            if nome_tarefa.lower() in tarefa.get('title', '').lower():
                # A magia acontece aqui: mudamos o status para 'completed'
                service.tasks().patch(
                    tasklist='@default', 
                    task=tarefa['id'], 
                    body={'status': 'completed'}
                ).execute()
                
                return f"Boa! A tarefa '{tarefa['title']}' foi marcada como concluída. Menos uma!"
                
        return f"Não encontrei nenhuma tarefa pendente com o nome '{nome_tarefa}' para concluir."
        
    except Exception as e:
        print("------- ERRO AO CONCLUIR TAREFA -------")
        print(e)
        return f"Erro técnico ao concluir a tarefa: {str(e)}"


def apagar_tarefa(nome_tarefa: str) -> str:
    """
    Procura uma tarefa pelo nome e apaga-a permanentemente.
    """
    try:
        service = get_tasks_service()
        resultados = service.tasks().list(tasklist='@default', showHidden=True).execute()
        tarefas = resultados.get('items', [])
        
        for tarefa in tarefas:
            if nome_tarefa.lower() in tarefa.get('title', '').lower():
                # Apaga o registo permanentemente
                service.tasks().delete(
                    tasklist='@default', 
                    task=tarefa['id']
                ).execute()
                
                return f"A tarefa '{tarefa['title']}' foi eliminada para sempre do teu Google Tasks."
                
        return f"Não encontrei nenhuma tarefa com o nome '{nome_tarefa}' para apagar."
        
    except Exception as e:
        print("------- ERRO AO APAGAR TAREFA -------")
        print(e)
        return f"Erro técnico ao apagar a tarefa: {str(e)}"
    
def limpar_tarefas_concluidas() -> str:
    """
    Limpa a lista manualmente: procura todas as tarefas concluídas e apaga-as uma a uma.
    """
    try:
        print("\n[DEBUG] 🕵️ O PICOTE VAI ASPIRAR AS TAREFAS CONCLUÍDAS MANUALMENTE")
        
        service = get_tasks_service()
        
        # O showHidden=True é obrigatório para a Google nos devolver as tarefas já riscadas
        resultados = service.tasks().list(tasklist='@default', showHidden=True).execute()
        tarefas = resultados.get('items', [])
        
        tarefas_apagadas = 0
        
        for tarefa in tarefas:
            # Verifica se o estado da tarefa é 'completed' (concluída)
            if tarefa.get('status') == 'completed':
                titulo = tarefa.get('title', 'Sem título')
                print(f"[DEBUG] 🧹 A apagar definitivamente: {titulo}")
                
                # Apaga a tarefa específica
                service.tasks().delete(
                    tasklist='@default', 
                    task=tarefa['id']
                ).execute()
                
                tarefas_apagadas += 1
                
        if tarefas_apagadas == 0:
            print("[DEBUG] 🤷 Não encontrei nenhuma tarefa com o estado 'completed'")
            return "Não encontrei nenhuma tarefa marcada como concluída para apagar."
            
        return f"Limpeza feita com sucesso! Apaguei definitivamente {tarefas_apagadas} tarefas concluídas."
        
    except Exception as e:
        print("------- ERRO AO LIMPAR TAREFAS CONCLUÍDAS -------")
        print(e)
        return f"Erro técnico ao limpar as tarefas concluídas: {str(e)}"