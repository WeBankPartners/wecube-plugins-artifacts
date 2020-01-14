import router from './router-plugin'
import ArtifactsSimpleTable from '../src/components/simple-table.vue'
import ArtifactsAutoFill from '../src/components/auto-fill.js'
import './locale/i18n'
import zhCN from './locale/i18n/zh-CN.json'
import enUS from './locale/i18n/en-US.json'

window.component('ArtifactsSimpleTable', ArtifactsSimpleTable)
window.component('ArtifactsAutoFill', ArtifactsAutoFill)

window.locale('zh-CN', zhCN)
window.locale('en-US', enUS)

window.addRoutes && window.addRoutes(router, 'artifacts')
