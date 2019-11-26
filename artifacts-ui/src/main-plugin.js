import Vue from 'vue'
import router from "./router-plugin";
import ArtifactsSimpleTable from "../src/components/simple-table.vue";
import ArtifactsAttrInput from "../src/components/attr-input.vue";

window.component("ArtifactsSimpleTable", ArtifactsSimpleTable);
window.component("ArtifactsAttrInput", ArtifactsAttrInput);

Vue.config.productionTip = false

window.addRoutes && window.addRoutes(router, "plugin-name");
