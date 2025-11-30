"""
增强版LLM响应解析器
"""
import json
import re
from typing import Optional, Dict, Any, Tuple

from ..core.exceptions import LLMConnectionError
from ..utils.logger import get_logger


class EnhancedResponseParser:
    """增强版响应解析器"""
    
    def __init__(self):
        """初始化解析器"""
        self.logger = get_logger()
    
    def parse_response(self, response: str) -> Dict[str, Any]:
        """
        解析LLM响应
        
        Args:
            response: LLM响应内容
            
        Returns:
            Dict: 解析后的结构化数据
            
        Raises:
            LLMConnectionError: 解析失败
        """
        try:
            # 提取JSON内容
            json_str = self._extract_json(response)
            data = json.loads(json_str)
            
            # 验证必需字段
            required_fields = ['analysis', 'is_sufficient']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"缺少必需字段: {field}")
            
            # 标准化数据结构
            result = {
                'analysis': data.get('analysis', ''),
                'is_sufficient': bool(data.get('is_sufficient', False)),
                'confidence': float(data.get('confidence', 0.5)),
                'answer': data.get('answer'),
                'reasoning': data.get('reasoning', ''),
                'next_command': None,
            }
            
            # 解析next_command
            if not result['is_sufficient'] and 'next_command' in data and data['next_command']:
                next_cmd = data['next_command']
                if isinstance(next_cmd, dict):
                    result['next_command'] = {
                        'command': next_cmd.get('command', ''),
                        'purpose': next_cmd.get('purpose', ''),
                        'expected_output': next_cmd.get('expected_output', ''),
                    }
                elif isinstance(next_cmd, str):
                    # 如果直接给了命令字符串
                    result['next_command'] = {
                        'command': next_cmd,
                        'purpose': 'LLM建议的命令',
                        'expected_output': '获取更多信息',
                    }
            
            return result
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析失败: {e}")
            self.logger.debug(f"原始响应: {response}")
            
            # 尝试宽松解析
            return self._fallback_parse(response)
        
        except Exception as e:
            self.logger.error(f"响应解析失败: {e}")
            raise LLMConnectionError(f"无法解析LLM响应: {e}")
    
    def _extract_json(self, text: str) -> str:
        """
        从文本中提取JSON内容
        
        Args:
            text: 包含JSON的文本
            
        Returns:
            str: JSON字符串
        """
        text = text.strip()
        
        # 尝试直接解析
        if text.startswith('{') and text.endswith('}'):
            return text
        
        # 查找JSON代码块
        if '```json' in text:
            start = text.find('```json') + 7
            end = text.find('```', start)
            if end != -1:
                return text[start:end].strip()
        
        if '```' in text:
            start = text.find('```') + 3
            end = text.find('```', start)
            if end != -1:
                potential_json = text[start:end].strip()
                if potential_json.startswith('{'):
                    return potential_json
        
        # 查找JSON对象
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            return text[start:end + 1]
        
        # 无法提取，返回原始文本
        return text
    
    def _fallback_parse(self, response: str) -> Dict[str, Any]:
        """
        宽松解析响应（当JSON解析失败时）
        
        Args:
            response: 响应文本
            
        Returns:
            Dict: 解析结果
        """
        self.logger.warning("使用宽松解析模式")
        
        # 判断是否充足
        sufficient_keywords = ['足够', '充足', 'sufficient', '可以回答', '已经找到']
        insufficient_keywords = ['不足', '不够', 'insufficient', '需要更多', '继续']
        
        is_sufficient = any(kw in response.lower() for kw in sufficient_keywords)
        is_insufficient = any(kw in response.lower() for kw in insufficient_keywords)
        
        # 如果明确说不足，则设为False
        if is_insufficient:
            is_sufficient = False
        
        # 尝试提取命令
        next_command = None
        if not is_sufficient:
            # 查找可能的命令（在代码块或引号中）
            command_patterns = [
                r'```bash\n(.+?)\n```',
                r'```\n(.+?)\n```',
                r'`(.+?)`',
                r'"(.+?)"',
            ]
            
            for pattern in command_patterns:
                match = re.search(pattern, response, re.DOTALL)
                if match:
                    potential_cmd = match.group(1).strip()
                    # 简单验证是否像命令
                    if any(cmd in potential_cmd for cmd in ['grep', 'find', 'cat', 'ls']):
                        next_command = {
                            'command': potential_cmd,
                            'purpose': '从响应中提取的命令',
                            'expected_output': '获取信息',
                        }
                        break
        
        return {
            'analysis': response[:500],  # 取前500字符作为分析
            'is_sufficient': is_sufficient,
            'confidence': 0.5,
            'answer': response if is_sufficient else None,
            'reasoning': '宽松解析模式',
            'next_command': next_command,
        }
    
    def validate_command_safety(self, command: str) -> Tuple[bool, str]:
        """
        快速验证命令安全性
        
        Args:
            command: 命令字符串
            
        Returns:
            Tuple[bool, str]: (是否安全, 原因)
        """
        if not command:
            return False, "命令为空"
        
        # 危险关键词 - 使用单词边界匹配
        import re
        dangerous = ['rm', 'sudo', 'chmod', 'wget', 'curl', 'bash', 'sh', 'nc', 'netcat']
        for danger in dangerous:
            # 使用单词边界匹配，避免误判（如 'nc' 匹配到 'include'）
            pattern = r'\b' + re.escape(danger) + r'\b'
            if re.search(pattern, command.lower()):
                return False, f"包含危险关键词: {danger}"
        
        # 危险符号
        if any(char in command for char in ['>', '<', '&', ';']):
            return False, "包含危险符号"
        
        return True, "初步检查通过"
