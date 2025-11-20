#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
报告保存模块
处理智能体消息和生成报告 - 只保存每个agent的最后一个输出
"""

import os
from datetime import datetime
from typing import AsyncGenerator, Dict, Any
import logging
from config import AGENT_NAMES, AGENT_ROLES


class ReportSaver:
    """报告保存器 - 只保存每个agent的最后一个输出"""

    def __init__(self, output_dir: str = None):
        """
        初始化报告保存器

        Args:
            output_dir: 输出目录，默认为当前目录下的 reports 文件夹
        """
        # 使用相对路径作为默认目录
        if output_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.output_dir = os.path.join(current_dir, "reports")
        else:
            self.output_dir = output_dir

        self.agent_results = {}
        self.user_request = ""  # 保存用户原始请求
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_agent = None

        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # 确保输出目录存在
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            self.logger.info(f"报告输出目录: {self.output_dir}")
        except Exception as e:
            self.logger.error(f"创建输出目录失败: {e}")
            raise

    def set_user_request(self, user_request: str):
        """
        设置用户原始请求信息

        Args:
            user_request: 用户的原始请求内容
        """
        self.user_request = user_request

    async def process_stream(self, stream: AsyncGenerator, stock_code: str = None) -> Dict[str, str]:
        """
        处理流式消息并收集智能体结果
        只保存每个agent的最后一个输出，替换之前的所有内容

        Args:
            stream: 消息流
            stock_code: 股票代码

        Returns:
            Dict[str, str]: 智能体名称到最后结果的映射
        """
        try:
            async for message in stream:
                await self._process_message(message)

            # 保存所有智能体的最后一个结果
            if self.agent_results:
                self.logger.info("正在保存智能体最终结果...")
                await self._save_agent_results(stock_code)
            else:
                self.logger.warning("没有收集到任何智能体结果")

            return self.agent_results

        except Exception as e:
            self.logger.error(f"处理消息流时发生错误: {e}")
            return self.agent_results

    async def _process_message(self, message: Any):
        """
        处理单个消息并保存为该agent的最终结果

        Args:
            message: 要处理的消息对象
        """
        try:
            # 检查消息是否有 source 和 content 属性
            if not hasattr(message, 'source') or not hasattr(message, 'content'):
                return

            source = message.source
            content = message.content

            # 跳过空内容
            if not content:
                return

            # 处理内容格式
            if isinstance(content, list):
                content_str = '\n'.join(str(item) for item in content if str(item).strip())
            else:
                content_str = str(content)

            if not content_str.strip():
                return

            # 显示消息
            print(f"\n---------- {source} ----------")
            print(content_str)
            print("-" * 60)

            # 更新当前 agent
            self.current_agent = source

            # 【关键修改】只保存每个agent的最后一个输出，替换之前的内容
            self.agent_results[source] = content_str
            self.logger.debug(f"已更新 {source} 的最终结果，长度: {len(content_str)}")

        except Exception as e:
            self.logger.error(f"处理消息时出错: {e}")
            # 不重新抛出异常，继续处理其他消息

    async def _save_agent_results(self, stock_code: str = None) -> str:
        """
        保存智能体最终结果到Markdown文件
        用户请求信息放在报告开头

        Args:
            stock_code: 股票代码

        Returns:
            str: 保存的文件路径，如果保存失败返回空字符串
        """
        try:
            # 生成文件名
            if stock_code:
                filename = f"股票分析报告_{stock_code}_{self.timestamp}.md"
            else:
                filename = f"分析报告_{self.timestamp}.md"

            filepath = os.path.join(self.output_dir, filename)

            # 智能体显示顺序 - 直接从 config.py 导入，确保一致性
            agent_display_order = dict(zip(AGENT_NAMES, AGENT_ROLES))

            # 按优先级排序智能体
            ordered_agents = []
            # 先添加已知顺序的智能体
            for agent_key in agent_display_order.keys():
                if agent_key in self.agent_results:
                    ordered_agents.append(agent_key)

            # 再添加其他智能体
            for agent_key in self.agent_results.keys():
                if agent_key not in agent_display_order:
                    ordered_agents.append(agent_key)

            with open(filepath, 'w', encoding='utf-8') as f:
                # 【修改1】首先写入用户请求信息
                f.write(f"# 股票分析报告\n\n")
                f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                if stock_code:
                    f.write(f"**股票代码**: {stock_code}\n\n")

                # 写入用户原始请求
                if self.user_request:
                    f.write("## 用户请求\n\n")
                    f.write(f"```\n{self.user_request}\n```\n\n")

                f.write("---\n\n")

                # 写入各智能体的最终结果
                f.write("## 智能体分析结果\n\n")
                f.write(f"**智能体数量**: {len(self.agent_results)} 个\n\n")
                f.write("---\n\n")

                for agent_name in ordered_agents:
                    display_name = agent_display_order.get(agent_name, agent_name)
                    f.write(f"### {display_name} ({agent_name})\n\n")
                    f.write(self.agent_results[agent_name])
                    f.write("\n\n---\n\n")

                # 写入总结
                f.write(f"## 分析总结\n\n")
                f.write(f"本次分析共涉及 {len(self.agent_results)} 个智能体，")
                f.write("每个智能体只保留最终输出结果，避免重复信息堆积。\n")
                f.write(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}。\n\n")

            self.logger.info(f"分析报告已保存到: {filepath}")
            return filepath

        except Exception as e:
            self.logger.error(f"保存报告时出错: {e}")
            return ""

    def get_agent_count(self) -> int:
        """获取已收集的智能体结果数量"""
        return len(self.agent_results)

    def get_agent_names(self) -> list:
        """获取已收集的智能体名称列表"""
        return list(self.agent_results.keys())

    def clear_results(self):
        """清空已收集的智能体结果"""
        self.agent_results.clear()
        self.user_request = ""
        self.current_agent = None
        self.logger.info("已清空智能体结果和用户请求")


# 便捷函数
def create_final_report_saver(output_dir: str = None) -> ReportSaver:
    """
    创建只保存最终结果的报告保存器
    
    Args:
        output_dir: 输出目录
        
    Returns:
        ReportSaver: 配置好的报告保存器
    """
    return ReportSaver(output_dir)