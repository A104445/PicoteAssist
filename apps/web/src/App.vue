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
        <q-btn flat round dense icon="more_horiz" color="grey-7" />
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

  </q-layout>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { marked } from 'marked'

const newMessage = ref('')
const isLoading = ref(false)

const isListening = ref(false)

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

  chatHistory.value.push({ role: 'user', content: texto })
  newMessage.value = ''
  isLoading.value = true

  await nextTick()
  window.scrollTo(0, document.body.scrollHeight)

  try {
    // Substitui pelo teu URL exato do Render
    const resposta = await fetch('https://picote-assist-api.onrender.com/api/chat', { 
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: texto })
    })

    if (!resposta.ok) throw new Error('Erro do servidor Python')

    const dados = await resposta.json()
    chatHistory.value.push({ role: 'assistant', content: dados.response })

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
</script>

<style>
/* =========================================
   1. FUNDO ANIMADO (AI BLOBS)
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
}

.blob {
  position: absolute;
  filter: blur(90px); /* O truque para parecer uma nuvem difusa */
  opacity: 0.6;
  border-radius: 50%;
  animation: float 15s infinite alternate ease-in-out;
}

/* Bolha Verde (Canto superior esquerdo) */
.blob-1 {
  top: -10%;
  left: -10%;
  width: 50vw;
  height: 50vw;
  background: #58fa7b;
  animation-delay: 0s;
}

/* Bolha Laranja (Canto inferior direito) */
.blob-2 {
  bottom: -15%;
  right: -10%;
  width: 60vw;
  height: 60vw;
  background: #ffc37e;
  animation-delay: -3s;
}

/* Bolha Azul Ciano (Meio/Esquerda) */
.blob-3 {
  top: 40%;
  left: 20%;
  width: 40vw;
  height: 40vw;
  background: #74cff9;
  animation-delay: -6s;
}

@keyframes float {
  0% { transform: translate(0, 0) scale(1); }
  100% { transform: translate(40px, 60px) scale(1.15); }
}

/* Tornar o layout transparente para as bolhas aparecerem */
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
}

.glass-footer {
  /* Retiramos a cor sólida para ver o vidro da barra */
  background: transparent !important; 
}

.input-container {
  max-width: 750px; 
  margin: 0 auto; 
  /* Fundo da barra translúcido */
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: 30px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
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

.custom-chat-bubble .q-message-text:before { display: none; }

/* Balão do Utilizador (Azul Claro e Vibrante) */
.bubble-user .q-message-text {
  /* Mudámos para um azul céu que vai até ao azul clássico, sem tons escuros */
  background: linear-gradient(135deg, #4da6ff 0%, #007AFF 100%) !important;
  color: white !important;
  border-bottom-right-radius: 4px !important;
  /* Adicionámos um brilho azulado subtil na sombra em vez de cinzento */
  box-shadow: 0 4px 15px rgba(0, 122, 255, 0.25) !important; 
}

.bubble-bot .q-message-text {
  /* Bot tem um balão ligeiramente translúcido para fundir com as bolhas */
  background: rgba(255, 255, 255, 0.9) !important;
  backdrop-filter: blur(5px);
  color: #2d3748 !important;
  border: 1px solid rgba(255,255,255,0.6);
  border-bottom-left-radius: 4px !important;
}

@keyframes popIn {
  0% { opacity: 0; transform: translateY(15px) scale(0.95); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}

.custom-chat-bubble {
  animation: popIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
}

.hover-effect { transition: transform 0.2s; }
.hover-effect:hover { transform: scale(1.1); }
html, body { scroll-behavior: smooth; }

/* =========================================
   AJUSTES PARA DISPOSITIVOS MÓVEIS (PWA)
   ========================================= */
   @media (max-width: 768px) {
  /* No telemóvel, aumentamos drasticamente o tamanho em vw 
     para compensar a falta de largura do ecrã */
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
</style>