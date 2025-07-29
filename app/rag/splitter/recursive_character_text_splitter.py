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
        import time
        start_time = time.time()
        
        # 记录分块开始
        Logger.debug(f"开始递归字符分块: 文本长度 {len(text)}, 分块大小 {self._chunk_size}, 重叠 {self._chunk_overlap}")
        Logger.debug(f"分隔符配置: {self._separators}, 保留分隔符: {self._keep_separator}")
        
        # 记录分块策略和参数配置
        Logger.rag_performance_metrics(
            operation="recursive_text_splitting_config",
            duration=0.0,
            content_length=len(text),
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
            separator_count=len(self._separators),
            keep_separator=self._keep_separator,
            separators=self._separators
        )
        
        try:
            # 执行分块
            result = self._split_text(text, self._separators)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 统计分块信息
            chunk_lengths = [len(chunk) for chunk in result]
            avg_chunk_length = sum(chunk_lengths) / len(chunk_lengths) if chunk_lengths else 0
            min_chunk_length = min(chunk_lengths) if chunk_lengths else 0
            max_chunk_length = max(chunk_lengths) if chunk_lengths else 0
            
            # 计算分块质量评估指标
            # 1. 分块大小一致性 (标准差)
            import statistics
            chunk_size_std = statistics.stdev(chunk_lengths) if len(chunk_lengths) > 1 else 0.0
            
            # 2. 分块大小利用率 (平均分块大小 / 目标分块大小)
            size_utilization = avg_chunk_length / self._chunk_size if self._chunk_size > 0 else 0.0
            
            # 3. 超大分块比例
            oversized_count = sum(1 for length in chunk_lengths if length > self._chunk_size)
            oversized_ratio = oversized_count / len(chunk_lengths) if chunk_lengths else 0.0
            
            # 4. 过小分块比例 (小于目标大小50%的分块)
            undersized_threshold = self._chunk_size * 0.5
            undersized_count = sum(1 for length in chunk_lengths if length < undersized_threshold)
            undersized_ratio = undersized_count / len(chunk_lengths) if chunk_lengths else 0.0
            
            # 记录分块成功
            Logger.debug(f"递归字符分块完成:")
            Logger.debug(f"  - 原文本长度: {len(text)}")
            Logger.debug(f"  - 分块数量: {len(result)}")
            Logger.debug(f"  - 平均分块长度: {avg_chunk_length:.1f}")
            Logger.debug(f"  - 最小分块长度: {min_chunk_length}")
            Logger.debug(f"  - 最大分块长度: {max_chunk_length}")
            Logger.debug(f"  - 分块大小标准差: {chunk_size_std:.1f}")
            Logger.debug(f"  - 大小利用率: {size_utilization:.2%}")
            Logger.debug(f"  - 超大分块比例: {oversized_ratio:.2%}")
            Logger.debug(f"  - 过小分块比例: {undersized_ratio:.2%}")
            Logger.debug(f"  - 处理耗时: {process_time:.3f}秒")
            
            # 记录性能指标和质量评估
            Logger.rag_performance_metrics(
                operation="recursive_text_splitting",
                duration=process_time,
                content_length=len(text),
                chunk_count=len(result),
                avg_chunk_length=avg_chunk_length,
                min_chunk_length=min_chunk_length,
                max_chunk_length=max_chunk_length,
                chunk_size_std=chunk_size_std,
                size_utilization=size_utilization,
                oversized_count=oversized_count,
                oversized_ratio=oversized_ratio,
                undersized_count=undersized_count,
                undersized_ratio=undersized_ratio,
                chunk_size=self._chunk_size,
                chunk_overlap=self._chunk_overlap,
                separator_count=len(self._separators),
                processing_speed=len(text) / process_time if process_time > 0 else 0.0  # 字符/秒
            )
            
            return result
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            import traceback
            error_info = traceback.format_exc()
            
            Logger.error(f"递归字符分块失败:")
            Logger.error(f"  - 文本长度: {len(text)}")
            Logger.error(f"  - 分块配置: 大小={self._chunk_size}, 重叠={self._chunk_overlap}")
            Logger.error(f"  - 分隔符数量: {len(self._separators)}")
            Logger.error(f"  - 错误信息: {str(e)}")
            Logger.debug(f"堆栈跟踪:\n{error_info}")
            
            # 记录失败的性能指标
            Logger.rag_performance_metrics(
                operation="recursive_text_splitting_failed",
                duration=process_time,
                content_length=len(text),
                chunk_size=self._chunk_size,
                chunk_overlap=self._chunk_overlap,
                separator_count=len(self._separators),
                error=str(e),
                error_type=type(e).__name__
            )
            
            raise
        
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
        
        # 记录分隔符选择过程
        Logger.debug(f"递归分块: 文本长度 {len(text)}, 可用分隔符 {len(separators)} 个")
        
        for i, _s in enumerate(separators):
            if _s == "":
                separator = _s
                Logger.debug(f"选择空字符分隔符 (字符级分割)")
                break
            if re.search(_s, text):
                separator = _s
                new_separators = separators[i + 1:]
                separator_display = repr(_s) if _s in ['\n', '\n\n', ' '] else _s
                Logger.debug(f"选择分隔符: {separator_display}, 剩余分隔符: {len(new_separators)} 个")
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
        
        # 记录合并开始
        total_input_length = sum(lengths)
        separator_display = repr(separator) if separator in ['\n', '\n\n', ' '] else separator
        Logger.debug(f"开始合并分块: {len(splits)} 个片段, 总长度 {total_input_length}, 分隔符: {separator_display}")
        
        # 结果列表
        docs = []
        current_doc = []
        total = 0
        merge_count = 0
        
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
                        merge_count += 1
                        Logger.debug(f"合并分块 {merge_count}: 长度 {len(doc)}, 包含 {len(current_doc)} 个片段")
                        
                    # 保留部分分块以实现重叠
                    overlap_removed = 0
                    while total > self._chunk_overlap or (
                        total + _len + (separator_len if current_doc else 0) > self._chunk_size and total > 0
                    ):
                        removed_len = len(current_doc[0]) + (separator_len if len(current_doc) > 1 else 0)
                        total -= removed_len
                        overlap_removed += removed_len
                        current_doc = current_doc[1:]
                    
                    if overlap_removed > 0:
                        Logger.debug(f"为重叠移除了 {overlap_removed} 个字符, 剩余 {len(current_doc)} 个片段")
                        
            # 添加当前分块
            current_doc.append(d)
            total += _len + (separator_len if len(current_doc) > 1 else 0)
            
        # 处理剩余的分块
        if current_doc:
            doc = separator.join(current_doc)
            if doc:
                docs.append(doc)
                merge_count += 1
                Logger.debug(f"合并最后分块 {merge_count}: 长度 {len(doc)}, 包含 {len(current_doc)} 个片段")
        
        # 记录合并完成
        final_lengths = [len(doc) for doc in docs]
        avg_final_length = sum(final_lengths) / len(final_lengths) if final_lengths else 0
        
        Logger.debug(f"分块合并完成:")
        Logger.debug(f"  - 输入片段: {len(splits)} 个")
        Logger.debug(f"  - 输出分块: {len(docs)} 个")
        Logger.debug(f"  - 平均分块长度: {avg_final_length:.1f}")
        Logger.debug(f"  - 压缩比: {len(docs)/len(splits):.2f}")
                
        return docs