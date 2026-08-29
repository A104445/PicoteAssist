from contextvars import ContextVar

# Guarda o token do utilizador isolado por cada pedido HTTP
current_google_token = ContextVar("current_google_token", default=None)