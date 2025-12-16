import Artifacts from './views/artifacts.vue'
import TemplateConfig from './views/template-config.vue'
import VariableTemplateBind from './views/variable-template-bind.vue'

export default [
  {
    path: '/artifacts/implementation/artifact-management',
    name: 'artifacts',
    component: Artifacts
  },
  {
    path: '/artifacts/implementation/template-config',
    name: 'template-config',
    component: TemplateConfig
  },
  {
    path: '/artifacts/implementation/variable-template-bind',
    name: 'variable-template-bind',
    component: VariableTemplateBind
  }
]
