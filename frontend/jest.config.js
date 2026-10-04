/** @type {import('jest').Config} */
const nextConfig = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  testMatch: ['<rootDir>/__tests__/**/*.test.ts', '<rootDir>/__tests__/**/*.test.tsx'],
  // `.next/standalone` holds a second copy of package.json, which the haste map
  // reports as a naming collision and silently doubles every scan.
  modulePathIgnorePatterns: ['<rootDir>/.next/'],
  collectCoverageFrom: ['lib/**/*.{ts,tsx}', 'components/**/*.{ts,tsx}'],
  transform: {
    '^.+\\.(t|j)sx?$': [
      'ts-jest',
      {
        tsconfig: {
          // The app tsconfig targets Next's compiler, so Jest needs its own JSX
          // and module settings to run the same files under Node.
          jsx: 'react-jsx',
          module: 'commonjs',
          target: 'ES2020',
          lib: ['dom', 'dom.iterable', 'esnext'],
          noEmit: false,
        },
      },
    ],
  },
}

module.exports = nextConfig
