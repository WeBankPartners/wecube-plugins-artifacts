module.exports = {
  devServer: {
    open: true,
    port: 3000,
    proxy: {
      '/artifacts': {
        target: 'http://127.0.0.1:19090'
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
  }
}
