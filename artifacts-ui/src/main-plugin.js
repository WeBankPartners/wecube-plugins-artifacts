import Vue from 'vue'
import router from "./router-plugin";
import ArtifactsSimpleTable from "../src/components/simple-table.vue";
import ArtifactsAttrInput from "../src/pages/components/attr-input";

Vue.component("ArtifactsSimpleTable", ArtifactsSimpleTable);
Vue.component("ArtifactsAttrInput", ArtifactsAttrInput);

Vue.config.productionTip = false

//window.component("WeCMDBSelect", WeCMDBSelect); -->  Vue.component("WeCMDBSelect", WeCMDBSelect)
//window.use(iview)  -->  Vue.use(iview)


window.addRoutes && window.addRoutes(router, "plugin-name");