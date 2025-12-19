import vuetify from 'eslint-config-vuetify'

export default [
  ...vuetify(),
  {
    ignores: [
      'src/client/**/*',
      'src/api/**/*',
      '**/*.gen.ts',
    ],
  },
]
