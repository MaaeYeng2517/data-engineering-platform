import '@testing-library/jest-dom'

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
