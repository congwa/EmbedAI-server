// API响应的基础接口
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export interface ApiResponse<T = any> {
  success: boolean;
  code: number;
  message: string;
  data: T;
}

// API错误响应的接口
export interface ApiErrorResponse {
  success: boolean;
  code: number;
  message: string;
  data: {
    error_type: string;
    path: string;
  };
}

// 分页数据结构
export interface PaginationInfo {
  total: number;
  page: number;
  page_size: number;
}

// 分页响应数据结构
export interface PaginationData<T> {
  items: T[];
  pagination: PaginationInfo;
}

// 管理员注册请求参数
export interface AdminRegisterRequest {
  email: string;
  password: string;
  register_code: string;
}

// 管理员登录请求参数
export interface AdminLoginRequest {
  email: string;
  password: string;
}

// 用户基础信息
export interface User {
  id: number;
  email: string;
  is_admin: boolean;
  is_active: boolean;
  sdk_key: string;
  secret_key: string;
  created_by_id: number;
  created_at: string;
}

// 登录响应数据
export interface LoginResponse {
  access_token: string;
  user: {
    id: number;
    email: string;
    is_admin: boolean;
    created_at: string;
  };
}

// 创建用户请求参数
export interface CreateUserRequest {
  email: string;
  password: string;
  is_admin?: boolean;
  is_active?: boolean;
}

// 知识库相关接口
export interface KnowledgeBase {
  id: number;
  name: string;
  domain: string;
  status: KnowledgeBaseStatus;
  example_queries: string[];
  entity_types: string[];
  owner_id: number;
  created_at: string;
  updated_at: string;
  llm_config?: KnowledgeBaseLLMConfig;
}

// 知识库状态枚举
export enum KnowledgeBaseStatus {
  INIT = "init",
  TRAINING = "training",
  READY = "ready",
  ERROR = "error"
}

// 知识库权限类型
export enum PermissionType {
  OWNER = "owner",
  ADMIN = "admin",
  EDITOR = "editor",
  VIEWER = "viewer"
}

// 知识库用户权限
export interface KnowledgeBaseUser {
  user_id: number;
  email: string;
  permission: PermissionType;
  created_at: string;
}

// 知识库详情
export interface KnowledgeBaseDetail extends KnowledgeBase {
  owner_email: string;
  users: KnowledgeBaseUser[];
}

// LLM配置接口
export interface LLMConfig {
  model: string;                 // LLM模型名称
  base_url: string;             // API基础URL
  api_key: string;              // API密钥
}

// Embeddings配置接口
export interface EmbeddingsConfig {
  model: string;                 // Embedding模型名称
  base_url: string;             // API基础URL
  api_key: string;              // API密钥
  embedding_dim: number;         // Embedding维度
}

// 完整的LLM配置接口
export interface KnowledgeBaseLLMConfig {
  llm: LLMConfig;               // LLM配置
  embeddings: EmbeddingsConfig; // Embeddings配置
}

// 知识库创建请求
export interface CreateKnowledgeBaseRequest {
  name: string;                           // 必填：知识库名称
  domain: string;                        // 可选：知识库领域，默认为"通用知识领域"
  example_queries?: string[];             // 可选：示例查询列表
  entity_types?: string[];               // 可选：实体类型列表
  llm_config?: KnowledgeBaseLLMConfig;   // 可选：LLM配置
}

// 知识库更新请求
export interface UpdateKnowledgeBaseRequest {
  name: string;                          // 必填：知识库名称
  domain: string;                        // 必填：知识库名称
  example_queries?: string[];             // 可选：示例查询列表
  entity_types?: string[];               // 可选：实体类型列表
  llm_config?: KnowledgeBaseLLMConfig;   // 可选：LLM配置
}

// 知识库权限创建请求
export interface KnowledgeBasePermissionCreate {
  user_id: number;
  permission: PermissionType;
}

// 知识库权限更新请求
export interface KnowledgeBasePermissionUpdate {
  permission: PermissionType;
}

