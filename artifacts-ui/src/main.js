import Vue from 'vue'
import App from './App.vue'
import router from './router'
import ViewUI from 'view-design'
import 'view-design/dist/styles/iview.css'
import ArtifactsSimpleTable from '../src/components/simple-table.vue'
import ArtifactsAutoFill from '../src/components/auto-fill.js'
import VueI18n from 'vue-i18n'
import locale from 'view-design/dist/locale/en-US'
import './locale/i18n'

Vue.component('ArtifactsSimpleTable', ArtifactsSimpleTable)
Vue.component('ArtifactsAutoFill', ArtifactsAutoFill)

Vue.config.productionTip = false

Vue.use(ViewUI, {
  transfer: true,
  size: 'default',
  VueI18n,
  locale
})
new Vue({
  router,
  render: h => h(App)
}).$mount('#app')
