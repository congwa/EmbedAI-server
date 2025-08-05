# EmbedAI Web SDK

🤖 **智能聊天助手嵌入式组件** - 轻松将AI聊天功能集成到任何网页中

[![npm version](https://badge.fury.io/js/@embedai/web-sdk.svg)](https://badge.fury.io/js/@embedai/web-sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![TypeScript](https://img.shields.io/badge/TypeScript-Ready-blue.svg)](https://www.typescriptlang.org/)

## ✨ 特性

- 🚀 **即插即用** - 一行代码集成智能聊天功能
- 🎨 **高度可定制** - 支持主题、位置、样式完全自定义
- 📱 **响应式设计** - 完美适配桌面和移动设备
- ⚡ **实时通信** - WebSocket实时消息推送
- 🔒 **安全可靠** - 企业级安全保障
- 🌍 **多语言支持** - 国际化友好
- 📦 **轻量级** - 压缩后仅 ~50KB
- 🔧 **TypeScript** - 完整的类型定义支持

## 🎯 快速开始

### 安装

#### NPM 安装
```bash
npm install @embedai/web-sdk
```

#### CDN 引入
```html
<script src="https://unpkg.com/@embedai/web-sdk@latest/dist/embedai.min.js"></script>
```

### 基础使用

```html
<!DOCTYPE html>
<html>
<head>
    <title>我的网站</title>
</head>
<body>
    <!-- 你的网页内容 -->
    <h1>欢迎来到我的网站</h1>
    
    <!-- 引入 EmbedAI SDK -->
    <script src="https://unpkg.com/@embedai/web-sdk@latest/dist/embedai.min.js"></script>
    <script>
        // 初始化 EmbedAI
        const embedai = new EmbedAI({
            serverUrl: 'https://your-embedai-server.com',
            knowledgeBaseId: 1,
            clientId: 'your-client-id',
            thirdPartyUserId: 1001
        });
        
        // 初始化并显示聊天按钮
        embedai.init();
    </script>
</body>
</html>
```

就这么简单！现在你的网页右下角会出现一个聊天按钮 💬

## 📖 详细配置

### 完整配置选项

```javascript
const embedai = new EmbedAI({
    // 必需配置
    serverUrl: 'https://your-embedai-server.com',  // EmbedAI服务器地址
    knowledgeBaseId: 1,                            // 知识库ID
    clientId: 'your-client-id',                    // 客户端ID
    thirdPartyUserId: 1001,                        // 第三方用户ID
    
    // 可选配置
    autoOpen: false,                               // 是否自动打开聊天窗口
    language: 'zh-CN',                             // 语言设置
    welcomeMessage: '您好！有什么可以帮助您的吗？',    // 欢迎消息
    placeholder: '输入您的问题...',                  // 输入框占位符
    showAvatar: true,                              // 是否显示头像
    avatarUrl: 'https://example.com/avatar.png',   // 自定义头像URL
    
    // 主题配置
    theme: {
        primaryColor: '#007bff',      // 主色调
        secondaryColor: '#6c757d',    // 次要颜色
        backgroundColor: '#ffffff',   // 背景颜色
        textColor: '#333333',         // 文本颜色
        borderColor: '#e0e0e0',       // 边框颜色
        borderRadius: '8px',          // 圆角大小
        fontSize: '14px',             // 字体大小
        fontFamily: 'Arial, sans-serif', // 字体
        boxShadow: '0 4px 20px rgba(0,0,0,0.15)' // 阴影
    },
    
    // 位置配置
    position: {
        horizontal: 'right',          // 水平位置: 'left' | 'right'
        vertical: 'bottom',           // 垂直位置: 'top' | 'bottom'
        offset: {
            x: 20,                    // 水平偏移
            y: 20                     // 垂直偏移
        }
    },
    
    // 连接配置
    maxReconnectAttempts: 5,          // 最大重连次数
    reconnectInterval: 3000           // 重连间隔(毫秒)
});
```

## 🎨 主题定制

### 预设主题

```javascript
// 蓝色主题（默认）
const blueTheme = {
    primaryColor: '#007bff',
    secondaryColor: '#6c757d'
};

// 绿色主题
const greenTheme = {
    primaryColor: '#28a745',
    secondaryColor: '#6c757d'
};

// 紫色主题
const purpleTheme = {
    primaryColor: '#6f42c1',
    secondaryColor: '#6c757d'
};

// 应用主题
const embedai = new EmbedAI({
    // ... 其他配置
    theme: greenTheme
});
```

### 深色模式

```javascript
const darkTheme = {
    primaryColor: '#0d6efd',
    backgroundColor: '#212529',
    textColor: '#ffffff',
    borderColor: '#495057',
    secondaryColor: '#6c757d'
};
```

### 自定义CSS

你也可以通过CSS覆盖样式：

```css
/* 自定义聊天按钮 */
.embedai-chat-button {
    background: linear-gradient(45deg, #ff6b6b, #ee5a24) !important;
    box-shadow: 0 8px 32px rgba(255, 107, 107, 0.3) !important;
}

/* 自定义聊天窗口 */
.embedai-chat-window {
    border-radius: 16px !important;
    backdrop-filter: blur(10px) !important;
}
```

## 🔧 API 参考

### 主要方法

```javascript
// 初始化SDK
await embedai.init();

// 打开聊天窗口
embedai.open();

// 关闭聊天窗口
embedai.close();

// 最小化聊天窗口
embedai.minimize();

// 发送消息（程序化）
await embedai.sendMessage('你好！');

// 查询知识库
await embedai.queryKnowledgeBase('如何使用这个功能？');

// 清空聊天记录
await embedai.clearChat();

// 更新配置
embedai.updateConfig({
    theme: { primaryColor: '#ff0000' }
});

// 获取连接状态
const status = embedai.getConnectionStatus();

// 获取当前聊天
const chat = embedai.getCurrentChat();

// 销毁实例
embedai.destroy();
```

### 事件监听

```javascript
// 聊天窗口打开
embedai.on('open', () => {
    console.log('聊天窗口已打开');
});

// 聊天窗口关闭
embedai.on('close', () => {
    console.log('聊天窗口已关闭');
});

// 收到新消息
embedai.on('message', (message) => {
    console.log('收到消息:', message);
});

// 连接状态变化
embedai.on('status_change', (status) => {
    console.log('连接状态:', status);
});

// 连接建立
embedai.on('connect', () => {
    console.log('已连接到服务器');
});

// 连接断开
embedai.on('disconnect', () => {
    console.log('与服务器断开连接');
});

// 发生错误
embedai.on('error', (error) => {
    console.error('发生错误:', error);
});

// 移除事件监听
embedai.off('message', messageHandler);
```

## 🌟 高级用法

### 多实例管理

```javascript
// 创建多个聊天实例
const customerService = new EmbedAI({
    serverUrl: 'https://api.example.com',
    knowledgeBaseId: 1,
    clientId: 'customer-service',
    thirdPartyUserId: 1001,
    position: { horizontal: 'right', vertical: 'bottom' }
});

const technicalSupport = new EmbedAI({
    serverUrl: 'https://api.example.com',
    knowledgeBaseId: 2,
    clientId: 'technical-support',
    thirdPartyUserId: 1001,
    position: { horizontal: 'left', vertical: 'bottom' }
});
```

### 条件加载

```javascript
// 根据用户类型加载不同配置
const userType = getUserType(); // 假设这是你的用户类型检测函数

const config = {
    serverUrl: 'https://api.example.com',
    knowledgeBaseId: userType === 'vip' ? 1 : 2,
    clientId: 'web-client',
    thirdPartyUserId: getCurrentUserId(),
    theme: userType === 'vip' ? goldTheme : defaultTheme
};

const embedai = new EmbedAI(config);
```

### 与现有系统集成

```javascript
// 与用户登录系统集成
function initChatForUser(user) {
    const embedai = new EmbedAI({
        serverUrl: 'https://api.example.com',
        knowledgeBaseId: 1,
        clientId: 'web-client',
        thirdPartyUserId: user.id,
        welcomeMessage: `您好 ${user.name}！有什么可以帮助您的吗？`
    });
    
    // 监听消息，发送到分析系统
    embedai.on('message', (message) => {
        analytics.track('chat_message', {
            userId: user.id,
            messageType: message.message_type,
            timestamp: message.created_at
        });
    });
    
    return embedai;
}

// 用户登录后初始化
onUserLogin((user) => {
    const chatInstance = initChatForUser(user);
    chatInstance.init();
});
```

## 📱 移动端适配

SDK 自动适配移动设备，在小屏幕上聊天窗口会全屏显示：

```javascript
// 移动端特定配置
const isMobile = window.innerWidth <= 768;

const embedai = new EmbedAI({
    // ... 基础配置
    position: isMobile ? 
        { horizontal: 'right', vertical: 'bottom', offset: { x: 10, y: 10 } } :
        { horizontal: 'right', vertical: 'bottom', offset: { x: 20, y: 20 } },
    theme: {
        fontSize: isMobile ? '16px' : '14px'
    }
});
```

## 🔍 故障排除

### 常见问题

**Q: 聊天按钮不显示？**
A: 检查控制台是否有错误，确认配置参数正确，特别是 `serverUrl` 格式。

**Q: 无法连接到服务器？**
A: 检查服务器地址是否正确，确认服务器支持跨域请求。

**Q: 样式被覆盖？**
A: SDK 使用高优先级的 CSS，如需自定义请使用 `!important` 或更具体的选择器。

**Q: 在某些浏览器中不工作？**
A: SDK 支持现代浏览器，IE 需要 polyfill 支持。

### 调试模式

```javascript
// 开启调试模式
const embedai = new EmbedAI({
    // ... 配置
    debug: true  // 开启详细日志
});

// 监听所有事件进行调试
['open', 'close', 'message', 'error', 'connect', 'disconnect'].forEach(event => {
    embedai.on(event, (...args) => {
        console.log(`[EmbedAI] ${event}:`, ...args);
    });
});
```

## 🤝 贡献

欢迎贡献代码！请查看 [贡献指南](CONTRIBUTING.md)。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件。

## 🔗 相关链接

- [官方文档](https://docs.embedai.com)
- [API 参考](https://api.embedai.com/docs)
- [示例代码](https://github.com/embedai/examples)
- [问题反馈](https://github.com/embedai/web-sdk/issues)

## 💬 支持

如有问题或建议，请通过以下方式联系我们：

- 📧 邮箱: support@embedai.com
- 💬 微信群: 扫描二维码加入
- 🐛 Bug 报告: [GitHub Issues](https://github.com/embedai/web-sdk/issues)

---

Made with ❤️ by EmbedAI Team