// 知识库成员信息
export interface KnowledgeBaseMember {
  id: number;
  email: string;
  permission: PermissionType;
  is_owner: boolean;
  is_admin: boolean;
  created_at: string;
}

// 知识库成员列表响应
export interface KnowledgeBaseMemberList {
  members: KnowledgeBaseMember[];
  total: number;
}

// 获取知识库列表的查询参数
export interface GetKnowledgeBasesQuery {
  page?: number;
  page_size?: number;
  name?: string;
}

// 文档类型枚举
export enum DocumentType {
  TEXT = 'text',
  WEBPAGE = 'webpage',
  PDF = 'pdf',
}

// 文档基础信息
export interface Document {
  id: number;
  title: string;
  content: string;
  doc_type: DocumentType;
  knowledge_base_id: number;
  created_at: string;
  updated_at: string;
  created_by_id: number;
  is_deleted: boolean;
  word_count: number;
  chunk_count: number;
  metadata?: Record<string, unknown>;
  source_url?: string;
}

// 创建文档请求参数
export interface CreateDocumentRequest {
  title: string;
  content: string;
  doc_type: DocumentType;
  metadata?: Record<string, unknown>;
}

// 更新文档请求参数
export interface UpdateDocumentRequest {
  title?: string;
  content?: string;
  doc_type?: DocumentType;
  metadata?: Record<string, unknown>;
}

// 获取文档列表的查询参数
export interface GetDocumentsQuery {
  knowledge_base_id: number;
  skip?: number;
  limit?: number;
  title?: string;
  doc_type?: DocumentType;
  start_time?: string;
  end_time?: string;
}

// 文档分页响应
export interface DocumentPagination {
  total: number;
  page: number;
  page_size: number;
  items: Document[];
}

// 用户列表分页响应
export interface GetUsersResponse {
  items: User[];
  total: number;
  page: number;
  page_size: number;
}

// 修改密码请求参数
export interface UpdatePasswordRequest {
  old_password: string;
  new_password: string;
}

// 管理员修改用户密码请求参数
export interface AdminChangeUserPasswordRequest {
  new_password: string;
}

// 知识库查询请求
export interface KnowledgeBaseQueryRequest {
  query: string;                          // 必填：查询文本
  stream?: boolean;                       // 可选：是否使用流式响应
  temperature?: number;                   // 可选：温度参数，控制响应的随机性
  top_k?: number;                        // 可选：返回的相关文档数量
  similarity_threshold?: number;          // 可选：相似度阈值
}

// 知识库查询响应
export interface KnowledgeBaseQueryResponse {
  answer: string;                         // 回答内容
  sources: Array<{                        // 引用来源
    document_id: number;                  // 文档ID
    document_name: string;                // 文档名称
    content: string;                      // 相关内容片段
    similarity: number;                   // 相似度分数
  }>;
  tokens_used?: {                         // 可选：token使用统计
    prompt_tokens: number;                // 提示词token数
    completion_tokens: number;            // 完成词token数
    total_tokens: number;                 // 总token数
  };
  metadata?: Record<string, unknown>;     // 可选：其他元数据
}

// 知识库训练响应
export interface KnowledgeBaseTrainResponse {
  status: KnowledgeBaseStatus;            // 知识库状态
  message: string;                        // 状态描述信息
  total_documents?: number;               // 可选：总文档数
  processed_documents?: number;           // 可选：已处理文档数
  error_documents?: number;               // 可选：处理失败文档数
  estimated_time_remaining?: number;      // 可选：预估剩余时间（秒）
}

// 文档上传进度跟踪
export interface DocumentUploadProgress {
  documentId?: number;
  filename: string;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
}

// 文档过滤参数
export interface DocumentFilter {
  knowledge_base_id?: number;
  title?: string;
  doc_type?: DocumentType;
  start_time?: string;
  end_time?: string;
  created_by_id?: number;
}

// 聊天相关接口

// 聊天状态枚举
export enum ChatStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  ARCHIVED = 'archived'
}

// 消息发送者类型
export enum MessageSenderType {
  USER = 'user',
  ADMIN = 'admin',
  SYSTEM = 'system'
}

