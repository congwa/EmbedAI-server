"""文本提取器，负责从文本文件中提取内容"""
import os
from typing import List, Dict, Any
import chardet

from app.core.logger import Logger
from app.rag.extractor.extractor_base import BaseExtractor

class TextExtractor(BaseExtractor):
    """文本提取器，负责从文本文件中提取内容"""
    
    def __init__(self, autodetect_encoding: bool = True):
        """初始化文本提取器
        
        Args:
            autodetect_encoding: 是否自动检测编码
        """
        self.autodetect_encoding = autodetect_encoding
        
    async def extract(self, file_path: str) -> List[Dict[str, Any]]:
        """从文本文件中提取内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            List[Dict[str, Any]]: 提取的文本内容列表
        """
        import time
        start_time = time.time()
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                Logger.error(f"文本文件不存在: {file_path}")
                return []
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            Logger.debug(f"开始提取文本文件: {file_path}, 大小: {file_size} bytes")
                
            # 读取文件内容
            encoding = 'utf-8'
            encoding_confidence = 1.0
            
            if self.autodetect_encoding:
                # 检测文件编码
                detect_start_time = time.time()
                with open(file_path, 'rb') as f:
                    raw_data = f.read()
                    result = chardet.detect(raw_data)
                    encoding = result['encoding'] or 'utf-8'
                    encoding_confidence = result['confidence'] or 0.0
                    
                detect_time = time.time() - detect_start_time
                Logger.debug(f"编码检测完成: {encoding} (置信度: {encoding_confidence:.2f}), 耗时: {detect_time:.3f}秒")
            else:
                Logger.debug(f"使用默认编码: {encoding}")
                    
            # 读取文件内容
            read_start_time = time.time()
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                content = f.read()
            read_time = time.time() - read_start_time
            
            # 统计文本信息
            line_count = content.count('\n') + 1 if content else 0
            char_count = len(content)
            word_count = len(content.split()) if content else 0
            
            # 计算总处理时间
            total_time = time.time() - start_time
            
            # 记录提取成功的详细信息
            Logger.debug(f"文本提取完成: {file_path}")
            Logger.debug(f"  - 编码: {encoding} (置信度: {encoding_confidence:.2f})")
            Logger.debug(f"  - 字符数: {char_count}")
            Logger.debug(f"  - 单词数: {word_count}")
            Logger.debug(f"  - 行数: {line_count}")
            Logger.debug(f"  - 读取耗时: {read_time:.3f}秒")
            Logger.debug(f"  - 总耗时: {total_time:.3f}秒")
            
            # 记录性能指标
            Logger.rag_performance_metrics(
                operation="text_extraction",
                duration=total_time,
                file_size=file_size,
                file_type="text",
                content_length=char_count,
                line_count=line_count,
                word_count=word_count,
                encoding=encoding,
                encoding_confidence=encoding_confidence,
                read_time=read_time,
                detect_time=detect_time if self.autodetect_encoding else 0
            )
                
            # 返回提取的内容
            return [{
                "text": content,
                "metadata": {
                    "source_type": "text",
                    "file_path": file_path,
                    "encoding": encoding,
                    "encoding_confidence": encoding_confidence,
                    "char_count": char_count,
                    "word_count": word_count,
                    "line_count": line_count,
                    "extraction_time": total_time
                }
            }]
            
        except Exception as e:
            # 计算处理时间
            total_time = time.time() - start_time
            
            import traceback
            error_info = traceback.format_exc()
            
            Logger.error(f"文本提取失败: {file_path}")
            Logger.error(f"错误信息: {str(e)}")
            Logger.debug(f"堆栈跟踪:\n{error_info}")
            
            # 记录失败的性能指标
            Logger.rag_performance_metrics(
                operation="text_extraction_failed",
                duration=total_time,
                file_size=file_size if 'file_size' in locals() else 0,
                file_type="text",
                encoding=encoding if 'encoding' in locals() else "unknown",
                error=str(e)
            )
            
            return []