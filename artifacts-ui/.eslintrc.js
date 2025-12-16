module.exports = {
  root: true,
  env: {
    node: true
  },
  extends: ['plugin:vue/essential', '@vue/standard'],
  rules: {
    'no-console': process.env.NODE_ENV === 'production' ? 'error' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'error' : 'off',
    'vue/no-parsing-error': [2, { 'x-invalid-end-tag': false }],
    'no-multi-spaces': 'off', // 禁用 no-multi-spaces 规则
    'no-trailing-spaces': 'off', // 禁用 no-trailing-spaces 规则
    indent: 'off'
  },
  parserOptions: {
    parser: 'babel-eslint'
  }
}
