import Vue from 'vue'
import Router from 'vue-router'
import Artifacts from './views/artifacts.vue'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      name: 'artifacts',
      component: Artifacts
    }
  ]
})
