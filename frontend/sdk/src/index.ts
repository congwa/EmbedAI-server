/**
 * EmbedAI Web SDK
 * 智能聊天助手嵌入式组件
 */

import { EmbedAI } from './embedai-sdk'
import { 
  EmbedAIConfig,
  ThemeConfig,
  PositionConfig,
  Message,
  Chat,
  ConnectionStatus,
  EventType,
  EventListener,
  EmbedAIError,
  NetworkError,
  AuthError,
  ConfigError
} from './types'

// 导出主类
export { EmbedAI }

// 导出类型定义
export type {
  EmbedAIConfig,
  ThemeConfig,
  PositionConfig,
  Message,
  Chat,
  ConnectionStatus,
  EventType,
  EventListener
}

// 导出错误类
export {
  EmbedAIError,
  NetworkError,
  AuthError,
  ConfigError
}

// 全局实例管理
let globalInstance: EmbedAI | null = null

/**
 * 创建EmbedAI实例
 */
export function createEmbedAI(config: EmbedAIConfig): EmbedAI {
  // 如果已存在全局实例，先销毁
  if (globalInstance) {
    globalInstance.destroy()
  }
  
  globalInstance = new EmbedAI(config)
  return globalInstance
}

/**
 * 获取全局实例
 */
export function getEmbedAI(): EmbedAI | null {
  return globalInstance
}

/**
 * 销毁全局实例
 */
export function destroyEmbedAI(): void {
  if (globalInstance) {
    globalInstance.destroy()
    globalInstance = null
  }
}

/**
 * 快速初始化函数
 */
export function initEmbedAI(config: EmbedAIConfig): Promise<EmbedAI> {
  const instance = createEmbedAI(config)
  return instance.init().then(() => instance)
}

// 默认导出
export default EmbedAI

// 浏览器环境下的全局暴露
if (typeof window !== 'undefined') {
  // 将EmbedAI挂载到window对象
  (window as any).EmbedAI = EmbedAI;
  (window as any).createEmbedAI = createEmbedAI;
  (window as any).initEmbedAI = initEmbedAI;
  
  // 支持AMD/UMD模块系统
  if (typeof define === 'function' && define.amd) {
    define('embedai', [], () => ({
      EmbedAI,
      createEmbedAI,
      initEmbedAI,
      getEmbedAI,
      destroyEmbedAI
    }))
  }
}

/**
 * 版本信息
 */
export const version = '1.0.0'

/**
 * SDK信息
 */
export const sdkInfo = {
  name: '@embedai/web-sdk',
  version,
  description: 'EmbedAI Web SDK - 智能聊天助手嵌入式组件',
  author: 'EmbedAI Team',
  license: 'MIT'
}
