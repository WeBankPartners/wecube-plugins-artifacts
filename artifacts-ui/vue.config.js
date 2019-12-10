const CompressionPlugin = require("compression-webpack-plugin");
module.exports = {
  devServer: {
    open: true,
    port: 3000,
    proxy: {
      "/artifacts": {
        target: "http://localhost:8081"
      }
    }
  },
  runtimeCompiler: true,
  publicPath: "",
  chainWebpack: config => {
    if (process.env.APP_TYPE === "plugin") {
      const img = config.module.rule("images");
      img.uses.clear()
      img.use('url-loader').loader('url-loader').options({
        limit: 1000000
      })
      const svg = config.module.rule('svg')
      svg.uses.clear()
      svg.use('url-loader').loader('url-loader').options({
        limit: 1000000
      })
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
    if (process.env.NODE_ENV === "production") {
      return {
        plugins: [
          new CompressionPlugin({
            algorithm: "gzip",
            test: /\.js$|\.html$|.\css/, //匹配文件名
            threshold: 10240, //对超过10k的数据压缩
            deleteOriginalAssets: false //不删除源文件
          })
        ]
      };
    }
  }
}