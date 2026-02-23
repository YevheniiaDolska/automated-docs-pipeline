---
title: "bare-stream: Node.js-compatible streams for Holepunch"
description: "Stream library with automatic string-to-Buffer conversion, Web Streams API support, and 87% smaller bundle than Node.js core streams."
content_type: reference
tags:
  - Streams
  - Holepunch
  - Node.js
  - TypeScript
---

# bare-stream

[![npm version](https://img.shields.io/npm/v/bare-stream.svg)](https://www.npmjs.com/package/bare-stream)
[![license](https://img.shields.io/npm/l/bare-stream.svg)](https://github.com/holepunchto/bare-stream/blob/main/LICENSE)
[![build status](https://img.shields.io/github/actions/workflow/status/holepunchto/bare-stream/test.yml)](https://github.com/holepunchto/bare-stream/actions)

bare-stream provides Node.js-compatible streams for the Holepunch ecosystem. The library enables processing data in chunks without loading everything into memory, with automatic string-to-Buffer conversion and Web Streams API support.

```javascript
const { Readable, Writable, pipeline } = require('bare-stream')

const source = new Readable({
  read() {
    this.push('Hello, streams!')
    this.push(null)
  }
})

const destination = new Writable({
  write(chunk, encoding, callback) {
    console.log(chunk.toString())
    callback()
  }
})

pipeline(source, destination, (err) => {
  if (err) console.error('Pipeline failed:', err)
})
```

This guide covers installation, all five stream classes, utility functions, error handling, and production best practices.

## Key features

| Feature | Why it matters |
|---------|----------------|
| **Automatic string conversion** | No manual `Buffer.from()` calls. Methods like `push()` and `write()` convert strings to Buffers automatically using UTF-8 encoding. |
| **Multiple entry points** | Choose Node.js callbacks, Promise-based API, or WHATWG Web Streams depending on your target environment. |
| **87% smaller than Node.js streams** | Built on streamx: 2.8 KB gzipped versus 18 KB for Node.js core streams. Critical for browser bundles. |
| **Proper lifecycle hooks** | `_open()` and `_destroy()` methods ensure resources initialize and clean up correctly, preventing memory leaks. |
| **Full TypeScript support** | Complete type definitions ship with the package for all exports. |

## Install bare-stream

Install the package using npm:

```bash
npm install bare-stream
```

For Bare runtime environments, install optional peer dependencies:

```bash
npm install bare-buffer bare-events
```

Verify the installation succeeded:

```javascript
const { Readable } = require('bare-stream')
console.log('bare-stream version:', require('bare-stream/package.json').version)
```

## Create your first stream pipeline

Create a data processing pipeline in three steps. This example transforms input text to uppercase:

```javascript
const { Readable, Transform, Writable, pipeline } = require('bare-stream')

const source = new Readable({
  read() {
    this.push('user input data')
    this.push(null)
  }
})

const processor = new Transform({
  transform(chunk, encoding, callback) {
    const processed = chunk.toString().toUpperCase()
    callback(null, processed)
  }
})

const destination = new Writable({
  write(chunk, encoding, callback) {
    console.log('Processed:', chunk.toString())
    callback()
  }
})

pipeline(source, processor, destination, (err) => {
  if (err) {
    console.error('Pipeline failed:', err.message)
    process.exit(1)
  }
  console.log('Pipeline completed successfully')
})
```

Expected output:

```
Processed: USER INPUT DATA
Pipeline completed successfully
```

## API reference

### Stream classes

bare-stream provides five stream classes for different data flow patterns:

| Class | Purpose | Common use cases |
|-------|---------|------------------|
| `Readable` | Data source | File reading, HTTP responses, data generation |
| `Writable` | Data destination | File writing, HTTP requests, logging |
| `Duplex` | Bidirectional | TCP sockets, WebSockets, IPC channels |
| `Transform` | Modify data in transit | Compression, encryption, parsing |
| `PassThrough` | Pass data unchanged | Monitoring, metrics, debugging |

### Utility functions

| Function | Purpose |
|----------|---------|
| `pipeline(streams..., callback)` | Chain streams with automatic error handling and cleanup |
| `finished(stream, callback)` | Receive notification when a stream completes or errors |
| `isStream(object)` | Check if an object is a stream instance |
| `isEnded(stream)` | Check if a readable stream has ended |
| `isFinished(stream)` | Check if a writable stream has finished |
| `getStreamError(stream)` | Retrieve the error if a stream failed |

### Entry points for different environments

| Entry point | Import statement | Use case |
|-------------|------------------|----------|
| **Standard** | `require('bare-stream')` | Node.js callbacks |
| **Promises** | `require('bare-stream/promises')` | Async/await syntax |
| **Web** | `require('bare-stream/web')` | WHATWG Web Streams API |
| **Global** | `require('bare-stream/global')` | Test environments |

## Readable stream example

Readable streams produce data. Override the `_read()` method to push data to consumers. Call `this.push(null)` to signal end of data.

```javascript
const { Readable } = require('bare-stream')

const counter = new Readable({
  read() {
    if (this.current === undefined) this.current = 1

    if (this.current <= 5) {
      this.push(`Count: ${this.current}\n`)
      this.current++
    } else {
      this.push(null)
    }
  }
})

counter.on('data', (chunk) => process.stdout.write(chunk.toString()))
counter.on('end', () => console.log('Done'))
counter.on('error', (err) => console.error('Error:', err.message))
```

Expected output:

```
Count: 1
Count: 2
Count: 3
Count: 4
Count: 5
Done
```

## Writable stream example

Writable streams consume data. Override the `_write()` method to process incoming chunks. Call `callback()` to signal readiness for more data.

```javascript
const { Writable } = require('bare-stream')

const logger = new Writable({
  write(chunk, encoding, callback) {
    const timestamp = new Date().toISOString()
    const message = chunk.toString().trim()
    console.log(`[${timestamp}] ${message}`)
    callback()
  }
})

logger.write('Application started')
logger.write('Processing user request')
logger.write('Request completed')
logger.end()

logger.on('finish', () => console.log('All logs written'))
logger.on('error', (err) => console.error('Logger error:', err.message))
```

## Duplex stream for bidirectional communication

Duplex streams handle bidirectional communication. The readable and writable sides operate independently, making them ideal for network protocols.

```javascript
const { Duplex } = require('bare-stream')

const socket = new Duplex({
  read() {
    this.push('Response: OK')
    this.push('Response: Data received')
    this.push(null)
  },
  write(chunk, encoding, callback) {
    console.log('Sent:', chunk.toString())
    callback()
  }
})

socket.write('Request: Hello')
socket.write('Request: Send data')
socket.end()

socket.on('data', (chunk) => console.log('Received:', chunk.toString()))
socket.on('end', () => console.log('Connection closed'))
```

Expected output:

```
Sent: Request: Hello
Sent: Request: Send data
Received: Response: OK
Received: Response: Data received
Connection closed
```

## Transform stream for data modification

Transform streams modify data as it passes through. Override `_transform()` to process each chunk.

```javascript
const { Transform } = require('bare-stream')

const jsonParser = new Transform({
  objectMode: true,
  transform(chunk, encoding, callback) {
    try {
      const parsed = JSON.parse(chunk.toString())
      callback(null, parsed)
    } catch (err) {
      callback(new Error(`Invalid JSON: ${err.message}`))
    }
  }
})

jsonParser.on('data', (obj) => {
  console.log('Parsed:', obj)
})

jsonParser.on('error', (err) => {
  console.error('Parse error:', err.message)
})

jsonParser.write('{"name": "Alice", "role": "admin"}')
jsonParser.write('{"name": "Bob", "role": "user"}')
jsonParser.end()
```

Expected output:

```
Parsed: { name: 'Alice', role: 'admin' }
Parsed: { name: 'Bob', role: 'user' }
```

## PassThrough stream for monitoring

PassThrough streams pass data unchanged. Use them for logging, metrics collection, or debugging without modifying the data flow.

```javascript
const { Readable, Writable, PassThrough, pipeline } = require('bare-stream')

const source = new Readable({
  read() {
    this.push('chunk-1')
    this.push('chunk-2')
    this.push('chunk-3')
    this.push(null)
  }
})

const monitor = new PassThrough()
let totalBytes = 0

monitor.on('data', (chunk) => {
  totalBytes += chunk.length
})

const destination = new Writable({
  write(chunk, encoding, callback) {
    callback()
  }
})

pipeline(source, monitor, destination, (err) => {
  if (err) console.error('Error:', err.message)
  else console.log('Total bytes processed:', totalBytes)
})
```

Expected output:

```
Total bytes processed: 21
```

## Handle errors with pipeline

Always use `pipeline()` instead of `pipe()`. The pipeline function automatically destroys all streams on error and prevents resource leaks.

```javascript
const { Readable, Transform, Writable, pipeline } = require('bare-stream')

const source = new Readable({
  read() {
    this.push('data')
    this.push(null)
  }
})

const processor = new Transform({
  transform(chunk, encoding, callback) {
    if (chunk.toString() === 'bad-data') {
      callback(new Error('Invalid data received'))
      return
    }
    callback(null, chunk.toString().toUpperCase())
  }
})

const destination = new Writable({
  write(chunk, encoding, callback) {
    console.log('Output:', chunk.toString())
    callback()
  }
})

pipeline(source, processor, destination, (err) => {
  if (err) {
    console.error('Pipeline failed:', err.message)
    return
  }
  console.log('Pipeline completed')
})
```

## Use async/await with promises

Import from `bare-stream/promises` for async/await syntax:

```javascript
const { Readable, Transform, Writable } = require('bare-stream')
const { pipeline } = require('bare-stream/promises')

async function processData() {
  const source = new Readable({
    read() {
      this.push('async data')
      this.push(null)
    }
  })

  const processor = new Transform({
    transform(chunk, encoding, callback) {
      callback(null, chunk.toString().toUpperCase())
    }
  })

  const destination = new Writable({
    write(chunk, encoding, callback) {
      console.log('Processed:', chunk.toString())
      callback()
    }
  })

  try {
    await pipeline(source, processor, destination)
    console.log('Success')
  } catch (err) {
    console.error('Failed:', err.message)
  }
}

processData()
```

## Use Web Streams API

Import from `bare-stream/web` for WHATWG-compatible streams. Requires Node.js version 18 or later.

```javascript
const { ReadableStream, WritableStream } = require('bare-stream/web')

const readable = new ReadableStream({
  start(controller) {
    controller.enqueue('Hello from Web Streams')
    controller.enqueue('Second chunk')
    controller.close()
  }
})

async function consume() {
  for await (const chunk of readable) {
    console.log('Received:', chunk)
  }
}

consume()
```

Expected output:

```
Received: Hello from Web Streams
Received: Second chunk
```

## Cancel streams with AbortSignal

Use AbortController to cancel long-running streams. The stream emits an error when aborted.

```javascript
const { Readable } = require('bare-stream')

const controller = new AbortController()

const readable = new Readable({
  signal: controller.signal,
  read() {
    setTimeout(() => {
      this.push('data chunk')
    }, 1000)
  }
})

readable.on('data', (chunk) => {
  console.log('Received:', chunk.toString())
})

readable.on('error', (err) => {
  if (err.name === 'AbortError' || err.message.includes('abort')) {
    console.log('Stream cancelled by user')
  } else {
    console.error('Stream error:', err.message)
  }
})

setTimeout(() => {
  console.log('Cancelling stream...')
  controller.abort()
}, 3000)
```

## Handle backpressure correctly

When `write()` returns `false`, the internal buffer is full. Wait for the `drain` event before writing more data.

```javascript
const { Writable } = require('bare-stream')

const writable = new Writable({
  highWaterMark: 1024,
  write(chunk, encoding, callback) {
    setTimeout(callback, 100)
  }
})

async function writeData(chunks) {
  for (const chunk of chunks) {
    const canContinue = writable.write(chunk)

    if (!canContinue) {
      await new Promise((resolve) => writable.once('drain', resolve))
    }
  }
  writable.end()
}

writeData(['chunk1', 'chunk2', 'chunk3'])
```

## Implement cleanup with _destroy

Override `_destroy()` to release file handles, network connections, or other resources when the stream closes.

```javascript
const { Readable } = require('bare-stream')
const fs = require('fs')

class FileReader extends Readable {
  constructor(path) {
    super()
    this.path = path
    this.fd = null
  }

  _open(callback) {
    fs.open(this.path, 'r', (err, fd) => {
      if (err) return callback(err)
      this.fd = fd
      callback()
    })
  }

  _read(size) {
    const buffer = Buffer.alloc(size)
    fs.read(this.fd, buffer, 0, size, null, (err, bytesRead) => {
      if (err) return this.destroy(err)
      if (bytesRead === 0) return this.push(null)
      this.push(buffer.slice(0, bytesRead))
    })
  }

  _destroy(callback) {
    if (this.fd === null) {
      if (callback) callback()
      return
    }
    const fd = this.fd
    this.fd = null
    fs.close(fd, (err) => {
      if (callback) callback(err)
    })
  }
}
```

## Common mistakes to avoid

### Always signal end of stream

Forgetting to push `null` causes consumers to wait indefinitely:

```javascript
// Wrong: consumers hang indefinitely
const bad = new Readable({
  read() {
    this.push('data')
  }
})

// Correct: always signal end
const good = new Readable({
  read() {
    this.push('data')
    this.push(null)
  }
})
```

### Use pipeline instead of pipe

The `pipe()` method does not handle errors properly. Use `pipeline()` for automatic cleanup:

```javascript
// Wrong: errors not handled, resources may leak
readable.pipe(transform).pipe(writable)

// Correct: errors handled, all streams destroyed on failure
pipeline(readable, transform, writable, (err) => {
  if (err) console.error('Error:', err.message)
})
```

## TypeScript support

bare-stream ships with TypeScript definitions for all exports:

```typescript
import { Readable, Writable, Transform, pipeline } from 'bare-stream'

const readable: Readable = new Readable({
  read(size: number): void {
    this.push('typed data')
    this.push(null)
  }
})

const writable: Writable = new Writable({
  write(chunk: Buffer, encoding: string, callback: (err?: Error) => void): void {
    console.log(chunk.toString())
    callback()
  }
})

pipeline(readable, writable, (err: Error | null) => {
  if (err) console.error(err)
})
```

For Web Streams API types:

```typescript
import { ReadableStream, WritableStream } from 'bare-stream/web'
```

## Compare with alternatives

| Feature | bare-stream | streamx | Node.js streams |
|---------|-------------|---------|-----------------|
| Bundle size (gzipped) | 3 KB | 2.8 KB | 18 KB |
| String auto-conversion | Yes | No | No |
| Web Streams API | Yes | No | Partial |
| Lifecycle hooks | Yes | Yes | Limited |
| Promise-based pipeline | Yes | Yes | Yes (Node 15+) |
| Bare runtime support | Yes | Yes | No |

**Choose bare-stream** when you need string auto-conversion, Web Streams support, or are building for the Holepunch ecosystem.

**Choose streamx** for minimal bundle size without convenience features.

**Choose Node.js streams** for maximum compatibility with existing npm packages.

## Related projects

| Project | Description |
|---------|-------------|
| [streamx](https://github.com/mafintosh/streamx) | Underlying stream implementation |
| [hypercore](https://github.com/holepunchto/hypercore) | Distributed append-only log |
| [hyperdrive](https://github.com/holepunchto/hyperdrive) | Distributed file system |
| [bare-buffer](https://github.com/holepunchto/bare-buffer) | Buffer for Bare runtime |
| [bare-events](https://github.com/holepunchto/bare-events) | Event emitter for Bare runtime |

## License

[Apache-2.0](https://github.com/holepunchto/bare-stream/blob/main/LICENSE)

**Source code:** [github.com/holepunchto/bare-stream](https://github.com/holepunchto/bare-stream)

**Issues:** [github.com/holepunchto/bare-stream/issues](https://github.com/holepunchto/bare-stream/issues)
