import json
from pathlib import Path
from typing import Dict, Any, Optional

class TestState:
    """测试状态管理器，用于保存测试进度和数据"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.state_file = Path(f"tests/states/{test_name}.json")
        self.state: Dict[str, Any] = self._load_state()
        
    def _load_state(self) -> Dict[str, Any]:
        """加载测试状态"""
        if not self.state_file.exists():
            return {
                "current_step": 0,
                "data": {},
                "completed_steps": []
            }
            
        with open(self.state_file, "r", encoding="utf-8") as f:
            return json.load(f)
            
    def save(self):
        """保存测试状态"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
            
    def get_data(self, key: str) -> Optional[Any]:
        """获取测试数据"""
        return self.state["data"].get(key)
        
    def set_data(self, key: str, value: Any):
        """设置测试数据"""
        self.state["data"][key] = value
        self.save()
        
    def step_completed(self, step_name: str) -> bool:
        """检查步骤是否已完成"""
        return step_name in self.state["completed_steps"]
        
    def mark_step_completed(self, step_name: str):
        """标记步骤为已完成"""
        if step_name not in self.state["completed_steps"]:
            self.state["completed_steps"].append(step_name)
            self.save()
            
    def reset(self):
        """重置测试状态"""
        self.state = {
            "current_step": 0,
            "data": {},
            "completed_steps": []
        }
        self.save()

    def get_step_data(self, key: str) -> Optional[Any]:
        """获取测试步骤数据"""
        return self.get_data(key)
        
    def save_step_data(self, key: str, value: Any):
        """保存测试步骤数据"""
        self.set_data(key, value) 