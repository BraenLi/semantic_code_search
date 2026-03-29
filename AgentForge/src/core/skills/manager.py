"""技能管理器 - 管理技能的加载和使用。"""

from typing import Any

from .loader import SkillLoader


class SkillManager:
    """技能管理器 - 管理技能的加载和使用。

    使用两层加载模式:
    1. 初始化时加载所有技能的元数据
    2. 按需加载技能的完整内容

    Attributes:
        loader: SkillLoader 实例
        loaded_skills: 已加载完整内容的技能
    """

    def __init__(self, skills_dir: str | None = None):
        """初始化技能管理器。

        Args:
            skills_dir: 技能目录
        """
        self.loader = SkillLoader(skills_dir)
        self.loaded_skills: dict[str, str] = {}

    def get_system_prompt(self) -> str:
        """获取用于 system prompt 的技能描述。

        Returns:
            技能描述字符串
        """
        return self.loader.get_descriptions()

    def load_skill(self, name: str) -> str:
        """加载技能的完整内容。

        Args:
            name: 技能名称

        Returns:
            技能完整内容
        """
        if name not in self.loaded_skills:
            content = self.loader.get_content(name)
            self.loaded_skills[name] = content
        return self.loaded_skills[name]

    def is_loaded(self, name: str) -> bool:
        """检查技能是否已加载。

        Args:
            name: 技能名称

        Returns:
            是否已加载
        """
        return name in self.loaded_skills

    def unload_skill(self, name: str) -> None:
        """卸载技能。

        Args:
            name: 技能名称
        """
        if name in self.loaded_skills:
            del self.loaded_skills[name]

    def unload_all(self) -> None:
        """卸载所有技能。"""
        self.loaded_skills.clear()

    def get_loaded_contents(self) -> dict[str, str]:
        """获取所有已加载技能的内容。

        Returns:
            {技能名：内容} 字典
        """
        return self.loaded_skills.copy()

    def to_tool_definition(self) -> dict:
        """生成 load_skill 工具的定义。

        Returns:
            OpenAI tool 格式的工具定义
        """
        return {
            "type": "function",
            "function": {
                "name": "load_skill",
                "description": "Load a skill's full content for detailed guidance",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the skill to load",
                        }
                    },
                    "required": ["name"],
                },
            },
        }

    def execute_load_skill(self, name: str) -> dict[str, Any]:
        """执行 load_skill 工具。

        Args:
            name: 技能名称

        Returns:
            工具执行结果
        """
        try:
            content = self.load_skill(name)
            return {"success": True, "content": content}
        except KeyError as e:
            return {"success": False, "error": str(e)}
