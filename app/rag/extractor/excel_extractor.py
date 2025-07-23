"""Excel提取器，负责从Excel文件中提取内容"""
import os
from typing import List, Dict, Any
import pandas as pd

from app.core.logger import Logger
from app.rag.extractor.extractor_base import BaseExtractor

class ExcelExtractor(BaseExtractor):
    """Excel提取器，负责从Excel文件中提取内容"""
    
    async def extract(self, file_path: str) -> List[Dict[str, Any]]:
        """从Excel文件中提取内容
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            List[Dict[str, Any]]: 提取的文本内容列表，每个元素对应一个工作表
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                Logger.error(f"File not found: {file_path}")
                return []
                
            # 读取Excel文件的所有工作表
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            results = []
            for sheet_name in sheet_names:
                # 读取工作表
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # 将DataFrame转换为字符串
                if not df.empty:
                    # 处理表头
                    headers = df.columns.tolist()
                    header_text = " | ".join([str(h) for h in headers])
                    
                    # 处理数据行
                    rows_text = []
                    for _, row in df.iterrows():
                        row_text = " | ".join([str(cell) for cell in row.tolist()])
                        rows_text.append(row_text)
                        
                    # 合并所有文本
                    sheet_text = header_text + "\n" + "\n".join(rows_text)
                    
                    # 添加到结果列表
                    results.append({
                        "text": sheet_text,
                        "metadata": {
                            "source_type": "excel",
                            "file_path": file_path,
                            "sheet_name": sheet_name,
                            "rows": len(df),
                            "columns": len(df.columns)
                        }
                    })
                    
            return results
            
        except Exception as e:
            Logger.error(f"Error extracting text from Excel file {file_path}: {str(e)}")
            return []