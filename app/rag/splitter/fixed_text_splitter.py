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
        import time
        start_time = time.time()
        
        # 记录分块开始
        separator_display = repr(self._fixed_separator) if self._fixed_separator in ['\n', '\n\n', ' '] else self._fixed_separator
        Logger.debug(f"开始固定分块: 文本长度 {len(text)}, 分块大小 {self._chunk_size}, 重叠 {self._chunk_overlap}")
        Logger.debug(f"固定分隔符: {separator_display}")
        
        # 记录分块策略和参数配置
        Logger.rag_performance_metrics(
            operation="fixed_text_splitting_config",
            duration=0.0,
            content_length=len(text),
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
            fixed_separator=separator_display
        )
        
        try:
            # 使用固定分隔符分割文本
            split_start_time = time.time()
            splits = text.split(self._fixed_separator)
            split_time = time.time() - split_start_time
            
            # 过滤空字符串
            original_split_count = len(splits)
            splits = [s for s in splits if s]
            filtered_count = len(splits)
            
            Logger.debug(f"初始分割完成: {original_split_count} 个片段, 过滤后 {filtered_count} 个, 耗时: {split_time:.3f}秒")
            
            # 合并分块
            merge_start_time = time.time()
            chunks = []
            current_chunk = []
            current_length = 0
            oversized_count = 0
            overlap_operations = 0
        
            for i, split in enumerate(splits):
                split_length = self._length_function(split)
                
                # 如果单个分块超过chunk_size，记录警告并添加
                if split_length > self._chunk_size:
                    Logger.warning(f"单个分块长度 {split_length} 超过了指定的分块大小 {self._chunk_size}")
                    oversized_count += 1
                    
                    if current_chunk:
                        chunk_text = self._fixed_separator.join(current_chunk)
                        chunks.append(chunk_text)
                        Logger.debug(f"保存累积分块: 长度 {len(chunk_text)}, 包含 {len(current_chunk)} 个片段")
                        current_chunk = []
                        current_length = 0
                        
                    chunks.append(split)
                    Logger.debug(f"添加超大分块: 长度 {split_length}")
                    continue
                    
                # 检查添加当前分块是否会超过chunk_size
                if current_length + split_length + (len(self._fixed_separator) if current_chunk else 0) > self._chunk_size:
                    # 如果有累积的分块，添加到结果列表
                    if current_chunk:
                        chunk_text = self._fixed_separator.join(current_chunk)
                        chunks.append(chunk_text)
                        Logger.debug(f"完成分块 {len(chunks)}: 长度 {len(chunk_text)}, 包含 {len(current_chunk)} 个片段")
                        
                        # 保留部分分块以实现重叠
                        overlap_length = 0
                        overlap_chunks = []
                        
                        for j in range(len(current_chunk) - 1, -1, -1):
                            chunk_length = self._length_function(current_chunk[j])
                            if overlap_length + chunk_length <= self._chunk_overlap:
                                overlap_chunks.insert(0, current_chunk[j])
                                overlap_length += chunk_length + (len(self._fixed_separator) if overlap_chunks else 0)
                            else:
                                break
                        
                        if overlap_chunks:
                            overlap_operations += 1
                            Logger.debug(f"重叠处理: 保留 {len(overlap_chunks)} 个片段, 长度 {overlap_length}")
                                
                        current_chunk = overlap_chunks
                        current_length = overlap_length
                        
                # 添加当前分块
                current_chunk.append(split)
                current_length += split_length + (len(self._fixed_separator) if len(current_chunk) > 1 else 0)
                
            # 处理剩余的分块
            if current_chunk:
                chunk_text = self._fixed_separator.join(current_chunk)
                chunks.append(chunk_text)
                Logger.debug(f"添加最后分块: 长度 {len(chunk_text)}, 包含 {len(current_chunk)} 个片段")
            
            # 计算处理时间
            merge_time = time.time() - merge_start_time
            process_time = time.time() - start_time
            
            # 统计分块信息
            chunk_lengths = [len(chunk) for chunk in chunks]
            avg_chunk_length = sum(chunk_lengths) / len(chunk_lengths) if chunk_lengths else 0
            min_chunk_length = min(chunk_lengths) if chunk_lengths else 0
            max_chunk_length = max(chunk_lengths) if chunk_lengths else 0
            
            # 计算分块质量评估指标
            import statistics
            chunk_size_std = statistics.stdev(chunk_lengths) if len(chunk_lengths) > 1 else 0.0
            size_utilization = avg_chunk_length / self._chunk_size if self._chunk_size > 0 else 0.0
            oversized_ratio = oversized_count / len(chunks) if chunks else 0.0
            
            # 过小分块比例 (小于目标大小50%的分块)
            undersized_threshold = self._chunk_size * 0.5
            undersized_count = sum(1 for length in chunk_lengths if length < undersized_threshold)
            undersized_ratio = undersized_count / len(chunks) if chunks else 0.0
            
            # 记录分块成功
            Logger.debug(f"固定分块完成:")
            Logger.debug(f"  - 原文本长度: {len(text)}")
            Logger.debug(f"  - 初始片段数: {original_split_count}")
            Logger.debug(f"  - 有效片段数: {filtered_count}")
            Logger.debug(f"  - 最终分块数: {len(chunks)}")
            Logger.debug(f"  - 平均分块长度: {avg_chunk_length:.1f}")
            Logger.debug(f"  - 最小分块长度: {min_chunk_length}")
            Logger.debug(f"  - 最大分块长度: {max_chunk_length}")
            Logger.debug(f"  - 分块大小标准差: {chunk_size_std:.1f}")
            Logger.debug(f"  - 大小利用率: {size_utilization:.2%}")
            Logger.debug(f"  - 超大分块数量: {oversized_count}")
            Logger.debug(f"  - 超大分块比例: {oversized_ratio:.2%}")
            Logger.debug(f"  - 过小分块比例: {undersized_ratio:.2%}")
            Logger.debug(f"  - 重叠操作次数: {overlap_operations}")
            Logger.debug(f"  - 分割耗时: {split_time:.3f}秒")
            Logger.debug(f"  - 合并耗时: {merge_time:.3f}秒")
            Logger.debug(f"  - 总处理耗时: {process_time:.3f}秒")
            
            # 记录性能指标和质量评估
            Logger.rag_performance_metrics(
                operation="fixed_text_splitting",
                duration=process_time,
                content_length=len(text),
                original_split_count=original_split_count,
                filtered_split_count=filtered_count,
                chunk_count=len(chunks),
                avg_chunk_length=avg_chunk_length,
                min_chunk_length=min_chunk_length,
                max_chunk_length=max_chunk_length,
                chunk_size_std=chunk_size_std,
                size_utilization=size_utilization,
                oversized_count=oversized_count,
                oversized_ratio=oversized_ratio,
                undersized_count=undersized_count,
                undersized_ratio=undersized_ratio,
                overlap_operations=overlap_operations,
                chunk_size=self._chunk_size,
                chunk_overlap=self._chunk_overlap,
                split_time=split_time,
                merge_time=merge_time,
                processing_speed=len(text) / process_time if process_time > 0 else 0.0  # 字符/秒
            )
            
            return chunks
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            import traceback
            error_info = traceback.format_exc()
            
            Logger.error(f"固定分块失败:")
            Logger.error(f"  - 文本长度: {len(text)}")
            Logger.error(f"  - 分块配置: 大小={self._chunk_size}, 重叠={self._chunk_overlap}")
            Logger.error(f"  - 固定分隔符: {separator_display}")
            Logger.error(f"  - 错误信息: {str(e)}")
            Logger.debug(f"堆栈跟踪:\n{error_info}")
            
            # 记录失败的性能指标
            Logger.rag_performance_metrics(
                operation="fixed_text_splitting_failed",
                duration=process_time,
                content_length=len(text),
                chunk_size=self._chunk_size,
                chunk_overlap=self._chunk_overlap,
                fixed_separator=separator_display,
                error=str(e),
                error_type=type(e).__name__
            )
            
            raise