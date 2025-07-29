"""HTML提取器，负责从HTML文件中提取内容"""
import os
from typing import List, Dict, Any
import chardet
from bs4 import BeautifulSoup

from app.core.logger import Logger
from app.rag.extractor.extractor_base import BaseExtractor

class HtmlExtractor(BaseExtractor):
    """HTML提取器，负责从HTML文件中提取内容"""
    
    async def extract(self, file_path: str) -> List[Dict[str, Any]]:
        """从HTML文件中提取内容
        
        Args:
            file_path: HTML文件路径
            
        Returns:
            List[Dict[str, Any]]: 提取的文本内容列表
        """
        import time
        start_time = time.time()
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                Logger.error(f"HTML文件不存在: {file_path}")
                return []
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            Logger.debug(f"开始提取HTML文件: {file_path}, 大小: {file_size} bytes")
                
            # 读取文件内容并检测编码
            detect_start_time = time.time()
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding'] or 'utf-8'
                encoding_confidence = result['confidence'] or 0.0
            detect_time = time.time() - detect_start_time
            
            Logger.debug(f"编码检测完成: {encoding} (置信度: {encoding_confidence:.2f}), 耗时: {detect_time:.3f}秒")
                
            # 解析HTML
            read_start_time = time.time()
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                html_content = f.read()
            read_time = time.time() - read_start_time
            
            # 使用BeautifulSoup提取文本
            parse_start_time = time.time()
            soup = BeautifulSoup(html_content, 'html.parser')
            parse_time = time.time() - parse_start_time
            
            Logger.debug(f"HTML解析完成: 耗时 {parse_time:.3f}秒")
            
            # 提取标题
            title_start_time = time.time()
            title = soup.title.string if soup.title else ""
            title_time = time.time() - title_start_time
            
            # 统计HTML元素
            all_tags = soup.find_all()
            tag_count = len(all_tags)
            
            # 统计特定元素
            script_tags = soup.find_all("script")
            style_tags = soup.find_all("style")
            link_tags = soup.find_all("a")
            img_tags = soup.find_all("img")
            
            Logger.debug(f"HTML元素统计: 总标签 {tag_count}, script {len(script_tags)}, style {len(style_tags)}, 链接 {len(link_tags)}, 图片 {len(img_tags)}")
            
            # 提取正文
            extract_start_time = time.time()
            
            # 移除script和style元素
            for script in soup(["script", "style"]):
                script.extract()
                
            # 获取文本
            text = soup.get_text(separator="\n", strip=True)
            extract_time = time.time() - extract_start_time
            
            # 统计文本信息
            line_count = text.count('\n') + 1 if text else 0
            char_count = len(text)
            word_count = len(text.split()) if text else 0
            
            # 计算总处理时间
            total_time = time.time() - start_time
            
            # 记录提取成功的详细信息
            Logger.debug(f"HTML提取完成: {file_path}")
            Logger.debug(f"  - 标题: {title[:50]}..." if len(title) > 50 else f"  - 标题: {title}")
            Logger.debug(f"  - 编码: {encoding} (置信度: {encoding_confidence:.2f})")
            Logger.debug(f"  - HTML标签数: {tag_count}")
            Logger.debug(f"  - 字符数: {char_count}")
            Logger.debug(f"  - 单词数: {word_count}")
            Logger.debug(f"  - 行数: {line_count}")
            Logger.debug(f"  - 总耗时: {total_time:.3f}秒")
            
            # 记录性能指标
            Logger.rag_performance_metrics(
                operation="html_extraction",
                duration=total_time,
                file_size=file_size,
                file_type="html",
                content_length=char_count,
                line_count=line_count,
                word_count=word_count,
                tag_count=tag_count,
                script_count=len(script_tags),
                style_count=len(style_tags),
                link_count=len(link_tags),
                img_count=len(img_tags),
                encoding=encoding,
                encoding_confidence=encoding_confidence,
                detect_time=detect_time,
                read_time=read_time,
                parse_time=parse_time,
                extract_time=extract_time
            )
            
            # 返回提取的内容
            return [{
                "text": text,
                "metadata": {
                    "source_type": "html",
                    "file_path": file_path,
                    "title": title,
                    "encoding": encoding,
                    "encoding_confidence": encoding_confidence,
                    "char_count": char_count,
                    "word_count": word_count,
                    "line_count": line_count,
                    "tag_count": tag_count,
                    "script_count": len(script_tags),
                    "style_count": len(style_tags),
                    "link_count": len(link_tags),
                    "img_count": len(img_tags),
                    "extraction_time": total_time
                }
            }]
            
        except Exception as e:
            # 计算处理时间
            total_time = time.time() - start_time
            
            import traceback
            error_info = traceback.format_exc()
            
            Logger.error(f"HTML提取失败: {file_path}")
            Logger.error(f"错误信息: {str(e)}")
            Logger.debug(f"堆栈跟踪:\n{error_info}")
            
            # 记录失败的性能指标
            Logger.rag_performance_metrics(
                operation="html_extraction_failed",
                duration=total_time,
                file_size=file_size if 'file_size' in locals() else 0,
                file_type="html",
                encoding=encoding if 'encoding' in locals() else "unknown",
                error=str(e)
            )
            
            return []