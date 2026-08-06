import os
from supabase import create_client, Client

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(supabase_url, supabase_key)

# --- TAREFAS ---
def add_task(title: str, due_date: str = None) -> str:
    """Adiciona uma nova tarefa à lista de afazeres."""
    try:
        data = {"title": title}
        if due_date:
            data["due_date"] = due_date
        supabase.table("tasks").insert(data).execute()
        return f"Tarefa '{title}' adicionada com sucesso."
    except Exception as e:
        return f"Erro ao adicionar tarefa: {str(e)}"

def list_tasks(only_pending: bool = True) -> str:
    """Lista as tarefas guardadas no Supabase."""
    try:
        query = supabase.table("tasks").select("*")
        if only_pending:
            query = query.eq("completed", False)
        res = query.execute()
        tasks = res.data
        if not tasks:
            return "Nenhuma tarefa pendente encontrada."
        
        output = "Tarefas pendentes:\n"
        for t in tasks:
            due = f" (Prazo: {t['due_date']})" if t.get('due_date') else ""
            output += f"- [{t['id']}] {t['title']}{due}\n"
        return output
    except Exception as e:
        return f"Erro ao listar tarefas: {str(e)}"

# --- NOTAS ---
def add_note(content: str, tags: list[str] = []) -> str:
    """Guarda uma anotação ou nota rápida."""
    try:
        supabase.table("notes").insert({"content": content, "tags": tags}).execute()
        return "Nota guardada com sucesso."
    except Exception as e:
        return f"Erro ao guardar nota: {str(e)}"

def list_notes() -> str:
    """Consulta as notas e anotações guardadas."""
    try:
        res = supabase.table("notes").select("*").order("created_at", desc=True).limit(10).execute()
        notes = res.data
        if not notes:
            return "Nenhuma nota encontrada."
        
        output = "Últimas notas:\n"
        for n in notes:
            output += f"- {n['content']}\n"
        return output
    except Exception as e:
        return f"Erro ao consultar notas: {str(e)}"

# --- FINANÇAS ---
def add_transaction(description: str, amount: float, category: str = "Geral") -> str:
    """Regista uma transação financeira. Valores positivos para receita/faturação, negativos para gastos."""
    try:
        supabase.table("transactions").insert({
            "description": description,
            "amount": amount,
            "category": category
        }).execute()
        tipo = "Receita/Faturação" if amount > 0 else "Gasto"
        return f"Registo de {tipo} de {abs(amount)}€ ('{description}') guardado com sucesso."
    except Exception as e:
        return f"Erro ao registar transação: {str(e)}"

def get_financial_summary() -> str:
    """Obtém o resumo do saldo global e movimentos recentes."""
    try:
        res = supabase.table("transactions").select("*").execute()
        txs = res.data
        if not txs:
            return "Nenhuma transação registada."
        
        total = sum(t["amount"] for t in txs)
        output = f"Resumo Financeiro:\nSaldo Total: {total:.2f}€\n\nÚltimos movimentos:\n"
        for t in txs[-5:]:
            output += f"- {t['description']}: {t['amount']}€ ({t['category']})\n"
        return output
    except Exception as e:
        return f"Erro ao obter resumo financeiro: {str(e)}"