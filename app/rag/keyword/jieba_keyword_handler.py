"""基于jieba的关键词提取器"""
import re
import jieba
import jieba.analyse
from typing import List, Optional, Set


class JiebaKeywordHandler:
    """基于jieba的关键词提取器"""
    
    def __init__(self):
        """初始化"""
        # 确保jieba已加载
        jieba.initialize()
    
    def extract_keywords(self, text: str, stopwords: Optional[Set[str]] = None) -> List[str]:
        """
        从文本中提取关键词
        
        Args:
            text: 待提取关键词的文本
            stopwords: 停用词集合
            
        Returns:
            关键词列表
        """
        if not text:
            return []
        
        # 清理文本
        text = self._clean_text(text)
        if not text:
            return []
        
        # 提取关键词
        keywords = []
        for word in jieba.cut(text):
            if stopwords and word in stopwords:
                continue
            if len(word.strip()) > 1:  # 过滤单字词
                keywords.append(word.lower())
        
        return keywords
    
    def extract_topk_keywords(self, text: str, topk: int = 10, stopwords: Optional[Set[str]] = None) -> List[str]:
        """
        从文本中提取前k个关键词
        
        Args:
            text: 待提取关键词的文本
            topk: 提取的关键词数量
            stopwords: 停用词集合
            
        Returns:
            关键词列表
        """
        if not text:
            return []
        
        # 清理文本
        text = self._clean_text(text)
        if not text:
            return []
        
        # 提取关键词
        keywords = jieba.analyse.extract_tags(text, topK=topk)
        
        # 过滤停用词
        if stopwords:
            keywords = [word for word in keywords if word not in stopwords]
        
        return keywords
    
    def _clean_text(self, text: str) -> str:
        """
        清理文本
        
        Args:
            text: 待清理的文本
            
        Returns:
            清理后的文本
        """
        # 移除URL
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # 移除HTML标签
        text = re.sub(r'<.*?>', '', text)
        
        # 移除多余空白字符
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text 