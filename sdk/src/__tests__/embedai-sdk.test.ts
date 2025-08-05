/**
 * EmbedAI SDK 测试
 */

import { EmbedAI } from '../embedai-sdk'
import { EmbedAIConfig, ConfigError } from '../types'

describe('EmbedAI SDK', () => {
  const mockConfig: EmbedAIConfig = {
    serverUrl: 'http://localhost:8000',
    knowledgeBaseId: 1,
    clientId: 'test-client-id',
    thirdPartyUserId: 123
  }

  beforeEach(() => {
    // 清理DOM
    document.body.innerHTML = ''
  })

  afterEach(() => {
    // 清理所有实例
    const widgets = document.querySelectorAll('.embedai-widget')
    widgets.forEach(widget => widget.remove())
  })

  describe('构造函数', () => {
    it('应该成功创建实例', () => {
      const embedai = new EmbedAI(mockConfig)
      expect(embedai).toBeInstanceOf(EmbedAI)
    })

    it('应该验证必需的配置项', () => {
      expect(() => {
        new EmbedAI({} as EmbedAIConfig)
      }).toThrow(ConfigError)
    })

    it('应该验证serverUrl格式', () => {
      expect(() => {
        new EmbedAI({
          ...mockConfig,
          serverUrl: 'invalid-url'
        })
      }).toThrow(ConfigError)
    })

    it('应该合并默认配置', () => {
      const embedai = new EmbedAI(mockConfig)
      const state = embedai.getConnectionStatus()
      expect(state).toBeDefined()
    })
  })

  describe('Widget创建', () => {
    it('应该在DOM中创建widget元素', () => {
      new EmbedAI(mockConfig)
      const widget = document.querySelector('.embedai-widget')
      expect(widget).toBeInTheDocument()
    })

    it('应该注入CSS样式', () => {
      new EmbedAI(mockConfig)
      const style = document.getElementById('embedai-widget-styles')
      expect(style).toBeInTheDocument()
    })

    it('应该根据配置设置位置', () => {
      const config = {
        ...mockConfig,
        position: {
          horizontal: 'left' as const,
          vertical: 'top' as const,
          offset: { x: 10, y: 10 }
        }
      }
      new EmbedAI(config)
      const widget = document.querySelector('.embedai-widget') as HTMLElement
      expect(widget.style.left).toBe('10px')
      expect(widget.style.top).toBe('10px')
    })
  })

  describe('主题配置', () => {
    it('应该应用自定义主题', () => {
      const config = {
        ...mockConfig,
        theme: {
          primaryColor: '#ff0000',
          backgroundColor: '#ffffff'
        }
      }
      new EmbedAI(config)
      const style = document.getElementById('embedai-widget-styles')
      expect(style?.textContent).toContain('#ff0000')
      expect(style?.textContent).toContain('#ffffff')
    })
  })

  describe('事件系统', () => {
    it('应该支持事件监听', () => {
      const embedai = new EmbedAI(mockConfig)
      const mockListener = jest.fn()
      
      embedai.on('open', mockListener)
      embedai.open()
      
      expect(mockListener).toHaveBeenCalled()
    })

    it('应该支持移除事件监听', () => {
      const embedai = new EmbedAI(mockConfig)
      const mockListener = jest.fn()
      
      embedai.on('open', mockListener)
      embedai.off('open', mockListener)
      embedai.open()
      
      expect(mockListener).not.toHaveBeenCalled()
    })
  })

  describe('Widget控制', () => {
    it('应该能够打开聊天窗口', () => {
      const embedai = new EmbedAI(mockConfig)
      embedai.open()
      
      const chatWindow = document.querySelector('.embedai-chat-window')
      expect(chatWindow).toBeInTheDocument()
    })

    it('应该能够关闭聊天窗口', () => {
      const embedai = new EmbedAI(mockConfig)
      embedai.open()
      embedai.close()
      
      const chatButton = document.querySelector('.embedai-chat-button')
      expect(chatButton).toBeInTheDocument()
    })

    it('应该能够最小化聊天窗口', () => {
      const embedai = new EmbedAI(mockConfig)
      embedai.open()
      embedai.minimize()
      
      const chatWindow = document.querySelector('.embedai-chat-window')
      expect(chatWindow).toHaveClass('minimized')
    })
  })

  describe('配置更新', () => {
    it('应该能够更新配置', () => {
      const embedai = new EmbedAI(mockConfig)
      
      embedai.updateConfig({
        theme: {
          primaryColor: '#00ff00'
        }
      })
      
      const style = document.getElementById('embedai-widget-styles')
      expect(style?.textContent).toContain('#00ff00')
    })
  })

  describe('销毁', () => {
    it('应该能够销毁实例', () => {
      const embedai = new EmbedAI(mockConfig)
      embedai.destroy()
      
      const widget = document.querySelector('.embedai-widget')
      expect(widget).not.toBeInTheDocument()
    })

    it('销毁后应该移除样式', () => {
      const embedai = new EmbedAI(mockConfig)
      embedai.destroy()
      
      const style = document.getElementById('embedai-widget-styles')
      expect(style).not.toBeInTheDocument()
    })
  })

  describe('静态方法', () => {
    it('应该返回正确的版本号', () => {
      const version = EmbedAI.getVersion()
      expect(version).toBe('1.0.0')
    })
  })
})
