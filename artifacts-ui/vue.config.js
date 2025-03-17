const { codeInspectorPlugin } = require('code-inspector-plugin')
const dotenv = require('dotenv')
dotenv.config()

module.exports = {
  devServer: {
    open: true,
    port: 3000,
    proxy: {
      '/artifacts': {
        target: process.env.ARTIFACTS_TARGET
      }
    }
  },
  runtimeCompiler: true,
  publicPath: '',
  chainWebpack: config => {
    if (process.env.APP_TYPE === 'plugin') {
      const img = config.module.rule('images')
      img.uses.clear()
      img
        .use('url-loader')
        .loader('url-loader')
        .options({
          limit: 1000000
        })
      const svg = config.module.rule('svg')
      svg.uses.clear()
      svg
        .use('url-loader')
        .loader('url-loader')
        .options({
          limit: 1000000
        })
    } else {
      config.plugin('code-inspector-plugin').use(
        codeInspectorPlugin({
          bundler: 'webpack'
        })
      )
    }

    config.when(process.env.APP_TYPE === 'plugin', config => {
      config
        .entry('app')
        .clear()
        .add('./src/main-plugin.js') // 作为插件时
    })
    config.when(!process.env.APP_TYPE, config => {
      config
        .entry('app')
        .clear()
        .add('./src/main.js') // 独立运行时
    })
  },
  productionSourceMap: process.env.APP_TYPE !== 'plugin',
  configureWebpack: config => {
    if (process.env.APP_TYPE === 'plugin') {
      config.optimization.splitChunks = {}
    }
  },
  css: {
    loaderOptions: {
      less: {
        // 启用内联 JavaScript
        javascriptEnabled: true
      }
    }
  }
}
