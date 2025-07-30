"""CSV 文件提取器"""
from typing import List, Dict, Any
import pandas as pd
from unstructured.partition.csv import partition_csv

from app.rag.extractor.extractor_base import BaseExtractor
from app.core.logger import Logger

class CsvExtractor(BaseExtractor):
    """CSV 文件提取器"""

    async def extract(self, file_path: str) -> List[Dict[str, Any]]:
        """从 CSV 文件中提取内容。

        Args:
            file_path: CSV 文件的路径。

        Returns:
            一个字典列表，每个字典代表一行，键是列名。
        """
        try:
            Logger.debug(f"使用 CsvExtractor 提取文件: {file_path}")
            elements = partition_csv(filename=file_path)
            text_content = "\n\n".join([el.text for el in elements])
            
            # 为了保持与其它提取器相似的输出结构，我们返回一个包含全部文本的字典
            return [{
                "type": "text",
                "text": text_content,
                "source": file_path
            }]

        except Exception as e:
            Logger.error(f"提取 CSV 文件失败: {file_path}, 错误: {e}")
            return []
