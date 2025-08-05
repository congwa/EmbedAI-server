import { MoreHorizontal, Pencil, Trash, UserPlus, FileText } from 'lucide-react'
import { KnowledgeBaseDetail, PermissionType } from '@/services/types'
import { Link } from '@tanstack/react-router'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'

interface KnowledgeBaseTableProps {
  data: KnowledgeBaseDetail[]
  onEdit: (kb: KnowledgeBaseDetail) => void
  onDelete: (kb: KnowledgeBaseDetail) => void
  onManageUsers: (kb: KnowledgeBaseDetail) => void
}

export function KnowledgeBaseTable({
  data,
  onEdit,
  onDelete,
  onManageUsers,
}: KnowledgeBaseTableProps) {
  const getPermissionColor = (permission: PermissionType): "default" | "secondary" | "destructive" | "outline" | "success" | "warning" => {
    switch (permission) {
      case PermissionType.OWNER:
        return 'success'
      case PermissionType.ADMIN:
        return 'warning'
      case PermissionType.EDITOR:
        return 'default'
      case PermissionType.VIEWER:
        return 'secondary'
      default:
        return 'default'
    }
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>ID</TableHead>
          <TableHead>名称</TableHead>
          <TableHead>创建者</TableHead>
          <TableHead>创建时间</TableHead>
          <TableHead>更新时间</TableHead>
          <TableHead className="text-right">操作</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.length === 0 ? (
          <TableRow>
            <TableCell colSpan={7} className="h-24 text-center">
              <div className="flex flex-col items-center justify-center text-sm text-muted-foreground">
                <p>暂无知识库数据</p>
                <p>点击右上角"创建知识库"按钮开始创建</p>
              </div>
            </TableCell>
          </TableRow>
        ) : (
          data.map((kb) => (
            <TableRow key={kb.id}>
              <TableCell>{kb.id}</TableCell>
              <TableCell>
                <Link
                  to="/knowledge-bases/$id/documents"
                  params={{ id: String(kb.id) }}
                  className="hover:underline"
                >
                  {kb.name}
                </Link>
              </TableCell>
             
              <TableCell>
                <div className="flex items-center gap-2">
                  {kb.owner_email}
                  <Badge variant={getPermissionColor(PermissionType.OWNER)}>
                    所有者
                  </Badge>
                </div>
              </TableCell>
              <TableCell>{new Date(kb.created_at).toLocaleString()}</TableCell>
              <TableCell>{new Date(kb.updated_at).toLocaleString()}</TableCell>
              <TableCell className="text-right">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" className="h-8 w-8 p-0">
                      <span className="sr-only">打开菜单</span>
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => onEdit(kb)}>
                      <Pencil className="mr-2 h-4 w-4" />
                      编辑
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => onManageUsers(kb)}>
                      <UserPlus className="mr-2 h-4 w-4" />
                      管理成员
                    </DropdownMenuItem>
                    <Link
                      to="/knowledge-bases/$id/documents"
                      params={{ id: String(kb.id) }}
                    >
                      <DropdownMenuItem>
                        <FileText className="mr-2 h-4 w-4" />
                        文档管理
                      </DropdownMenuItem>
                    </Link>
                    <DropdownMenuItem
                      className="text-red-600"
                      onClick={() => onDelete(kb)}
                    >
                      <Trash className="mr-2 h-4 w-4" />
                      删除
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
  )
} 