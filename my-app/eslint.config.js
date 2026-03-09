import globals from 'globals'
import pluginJs from '@eslint/js'
import tseslint from 'typescript-eslint'
import pluginVue from 'eslint-plugin-vue'

const ignores = {
  ignores: ['dist', 'node_modules']
}

const baseConfigs = [
  pluginJs.configs.recommended,
  ...tseslint.configs.recommended,
  ...pluginVue.configs['flat/essential']
]

const projectRules = {
  files: ['src/**/*.{js,ts,vue}'],
  languageOptions: {
    parser: pluginVue.parser,
    parserOptions: {
      parser: tseslint.parser,
      sourceType: 'module',
      ecmaVersion: 'latest'
    },
    globals: globals.browser
  },
  rules: {
    'vue/multi-word-component-names': 'off'
  }
}

/** @type {import('eslint').Linter.Config[]} */
export default [ignores, ...baseConfigs, projectRules]
