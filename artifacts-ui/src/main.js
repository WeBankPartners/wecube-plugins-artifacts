import Vue from 'vue'
import App from './App.vue'
import router from './router'
import ViewUI from "view-design";
import "view-design/dist/styles/iview.css";
import ArtifactsSimpleTable from "../src/components/simple-table.vue";
import ArtifactsAttrInput from "../src/pages/components/attr-input.vue";

Vue.component("ArtifactsSimpleTable", ArtifactsSimpleTable);
Vue.component("ArtifactsAttrInput", ArtifactsAttrInput);

Vue.config.productionTip = false

Vue.use(ViewUI, {
  transfer: true,
  size: "default"
});
new Vue({
  router,
  render: h => h(App)
}).$mount('#app')
