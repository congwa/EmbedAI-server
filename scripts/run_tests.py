#!/usr/bin/env python3
"""
测试运行脚本
提供完整的测试套件执行和报告生成
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.project_root = project_root
        self.test_results = {}
        
    def run_unit_tests(self) -> Dict[str, Any]:
        """运行单元测试"""
        print("🧪 运行单元测试...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/unit/",
            "-v",
            "--tb=short",
            "--cov=app",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--junit-xml=test-results/unit-tests.xml",
            "-m", "unit"
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        duration = time.time() - start_time
        
        return {
            "name": "单元测试",
            "success": result.returncode == 0,
            "duration": duration,
            "output": result.stdout,
            "error": result.stderr
        }
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """运行集成测试"""
        print("🔗 运行集成测试...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/integration/",
            "-v",
            "--tb=short",
            "--junit-xml=test-results/integration-tests.xml",
            "-m", "integration"
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        duration = time.time() - start_time
        
        return {
            "name": "集成测试",
            "success": result.returncode == 0,
            "duration": duration,
            "output": result.stdout,
            "error": result.stderr
        }
    
    def run_e2e_tests(self) -> Dict[str, Any]:
        """运行端到端测试"""
        print("🎯 运行端到端测试...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/e2e/",
            "-v",
            "--tb=short",
            "--junit-xml=test-results/e2e-tests.xml",
            "-m", "e2e"
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        duration = time.time() - start_time
        
        return {
            "name": "端到端测试",
            "success": result.returncode == 0,
            "duration": duration,
            "output": result.stdout,
            "error": result.stderr
        }
    
    def run_performance_tests(self, users: int = 10, spawn_rate: int = 2, run_time: str = "60s") -> Dict[str, Any]:
        """运行性能测试"""
        print("⚡ 运行性能测试...")
        
        # 检查Locust是否安装
        try:
            subprocess.run(["locust", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {
                "name": "性能测试",
                "success": False,
                "duration": 0,
                "output": "",
                "error": "Locust未安装，请运行: pip install locust"
            }
        
        cmd = [
            "locust",
            "-f", "tests/performance/locustfile.py",
            "--host", "http://localhost:8000",
            "--users", str(users),
            "--spawn-rate", str(spawn_rate),
            "--run-time", run_time,
            "--headless",
            "--html", "test-results/performance-report.html"
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        duration = time.time() - start_time
        
        return {
            "name": "性能测试",
            "success": result.returncode == 0,
            "duration": duration,
            "output": result.stdout,
            "error": result.stderr
        }
    
    def run_security_tests(self) -> Dict[str, Any]:
        """运行安全测试"""
        print("🔒 运行安全测试...")
        
        # 使用bandit进行安全扫描
        cmd = [
            "python", "-m", "bandit",
            "-r", "app/",
            "-f", "json",
            "-o", "test-results/security-report.json"
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        duration = time.time() - start_time
        
        # bandit返回非零状态码表示发现问题，但不一定是错误
        success = result.returncode in [0, 1]
        
        return {
            "name": "安全测试",
            "success": success,
            "duration": duration,
            "output": result.stdout,
            "error": result.stderr if result.returncode > 1 else ""
        }
    
    def run_code_quality_tests(self) -> Dict[str, Any]:
        """运行代码质量测试"""
        print("📊 运行代码质量测试...")
        
        results = []
        
        # Flake8 代码风格检查
        flake8_cmd = ["python", "-m", "flake8", "app/", "--output-file=test-results/flake8-report.txt"]
        flake8_result = subprocess.run(flake8_cmd, cwd=self.project_root, capture_output=True, text=True)
        
        # MyPy 类型检查
        mypy_cmd = ["python", "-m", "mypy", "app/", "--ignore-missing-imports"]
        mypy_result = subprocess.run(mypy_cmd, cwd=self.project_root, capture_output=True, text=True)
        
        success = flake8_result.returncode == 0 and mypy_result.returncode == 0
        
        return {
            "name": "代码质量测试",
            "success": success,
            "duration": 0,
            "output": f"Flake8: {flake8_result.stdout}\nMyPy: {mypy_result.stdout}",
            "error": f"Flake8: {flake8_result.stderr}\nMyPy: {mypy_result.stderr}"
        }
    
    def setup_test_environment(self):
        """设置测试环境"""
        print("🔧 设置测试环境...")
        
        # 创建测试结果目录
        os.makedirs("test-results", exist_ok=True)
        
        # 设置环境变量
        os.environ["TESTING"] = "1"
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
        
        # 安装测试依赖
        subprocess.run([
            "pip", "install", "-e", ".",
            "pytest", "pytest-asyncio", "pytest-cov",
            "httpx", "bandit", "flake8", "mypy"
        ], check=True)
    
    def cleanup_test_environment(self):
        """清理测试环境"""
        print("🧹 清理测试环境...")
        
        # 删除测试数据库
        test_db_files = ["test.db", "test.db-shm", "test.db-wal"]
        for file in test_db_files:
            if os.path.exists(file):
                os.remove(file)
    
    def generate_report(self, results: List[Dict[str, Any]]):
        """生成测试报告"""
        print("\n" + "="*60)
        print("📋 测试报告")
        print("="*60)
        
        total_duration = sum(r["duration"] for r in results)
        passed_tests = sum(1 for r in results if r["success"])
        total_tests = len(results)
        
        print(f"总测试套件: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {total_tests - passed_tests}")
        print(f"总耗时: {total_duration:.2f}秒")
        print()
        
        for result in results:
            status = "✅ 通过" if result["success"] else "❌ 失败"
            print(f"{status} {result['name']} ({result['duration']:.2f}s)")
            
            if not result["success"] and result["error"]:
                print(f"   错误: {result['error'][:200]}...")
        
        print("\n" + "="*60)
        
        # 生成HTML报告
        self.generate_html_report(results)
    
    def generate_html_report(self, results: List[Dict[str, Any]]):
        """生成HTML测试报告"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>EmbedAI 测试报告</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .test-result {{ margin: 10px 0; padding: 15px; border-radius: 5px; }}
                .success {{ background: #d4edda; border: 1px solid #c3e6cb; }}
                .failure {{ background: #f8d7da; border: 1px solid #f5c6cb; }}
                .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
                .metric {{ text-align: center; padding: 15px; background: #e9ecef; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>EmbedAI 系统测试报告</h1>
                <p>生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="summary">
                <div class="metric">
                    <h3>{len(results)}</h3>
                    <p>总测试套件</p>
                </div>
                <div class="metric">
                    <h3>{sum(1 for r in results if r['success'])}</h3>
                    <p>通过</p>
                </div>
                <div class="metric">
                    <h3>{sum(1 for r in results if not r['success'])}</h3>
                    <p>失败</p>
                </div>
                <div class="metric">
                    <h3>{sum(r['duration'] for r in results):.1f}s</h3>
                    <p>总耗时</p>
                </div>
            </div>
            
            <h2>详细结果</h2>
        """
        
        for result in results:
            status_class = "success" if result["success"] else "failure"
            status_text = "通过" if result["success"] else "失败"
            
            html_content += f"""
            <div class="test-result {status_class}">
                <h3>{result['name']} - {status_text} ({result['duration']:.2f}s)</h3>
                <details>
                    <summary>查看详情</summary>
                    <pre>{result['output'][:1000]}...</pre>
                    {f'<p><strong>错误:</strong> {result["error"][:500]}...</p>' if result['error'] else ''}
                </details>
            </div>
            """
        
        html_content += """
        </body>
        </html>
        """
        
        with open("test-results/test-report.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"📄 HTML报告已生成: test-results/test-report.html")
    
    def run_all_tests(self, include_performance: bool = False, performance_config: Dict = None):
        """运行所有测试"""
        print("🚀 开始完整系统测试...")
        
        # 设置测试环境
        self.setup_test_environment()
        
        try:
            results = []
            
            # 运行各种测试
            results.append(self.run_unit_tests())
            results.append(self.run_integration_tests())
            results.append(self.run_e2e_tests())
            results.append(self.run_security_tests())
            results.append(self.run_code_quality_tests())
            
            if include_performance:
                perf_config = performance_config or {}
                results.append(self.run_performance_tests(**perf_config))
            
            # 生成报告
            self.generate_report(results)
            
            # 返回总体结果
            all_passed = all(r["success"] for r in results)
            return all_passed
            
        finally:
            # 清理测试环境
            self.cleanup_test_environment()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="EmbedAI 系统测试运行器")
    parser.add_argument("--unit", action="store_true", help="只运行单元测试")
    parser.add_argument("--integration", action="store_true", help="只运行集成测试")
    parser.add_argument("--e2e", action="store_true", help="只运行端到端测试")
    parser.add_argument("--performance", action="store_true", help="包含性能测试")
    parser.add_argument("--users", type=int, default=10, help="性能测试用户数")
    parser.add_argument("--spawn-rate", type=int, default=2, help="性能测试生成速率")
    parser.add_argument("--run-time", default="60s", help="性能测试运行时间")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.unit:
        result = runner.run_unit_tests()
        print(f"单元测试结果: {'通过' if result['success'] else '失败'}")
    elif args.integration:
        result = runner.run_integration_tests()
        print(f"集成测试结果: {'通过' if result['success'] else '失败'}")
    elif args.e2e:
        result = runner.run_e2e_tests()
        print(f"端到端测试结果: {'通过' if result['success'] else '失败'}")
    else:
        # 运行所有测试
        performance_config = {
            "users": args.users,
            "spawn_rate": args.spawn_rate,
            "run_time": args.run_time
        } if args.performance else None
        
        success = runner.run_all_tests(
            include_performance=args.performance,
            performance_config=performance_config
        )
        
        exit_code = 0 if success else 1
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
