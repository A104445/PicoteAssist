# PicoteAssist

Assistente inteligente e modular desenvolvido em arquitetura monorepo, combinando um backend robusto em Python (FastAPI) com um frontend moderno e reativo em Vue.js (Vite), integrado com serviços na nuvem e ferramentas de produtividade.

## Sobre o Projeto

O **PicoteAssist** foi concebido para atuar como um hub central de produtividade e gestão automatizada. A aplicação integra serviços externos essenciais (como o ecossistema Google Calendar e Google Tasks) através de microsserviços de API, permitindo a sincronização de tarefas, gestão de eventos e persistência inteligente de dados.

### Principais Funcionalidades:

* **API Backend Robusta (`apps/api/`):** Desenvolvida em **FastAPI (Python)**, fornecendo endpoints de alta performance, gestão de estado e integração modular.
* **Serviços Especializados:**
  * `calendar_service.py`: Integração com gestão de calendário e eventos.
  * `tasks_service.py`: Automação e gestão de listas de tarefas.
  * `supabase_service.py`: Camada de persistência e comunicação com a base de dados Supabase.
* **Frontend Moderno (`apps/web/`):** Interface construída com **Vue 3** e **Vite**, otimizada como Progressive Web App (PWA) para uma experiência fluida em dispositivos móveis e desktop.
* **Automação e Utilitários:** Scripts de suporte para geração de tokens e verificação de modelos (`gerar_token.py`, `verModelos.py`).

## Stack Tecnológica

* **Backend:** Python, FastAPI, Uvicorn, bibliotecas de integração com Google APIs.
* **Frontend:** Vue 3, Vite, HTML5, CSS3, suporte a PWA.
* **Base de Dados & Cloud:** Supabase.
* **Configuração de Deploy:** Suporte a Vercel (`vercel.json`).

## Estrutura do Repositório

O projeto segue uma arquitetura em monorepo estruturada da seguinte forma:

```
PicoteAssist-main/
├── apps/
│   ├── api/                    # Backend FastAPI (Python)
│   │   ├── services/           # Lógica de serviços externos
│   │   │   ├── __init__.py
│   │   │   ├── calendar_service.py
│   │   │   ├── supabase_service.py
│   │   │   └── tasks_service.py
│   │   ├── main.py             # Ponto de entrada da API
│   │   ├── requirements.txt    # Dependências Python
│   │   ├── state.py            # Gestão de estado da aplicação
│   │   └── verModelos.py       # Utilitários de validação/modelos
│   │
│   └── web/                    # Frontend Vue.js (Vite)
│       ├── public/             # Assets estáticos e manifestos PWA
│       ├── src/                # Componentes Vue e estilos principais
│       │   ├── assets/
│       │   ├── components/
│       │   ├── App.vue
│       │   ├── main.js
│       │   └── style.css
│       ├── index.html
│       ├── package.json
│       └── vite.config.js
├── gerar_token.py              # Script utilitário para autenticação/tokens
├── comandos.txt                # Registos de comandos úteis do projeto
└── vercel.json                 # Configuração de deploy
```

## Como Executar Localmente

### 1. Configurar e Executar o Backend (API)
1. Navega até à pasta da API:
   ```bash
   cd apps/api
   ```
2. Instala as dependências Python necessárias:
   ```bash
   pip install -r requirements.txt
   ```
3. Arranca o servidor FastAPI:
   ```bash
   uvicorn main:app --reload
   ```

### 2. Configurar e Executar o Frontend (Web)
1. Num novo terminal, navega até à pasta web:
   ```bash
   cd apps/web
   ```
2. Instala as dependências de Node.js:
   ```bash
   npm install
   ```
3. Inicia o servidor de desenvolvimento do Vite:
   ```bash
   npm run dev
   ```

---
*Projeto desenvolvido para centralizar a automação de tarefas e a gestão de produtividade através de uma arquitetura full-stack moderna.*
