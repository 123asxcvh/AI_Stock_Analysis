"""
提示词管理器 - 管理AI分析相关的提示词
"""

from typing import Dict, Tuple

class PromptManager:
    """
    提示词管理器
    负责管理和生成各种分析提示词
    """

    def __init__(self):
        """初始化提示词管理器"""

    def get_stock_prompt(self, data_type: str, stock_code: str = None) -> Tuple[str, str]:
        """获取个股分析提示词"""
        from src.ai_analysis.prompts.stock_user_prompts import STOCK_PROMPTS
        prompt_config = STOCK_PROMPTS.get(data_type, {})
        
        system_prompt = prompt_config.get("stock_system_prompt", "corporate_strategist")
        user_prompt = prompt_config.get("stock_user_prompt", f"请对股票{stock_code}的{data_type}数据进行专业分析。")
        
        if stock_code and user_prompt:
            user_prompt = user_prompt.replace("{stock_code}", stock_code)
        
        return system_prompt, user_prompt

    def get_comprehensive_prompt(self, stock_code: str) -> Tuple[str, str]:
        """
        获取综合分析提示词

        Args:
            stock_code: 股票代码

        Returns:
            (system_prompt, user_prompt) 元组
        """
        return self.get_stock_prompt("comprehensive_analysis", stock_code)

    def get_comprehensive_market_prompt(self) -> Tuple[str, str]:
        """
        获取综合市场分析提示词

        Returns:
            (system_prompt, user_prompt) 元组
        """
        market_prompt_dict = self.get_market_prompt("market_comprehensive_analysis")
        return (
            market_prompt_dict.get("market_system_prompt", "market_strategist"),
            market_prompt_dict.get("market_user_prompt", "请对综合市场数据进行专业分析。")
        )


    def get_market_prompt(self, data_type: str) -> Dict[str, str]:
        """
        获取市场数据分析提示词

        Args:
            data_type: 数据类型

        Returns:
            包含system_prompt和user_prompt的字典
        """
        from src.ai_analysis.prompts.market_user_prompts import MARKET_PROMPTS

        prompt_config = MARKET_PROMPTS.get(data_type, {})
        market_system_prompt = prompt_config.get("market_system_prompt", "market_strategist")
        market_user_prompt = prompt_config.get("market_user_prompt", "请对以下市场数据进行专业分析。")

        return {
            "market_system_prompt": market_system_prompt,
            "market_user_prompt": market_user_prompt
        }

    def get_system_prompt(self, role: str) -> str:
        """获取系统角色提示词"""
        from src.ai_analysis.prompts.stock_system_prompts import get_system_prompt as get_sys_prompt
        return get_sys_prompt(role)

    def get_market_system_prompt(self, role: str) -> str:
        """获取市场分析系统角色提示词"""
        from src.ai_analysis.prompts.market_system_prompts import get_market_system_prompt as get_market_sys_prompt
        return get_market_sys_prompt(role)