// 消息类型
export enum MessageType {
  TEXT = 'text',
  FILE = 'file',
  SYSTEM = 'system'
}

// 聊天会话基础信息 (基于实际API响应)
export interface Chat {
  id: number; // 实际API使用数字ID
  third_party_user_id: number; // 实际API字段名
  kb_id: number; // 实际API字段名
  title?: string; // 聊天标题
  status: ChatStatus;
  created_at: string;
  updated_at: string;
  last_message_at?: string;
  message_count?: number;
  is_active: boolean;
  user_email?: string; // 可能需要从其他地方获取
  knowledge_base_name?: string; // 可能需要从其他地方获取
}

// 聊天消息 (基于实际API响应)
export interface ChatMessage {
  id: number;
  chat_id: number;
  sender_type: 'official' | 'third_party'; // 实际API使用的类型
  sender_id: number;
  content: string;
  message_type: string; // 实际API使用字符串而不是枚举
  created_at: string;
  metadata: Record<string, unknown>;
  sender_email?: string; // 这个可能需要从其他地方获取
}

// 创建聊天消息请求 (基于实际API)
export interface ChatMessageCreate {
  content: string;
  message_type?: string; // 实际API使用字符串，且为可选
  metadata?: Record<string, unknown>;
}

// 获取聊天列表查询参数 (基于实际API)
export interface GetChatsQuery {
  skip?: number;
  limit?: number;
  include_inactive?: boolean;
  all_chats?: boolean;
  user_id?: number; // 实际API使用数字ID
  knowledge_base_id?: number;
  status?: ChatStatus;
}

// 聊天统计信息
export interface ChatStats {
  total_chats: number;
  active_chats: number;
  total_messages: number;
  avg_messages_per_chat: number;
  last_activity: string;
}

// WebSocket 消息基础接口 (基于实际协议 V2)
export interface WebSocketMessage {
  type: string; // 格式为 "domain.action"
  payload: unknown;
  request_id?: string;
}

// 客户端到服务器消息类型
export interface MessageCreateRequest extends WebSocketMessage {
  type: 'message.create';
  payload: {
    content: string;
    message_type?: string;
    metadata?: Record<string, unknown>;
  };
}

export interface HistoryRequest extends WebSocketMessage {
  type: 'history.request';
  payload: {
    before_message_id?: number;
    limit?: number;
  };
}

export interface TypingStartRequest extends WebSocketMessage {
  type: 'typing.start';
  payload: {
    is_typing: boolean;
  };
}

export interface TypingStopRequest extends WebSocketMessage {
  type: 'typing.stop';
  payload: {
    is_typing: boolean;
  };
}

export interface MessageReadRequest extends WebSocketMessage {
  type: 'message.read';
  payload: {
    message_ids: number[];
  };
}

export interface MembersRequest extends WebSocketMessage {
  type: 'members.request';
  payload: Record<string, never>; // 空对象
}

// 服务器到客户端消息类型
export interface MessageNewEvent extends WebSocketMessage {
  type: 'message.new';
  payload: {
    message: {
      id: number;
      chat_id: number;
      content: string;
      message_type: string;
      sender_id: number;
      sender_type: 'official' | 'third_party';
      created_at: string;
      metadata: Record<string, unknown>;
    };
  };
}

export interface HistoryResponse extends WebSocketMessage {
  type: 'history.response';
  payload: {
    messages: Array<{
      id: number;
      chat_id: number;
      content: string;
      message_type: string;
      sender_id: number;
      sender_type: 'official' | 'third_party';
      created_at: string;
      metadata: Record<string, unknown>;
    }>;
  };
}

export interface TypingUpdateEvent extends WebSocketMessage {
  type: 'typing.update';
  payload: {
    sender: {
      user_id: number;
      client_id: string;
      user_type: 'official' | 'third_party';
    };
    is_typing: boolean;
  };
}

export interface MessageReadUpdateEvent extends WebSocketMessage {
  type: 'message.read.update';
  payload: {
    sender: {
      user_id: number;
      client_id: string;
      user_type: 'official' | 'third_party';
    };
    message_ids: number[];
  };
}

