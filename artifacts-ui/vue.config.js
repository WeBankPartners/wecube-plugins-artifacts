module.exports = {
  devServer: {
    open: true,
    port: 3000,
    proxy: {
    	"": {
            target: "http://localhost:8081"
          }
    }
  },
  runtimeCompiler: true,
  publicPath: "",
  chainWebpack: config => {
    if (process.env.APP_TYPE === "plugin") {
      const img = config.module.rule("images");
      img.uses.clear();
      img
        .use("file-loader")
        .loader("file-loader")
        .options({
          outputPath: "img"
        });
    }

    config.when(process.env.APP_TYPE === "plugin", config => {
      config
        .entry("app")
        .clear()
        .add("./src/main-plugin.js"); //作为插件时
    });
    config.when(!process.env.APP_TYPE, config => {
      config
        .entry("app")
        .clear()
        .add("./src/main.js"); //独立运行时
    });
  },
  productionSourceMap: process.env.APP_TYPE !== "plugin",
  configureWebpack: config => {
    if (process.env.APP_TYPE === "plugin") {
      config.optimization.splitChunks = {}
      return;
    } 
  }
}