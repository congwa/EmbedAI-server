import { useState } from 'react'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { MobileHeader, MobilePageHeader } from '@/components/layout/mobile-header'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { ChatList } from './components/chat-list'
import { ChatDetail } from './components/chat-detail'
import { MobileChatList } from './components/mobile-chat-list'
import { MobileChatDetail } from './components/mobile-chat-detail'
import { Chat } from '@/services/types'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useIsMobile } from '@/hooks/use-media-query'

export default function Chats() {
  const [selectedChat, setSelectedChat] = useState<Chat | null>(null)
  const [activeTab, setActiveTab] = useState('active')
  const isMobile = useIsMobile()

  const handleChatSelect = (chat: Chat) => {
    setSelectedChat(chat)
  }

  const handleBackToList = () => {
    setSelectedChat(null)
  }

  // 移动端布局
  if (isMobile) {
    return (
      <>
        {selectedChat ? (
          <MobileChatDetail
            chat={selectedChat}
            onBack={handleBackToList}
          />
        ) : (
          <>
            <MobileHeader
              title="聊天管理"
              subtitle="管理和监控用户聊天对话"
            />
            
            <div className="flex-1 overflow-hidden">
              <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
                <div className="border-b bg-background px-4 py-2">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="active">活跃聊天</TabsTrigger>
                    <TabsTrigger value="deleted">已删除聊天</TabsTrigger>
                  </TabsList>
                </div>
                
                <TabsContent value="active" className="flex-1 overflow-hidden m-0 p-4">
                  <MobileChatList onChatSelect={handleChatSelect} />
                </TabsContent>
                
                <TabsContent value="deleted" className="flex-1 overflow-hidden m-0 p-4">
                  <MobileChatList onChatSelect={handleChatSelect} showDeleted={true} />
                </TabsContent>
              </Tabs>
            </div>
          </>
        )}
      </>
    )
  }

  // 桌面端布局
  return (
    <>
      {/* ===== Top Heading ===== */}
      <Header>
        <Search />
        <div className='ml-auto flex items-center space-x-4'>
          <ThemeSwitch />
          <ProfileDropdown />
        </div>
      </Header>

      <Main>
        <div className="h-full flex flex-col">
          {!selectedChat ? (
            // 聊天列表视图
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold tracking-tight">聊天管理</h2>
                <p className="text-muted-foreground">
                  管理和监控用户与知识库的聊天对话
                </p>
              </div>

              <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
                <TabsList>
                  <TabsTrigger value="active">活跃聊天</TabsTrigger>
                  <TabsTrigger value="deleted">已删除聊天</TabsTrigger>
                </TabsList>
                
                <TabsContent value="active" className="space-y-4">
                  <ChatList onChatSelect={handleChatSelect} />
                </TabsContent>
                
                <TabsContent value="deleted" className="space-y-4">
                  <ChatList onChatSelect={handleChatSelect} showDeleted={true} />
                </TabsContent>
              </Tabs>
            </div>
          ) : (
            // 聊天详情视图
            <div className="flex-1 flex flex-col min-h-0">
              <ChatDetail
                chat={selectedChat}
                onBack={handleBackToList}
                className="flex-1"
              />
            </div>
          )}
        </div>
      </Main>
    </>
  )
}