export interface SystemNotificationEvent extends WebSocketMessage {
  type: 'notification.system';
  payload: {
    level: 'info' | 'warning' | 'error';
    content: string;
  };
}

export interface ErrorResponse extends WebSocketMessage {
  type: 'response.error';
  payload: {
    code: string;
    message: string;
  };
}

export interface MembersResponse extends WebSocketMessage {
  type: 'members.response';
  payload: {
    members: string[];
    count: number;
  };
}

// 分析报告相关类型

// 仪表板数据
export interface DashboardData {
  overview: {
    total_users: number
    active_users: number
    total_knowledge_bases: number
    total_documents: number
    total_queries: number
    system_uptime: number
  }
  recent_activities: Array<{
    user_id: number
    user_email: string
    activity_type: string
    activity_details: Record<string, any>
    timestamp: string
  }>
  top_knowledge_bases: Array<{
    id: number
    name: string
    domain: string
    document_count: number
    query_count: number
    last_updated: string
  }>
  performance_trends: {
    dates: string[]
    response_times: number[]
    query_counts: number[]
    error_rates: number[]
  }
  cost_summary: {
    current_month: {
      total_cost: number
      llm_cost: number
      storage_cost: number
      api_cost: number
    }
    previous_month: {
      total_cost: number
      growth_rate: number
    }
  }
}

// 系统概览
export interface SystemOverview {
  period: string
  total_users: number
  new_users: number
  active_users: number
  total_knowledge_bases: number
  new_knowledge_bases: number
  total_documents: number
  new_documents: number
  total_queries: number
  successful_queries: number
  failed_queries: number
  average_response_time: number
  system_uptime: number
  storage_used: string
  bandwidth_used: string
}

// 用户活动统计查询参数
export interface UserActivityStatsQuery {
  start_date?: string
  end_date?: string
  user_id?: number
  activity_type?: string
  limit?: number
}

// 用户活动统计
export interface UserActivityStats {
  period: {
    start_date: string
    end_date: string
  }
  summary: {
    total_activities: number
    unique_users: number
    most_active_user: {
      user_id: number
      email: string
      activity_count: number
    }
  }
  activity_breakdown: Record<string, number>
  daily_trends: Array<{
    date: string
    total_activities: number
    unique_users: number
  }>
  recent_activities: Array<{
    id: number
    user_id: number
    user_email: string
    activity_type: string
    activity_details: Record<string, any>
    ip_address: string
    user_agent: string
    timestamp: string
    duration: number
  }>
}

// 知识库统计查询参数
export interface KnowledgeBaseStatsQuery {
  period?: string
  sort_by?: string
  limit?: number
}

// 知识库统计
export interface KnowledgeBaseStats {
  period: string
  summary: {
    total_knowledge_bases: number
    active_knowledge_bases: number
    total_documents: number
    total_queries: number
    average_accuracy: number
  }
  top_knowledge_bases: Array<{
    id: number
    name: string
    domain: string
    document_count: number
    total_size: string
    query_count: number
    successful_queries: number
    failed_queries: number
    accuracy_rate: number
    average_response_time: number
    last_updated: string
    created_at: string
  }>
  usage_trends: {
    dates: string[]
    query_counts: number[]
    accuracy_rates: number[]
  }
}

// 性能指标查询参数
export interface PerformanceMetricsQuery {
  start_date?: string
  end_date?: string
  metric_type?: string
  granularity?: string
}

// 性能指标
export interface PerformanceMetrics {
  period: {
    start_date: string
    end_date: string
    granularity: string
  }
  summary: {
    average_response_time: number
    max_response_time: number
    min_response_time: number
    total_requests: number
    successful_requests: number
    error_rate: number
    uptime_percentage: number
  }
  metrics: Array<{
    timestamp: string
    response_time: number
    request_count: number
    error_count: number
    cpu_usage: number
    memory_usage: number
    disk_usage: number
  }>
  alerts: Array<{
    timestamp: string
    type: string
    value: number
    threshold: number
    severity: string
  }>
}

