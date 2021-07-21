module.exports = {
  coverageThreshold: {
    './js/config': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90,
    },
    './js/components': {
      branches: 67, // 75
      functions: 67, // 75
      lines: 75, // 75
      statements: 75, // 75
    },
    './js/pages': {
      branches: 65, // 75
      functions: 72, // 75
      lines: 81, // 75
      statements: 78, // 75
    },
    './js/ducks': {
      branches: 65, // 75
      functions: 80,
      lines: 80,
      statements: 80,
    },
    './js/fixtures': {
      branches: 100,
      functions: 100,
      lines: 100,
      statements: 100,
    },
  },
  roots: ['<rootDir>/js'],
  setupFiles: ['<rootDir>/test-setup.ts'],
  transform: {
    '^.+\\.tsx?$': 'ts-jest',
    '^.+\\.js$': 'babel-jest',
  },
  testRegex: '(test|spec)\\.(j|t)sx?$',
  moduleDirectories: ['node_modules', 'js'],
  coveragePathIgnorePatterns: [
    'stories/*',
    'constants.ts',
    '.story.tsx',
    'js/index.tsx',
  ],
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],
  moduleNameMapper: {
    '^.+\\.(css|scss)$': '<rootDir>/node_modules/jest-css-modules',
  },
  globals: {
    'ts-jest': {
      diagnostics: false,
    },
  },
};
