/**
 * EmbedAI SDK 类型定义
 */

// 基础配置接口
export interface EmbedAIConfig {
  /** 服务器地址 */
  serverUrl: string
  /** 知识库ID */
  knowledgeBaseId: number
  /** 客户端ID */
  clientId: string
  /** 第三方用户ID */
  thirdPartyUserId: number
  /** 主题配置 */
  theme?: ThemeConfig
  /** 位置配置 */
  position?: PositionConfig
  /** 语言配置 */
  language?: string
  /** 是否自动打开 */
  autoOpen?: boolean
  /** 欢迎消息 */
  welcomeMessage?: string
  /** 占位符文本 */
  placeholder?: string
  /** 是否显示头像 */
  showAvatar?: boolean
  /** 自定义头像URL */
  avatarUrl?: string
  /** 最大重连次数 */
  maxReconnectAttempts?: number
  /** 重连间隔(毫秒) */
  reconnectInterval?: number
}

// 主题配置
export interface ThemeConfig {
  /** 主色调 */
  primaryColor?: string
  /** 次要颜色 */
  secondaryColor?: string
  /** 背景颜色 */
  backgroundColor?: string
  /** 文本颜色 */
  textColor?: string
  /** 边框颜色 */
  borderColor?: string
  /** 圆角大小 */
  borderRadius?: string
  /** 字体大小 */
  fontSize?: string
  /** 字体家族 */
  fontFamily?: string
  /** 阴影 */
  boxShadow?: string
}

// 位置配置
export interface PositionConfig {
  /** 水平位置 */
  horizontal?: 'left' | 'right'
  /** 垂直位置 */
  vertical?: 'top' | 'bottom'
  /** 距离边缘的偏移 */
  offset?: {
    x?: number
    y?: number
  }
}

// 消息类型
export type MessageType = 'USER' | 'ASSISTANT' | 'OFFICIAL' | 'SYSTEM'

// 用户类型
export type UserType = 'third_party' | 'official'

// 消息接口
export interface Message {
  id: number
  chat_id: number
  content: string
  message_type: MessageType
  sender_id: number
  sender_type: UserType
  created_at: string
  metadata?: Record<string, any>
  read_by?: ReadByUser[]
}

// 已读用户
export interface ReadByUser {
  id: number
  user_id: number
  user_type: UserType
}

// 聊天会话
export interface Chat {
  id: number
  third_party_user_id: number
  kb_id: number
  title: string
  created_at: string
  updated_at: string
}

// WebSocket消息格式
export interface WSMessage {
  type: string
  payload: any
  request_id?: string
}

// 查询请求
export interface QueryRequest {
  query: string
  top_k?: number
}

// 查询响应
export interface QueryResponse {
  answer: string
  sources?: any[]
  metadata?: Record<string, any>
}

// 聊天创建请求
export interface ChatCreateRequest {
  third_party_user_id: number
  kb_id: number
  title?: string
}

// API响应格式
export interface APIResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: {
    code: string
    message: string
    details?: any
  }
}

// 事件类型
export type EventType = 
  | 'ready'
  | 'open'
  | 'close'
  | 'message'
  | 'error'
  | 'typing'
  | 'connect'
  | 'disconnect'
  | 'reconnect'

// 事件监听器
export type EventListener = (...args: any[]) => void

// 连接状态
export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting' | 'error'

// 组件状态
export interface WidgetState {
  isOpen: boolean
  isMinimized: boolean
  connectionStatus: ConnectionStatus
  currentChat?: Chat
  messages: Message[]
  isTyping: boolean
  unreadCount: number
}

// 错误类型
export class EmbedAIError extends Error {
  constructor(
    message: string,
    public code?: string,
    public details?: any
  ) {
    super(message)
    this.name = 'EmbedAIError'
  }
}

// 网络错误
export class NetworkError extends EmbedAIError {
  constructor(message: string, details?: any) {
    super(message, 'NETWORK_ERROR', details)
    this.name = 'NetworkError'
  }
}

// 认证错误
export class AuthError extends EmbedAIError {
  constructor(message: string, details?: any) {
    super(message, 'AUTH_ERROR', details)
    this.name = 'AuthError'
  }
}

// 配置错误
export class ConfigError extends EmbedAIError {
  constructor(message: string, details?: any) {
    super(message, 'CONFIG_ERROR', details)
    this.name = 'ConfigError'
  }
}