// 成本分析查询参数
export interface CostAnalysisQuery {
  start_date?: string
  end_date?: string
  breakdown?: string
}

// 成本分析
export interface CostAnalysis {
  period: {
    start_date: string
    end_date: string
  }
  total_cost: number
  cost_breakdown: {
    llm_api: {
      cost: number
      percentage: number
      requests: number
      cost_per_request: number
    }
    storage: {
      cost: number
      percentage: number
      storage_gb: number
      cost_per_gb: number
    }
    compute: {
      cost: number
      percentage: number
      hours: number
      cost_per_hour: number
    }
    bandwidth: {
      cost: number
      percentage: number
      gb_transferred: number
      cost_per_gb: number
    }
  }
  daily_costs: Array<{
    date: string
    total_cost: number
    llm_cost: number
    storage_cost: number
    compute_cost: number
    bandwidth_cost: number
  }>
  projections: {
    monthly_estimate: number
    yearly_estimate: number
    growth_rate: number
  }
}

// 导出分析数据请求
export interface ExportAnalyticsRequest {
  data_type: 'user_activity' | 'knowledge_bases' | 'performance' | 'cost'
  format?: 'csv' | 'excel'
  start_date?: string
  end_date?: string
  filters?: Record<string, any>
}

// 系统健康监控相关类型

// 系统健康状态
export interface SystemHealth {
  status: 'healthy' | 'warning' | 'critical'
  timestamp: string
  uptime: number
  version: string
  services: {
    database: ServiceHealthStatus
    redis: ServiceHealthStatus
    storage: ServiceHealthStatus
    llm_api: ServiceHealthStatus
  }
  system_info: {
    cpu_usage: number
    memory_usage: number
    disk_usage: number
    network_io: {
      bytes_sent: number
      bytes_received: number
    }
  }
  recent_errors: Array<{
    timestamp: string
    level: string
    message: string
    source: string
  }>
}

// 服务健康状态
export interface ServiceHealthStatus {
  status: 'healthy' | 'warning' | 'critical' | 'unknown'
  response_time: number
  last_check: string
  error_message?: string
}

// 系统指标查询参数
export interface SystemMetricsQuery {
  start_time?: string
  end_time?: string
  granularity?: 'minute' | 'hour' | 'day'
  metrics?: string[]
}

// 系统指标
export interface SystemMetrics {
  period: {
    start_time: string
    end_time: string
    granularity: string
  }
  metrics: Array<{
    timestamp: string
    cpu_usage: number
    memory_usage: number
    disk_usage: number
    network_io: {
      bytes_sent: number
      bytes_received: number
    }
    active_connections: number
    request_count: number
    response_time: number
    error_count: number
  }>
  summary: {
    avg_cpu_usage: number
    max_cpu_usage: number
    avg_memory_usage: number
    max_memory_usage: number
    avg_response_time: number
    max_response_time: number
    total_requests: number
    total_errors: number
    error_rate: number
  }
}

// 服务状态
export interface ServiceStatus {
  name: string
  status: 'running' | 'stopped' | 'error' | 'unknown'
  version: string
  uptime: number
  health_check_url?: string
  last_health_check: string
  response_time: number
  error_message?: string
  dependencies: Array<{
    name: string
    status: 'healthy' | 'unhealthy'
    response_time: number
  }>
  metrics: {
    cpu_usage: number
    memory_usage: number
    request_count: number
    error_count: number
  }
}

// 性能监控查询参数
export interface PerformanceMonitoringQuery {
  start_time?: string
  end_time?: string
  service?: string
  metric_type?: string
}

// 性能监控数据
export interface PerformanceMonitoring {
  period: {
    start_time: string
    end_time: string
  }
  services: Array<{
    name: string
    status: 'healthy' | 'warning' | 'critical'
    metrics: {
      response_time: {
        current: number
        average: number
        p95: number
        p99: number
      }
      throughput: {
        requests_per_second: number
        peak_rps: number
      }
      error_rate: {
        current: number
        average: number
      }
      resource_usage: {
        cpu: number
        memory: number
        disk: number
      }
    }
    alerts: Array<{
      type: string
      severity: 'low' | 'medium' | 'high' | 'critical'
      message: string
      timestamp: string
    }>
  }>
  trends: {
    timestamps: string[]
    response_times: number[]
    throughput: number[]
    error_rates: number[]
    cpu_usage: number[]
    memory_usage: number[]
  }
}

