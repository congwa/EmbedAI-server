import { useCallback, useRef } from 'react'
import { toast } from '@/hooks/use-toast'

interface WebSocketConnection {
  id: string
  websocket: WebSocket
  reconnectAttempts: number
  maxReconnectAttempts: number
  autoReconnect: boolean
}

interface WebSocketManagerOptions {
  maxConnections?: number
  defaultMaxReconnectAttempts?: number
  defaultAutoReconnect?: boolean
}

/**
 * WebSocket连接管理器
 * 用于管理多个WebSocket连接，提供连接池和重连机制
 */
export function useWebSocketManager(options: WebSocketManagerOptions = {}) {
  const {
    maxConnections = 10,
    defaultMaxReconnectAttempts = 5,
    defaultAutoReconnect = true,
  } = options

  const connectionsRef = useRef<Map<string, WebSocketConnection>>(new Map())

  // 获取重连延迟（指数退避）
  const getReconnectDelay = useCallback((attempt: number): number => {
    return Math.min(1000 * Math.pow(2, attempt), 30000) // 最大30秒
  }, [])

  // 创建WebSocket连接
  const createConnection = useCallback(
    (
      id: string,
      url: string,
      options: {
        onOpen?: (event: Event) => void
        onMessage?: (event: MessageEvent) => void
        onError?: (event: Event) => void
        onClose?: (event: CloseEvent) => void
        autoReconnect?: boolean
        maxReconnectAttempts?: number
      } = {}
    ): WebSocket | null => {
      // 检查连接数限制
      if (connectionsRef.current.size >= maxConnections) {
        toast({
          title: '连接数超限',
          description: `最多只能同时维持${maxConnections}个WebSocket连接`,
          variant: 'destructive',
        })
        return null
      }

      // 如果连接已存在，先关闭旧连接
      const existingConnection = connectionsRef.current.get(id)
      if (existingConnection) {
        existingConnection.websocket.close()
        connectionsRef.current.delete(id)
      }

      try {
        const ws = new WebSocket(url)
        const connection: WebSocketConnection = {
          id,
          websocket: ws,
          reconnectAttempts: 0,
          maxReconnectAttempts: options.maxReconnectAttempts ?? defaultMaxReconnectAttempts,
          autoReconnect: options.autoReconnect ?? defaultAutoReconnect,
        }

        ws.onopen = (event) => {
          connection.reconnectAttempts = 0
          options.onOpen?.(event)
        }

        ws.onmessage = options.onMessage

        ws.onerror = (event) => {
          options.onError?.(event)
        }

        ws.onclose = (event) => {
          connectionsRef.current.delete(id)
          options.onClose?.(event)

          // 自动重连逻辑
          if (
            event.code !== 1000 &&
            connection.autoReconnect &&
            connection.reconnectAttempts < connection.maxReconnectAttempts
          ) {
            const delay = getReconnectDelay(connection.reconnectAttempts)
            connection.reconnectAttempts++

            setTimeout(() => {
              createConnection(id, url, options)
            }, delay)
          }
        }

        connectionsRef.current.set(id, connection)
        return ws
      } catch (error) {
        // eslint-disable-next-line no-console
        console.error('Failed to create WebSocket connection:', error)
        toast({
          title: 'WebSocket连接失败',
          description: '无法创建WebSocket连接，请检查网络状态',
          variant: 'destructive',
        })
        return null
      }
    },
    [maxConnections, defaultMaxReconnectAttempts, defaultAutoReconnect, getReconnectDelay]
  )

  // 获取连接
  const getConnection = useCallback((id: string): WebSocket | null => {
    const connection = connectionsRef.current.get(id)
    return connection?.websocket ?? null
  }, [])

  // 关闭连接
  const closeConnection = useCallback((id: string, code = 1000, reason = 'Manual close') => {
    const connection = connectionsRef.current.get(id)
    if (connection) {
      connection.websocket.close(code, reason)
      connectionsRef.current.delete(id)
    }
  }, [])

  // 关闭所有连接
  const closeAllConnections = useCallback(() => {
    connectionsRef.current.forEach((connection) => {
      connection.websocket.close(1000, 'Manager cleanup')
    })
    connectionsRef.current.clear()
  }, [])

  // 获取连接状态
  const getConnectionState = useCallback((id: string) => {
    const connection = connectionsRef.current.get(id)
    if (!connection) return null

    return {
      id,
      readyState: connection.websocket.readyState,
      reconnectAttempts: connection.reconnectAttempts,
      maxReconnectAttempts: connection.maxReconnectAttempts,
      autoReconnect: connection.autoReconnect,
    }
  }, [])

  // 获取所有连接状态
  const getAllConnectionStates = useCallback(() => {
    const states: Array<{
      id: string
      readyState: number
      reconnectAttempts: number
      maxReconnectAttempts: number
      autoReconnect: boolean
    }> = []

    connectionsRef.current.forEach((connection) => {
      states.push({
        id: connection.id,
        readyState: connection.websocket.readyState,
        reconnectAttempts: connection.reconnectAttempts,
        maxReconnectAttempts: connection.maxReconnectAttempts,
        autoReconnect: connection.autoReconnect,
      })
    })

    return states
  }, [])

  // 发送消息
  const sendMessage = useCallback((id: string, data: string | object) => {
    const connection = connectionsRef.current.get(id)
    if (!connection) {
      throw new Error(`WebSocket connection '${id}' not found`)
    }

    if (connection.websocket.readyState !== WebSocket.OPEN) {
      throw new Error(`WebSocket connection '${id}' is not open`)
    }

    const message = typeof data === 'string' ? data : JSON.stringify(data)
    connection.websocket.send(message)
  }, [])

  return {
    createConnection,
    getConnection,
    closeConnection,
    closeAllConnections,
    getConnectionState,
    getAllConnectionStates,
    sendMessage,
    connectionCount: connectionsRef.current.size,
  }
}