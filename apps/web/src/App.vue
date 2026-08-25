<template>
  <!-- NOVO FUNDO ANIMADO (ESTILO AI) -->
  <div class="ai-background">
    <div class="blob blob-1"></div>
    <div class="blob blob-2"></div>
    <div class="blob blob-3"></div>
  </div>

  <!-- Adicionámos a classe 'transparent-layout' para o fundo se ver -->
  <q-layout view="hHh Lpr lFf" class="transparent-layout">
    
    <!-- CABEÇALHO PREMIUM -->
    <q-header class="glass-header text-dark">
      <q-toolbar class="q-px-md q-py-sm" style="max-width: 800px; margin: 0 auto;">
        <!-- NOVO ÍCONE: O Robô Minimalista de volta -->
        <q-avatar size="45px" class="shadow-3" style="background: transparent;">
          <img src="https://api.dicebear.com/7.x/bottts-neutral/svg?seed=Picote&backgroundColor=1e3c72" alt="Picote" />
        </q-avatar>
        <div class="q-ml-md column justify-center">
          <span class="text-weight-bold" style="font-size: 1.1rem; letter-spacing: -0.5px;">Picote Assist</span>
          <span class="text-caption text-primary" style="font-weight: 600; margin-top: -2px;">
            <q-icon name="circle" color="positive" size="8px" class="q-mr-xs" />Online
          </span>
        </div>
        <q-space />
        <q-btn-dropdown flat round dense class="q-mr-sm">
          
          <!-- O "rótulo" do botão que muda dinamicamente -->
          <template v-slot:label>
            <q-avatar size="32px">
              <img v-if="userAvatar" :src="userAvatar" referrerpolicy="no-referrer" />
              <q-icon v-else name="account_circle" size="32px" color="grey-7" />
            </q-avatar>
          </template>
          <q-list style="min-width: 200px">
            
            <q-item-label header>Integrações</q-item-label>
            
            <q-item clickable v-close-popup @click="conectarGoogle">
              <q-item-section avatar>
                <q-icon name="event" color="primary" />
              </q-item-section>
              <q-item-section>
                <q-item-label>Conectar Google</q-item-label>
                <q-item-label caption>Sincronizar Calendário</q-item-label>
              </q-item-section>
            </q-item>

            <q-separator />
            
            <q-item-label header>Conta</q-item-label>

            <!-- Espaço para futuras funcionalidades -->
            <q-item clickable v-close-popup @click="showSettingsModal = true">
              <q-item-section avatar>
                <q-icon name="settings" />
              </q-item-section>
              <q-item-section>Definições</q-item-section>
            </q-item>
            
            <q-item clickable v-close-popup @click="fazerLogout">
              <q-item-section avatar>
                <q-icon name="logout" color="negative" />
              </q-item-section>
              <q-item-section>Sair</q-item-section>
            </q-item>
          </q-list>
        </q-btn-dropdown>
      </q-toolbar>
    </q-header>

    <!-- ÁREA DE MENSAGENS -->
    <q-page-container>
      <q-page class="q-pa-md flex column justify-end" style="max-width: 800px; margin: 0 auto; padding-bottom: 20px;">
        
        <q-chat-message
          v-for="(msg, index) in chatHistory"
          :key="index"
          :sent="msg.role === 'user'"
          class="q-mb-md custom-chat-bubble"
          :class="msg.role === 'user' ? 'bubble-user' : 'bubble-bot'"
        >
          <template v-slot:default>
            <div class="message-text" v-html="formatText(msg.content)"></div>
          </template>
        </q-chat-message>
        
        <q-chat-message
          v-if="isLoading"
          class="q-mb-md custom-chat-bubble bubble-bot"
        >
          <q-spinner-dots size="2rem" color="primary" />
        </q-chat-message>

      </q-page>
    </q-page-container>

    <!-- BARRA DE ESCRITA -->
    <q-footer class="glass-footer q-pa-md">
      <div class="input-container shadow-10">
        <q-input
          v-model="newMessage"
          borderless
          dense
          placeholder="Escreve uma mensagem..."
          class="full-width q-px-md q-py-xs"
          @keyup.enter="enviarParaOPython"
          :disable="isLoading"
        >
          <template v-slot:after>
            <q-btn 
              round 
              dense 
              flat 
              icon="mic" 
              :color="isListening ? 'negative' : 'grey-7'" 
              class="q-mr-xs hover-effect"
              :class="isListening ? 'glossy' : ''"
              @click="startVoiceRecognition" 
            />
            <q-btn 
              round 
              dense 
              flat 
              icon="send" 
              :color="newMessage ? 'primary' : 'grey-4'" 
              class="hover-effect"
              @click="enviarParaOPython" 
              :disable="!newMessage || isLoading" 
            />
          </template>
        </q-input>
      </div>
    </q-footer>

    <!-- MODAL DE DEFINIÇÕES -->
    <q-dialog v-model="showSettingsModal">
      <q-card style="min-width: 320px; border-radius: 16px;" class="q-pa-sm">
        <q-card-section class="row items-center q-pb-none">
          <div class="text-h6 text-weight-bold">Definições</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section class="q-gutter-md">
          <!-- Opção 1: Voz do Picote -->
          <div class="row items-center justify-between">
            <div>
              <div class="text-weight-medium">Voz do Picote</div>
              <div class="text-caption text-grey">Ler respostas em voz alta</div>
            </div>
            <q-toggle 
              :model-value="vozAtiva" 
              color="primary" 
              @update:model-value="alternarVoz" 
            />
          </div>

          <q-separator />

          <!-- Opção 2: Dark Mode -->
          <div class="row items-center justify-between">
            <div>
              <div class="text-weight-medium">Modo Escuro</div>
              <div class="text-caption text-grey">Alternar tema visual</div>
            </div>
            <q-toggle 
              :model-value="darkModeAtivo" 
              color="primary" 
              @update:model-value="aplicarDarkMode" 
            />
          </div>
        </q-card-section>

        <q-card-actions align="right" class="q-pt-none">
          <q-btn flat label="Fechar" color="primary" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>

  </q-layout>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { marked } from 'marked'
