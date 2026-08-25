import { createApp } from 'vue'
import { Quasar, Dark } from 'quasar' // <-- Importa o 'Dark' aqui

// Estilos do Quasar e ícones
import '@quasar/extras/material-icons/material-icons.css'
import 'quasar/src/css/index.sass'
import App from './App.vue'

const app = createApp(App)

app.use(Quasar, {
  plugins: {
    Dark // <-- Regista o plugin Dark
  },
})

app.mount('#app')