import Vue from 'vue'
import Router from 'vue-router'
import Artifacts from './views/artifacts.vue'
import TemplateConfig from './views/template-config.vue'
import VariableTemplateBind from './views/variable-template-bind.vue'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      name: 'artifacts',
      component: Artifacts
    },
    {
      path: '/template-config',
      name: 'template-config',
      component: TemplateConfig
    },
    {
      path: '/variable-template-bind',
      name: 'variable-template-bind',
      component: VariableTemplateBind
    }
  ]
})
