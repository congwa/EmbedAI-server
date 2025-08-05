/**
 * 聊天Widget UI组件
 */

import { 
  EmbedAIConfig, 
  WidgetState, 
  Message, 
  ConnectionStatus,
  EventListener 
} from '@/types'
import { generateStyles } from './styles'
import { getIconHTML } from './icons'

export class ChatWidget {
  private container: HTMLElement
  private config: EmbedAIConfig
  private state: WidgetState
  private listeners: Map<string, EventListener[]> = new Map()
  private messagesContainer: HTMLElement | null = null
  private inputElement: HTMLTextAreaElement | null = null
  private sendButton: HTMLButtonElement | null = null
  private statusIndicator: HTMLElement | null = null
  private unreadBadge: HTMLElement | null = null

  constructor(config: EmbedAIConfig) {
    this.config = config
    this.state = {
      isOpen: config.autoOpen || false,
      isMinimized: false,
      connectionStatus: 'disconnected',
      messages: [],
      isTyping: false,
      unreadCount: 0
    }

    this.container = this.createContainer()
    this.injectStyles()
    this.render()
    this.bindEvents()
  }

  /**
   * 创建容器元素
   */
  private createContainer(): HTMLElement {
    const container = document.createElement('div')
    container.className = 'embedai-widget'
    container.style.cssText = this.getPositionStyles()
    
    document.body.appendChild(container)
    return container
  }

  /**
   * 获取位置样式
   */
  private getPositionStyles(): string {
    const position = this.config.position || { horizontal: 'right', vertical: 'bottom' }
    const offset = position.offset || { x: 20, y: 20 }

    let styles = ''
    
    if (position.horizontal === 'right') {
      styles += `right: ${offset.x}px;`
    } else {
      styles += `left: ${offset.x}px;`
    }

    if (position.vertical === 'bottom') {
      styles += `bottom: ${offset.y}px;`
    } else {
      styles += `top: ${offset.y}px;`
    }

    return styles
  }

  /**
   * 注入样式
   */
  private injectStyles(): void {
    const styleId = 'embedai-widget-styles'
    if (document.getElementById(styleId)) {
      return
    }

    const style = document.createElement('style')
    style.id = styleId
    style.textContent = generateStyles(this.config.theme)
    document.head.appendChild(style)
  }

  /**
   * 渲染组件
   */
  private render(): void {
    if (this.state.isOpen) {
      this.renderChatWindow()
    } else {
      this.renderChatButton()
    }
  }

  /**
   * 渲染聊天按钮
   */
  private renderChatButton(): void {
    this.container.innerHTML = `
      <button class="embedai-chat-button" title="打开聊天">
        ${getIconHTML('chat')}
        ${this.state.unreadCount > 0 ? `<span class="embedai-badge">${this.state.unreadCount}</span>` : ''}
      </button>
    `

    this.unreadBadge = this.container.querySelector('.embedai-badge')
    
    const button = this.container.querySelector('.embedai-chat-button') as HTMLButtonElement
    button.addEventListener('click', () => this.open())
  }

  /**
   * 渲染聊天窗口
   */
  private renderChatWindow(): void {
    this.container.innerHTML = `
      <div class="embedai-chat-window ${this.state.isMinimized ? 'minimized' : ''} embedai-fade-in">
        <div class="embedai-chat-header">
          <div>
            <h3 class="embedai-chat-title">智能助手</h3>
            <div class="embedai-status-indicator">
              <span class="embedai-status-dot ${this.state.connectionStatus}"></span>
              <span>${this.getStatusText()}</span>
            </div>
          </div>
          <div class="embedai-chat-controls">
            <button class="embedai-control-button" title="最小化" data-action="minimize">
              ${getIconHTML('minimize')}
            </button>
            <button class="embedai-control-button" title="关闭" data-action="close">
              ${getIconHTML('close')}
            </button>
          </div>
        </div>
        
        ${!this.state.isMinimized ? `
          <div class="embedai-messages" id="embedai-messages">
            ${this.renderMessages()}
            ${this.state.isTyping ? this.renderTypingIndicator() : ''}
          </div>
          
          <div class="embedai-input-area">
            <div class="embedai-input-container">
              <textarea 
                class="embedai-input" 
                placeholder="${this.config.placeholder || '输入您的问题...'}"
                rows="1"
                maxlength="1000"
              ></textarea>
              <button class="embedai-send-button" title="发送" ${this.state.connectionStatus !== 'connected' ? 'disabled' : ''}>
                ${getIconHTML('send')}
              </button>
            </div>
          </div>
        ` : ''}
      </div>
    `

    this.bindChatWindowEvents()
  }

