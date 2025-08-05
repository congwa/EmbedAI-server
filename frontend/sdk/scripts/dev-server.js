#!/usr/bin/env node

/**
 * 开发服务器
 */

const express = require('express')
const path = require('path')
const { createProxyMiddleware } = require('http-proxy-middleware')

const app = express()
const PORT = process.env.PORT || 3000
const API_URL = process.env.API_URL || 'http://localhost:8000'

// 静态文件服务
app.use(express.static(path.join(__dirname, '..')))
app.use('/dist', express.static(path.join(__dirname, '../dist')))

// API代理
app.use('/api', createProxyMiddleware({
  target: API_URL,
  changeOrigin: true,
  logLevel: 'debug'
}))

// WebSocket代理
app.use('/ws', createProxyMiddleware({
  target: API_URL.replace('http', 'ws'),
  ws: true,
  changeOrigin: true,
  logLevel: 'debug'
}))

// 示例页面路由
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '../examples/basic.html'))
})

app.get('/examples/:example', (req, res) => {
  const exampleFile = path.join(__dirname, '../examples', `${req.params.example}.html`)
  if (require('fs').existsSync(exampleFile)) {
    res.sendFile(exampleFile)
  } else {
    res.status(404).send('Example not found')
  }
})

// 启动服务器
app.listen(PORT, () => {
  console.log(`🚀 开发服务器启动成功！`)
  console.log(`📱 本地地址: http://localhost:${PORT}`)
  console.log(`🔗 API代理: ${API_URL}`)
  console.log(`📖 示例页面: http://localhost:${PORT}/examples/basic`)
  console.log(`\n按 Ctrl+C 停止服务器`)
})

// 优雅关闭
process.on('SIGINT', () => {
  console.log('\n👋 服务器已停止')
  process.exit(0)
})
