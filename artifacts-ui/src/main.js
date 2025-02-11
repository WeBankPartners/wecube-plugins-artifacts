import ViewUI from 'view-design'
import Vue from 'vue'
import App from './App.vue'
import router from './router'

import './styles/index.less'

import locale from 'view-design/dist/locale/en-US'
import VueI18n from 'vue-i18n'
import commonUI from 'wecube-common-ui'
import 'wecube-common-ui/lib/wecube-common-ui.css'
import ArtifactsAutoFill from '../src/components/auto-fill.js'
import ArtifactsSimpleTable from '../src/components/simple-table.vue'
import './locale/i18n'
Vue.use(commonUI)
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
