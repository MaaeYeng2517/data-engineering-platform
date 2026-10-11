import '@testing-library/jest-dom'

// Mock react-markdown in Jest to avoid ESM transform issues in node_modules
jest.mock('react-markdown', () => {
  const React = require('react')
  const Markdown = ({ children }: { children?: React.ReactNode }) =>
    React.createElement('div', { 'data-testid': 'markdown' }, children)
  return { __esModule: true, default: Markdown, ReactMarkdown: Markdown }
})
jest.mock('remark-gfm', () => ({}))

// React 18 wants this flag so `act` warnings do not fail assertions in tests.
;(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true

// jsdom does not implement the streaming primitives that `fetch` responses and
// the chat SSE parser rely on, so borrow the Node implementations.
const globals = globalThis as unknown as Record<string, unknown>
if (typeof globals.ReadableStream === 'undefined') {
  globals.ReadableStream = require('node:stream/web').ReadableStream
}
if (typeof globals.TextEncoder === 'undefined') {
  const util = require('node:util')
  globals.TextEncoder = util.TextEncoder
  globals.TextDecoder = util.TextDecoder
}