  /**
   * 渲染消息列表
   */
  private renderMessages(): string {
    if (this.state.messages.length === 0) {
      return `
        <div class="embedai-message assistant">
          ${this.config.showAvatar !== false ? `
            <div class="embedai-message-avatar">
              ${this.config.avatarUrl ? 
                `<img src="${this.config.avatarUrl}" alt="助手">` : 
                getIconHTML('bot')
              }
            </div>
          ` : ''}
          <div class="embedai-message-content">
            ${this.config.welcomeMessage || '您好！我是您的智能助手，有什么可以帮助您的吗？'}
          </div>
        </div>
      `
    }

    return this.state.messages.map(message => this.renderMessage(message)).join('')
  }

  /**
   * 渲染单条消息
   */
  private renderMessage(message: Message): string {
    const isUser = message.message_type === 'USER'
    const time = new Date(message.created_at).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    })

    return `
      <div class="embedai-message ${isUser ? 'user' : 'assistant'} embedai-slide-up">
        ${this.config.showAvatar !== false ? `
          <div class="embedai-message-avatar">
            ${isUser ? 
              getIconHTML('user') : 
              (this.config.avatarUrl ? 
                `<img src="${this.config.avatarUrl}" alt="助手">` : 
                getIconHTML('bot')
              )
            }
          </div>
        ` : ''}
        <div class="embedai-message-content">
          ${this.formatMessageContent(message.content)}
          <div class="embedai-message-time">${time}</div>
        </div>
      </div>
    `
  }

  /**
   * 格式化消息内容
   */
  private formatMessageContent(content: string): string {
    // 简单的文本格式化，可以扩展支持Markdown等
    return content
      .replace(/\n/g, '<br>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
  }

  /**
   * 渲染打字指示器
   */
  private renderTypingIndicator(): string {
    return `
      <div class="embedai-typing-indicator">
        <div class="embedai-typing-dots">
          <div class="embedai-typing-dot"></div>
          <div class="embedai-typing-dot"></div>
          <div class="embedai-typing-dot"></div>
        </div>
        <span>正在输入...</span>
      </div>
    `
  }

  /**
   * 获取状态文本
   */
  private getStatusText(): string {
    switch (this.state.connectionStatus) {
      case 'connected':
        return '已连接'
      case 'connecting':
        return '连接中...'
      case 'disconnected':
        return '已断开'
      case 'reconnecting':
        return '重连中...'
      case 'error':
        return '连接错误'
      default:
        return '未知状态'
    }
  }

  /**
   * 绑定聊天窗口事件
   */
  private bindChatWindowEvents(): void {
    // 获取元素引用
    this.messagesContainer = this.container.querySelector('#embedai-messages')
    this.inputElement = this.container.querySelector('.embedai-input') as HTMLTextAreaElement
    this.sendButton = this.container.querySelector('.embedai-send-button') as HTMLButtonElement
    this.statusIndicator = this.container.querySelector('.embedai-status-dot')

    // 控制按钮事件
    const controlButtons = this.container.querySelectorAll('.embedai-control-button')
    controlButtons.forEach(button => {
      button.addEventListener('click', (e) => {
        const action = (e.target as HTMLElement).closest('button')?.dataset.action
        if (action === 'minimize') {
          this.minimize()
        } else if (action === 'close') {
          this.close()
        }
      })
    })

    // 输入框事件
    if (this.inputElement) {
      this.inputElement.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault()
          this.sendMessage()
        }
      })

      this.inputElement.addEventListener('input', () => {
        this.autoResizeTextarea()
      })
    }

    // 发送按钮事件
    if (this.sendButton) {
      this.sendButton.addEventListener('click', () => {
        this.sendMessage()
      })
    }
  }

  /**
   * 绑定通用事件
   */
  private bindEvents(): void {
    // 点击外部关闭（可选）
    document.addEventListener('click', (e) => {
      if (this.state.isOpen && !this.container.contains(e.target as Node)) {
        // 可以在这里添加点击外部关闭的逻辑
      }
    })

    // 键盘快捷键
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.state.isOpen) {
        this.close()
      }
    })
  }

  /**
   * 自动调整文本框高度
   */
  private autoResizeTextarea(): void {
    if (!this.inputElement) return

    this.inputElement.style.height = 'auto'
    this.inputElement.style.height = Math.min(this.inputElement.scrollHeight, 100) + 'px'
  }

  /**
   * 发送消息
   */
  private sendMessage(): void {
    if (!this.inputElement || !this.inputElement.value.trim()) {
      return
    }

    const content = this.inputElement.value.trim()
    this.inputElement.value = ''
    this.autoResizeTextarea()

    // 触发发送消息事件
    this.emit('send_message', content)
  }

  /**
   * 滚动到底部
   */
  private scrollToBottom(): void {
    if (this.messagesContainer) {
      this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight
    }
  }

  // 公共方法

  /**
   * 打开聊天窗口
   */
  open(): void {
    this.state.isOpen = true
    this.state.unreadCount = 0
    this.render()
    this.emit('open')
  }

  /**
   * 关闭聊天窗口
   */
  close(): void {
    this.state.isOpen = false
    this.state.isMinimized = false
    this.render()
    this.emit('close')
  }

  /**
   * 最小化聊天窗口
   */
  minimize(): void {
    this.state.isMinimized = !this.state.isMinimized
    this.render()
    this.emit('minimize', this.state.isMinimized)
  }

  /**
   * 添加消息
   */
  addMessage(message: Message): void {
    this.state.messages.push(message)
    
    if (this.state.isOpen && !this.state.isMinimized) {
      this.updateMessagesDisplay()
    } else {
      // 增加未读计数
      if (message.message_type !== 'USER') {
        this.state.unreadCount++
        this.updateUnreadBadge()
      }
    }
  }

  /**
   * 更新消息显示
   */
  private updateMessagesDisplay(): void {
    if (this.messagesContainer) {
      this.messagesContainer.innerHTML = this.renderMessages()
      this.scrollToBottom()
    }
  }

  /**
   * 更新未读徽章
   */
  private updateUnreadBadge(): void {
    if (this.unreadBadge) {
      this.unreadBadge.textContent = this.state.unreadCount.toString()
      this.unreadBadge.style.display = this.state.unreadCount > 0 ? 'flex' : 'none'
    }
  }

  /**
   * 设置连接状态
   */
  setConnectionStatus(status: ConnectionStatus): void {
    this.state.connectionStatus = status
    
    if (this.statusIndicator) {
      this.statusIndicator.className = `embedai-status-dot ${status}`
    }

    if (this.sendButton) {
      this.sendButton.disabled = status !== 'connected'
    }

    // 更新状态文本
    const statusText = this.container.querySelector('.embedai-status-indicator span')
    if (statusText) {
      statusText.textContent = this.getStatusText()
    }
  }

  /**
   * 设置打字状态
   */
  setTyping(isTyping: boolean): void {
    this.state.isTyping = isTyping
    this.updateMessagesDisplay()
  }

  /**
   * 清空消息
   */
  clearMessages(): void {
    this.state.messages = []
    this.updateMessagesDisplay()
  }

  /**
   * 销毁组件
   */
  destroy(): void {
    if (this.container && this.container.parentNode) {
      this.container.parentNode.removeChild(this.container)
    }

    // 移除样式
    const style = document.getElementById('embedai-widget-styles')
    if (style) {
      style.remove()
    }

    this.listeners.clear()
  }

  /**
   * 添加事件监听器
   */
  on(event: string, listener: EventListener): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event)!.push(listener)
  }

  /**
   * 移除事件监听器
   */
  off(event: string, listener?: EventListener): void {
    if (!this.listeners.has(event)) {
      return
    }

    if (!listener) {
      this.listeners.delete(event)
      return
    }

    const listeners = this.listeners.get(event)!
    const index = listeners.indexOf(listener)
    if (index > -1) {
      listeners.splice(index, 1)
    }
  }

  /**
   * 触发事件
   */
  private emit(event: string, ...args: any[]): void {
    const listeners = this.listeners.get(event)
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener(...args)
        } catch (error) {
          console.error('Widget event listener error:', error)
        }
      })
    }
  }

  /**
   * 获取当前状态
   */
  getState(): WidgetState {
    return { ...this.state }
  }

  /**
   * 更新配置
   */
  updateConfig(newConfig: Partial<EmbedAIConfig>): void {
    this.config = { ...this.config, ...newConfig }

    // 重新注入样式
    const style = document.getElementById('embedai-widget-styles')
    if (style) {
      style.textContent = generateStyles(this.config.theme)
    }

    // 更新位置
    this.container.style.cssText = this.getPositionStyles()

    // 重新渲染
    this.render()
  }
}
