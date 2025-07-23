"""递归字符文本分块器"""
import re
from typing import List, Any, Dict, Optional, Callable

from app.core.logger import Logger
from app.rag.splitter.text_splitter import TextSplitter

def _split_text_with_regex(text: str, separator: str, keep_separator: bool) -> List[str]:
    """使用正则表达式分割文本
    
    Args:
        text: 要分割的文本
        separator: 分隔符
        keep_separator: 是否保留分隔符
        
    Returns:
        List[str]: 分割后的文本块列表
    """
    # 使用分隔符分割文本
    if separator:
        if keep_separator:
            # 括号在模式中保留分隔符
            _splits = re.split(f"({re.escape(separator)})", text)
            splits = [_splits[i - 1] + _splits[i] for i in range(1, len(_splits), 2)]
            if len(_splits) % 2 != 0:
                splits += _splits[-1:]
        else:
            splits = re.split(separator, text)
    else:
        splits = list(text)
    return [s for s in splits if s]  # 过滤空字符串

class RecursiveCharacterTextSplitter(TextSplitter):
    """递归字符文本分块器
    
    通过递归地尝试不同的分隔符来分割文本
    """
    
    def __init__(
        self,
        separators: Optional[List[str]] = None,
        keep_separator: bool = True,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        length_function: Callable[[str], int] = len,
    ):
        """初始化递归字符文本分块器
        
        Args:
            separators: 分隔符列表，按优先级排序
            keep_separator: 是否保留分隔符
            chunk_size: 分块大小
            chunk_overlap: 分块重叠大小
            length_function: 计算文本长度的函数
        """
        super().__init__(chunk_size, chunk_overlap, length_function)
        self._separators = separators or ["\n\n", "\n", ". ", " ", ""]
        self._keep_separator = keep_separator
        
    def split_text(self, text: str) -> List[str]:
        """将文本分割为多个块
        
        Args:
            text: 要分割的文本
            
        Returns:
            List[str]: 分割后的文本块列表
        """
        return self._split_text(text, self._separators)
        
    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """递归分割文本
        
        Args:
            text: 要分割的文本
            separators: 分隔符列表
            
        Returns:
            List[str]: 分割后的文本块列表
        """
        # 最终的分块列表
        final_chunks = []
        
        # 确定使用哪个分隔符
        separator = separators[-1]  # 默认使用最后一个分隔符
        new_separators = []
        
        for i, _s in enumerate(separators):
            if _s == "":
                separator = _s
                break
            if re.search(_s, text):
                separator = _s
                new_separators = separators[i + 1:]
                break
                
        # 使用选定的分隔符分割文本
        splits = _split_text_with_regex(text, separator, self._keep_separator)
        
        # 处理分割后的文本
        _good_splits = []
        _good_splits_lengths = []  # 缓存分块长度
        _separator = "" if self._keep_separator else separator
        
        # 计算每个分块的长度
        s_lens = [self._length_function(s) for s in splits]
        
        for s, s_len in zip(splits, s_lens):
            # 如果分块长度小于chunk_size，添加到_good_splits
            if s_len < self._chunk_size:
                _good_splits.append(s)
                _good_splits_lengths.append(s_len)
            else:
                # 如果有累积的分块，先处理它们
                if _good_splits:
                    merged_text = self._merge_splits(_good_splits, _separator, _good_splits_lengths)
                    final_chunks.extend(merged_text)
                    _good_splits = []
                    _good_splits_lengths = []
                    
                # 处理当前过长的分块
                if not new_separators:
                    # 如果没有更多分隔符，直接添加
                    final_chunks.append(s)
                else:
                    # 递归处理
                    other_chunks = self._split_text(s, new_separators)
                    final_chunks.extend(other_chunks)
                    
        # 处理剩余的分块
        if _good_splits:
            merged_text = self._merge_splits(_good_splits, _separator, _good_splits_lengths)
            final_chunks.extend(merged_text)
            
        return final_chunks
        
    def _merge_splits(self, splits: List[str], separator: str, lengths: List[int]) -> List[str]:
        """合并分块
        
        Args:
            splits: 分块列表
            separator: 分隔符
            lengths: 分块长度列表
            
        Returns:
            List[str]: 合并后的分块列表
        """
        # 分隔符长度
        separator_len = len(separator)
        
        # 结果列表
        docs = []
        current_doc = []
        total = 0
        
        for i, (d, _len) in enumerate(zip(splits, lengths)):
            # 检查添加当前分块是否会超过chunk_size
            if total + _len + (separator_len if current_doc else 0) > self._chunk_size:
                if total > self._chunk_size:
                    Logger.warning(f"创建了大小为 {total} 的分块，大于指定的 {self._chunk_size}")
                    
                # 如果有累积的分块，添加到结果列表
                if current_doc:
                    doc = separator.join(current_doc)
                    if doc:
                        docs.append(doc)
                        
                    # 保留部分分块以实现重叠
                    while total > self._chunk_overlap or (
                        total + _len + (separator_len if current_doc else 0) > self._chunk_size and total > 0
                    ):
                        total -= len(current_doc[0]) + (separator_len if len(current_doc) > 1 else 0)
                        current_doc = current_doc[1:]
                        
            # 添加当前分块
            current_doc.append(d)
            total += _len + (separator_len if len(current_doc) > 1 else 0)
            
        # 处理剩余的分块
        if current_doc:
            doc = separator.join(current_doc)
            if doc:
                docs.append(doc)
                
        return docs