import { useQuasar } from 'quasar'

const newMessage = ref('')
const isLoading = ref(false)

const isListening = ref(false)

const conectarGoogle = () => {
  // Ajusta a porta caso o teu FastAPI local não esteja na 8000
  const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
  window.location.href = `${backendUrl}/api/google/login`;
};

const fazerLogout = () => {
  console.log("Logout clicado! Futura ligação ao Supabase.");
};

const startVoiceRecognition = () => {
  // Verifica se o browser suporta reconhecimento de voz
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SpeechRecognition) {
    alert('O teu browser atual não suporta o reconhecimento de voz. Tenta no Chrome ou Edge!')
    return
  }

  const recognition = new SpeechRecognition()
  recognition.lang = 'pt-PT' // Define a língua para Português de Portugal
  recognition.continuous = false
  recognition.interimResults = false

  recognition.onstart = () => {
    isListening.value = true
  }

  recognition.onresult = (event) => {
    // Apanha o que disseste e coloca na barra de texto
    const transcript = event.results[0][0].transcript
    newMessage.value = transcript
  }

  recognition.onerror = (event) => {
    console.error('Erro no microfone:', event.error)
    isListening.value = false
  }

  recognition.onend = () => {
    isListening.value = false
    // Se quiseres que ele envie automaticamente após falares, 
    // podes descomentar a linha abaixo:
    enviarParaOPython() 
  }

  recognition.start()
}

const chatHistory = ref([
  { role: 'assistant', content: 'Olá! Sou o Picote. Em que te posso ajudar hoje?' }
])

const formatText = (text) => {
  if (!text) return ''
  // O marked converte automaticamente os **, listas e links para HTML perfeito!
  return marked.parse(text) 
}