// 告警查询参数
export interface AlertsQuery {
  page?: number
  page_size?: number
  status?: 'active' | 'resolved' | 'acknowledged'
  severity?: 'low' | 'medium' | 'high' | 'critical'
  service?: string
  start_time?: string
  end_time?: string
}

// 告警
export interface Alert {
  id: number
  name: string
  description: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  status: 'active' | 'resolved' | 'acknowledged'
  service: string
  metric: string
  condition: string
  threshold: number
  current_value: number
  triggered_at: string
  resolved_at?: string
  acknowledged_at?: string
  acknowledged_by?: string
  rule_id: number
  tags: string[]
  metadata: Record<string, any>
}

// 创建告警请求
export interface CreateAlertRequest {
  name: string
  description: string
  service: string
  metric: string
  condition: 'greater_than' | 'less_than' | 'equals' | 'not_equals'
  threshold: number
  severity: 'low' | 'medium' | 'high' | 'critical'
  enabled: boolean
  tags?: string[]
  notification_channels?: string[]
}

// 更新告警请求
export interface UpdateAlertRequest {
  name?: string
  description?: string
  condition?: 'greater_than' | 'less_than' | 'equals' | 'not_equals'
  threshold?: number
  severity?: 'low' | 'medium' | 'high' | 'critical'
  enabled?: boolean
  tags?: string[]
  notification_channels?: string[]
}

// 告警阈值配置
export interface AlertThresholds {
  cpu_usage: {
    warning: number
    critical: number
  }
  memory_usage: {
    warning: number
    critical: number
  }
  disk_usage: {
    warning: number
    critical: number
  }
  response_time: {
    warning: number
    critical: number
  }
  error_rate: {
    warning: number
    critical: number
  }
  uptime: {
    warning: number
    critical: number
  }
}

// 更新告警阈值请求
export interface UpdateAlertThresholdsRequest {
  cpu_usage?: {
    warning: number
    critical: number
  }
  memory_usage?: {
    warning: number
    critical: number
  }
  disk_usage?: {
    warning: number
    critical: number
  }
  response_time?: {
    warning: number
    critical: number
  }
  error_rate?: {
    warning: number
    critical: number
  }
  uptime?: {
    warning: number
    critical: number
  }
}

// 运行时间查询参数
export interface UptimeQuery {
  start_date?: string
  end_date?: string
  service?: string
}

// 运行时间记录
export interface UptimeRecord {
  date: string
  service: string
  uptime_percentage: number
  total_downtime_minutes: number
  incidents: Array<{
    start_time: string
    end_time: string
    duration_minutes: number
    reason: string
    severity: string
  }>
}

// 安全管理相关类型

// IP列表查询参数
export interface IpListQuery {
  page?: number
  page_size?: number
  ip_address?: string
  status?: 'active' | 'inactive'
  created_by?: number
}

// IP白名单条目
export interface IpWhitelistEntry {
  id: number
  ip_address: string
  description: string
  status: 'active' | 'inactive'
  created_by: number
  created_by_email: string
  created_at: string
  updated_at: string
  last_accessed?: string
  access_count: number
}

// 创建IP白名单请求
export interface CreateIpWhitelistRequest {
  ip_address: string
  description: string
  status?: 'active' | 'inactive'
}

// 更新IP白名单请求
export interface UpdateIpWhitelistRequest {
  ip_address?: string
  description?: string
  status?: 'active' | 'inactive'
}

// IP黑名单条目
export interface IpBlacklistEntry {
  id: number
  ip_address: string
  reason: string
  status: 'active' | 'inactive'
  blocked_at: string
  blocked_by: number
  blocked_by_email: string
  created_at: string
  updated_at: string
  block_count: number
  last_blocked?: string
}

