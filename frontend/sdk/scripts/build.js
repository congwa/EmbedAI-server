#!/usr/bin/env node

/**
 * 构建脚本
 */

const { execSync } = require('child_process')
const fs = require('fs')
const path = require('path')

console.log('🚀 开始构建 EmbedAI SDK...\n')

// 清理dist目录
console.log('📁 清理构建目录...')
if (fs.existsSync('dist')) {
  fs.rmSync('dist', { recursive: true, force: true })
}

try {
  // 构建TypeScript
  console.log('🔨 编译 TypeScript...')
  execSync('tsc', { stdio: 'inherit' })

  // 构建Vite
  console.log('📦 打包文件...')
  execSync('vite build', { stdio: 'inherit' })

  // 生成类型定义
  console.log('📝 生成类型定义...')
  execSync('npm run build:types', { stdio: 'inherit' })

  // 复制额外文件
  console.log('📋 复制文件...')
  const filesToCopy = [
    { src: 'README.md', dest: 'dist/README.md' },
    { src: 'package.json', dest: 'dist/package.json' },
    { src: 'LICENSE', dest: 'dist/LICENSE' }
  ]

  filesToCopy.forEach(({ src, dest }) => {
    if (fs.existsSync(src)) {
      fs.copyFileSync(src, dest)
      console.log(`  ✅ ${src} -> ${dest}`)
    }
  })

  // 创建简化的package.json
  const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'))
  const distPackageJson = {
    name: packageJson.name,
    version: packageJson.version,
    description: packageJson.description,
    main: packageJson.main,
    module: packageJson.module,
    types: packageJson.types,
    files: packageJson.files,
    keywords: packageJson.keywords,
    author: packageJson.author,
    license: packageJson.license,
    repository: packageJson.repository,
    bugs: packageJson.bugs,
    homepage: packageJson.homepage,
    peerDependencies: packageJson.peerDependencies || {},
    browserslist: packageJson.browserslist
  }

  fs.writeFileSync('dist/package.json', JSON.stringify(distPackageJson, null, 2))

  // 显示构建结果
  console.log('\n📊 构建结果:')
  const distFiles = fs.readdirSync('dist')
  distFiles.forEach(file => {
    const filePath = path.join('dist', file)
    const stats = fs.statSync(filePath)
    if (stats.isFile()) {
      const size = (stats.size / 1024).toFixed(2)
      console.log(`  📄 ${file} (${size} KB)`)
    }
  })

  console.log('\n✅ 构建完成！')
  console.log('\n📦 发布命令:')
  console.log('  cd dist && npm publish')

} catch (error) {
  console.error('\n❌ 构建失败:', error.message)
  process.exit(1)
}
