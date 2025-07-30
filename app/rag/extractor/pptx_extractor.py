"""PPTX 文件提取器"""
from typing import List, Dict, Any
from unstructured.partition.pptx import partition_pptx

from app.rag.extractor.extractor_base import BaseExtractor
from app.core.logger import Logger

class PptxExtractor(BaseExtractor):
    """PPTX 文件提取器"""

    async def extract(self, file_path: str) -> List[Dict[str, Any]]:
        """从 PPTX 文件中提取内容。

        Args:
            file_path: PPTX 文件的路径。

        Returns:
            一个字典列表，每个字典包含页码和该页的文本内容。
        """
        try:
            Logger.debug(f"使用 PptxExtractor 提取文件: {file_path}")
            elements = partition_pptx(filename=file_path)
            
            slides_content = []
            for element in elements:
                slide_info = {
                    "type": "slide",
                    "text": element.text,
                    "source": file_path
                }
                if hasattr(element.metadata, 'page_number'):
                    slide_info['page'] = element.metadata.page_number
                slides_content.append(slide_info)

            return slides_content

        except Exception as e:
            Logger.error(f"提取 PPTX 文件失败: {file_path}, 错误: {e}")
            return []
