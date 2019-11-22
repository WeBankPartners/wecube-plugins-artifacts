import Vue from 'vue'
import router from "./router-plugin";

Vue.config.productionTip = false

//window.component("WeCMDBSelect", WeCMDBSelect); -->  Vue.component("WeCMDBSelect", WeCMDBSelect)
//window.use(iview)  -->  Vue.use(iview)


window.addRoutes && window.addRoutes(router, "plugin-name");