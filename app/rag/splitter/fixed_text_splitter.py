"""固定文本分块器"""
from typing import List, Optional, Callable

from app.core.logger import Logger
from app.rag.splitter.text_splitter import TextSplitter

class FixedTextSplitter(TextSplitter):
    """固定文本分块器
    
    使用固定的分隔符和大小分割文本
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        fixed_separator: Optional[str] = None,
        length_function: Callable[[str], int] = len,
    ):
        """初始化固定文本分块器
        
        Args:
            chunk_size: 分块大小
            chunk_overlap: 分块重叠大小
            fixed_separator: 固定分隔符
            length_function: 计算文本长度的函数
        """
        super().__init__(chunk_size, chunk_overlap, length_function)
        self._fixed_separator = fixed_separator or "\n"
        
    def split_text(self, text: str) -> List[str]:
        """将文本分割为多个块
        
        Args:
            text: 要分割的文本
            
        Returns:
            List[str]: 分割后的文本块列表
        """
        # 使用固定分隔符分割文本
        splits = text.split(self._fixed_separator)
        
        # 过滤空字符串
        splits = [s for s in splits if s]
        
        # 合并分块
        chunks = []
        current_chunk = []
        current_length = 0
        
        for split in splits:
            split_length = self._length_function(split)
            
            # 如果单个分块超过chunk_size，记录警告并添加
            if split_length > self._chunk_size:
                Logger.warning(f"单个分块长度 {split_length} 超过了指定的分块大小 {self._chunk_size}")
                if current_chunk:
                    chunks.append(self._fixed_separator.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                chunks.append(split)
                continue
                
            # 检查添加当前分块是否会超过chunk_size
            if current_length + split_length + (len(self._fixed_separator) if current_chunk else 0) > self._chunk_size:
                # 如果有累积的分块，添加到结果列表
                if current_chunk:
                    chunks.append(self._fixed_separator.join(current_chunk))
                    
                    # 保留部分分块以实现重叠
                    overlap_length = 0
                    overlap_chunks = []
                    
                    for i in range(len(current_chunk) - 1, -1, -1):
                        chunk_length = self._length_function(current_chunk[i])
                        if overlap_length + chunk_length <= self._chunk_overlap:
                            overlap_chunks.insert(0, current_chunk[i])
                            overlap_length += chunk_length + (len(self._fixed_separator) if overlap_chunks else 0)
                        else:
                            break
                            
                    current_chunk = overlap_chunks
                    current_length = overlap_length
                    
            # 添加当前分块
            current_chunk.append(split)
            current_length += split_length + (len(self._fixed_separator) if len(current_chunk) > 1 else 0)
            
        # 处理剩余的分块
        if current_chunk:
            chunks.append(self._fixed_separator.join(current_chunk))
            
        return chunks