const enviarParaOPython = async () => {
  const texto = newMessage.value.trim()
  if (!texto) return

  // 1. Adicionamos a mensagem ao ecrã (como já tinhas)
  chatHistory.value.push({ role: 'user', content: texto })
  newMessage.value = ''
  isLoading.value = true

  await nextTick()
  window.scrollTo(0, document.body.scrollHeight)

  // 2. PREPARAR A MEMÓRIA: Copiamos o histórico (exceto a mensagem atual que acabámos de adicionar)
  // e formatamos para o padrão que o teu backend em Python espera.
  const historicoParaEnviar = chatHistory.value
    .slice(0, -1) // Ignora a última mensagem para não ir duplicada
    .map(msg => ({
      role: msg.role === 'assistant' ? 'model' : 'user', // O Gemini precisa que seja 'model'
      text: msg.content // O Python está à procura da chave 'text'
    }))

    try {
      // Vai buscar o URL base (localhost no teu PC, ou o URL do Vercel na nuvem)
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
      
      const resposta = await fetch(`${backendUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
           message: texto,
           history: historicoParaEnviar 
        })
      })

    if (!resposta.ok) throw new Error('Erro do servidor Python')
    
    const dados = await resposta.json()
    chatHistory.value.push({ role: 'assistant', content: dados.response })

    if (vozAtiva.value) {
      falarComOVutilizador(dados.response)
    }

  } catch (erro) {
    console.error("Erro:", erro)
    chatHistory.value.push({ 
       role: 'assistant', 
       content: 'Ups, perdi a ligação à base! O servidor Python está a correr?' 
     })
  } finally {
    isLoading.value = false
    await nextTick()
    window.scrollTo(0, document.body.scrollHeight)
  }
}

const falarComOVutilizador = (texto) => {
  if (!('speechSynthesis' in window)) return

  window.speechSynthesis.cancel()

  const textoLimpo = texto
    .replace(/[*_#`[\]()]/g, '')
    .replace(/https?:\/\/\S+/g, 'link')

  const utterance = new SpeechSynthesisUtterance(textoLimpo)
  utterance.lang = 'pt-PT'
  utterance.rate = 1.0

  const tentarFalar = () => {
    const voices = window.speechSynthesis.getVoices()
    // Procura qualquer voz que seja de Portugal
    const vozPT = voices.find(v => v.lang === 'pt-PT' || v.lang.includes('PT') || v.name.includes('Portugal'))
    if (vozPT) {
      utterance.voice = vozPT
    }
    window.speechSynthesis.speak(utterance)
  }

  // Se as vozes já estiverem carregadas, fala logo; senão espera o evento
  const voices = window.speechSynthesis.getVoices()
  if (voices.length > 0) {
    tentarFalar()
  } else {
    window.speechSynthesis.onvoiceschanged = tentarFalar
  }
}

const vozAtiva = ref(localStorage.getItem('vozAtiva') === 'true')

const $q = useQuasar()

// Estados para as Definições
const showSettingsModal = ref(false)
const darkModeAtivo = ref(localStorage.getItem('darkMode') === 'true')

// Aplica o dark mode logo ao iniciar se estiver guardado
if (darkModeAtivo.value) {
  $q.dark.set(true)
}

const alternarDarkMode = () => {
  darkModeAtivo.value = !darkModeAtivo.value
  $q.dark.set(darkModeAtivo.value)
  localStorage.setItem('darkMode', darkModeAtivo.value)
}

// Cria a variável da foto (tenta ler do PC primeiro)
const userAvatar = ref(localStorage.getItem('googleAvatar') || '')

// Função para aplicar o Dark Mode de forma segura
const aplicarDarkMode = (isDark) => {
  darkModeAtivo.value = isDark
  $q.dark.set(isDark)
  localStorage.setItem('darkMode', isDark)
}

// Função para a voz
const alternarVoz = (val) => {
  vozAtiva.value = val
  localStorage.setItem('vozAtiva', val)
}

// Quando a página carrega, aplica imediatamente as preferências salvas
onMounted(() => {
  // 1. Aplica o Dark Mode guardado
  const savedDark = localStorage.getItem('darkMode') === 'true'
  aplicarDarkMode(savedDark)

  // 2. Recupera o avatar da Google se vier no URL ou localStorage
  const urlParams = new URLSearchParams(window.location.search);
  const avatarUrl = urlParams.get('avatar');
  if (avatarUrl) {
    userAvatar.value = avatarUrl;
    localStorage.setItem('googleAvatar', avatarUrl);
    window.history.replaceState({}, document.title, window.location.pathname);
  }
})
</script>

<style>
/* =========================================
   1. FUNDO ANIMADO (AI BLOBS - ADAPTÁVEL)
   ========================================= */
.ai-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: -1;
  background-color: #f8f9fc;
  overflow: hidden;
  transition: background-color 0.3s ease;
}

/* Quando o Quasar ativa o modo escuro, o body ganha a classe .body--dark */
.body--dark .ai-background {
  background-color: #0f1015 !important;
}

.blob {
  position: absolute;
  filter: blur(90px);
  opacity: 0.5;
  border-radius: 50%;
  animation: float 15s infinite alternate ease-in-out;
}

.blob-1 {
  top: -10%;
  left: -10%;
  width: 50vw;
  height: 50vw;
  background: #58fa7b;
  animation-delay: 0s;
}

