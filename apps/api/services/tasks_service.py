import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

def get_tasks_service():
    """Autentica na Google Tasks API lendo o ficheiro token.json."""
    SCOPES = [
            'https://www.googleapis.com/auth/calendar', 
            'https://www.googleapis.com/auth/tasks',
            'https://www.googleapis.com/auth/userinfo.profile'
        ]    
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        raise Exception("Token não encontrado. Clica no botão 'Conectar Google' primeiro.")

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open('token.json', 'w') as token_file:
                token_file.write(creds.to_json())
                
    return build("tasks", "v1", credentials=creds)

def ler_tarefas() -> str:
    """Lê as tarefas pendentes gerais, ocultando todas as categorias especiais."""
    try:
        service = get_tasks_service()
        resultados = service.tasks().list(tasklist='@default', showCompleted=False).execute()
        tarefas = resultados.get('items', [])
        
        if not tarefas:
            return "A tua lista de tarefas está vazia."
            
        texto_resposta = "Aqui estão as tuas tarefas pendentes (gerais):\n"
        tarefas_encontradas = 0
        
        # Oculta qualquer tarefa que tenha uma destas etiquetas
        etiquetas_ocultas = ['[nota]', '[compra]', '[projeto]', '[media]', '[ideia]', '[rotina]']
        
        for tarefa in tarefas:
            titulo = tarefa.get('title', '').lower()
            if not any(etiqueta in titulo for etiqueta in etiquetas_ocultas):
                texto_resposta += f"- {tarefa.get('title', '')}\n"
                tarefas_encontradas += 1
                
        if tarefas_encontradas == 0:
            return "Não tens tarefas gerais pendentes (apenas notas e listas organizadas)."
            
        return texto_resposta
    except Exception as e:
        return f"Erro técnico ao aceder às tarefas: {str(e)}"

def consultar_lista_especifica(categoria: str) -> str:
    """
    Lê tarefas que contêm uma etiqueta específica (ex: '[COMPRA]', '[PROJETO]', '[MEDIA]', '[IDEIA]', '[NOTA]').
    """
    try:
        service = get_tasks_service()
        resultados = service.tasks().list(tasklist='@default', showCompleted=False).execute()
        tarefas = resultados.get('items', [])
        
        texto_resposta = f"Aqui estão os teus registos para a categoria {categoria}:\n\n"
        encontrados = 0
        
        for tarefa in tarefas:
            titulo = tarefa.get('title', '')
            if categoria.lower() in titulo.lower():
                encontrados += 1
                descricao = tarefa.get('notes', 'Sem conteúdo.')
                titulo_limpo = titulo.lower().replace(categoria.lower(), '').strip().title()
                texto_resposta += f"• {titulo_limpo}\n  Detalhes: {descricao}\n\n"
                
        if encontrados == 0:
            return f"Não tens nenhum registo com a etiqueta {categoria} neste momento."
            
        return texto_resposta
    except Exception as e:
        return f"Erro ao consultar a categoria {categoria}: {str(e)}"

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
    Limpa a lista manualmente: procura tarefas concluídas e apaga-as uma a uma, 
    EXCETO as que estão marcadas como [ROTINA].
    """
    try:
        print("\n[DEBUG] O PICOTE VAI ASPIRAR AS TAREFAS CONCLUÍDAS (IGNORANDO ROTINAS)")
        
        service = get_tasks_service()
        
        # showHidden=True é obrigatório para a Google nos devolver as tarefas já riscadas
        resultados = service.tasks().list(tasklist='@default', showHidden=True).execute()
        tarefas = resultados.get('items', [])
        
        tarefas_apagadas = 0
        rotinas_poupadas = 0
        
        for tarefa in tarefas:
            # Verifica se o estado da tarefa é 'completed' (concluída)
            if tarefa.get('status') == 'completed':
                titulo = tarefa.get('title', 'Sem título')
                
                # === PROTEÇÃO DAS ROTINAS ===
                if '[rotina]' in titulo.lower():
                    print(f"[DEBUG] Rotina protegida (não apagada): {titulo}")
                    rotinas_poupadas += 1
                    continue # Salta para a próxima tarefa sem apagar esta
                    
                print(f"[DEBUG] A apagar definitivamente: {titulo}")
                
                # Apaga a tarefa comum
                service.tasks().delete(
                    tasklist='@default', 
                    task=tarefa['id']
                ).execute()
                
                tarefas_apagadas += 1
                
        if tarefas_apagadas == 0:
            return f"Não encontrei nenhuma tarefa comum marcada como concluída para apagar. (Rotinas concluídas mantidas: {rotinas_poupadas})"
            
        return f"Limpeza feita com sucesso! Apaguei definitivamente {tarefas_apagadas} tarefas concluídas. (Protegi {rotinas_poupadas} rotinas)."
        
    except Exception as e:
        print("------- ERRO AO LIMPAR TAREFAS CONCLUÍDAS -------")
        print(e)
        return f"Erro técnico ao limpar as tarefas concluídas: {str(e)}"
    
def reiniciar_rotinas() -> str:
    """Procura todas as tarefas com '[ROTINA]' concluídas e volta a marcá-las como pendentes para o novo dia."""
    try:
        service = get_tasks_service()
        # showHidden=True é obrigatório para a API ver tarefas que já foram concluídas e ocultadas
        resultados = service.tasks().list(tasklist='@default', showHidden=True).execute()
        tarefas = resultados.get('items', [])
        
        rotinas_reiniciadas = 0
        
        for tarefa in tarefas:
            titulo = tarefa.get('title', '').lower()
            if '[rotina]' in titulo and tarefa.get('status') == 'completed':
                # Desmarca a tarefa no Google Tasks
                service.tasks().patch(
                    tasklist='@default', 
                    task=tarefa['id'], 
                    body={'status': 'needsAction'}
                ).execute()
                rotinas_reiniciadas += 1
                
        if rotinas_reiniciadas == 0:
            return "Nenhuma rotina precisava de ser reiniciada hoje."
            
        return f"Feito! {rotinas_reiniciadas} rotinas diárias foram desmarcadas e estão prontas para hoje."
    except Exception as e:
        return f"Erro ao reiniciar rotinas: {str(e)}"