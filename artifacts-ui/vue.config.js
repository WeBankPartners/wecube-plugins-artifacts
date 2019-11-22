module.exports = {
  devServer: {
    open: true,
    port: 3000
  },
  runtimeCompiler: true,
  publicPath: "",
  chainWebpack: config => {
    if (process.env.PLUGIN === "plugin") {
      const img = config.module.rule("images");
      img.uses.clear();
      img
        .use("file-loader")
        .loader("file-loader")
        .options({
          outputPath: "img"
        });
    }

    config.when(process.env.PLUGIN === "plugin", config => {
      config
        .entry("app")
        .clear()
        .add("./src/main-plugin.js"); //作为插件时
    });
    config.when(!process.env.PLUGIN, config => {
      config
        .entry("app")
        .clear()
        .add("./src/main.js"); //独立运行时
    });
  },
  productionSourceMap: process.env.PLUGIN !== "plugin",
  configureWebpack: config => {
    if (process.env.PLUGIN === "plugin") {
      // Do Something
    } 
  }
}