.blob-2 {
  bottom: -15%;
  right: -10%;
  width: 60vw;
  height: 60vw;
  background: #ffc37e;
  animation-delay: -3s;
}

.blob-3 {
  top: 40%;
  left: 20%;
  width: 40vw;
  height: 40vw;
  background: #74cff9;
  animation-delay: -6s;
}

/* No modo escuro, escurecemos e suavizamos um pouco os blobs para não brilharem demasiado */
.body--dark .blob {
  opacity: 0.25;
}

@keyframes float {
  0% { transform: translate(0, 0) scale(1); }
  100% { transform: translate(40px, 60px) scale(1.15); }
}

.transparent-layout {
  background: transparent !important;
}

/* =========================================
   2. EFEITOS DE VIDRO (GLASSMORPHISM)
   ========================================= */
.glass-header {
  background: rgba(255, 255, 255, 0.6) !important;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.5);
  transition: background 0.3s, border-color 0.3s;
}

.body--dark .glass-header {
  background: rgba(26, 28, 36, 0.75) !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.glass-footer {
  background: transparent !important;
}

.input-container {
  max-width: 750px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: 30px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.body--dark .input-container {
  background: rgba(26, 28, 36, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

/* Força a cor do texto do input no modo escuro */
.body--dark .q-field__native, 
.body--dark .q-field__input, 
.body--dark .q-field__marginal {
  color: #f3f4f6 !important;
}

/* =========================================
   3. ESTILOS DO CHAT E BALÕES
   ========================================= */
.custom-chat-bubble .q-message-text {
  border-radius: 20px !important;
  padding: 12px 18px !important;
  font-size: 15px;
  line-height: 1.5;
  box-shadow: 0 4px 15px rgba(0,0,0,0.04);
}

.custom-chat-bubble .q-message-text:before { 
  display: none; 
}

/* Balão do Utilizador (Azul vibrante em ambos os modos) */
.bubble-user .q-message-text {
  background: linear-gradient(135deg, #4da6ff 0%, #007AFF 100%) !important;
  color: white !important;
  border-bottom-right-radius: 4px !important;
  box-shadow: 0 4px 15px rgba(0, 122, 255, 0.25) !important;
}

/* Balão do Bot (Adapta-se ao modo escuro) */
.bubble-bot .q-message-text {
  background: rgba(255, 255, 255, 0.9) !important;
  backdrop-filter: blur(5px);
  color: #2d3748 !important;
  border: 1px solid rgba(255,255,255,0.6);
  border-bottom-left-radius: 4px !important;
}

.body--dark .bubble-bot .q-message-text {
  background: rgba(30, 32, 44, 0.9) !important;
  color: #f3f4f6 !important;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

@keyframes popIn {
  0% { opacity: 0; transform: translateY(15px) scale(0.95); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}

.custom-chat-bubble {
  animation: popIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
}

.hover-effect { 
  transition: transform 0.2s; 
}

.hover-effect:hover { 
  transform: scale(1.1); 
}

html, body { 
  scroll-behavior: smooth; 
}

@media (max-width: 768px) {
  .blob-1 {
    top: -5%;
    left: -30%;
    width: 130vw;
    height: 130vw;
  }
  .blob-2 {
    bottom: -5%;
    right: -30%;
    width: 140vw;
    height: 140vw;
  }
  .blob-3 {
    top: 30%;
    left: -15%;
    width: 120vw;
    height: 120vw;
  }
}


/* =========================================
   4. CORES DE TEXTO NO MODO ESCURO
   ========================================= */

/* Torna o texto do cabeçalho e títulos branco/claro no modo escuro */
.body--dark .text-dark {
  color: #f3f4f6 !important;
}

/* Garante que o texto dentro das mensagens do chat fica legível */
.body--dark .message-text,
.body--dark .q-message-text-content {
  color: #f3f4f6 !important;
}

/* Ajusta o texto dos cabeçalhos dos menus suspensos e modais */
.body--dark .q-item__label {
  color: #f3f4f6 !important;
}

.body--dark .q-item__label--caption {
  color: #9ca3af !important;
}

/* Estiliza o fundo do Modal de Definições para escuro */
.body--dark .q-card {
  background-color: #1a1c24 !important;
  color: #f3f4f6 !important;
  border: 1px solid rgba(255, 255, 255, 0.1);
}
</style>