// 创建IP黑名单请求
export interface CreateIpBlacklistRequest {
  ip_address: string
  reason: string
  status?: 'active' | 'inactive'
}

// 更新IP黑名单请求
export interface UpdateIpBlacklistRequest {
  ip_address?: string
  reason?: string
  status?: 'active' | 'inactive'
}

// 安全事件查询参数
export interface SecurityEventsQuery {
  page?: number
  page_size?: number
  event_type?: string
  severity?: 'low' | 'medium' | 'high' | 'critical'
  start_time?: string
  end_time?: string
  user_id?: number
  ip_address?: string
}

// 安全事件
export interface SecurityEvent {
  id: number
  event_type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  description: string
  user_id?: number
  user_email?: string
  ip_address: string
  user_agent: string
  location?: {
    country: string
    city: string
    latitude: number
    longitude: number
  }
  metadata: Record<string, any>
  timestamp: string
  resolved: boolean
  resolved_at?: string
  resolved_by?: number
  resolved_by_email?: string
}

// 双因子认证设置
export interface TwoFactorAuthSettings {
  enabled: boolean
  method: 'totp' | 'sms' | 'email'
  backup_codes_count: number
  last_used?: string
  setup_at?: string
}

// 启用双因子认证请求
export interface Enable2FARequest {
  method: 'totp' | 'sms' | 'email'
  phone_number?: string
  email?: string
}

// 双因子认证响应
export interface TwoFactorAuthResponse {
  secret: string
  qr_code: string
  backup_codes: string[]
}

// 禁用双因子认证请求
export interface Disable2FARequest {
  password: string
  verification_code: string
}

// 验证双因子认证请求
export interface Verify2FARequest {
  verification_code: string
}

// 密码策略
export interface PasswordPolicy {
  min_length: number
  require_uppercase: boolean
  require_lowercase: boolean
  require_numbers: boolean
  require_special_chars: boolean
  max_age_days: number
  history_count: number
  lockout_attempts: number
  lockout_duration_minutes: number
  complexity_score: number
}

// 更新密码策略请求
export interface UpdatePasswordPolicyRequest {
  min_length?: number
  require_uppercase?: boolean
  require_lowercase?: boolean
  require_numbers?: boolean
  require_special_chars?: boolean
  max_age_days?: number
  history_count?: number
  lockout_attempts?: number
  lockout_duration_minutes?: number
  complexity_score?: number
}

// 设备指纹查询参数
export interface DeviceFingerprintsQuery {
  page?: number
  page_size?: number
  user_id?: number
  device_type?: string
  status?: 'trusted' | 'suspicious' | 'blocked'
}

// 设备指纹
export interface DeviceFingerprint {
  id: number
  user_id: number
  user_email: string
  device_id: string
  device_type: string
  browser: string
  os: string
  screen_resolution: string
  timezone: string
  language: string
  ip_address: string
  location?: {
    country: string
    city: string
  }
  status: 'trusted' | 'suspicious' | 'blocked'
  first_seen: string
  last_seen: string
  access_count: number
  risk_score: number
}

// 安全审计查询参数
export interface SecurityAuditQuery {
  start_date?: string
  end_date?: string
  audit_type?: string
}

// 安全审计报告
export interface SecurityAuditReport {
  period: {
    start_date: string
    end_date: string
  }
  summary: {
    total_events: number
    high_risk_events: number
    blocked_attempts: number
    successful_logins: number
    failed_logins: number
    unique_ips: number
    new_devices: number
  }
  risk_analysis: {
    overall_risk_level: 'low' | 'medium' | 'high' | 'critical'
    risk_factors: Array<{
      factor: string
      score: number
      description: string
    }>
    recommendations: string[]
  }
  event_breakdown: Record<string, number>
  geographic_distribution: Array<{
    country: string
    event_count: number
    risk_level: string
  }>
  time_series: {
    timestamps: string[]
    event_counts: number[]
    risk_scores: number[]
  }
  top_threats: Array<{
    threat_type: string
    count: number
    severity: string
    description: string
  }>
}