from google_auth_oauthlib.flow import InstalledAppFlow

# Coloca aqui o caminho para o ficheiro credentials.json que sacaste da Google Cloud
# (Se não o tens na pasta, tens de o descarregar novamente da Cloud Console)
FICHEIRO_CREDENCIAIS = 'credentials.json' 

# Pedimos acesso TOTAL ao Calendário E às Tarefas
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/tasks'
]

def gerar_novo_refresh_token():
    try:
        flow = InstalledAppFlow.from_client_secrets_file(FICHEIRO_CREDENCIAIS, SCOPES)
        creds = flow.run_local_server(port=8080)
        
        print("\n" + "="*50)
        print("🎉 SUCESSO! AQUI ESTÁ O TEU NOVO REFRESH TOKEN:")
        print("="*50)
        print(creds.refresh_token)
        print("="*50 + "\n")
        print("Copia o código acima e substitui o GOOGLE_REFRESH_TOKEN no teu ficheiro .env")
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == '__main__':
    gerar_novo_refresh_token()