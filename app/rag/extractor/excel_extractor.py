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
        import time
        start_time = time.time()
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                Logger.error(f"Excel文件不存在: {file_path}")
                return []
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            Logger.debug(f"开始提取Excel文件: {file_path}, 大小: {file_size} bytes")
                
            # 读取Excel文件的所有工作表
            open_start_time = time.time()
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            open_time = time.time() - open_start_time
            
            Logger.debug(f"Excel文件打开成功: {len(sheet_names)} 个工作表, 耗时: {open_time:.3f}秒")
            Logger.debug(f"工作表列表: {sheet_names}")
            
            results = []
            total_rows = 0
            total_columns = 0
            total_content_length = 0
            
            for i, sheet_name in enumerate(sheet_names):
                sheet_start_time = time.time()
                
                Logger.debug(f"开始处理工作表 {i+1}/{len(sheet_names)}: {sheet_name}")
                
                # 读取工作表
                read_start_time = time.time()
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                read_time = time.time() - read_start_time
                
                # 将DataFrame转换为字符串
                if not df.empty:
                    convert_start_time = time.time()
                    
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
                    convert_time = time.time() - convert_start_time
                    
                    sheet_time = time.time() - sheet_start_time
                    
                    # 统计信息
                    sheet_rows = len(df)
                    sheet_columns = len(df.columns)
                    sheet_content_length = len(sheet_text)
                    
                    total_rows += sheet_rows
                    total_columns = max(total_columns, sheet_columns)  # 取最大列数
                    total_content_length += sheet_content_length
                    
                    Logger.debug(f"工作表 {sheet_name} 处理完成:")
                    Logger.debug(f"  - 行数: {sheet_rows}, 列数: {sheet_columns}")
                    Logger.debug(f"  - 内容长度: {sheet_content_length}")
                    Logger.debug(f"  - 读取耗时: {read_time:.3f}秒, 转换耗时: {convert_time:.3f}秒")
                    
                    # 添加到结果列表
                    results.append({
                        "text": sheet_text,
                        "metadata": {
                            "source_type": "excel",
                            "file_path": file_path,
                            "sheet_name": sheet_name,
                            "sheet_index": i,
                            "rows": sheet_rows,
                            "columns": sheet_columns,
                            "content_length": sheet_content_length,
                            "read_time": read_time,
                            "convert_time": convert_time,
                            "total_time": sheet_time
                        }
                    })
                else:
                    Logger.debug(f"工作表 {sheet_name} 为空，跳过")
                    
            # 计算总处理时间
            total_time = time.time() - start_time
            
            # 记录提取成功的详细信息
            Logger.debug(f"Excel提取完成: {file_path}")
            Logger.debug(f"  - 工作表数: {len(sheet_names)}")
            Logger.debug(f"  - 有效工作表数: {len(results)}")
            Logger.debug(f"  - 总行数: {total_rows}")
            Logger.debug(f"  - 最大列数: {total_columns}")
            Logger.debug(f"  - 总内容长度: {total_content_length}")
            Logger.debug(f"  - 总耗时: {total_time:.3f}秒")
            
            # 记录性能指标
            Logger.rag_performance_metrics(
                operation="excel_extraction",
                duration=total_time,
                file_size=file_size,
                file_type="excel",
                sheet_count=len(sheet_names),
                valid_sheet_count=len(results),
                total_rows=total_rows,
                max_columns=total_columns,
                content_length=total_content_length,
                open_time=open_time
            )
                    
            return results
            
        except Exception as e:
            # 计算处理时间
            total_time = time.time() - start_time
            
            import traceback
            error_info = traceback.format_exc()
            
            Logger.error(f"Excel提取失败: {file_path}")
            Logger.error(f"错误信息: {str(e)}")
            Logger.debug(f"堆栈跟踪:\n{error_info}")
            
            # 记录失败的性能指标
            Logger.rag_performance_metrics(
                operation="excel_extraction_failed",
                duration=total_time,
                file_size=file_size if 'file_size' in locals() else 0,
                file_type="excel",
                error=str(e)
            )
            
            return []