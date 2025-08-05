/**
 * UI样式定义
 */

import { ThemeConfig } from '@/types'

// 默认主题配置
export const defaultTheme: Required<ThemeConfig> = {
  primaryColor: '#007bff',
  secondaryColor: '#6c757d',
  backgroundColor: '#ffffff',
  textColor: '#333333',
  borderColor: '#e0e0e0',
  borderRadius: '8px',
  fontSize: '14px',
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)'
}

/**
 * 生成CSS样式
 */
export function generateStyles(theme: ThemeConfig = {}): string {
  const mergedTheme = { ...defaultTheme, ...theme }
  
  return `
    /* EmbedAI Widget 基础样式 */
    .embedai-widget {
      position: fixed;
      z-index: 999999;
      font-family: ${mergedTheme.fontFamily};
      font-size: ${mergedTheme.fontSize};
      color: ${mergedTheme.textColor};
      box-sizing: border-box;
    }
    
    .embedai-widget *,
    .embedai-widget *::before,
    .embedai-widget *::after {
      box-sizing: border-box;
    }
    
    /* 聊天按钮 */
    .embedai-chat-button {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: ${mergedTheme.primaryColor};
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: ${mergedTheme.boxShadow};
      transition: all 0.3s ease;
      position: relative;
      overflow: hidden;
    }
    
    .embedai-chat-button:hover {
      transform: scale(1.05);
      box-shadow: 0 6px 25px rgba(0, 0, 0, 0.2);
    }
    
    .embedai-chat-button svg {
      width: 24px;
      height: 24px;
      fill: white;
    }
    
    /* 未读消息徽章 */
    .embedai-badge {
      position: absolute;
      top: -5px;
      right: -5px;
      background: #ff4757;
      color: white;
      border-radius: 50%;
      width: 20px;
      height: 20px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      font-weight: bold;
      min-width: 20px;
    }
    
    /* 聊天窗口 */
    .embedai-chat-window {
      width: 380px;
      height: 600px;
      background: ${mergedTheme.backgroundColor};
      border-radius: ${mergedTheme.borderRadius};
      box-shadow: ${mergedTheme.boxShadow};
      display: flex;
      flex-direction: column;
      overflow: hidden;
      transition: all 0.3s ease;
      border: 1px solid ${mergedTheme.borderColor};
    }
    
    .embedai-chat-window.minimized {
      height: 60px;
    }
    
    /* 聊天头部 */
    .embedai-chat-header {
      background: ${mergedTheme.primaryColor};
      color: white;
      padding: 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      min-height: 60px;
    }
    
    .embedai-chat-title {
      font-weight: 600;
      font-size: 16px;
      margin: 0;
    }
    
    .embedai-chat-controls {
      display: flex;
      gap: 8px;
    }
    
    .embedai-control-button {
      background: none;
      border: none;
      color: white;
      cursor: pointer;
      padding: 4px;
      border-radius: 4px;
      transition: background-color 0.2s;
    }
    
    .embedai-control-button:hover {
      background: rgba(255, 255, 255, 0.2);
    }
    
    .embedai-control-button svg {
      width: 16px;
      height: 16px;
      fill: currentColor;
    }
    
    /* 连接状态指示器 */
    .embedai-status-indicator {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      opacity: 0.9;
    }
    
    .embedai-status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #28a745;
    }
    
    .embedai-status-dot.connecting {
      background: #ffc107;
      animation: pulse 1.5s infinite;
    }
    
    .embedai-status-dot.disconnected {
      background: #dc3545;
    }
    
    .embedai-status-dot.error {
      background: #dc3545;
      animation: pulse 1s infinite;
    }
    
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
    
    /* 消息列表 */
    .embedai-messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    
    .embedai-messages::-webkit-scrollbar {
      width: 6px;
    }
    
    .embedai-messages::-webkit-scrollbar-track {
      background: #f1f1f1;
      border-radius: 3px;
    }
    
    .embedai-messages::-webkit-scrollbar-thumb {
      background: ${mergedTheme.borderColor};
      border-radius: 3px;
    }
    
    .embedai-messages::-webkit-scrollbar-thumb:hover {
      background: ${mergedTheme.secondaryColor};
    }
    
    /* 消息项 */
    .embedai-message {
      display: flex;
      gap: 8px;
      max-width: 85%;
    }
    
    .embedai-message.user {
      align-self: flex-end;
      flex-direction: row-reverse;
    }
    
    .embedai-message.assistant {
      align-self: flex-start;
    }
    
    .embedai-message-avatar {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: ${mergedTheme.secondaryColor};
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      overflow: hidden;
    }
    
    .embedai-message-avatar img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    
    .embedai-message-avatar svg {
      width: 18px;
      height: 18px;
      fill: white;
    }
    
    .embedai-message-content {
      background: ${mergedTheme.backgroundColor};
      border: 1px solid ${mergedTheme.borderColor};
      border-radius: ${mergedTheme.borderRadius};
      padding: 12px;
      position: relative;
      word-wrap: break-word;
      line-height: 1.4;
    }
    
    .embedai-message.user .embedai-message-content {
      background: ${mergedTheme.primaryColor};
      color: white;
      border-color: ${mergedTheme.primaryColor};
    }
    
    .embedai-message-time {
      font-size: 11px;
      color: ${mergedTheme.secondaryColor};
      margin-top: 4px;
    }
    
    /* 输入区域 */
    .embedai-input-area {
      padding: 16px;
      border-top: 1px solid ${mergedTheme.borderColor};
      background: ${mergedTheme.backgroundColor};
    }
    
    .embedai-input-container {
      display: flex;
      gap: 8px;
      align-items: flex-end;
    }
    
    .embedai-input {
      flex: 1;
      border: 1px solid ${mergedTheme.borderColor};
      border-radius: ${mergedTheme.borderRadius};
      padding: 12px;
      font-size: ${mergedTheme.fontSize};
      font-family: ${mergedTheme.fontFamily};
      resize: none;
      min-height: 20px;
      max-height: 100px;
      outline: none;
      transition: border-color 0.2s;
    }
    
    .embedai-input:focus {
      border-color: ${mergedTheme.primaryColor};
    }
    
    .embedai-send-button {
      background: ${mergedTheme.primaryColor};
      color: white;
      border: none;
      border-radius: ${mergedTheme.borderRadius};
      padding: 12px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background-color 0.2s;
      min-width: 44px;
      height: 44px;
    }
    
    .embedai-send-button:hover:not(:disabled) {
      background: ${adjustColor(mergedTheme.primaryColor, -10)};
    }
    
    .embedai-send-button:disabled {
      background: ${mergedTheme.secondaryColor};
      cursor: not-allowed;
    }
    
    .embedai-send-button svg {
      width: 16px;
      height: 16px;
      fill: currentColor;
    }
    
    /* 打字指示器 */
    .embedai-typing-indicator {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px;
      color: ${mergedTheme.secondaryColor};
      font-style: italic;
    }
    
    .embedai-typing-dots {
      display: flex;
      gap: 2px;
    }
    
    .embedai-typing-dot {
      width: 4px;
      height: 4px;
      border-radius: 50%;
      background: ${mergedTheme.secondaryColor};
      animation: typing 1.4s infinite;
    }
    
    .embedai-typing-dot:nth-child(2) {
      animation-delay: 0.2s;
    }
    
    .embedai-typing-dot:nth-child(3) {
      animation-delay: 0.4s;
    }
    
    @keyframes typing {
      0%, 60%, 100% {
        transform: translateY(0);
        opacity: 0.5;
      }
      30% {
        transform: translateY(-10px);
        opacity: 1;
      }
    }
    
    /* 响应式设计 */
    @media (max-width: 480px) {
      .embedai-chat-window {
        width: 100vw;
        height: 100vh;
        border-radius: 0;
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
      }
    }
    
    /* 动画 */
    .embedai-fade-in {
      animation: fadeIn 0.3s ease;
    }
    
    .embedai-slide-up {
      animation: slideUp 0.3s ease;
    }
    
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
    
    @keyframes slideUp {
      from {
        opacity: 0;
        transform: translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
  `
}

/**
 * 调整颜色亮度
 */
function adjustColor(color: string, amount: number): string {
  const usePound = color[0] === '#'
  const col = usePound ? color.slice(1) : color
  
  const num = parseInt(col, 16)
  let r = (num >> 16) + amount
  let g = (num >> 8 & 0x00FF) + amount
  let b = (num & 0x0000FF) + amount
  
  r = r > 255 ? 255 : r < 0 ? 0 : r
  g = g > 255 ? 255 : g < 0 ? 0 : g
  b = b > 255 ? 255 : b < 0 ? 0 : b
  
  return (usePound ? '#' : '') + (r << 16 | g << 8 | b).toString(16).padStart(6, '0')
}
