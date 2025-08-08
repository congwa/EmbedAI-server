"""API响应系统迁移工具

提供从旧的APIResponse机制迁移到新的ResponseModel机制的工具和指导
"""

import re
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import ast
import warnings


class ResponseMigrationAnalyzer:
    """响应机制迁移分析器"""
    
    def __init__(self, project_root: str = "."):
        """初始化迁移分析器
        
        Args:
            project_root: 项目根目录路径
        """
        self.project_root = Path(project_root)
        self.api_files = []
        self.migration_issues = []
    
    def scan_project(self) -> Dict[str, Any]:
        """扫描项目中需要迁移的代码
        
        Returns:
            Dict[str, Any]: 扫描结果
        """
        print("🔍 扫描项目中的API响应代码...")
        
        # 扫描API文件
        api_dirs = [
            self.project_root / "app" / "api",
            self.project_root / "app" / "services"
        ]
        
        for api_dir in api_dirs:
            if api_dir.exists():
                self._scan_directory(api_dir)
        
        # 分析迁移问题
        self._analyze_migration_issues()
        
        return {
            "total_files": len(self.api_files),
            "files_with_issues": len([f for f in self.api_files if f["issues"]]),
            "total_issues": sum(len(f["issues"]) for f in self.api_files),
            "files": self.api_files,
            "migration_summary": self._generate_migration_summary()
        }
    
    def _scan_directory(self, directory: Path) -> None:
        """扫描目录中的Python文件"""
        for file_path in directory.rglob("*.py"):
            if file_path.name.startswith("__"):
                continue
            
            file_info = self._analyze_file(file_path)
            if file_info["issues"]:
                self.api_files.append(file_info)
    
    def _analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """分析单个文件中的迁移问题
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict[str, Any]: 文件分析结果
        """
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查APIResponse.success()使用
            success_matches = re.finditer(r'APIResponse\.success\s*\(', content)
            for match in success_matches:
                line_num = content[:match.start()].count('\n') + 1
                issues.append({
                    "type": "deprecated_success",
                    "line": line_num,
                    "message": "使用了废弃的 APIResponse.success()",
                    "suggestion": "替换为 ResponseModel.create_success()",
                    "severity": "warning"
                })
            
            # 检查APIResponse.error()使用
            error_matches = re.finditer(r'APIResponse\.error\s*\(', content)
            for match in error_matches:
                line_num = content[:match.start()].count('\n') + 1
                issues.append({
                    "type": "deprecated_error",
                    "line": line_num,
                    "message": "使用了废弃的 APIResponse.error()",
                    "suggestion": "替换为 ResponseModel.create_error() 或抛出自定义异常",
                    "severity": "warning"
                })
            
            # 检查try-catch包装的HTTPException
            try_catch_pattern = r'try:\s*.*?except\s+.*?Exception.*?:\s*.*?HTTPException'
            try_catch_matches = re.finditer(try_catch_pattern, content, re.DOTALL)
            for match in try_catch_matches:
                line_num = content[:match.start()].count('\n') + 1
                issues.append({
                    "type": "manual_exception_handling",
                    "line": line_num,
                    "message": "发现手动异常处理，可以简化",
                    "suggestion": "移除try-catch，让全局异常处理器处理",
                    "severity": "info"
                })
            
            # 检查response_wrapper装饰器使用
            wrapper_matches = re.finditer(r'@response_wrapper', content)
            for match in wrapper_matches:
                line_num = content[:match.start()].count('\n') + 1
                issues.append({
                    "type": "deprecated_wrapper",
                    "line": line_num,
                    "message": "使用了废弃的 @response_wrapper 装饰器",
                    "suggestion": "移除装饰器，使用新的响应机制",
                    "severity": "warning"
                })
            
        except Exception as e:
            issues.append({
                "type": "analysis_error",
                "line": 0,
                "message": f"文件分析失败: {str(e)}",
                "suggestion": "手动检查此文件",
                "severity": "error"
            })
        
        return {
            "file_path": str(file_path.relative_to(self.project_root)),
            "issues": issues
        }
    
    def _analyze_migration_issues(self) -> None:
        """分析迁移问题的优先级和复杂度"""
        for file_info in self.api_files:
            file_info["migration_complexity"] = self._calculate_complexity(file_info["issues"])
            file_info["migration_priority"] = self._calculate_priority(file_info["issues"])
    
    def _calculate_complexity(self, issues: List[Dict[str, Any]]) -> str:
        """计算迁移复杂度
        
        Args:
            issues: 问题列表
            
        Returns:
            str: 复杂度等级 (low, medium, high)
        """
        error_count = len([i for i in issues if i["severity"] == "error"])
        warning_count = len([i for i in issues if i["severity"] == "warning"])
        
        if error_count > 0:
            return "high"
        elif warning_count > 5:
            return "medium"
        else:
            return "low"
    
    def _calculate_priority(self, issues: List[Dict[str, Any]]) -> str:
        """计算迁移优先级
        
        Args:
            issues: 问题列表
            
        Returns:
            str: 优先级等级 (low, medium, high)
        """
        deprecated_count = len([i for i in issues if "deprecated" in i["type"]])
        
        if deprecated_count > 3:
            return "high"
        elif deprecated_count > 1:
            return "medium"
        else:
            return "low"
    
    def _generate_migration_summary(self) -> Dict[str, Any]:
        """生成迁移摘要
        
        Returns:
            Dict[str, Any]: 迁移摘要
        """
        total_files = len(self.api_files)
        high_priority = len([f for f in self.api_files if f.get("migration_priority") == "high"])
        medium_priority = len([f for f in self.api_files if f.get("migration_priority") == "medium"])
        low_priority = len([f for f in self.api_files if f.get("migration_priority") == "low"])
        
        return {
            "total_files_to_migrate": total_files,
            "high_priority_files": high_priority,
            "medium_priority_files": medium_priority,
            "low_priority_files": low_priority,
            "estimated_effort": self._estimate_effort(total_files, high_priority, medium_priority)
        }
    
    def _estimate_effort(self, total: int, high: int, medium: int) -> str:
        """估算迁移工作量
        
        Args:
            total: 总文件数
            high: 高优先级文件数
            medium: 中优先级文件数
            
        Returns:
            str: 工作量估算
        """
        if total == 0:
            return "无需迁移"
        elif high > 5 or total > 20:
            return "大型迁移 (建议分阶段进行)"
        elif high > 2 or total > 10:
            return "中型迁移 (需要仔细规划)"
        else:
            return "小型迁移 (可以快速完成)"
    
    def generate_migration_report(self, output_file: str = "migration_report.md") -> None:
        """生成迁移报告
        
        Args:
            output_file: 输出文件路径
        """
        scan_result = self.scan_project()
        
        report_content = self._generate_report_content(scan_result)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📋 迁移报告已生成: {output_file}")
    
    def _generate_report_content(self, scan_result: Dict[str, Any]) -> str:
        """生成报告内容
        
        Args:
            scan_result: 扫描结果
            
        Returns:
            str: 报告内容
        """
        summary = scan_result["migration_summary"]
        
        content = f"""# API响应系统迁移报告

## 迁移摘要

- **总文件数**: {scan_result['total_files']}
- **需要迁移的文件**: {scan_result['files_with_issues']}
- **总问题数**: {scan_result['total_issues']}
- **工作量估算**: {summary['estimated_effort']}

## 优先级分布

- 🔴 **高优先级**: {summary['high_priority_files']} 个文件
- 🟡 **中优先级**: {summary['medium_priority_files']} 个文件
- 🟢 **低优先级**: {summary['low_priority_files']} 个文件

## 迁移建议

### 第一阶段：高优先级文件
优先迁移使用大量废弃API的文件，这些文件对系统稳定性影响最大。

### 第二阶段：中优先级文件
迁移中等复杂度的文件，通常只需要简单的API替换。

### 第三阶段：低优先级文件
最后处理简单的迁移，主要是清理工作。

## 详细问题列表

"""
        
        for file_info in scan_result["files"]:
            if not file_info["issues"]:
                continue
            
            priority_emoji = {
                "high": "🔴",
                "medium": "🟡", 
                "low": "🟢"
            }.get(file_info.get("migration_priority", "low"), "🟢")
            
            content += f"""### {priority_emoji} {file_info['file_path']}

**迁移复杂度**: {file_info.get('migration_complexity', 'unknown')}
**迁移优先级**: {file_info.get('migration_priority', 'unknown')}

"""
            
            for issue in file_info["issues"]:
                severity_emoji = {
                    "error": "❌",
                    "warning": "⚠️",
                    "info": "ℹ️"
                }.get(issue["severity"], "ℹ️")
                
                content += f"""- {severity_emoji} **第{issue['line']}行**: {issue['message']}
  - 建议: {issue['suggestion']}

"""
        
        content += """
## 迁移步骤指南

### 1. 替换APIResponse.success()

**旧代码:**
```python
return APIResponse.success(data=result, message="操作成功")
```

**新代码:**
```python
return ResponseModel.create_success(data=result, message="操作成功")
```

### 2. 替换异常处理

**旧代码:**
```python
try:
    result = await some_operation()
    return APIResponse.success(data=result)
except Exception as e:
    Logger.error(f"操作失败: {str(e)}")
    raise HTTPException(status_code=500, detail="操作失败")
```

**新代码:**
```python
result = await some_operation()
return ResponseModel.create_success(data=result)
```

### 3. 移除response_wrapper装饰器

**旧代码:**
```python
@response_wrapper()
async def my_endpoint():
    return some_data
```

**新代码:**
```python
async def my_endpoint():
    return ResponseModel.create_success(data=some_data)
```

### 4. 使用新的异常类

**旧代码:**
```python
raise HTTPException(status_code=404, detail="资源不存在")
```

**新代码:**
```python
raise ResourceNotFoundException("资源", resource_id)
```

## 验证清单

迁移完成后，请检查以下项目：

- [ ] 所有APIResponse.success()调用已替换
- [ ] 所有APIResponse.error()调用已替换
- [ ] 所有@response_wrapper装饰器已移除
- [ ] 手动异常处理已简化
- [ ] 使用新的异常类替代HTTPException
- [ ] API文档生成正常
- [ ] 响应格式保持一致
- [ ] 所有测试通过

## 注意事项

1. **渐进式迁移**: 可以逐个文件进行迁移，新旧机制可以并存
2. **测试验证**: 每次迁移后都要运行相关测试
3. **响应格式**: 确保迁移后的响应格式与之前完全一致
4. **错误处理**: 新的异常处理机制更简洁，但要确保错误信息准确
5. **性能影响**: 新机制性能更好，但要注意大数据量的处理

"""
        
        return content


class CompatibilityLayer:
    """兼容性层，确保新旧机制可以并存"""
    
    @staticmethod
    def enable_deprecation_warnings() -> None:
        """启用废弃警告"""
        warnings.filterwarnings("default", category=DeprecationWarning)
    
    @staticmethod
    def check_legacy_usage(func):
        """装饰器：检查遗留API使用情况"""
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"函数 {func.__name__} 使用了遗留的响应机制，建议迁移到新的ResponseModel",
                DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper


def run_migration_analysis(project_root: str = ".") -> None:
    """运行迁移分析
    
    Args:
        project_root: 项目根目录
    """
    print("🚀 开始API响应系统迁移分析...")
    
    analyzer = ResponseMigrationAnalyzer(project_root)
    analyzer.generate_migration_report()
    
    print("✅ 迁移分析完成！")
    print("📖 请查看 migration_report.md 了解详细的迁移指导")


if __name__ == "__main__":
    run_migration_analysis()