"""LoadSkill 工具 - 加载技能内容。"""

from typing import Any

from .base import BaseTool, ToolMetadata


class LoadSkillTool(BaseTool):
    """LoadSkill 工具 - 按需加载技能的完整内容。

    配合 SkillManager 使用，实现两层加载模式：
    1. Layer 1: 元数据在 system prompt
    2. Layer 2: 通过此工具按需加载完整内容
    """

    name = "load_skill"
    description = "Load a skill's full content for detailed guidance"
    metadata = ToolMetadata(category="skills", tags=["skill", "load"])

    def __init__(self, skill_manager: Any = None):
        """初始化 LoadSkill 工具。

        Args:
            skill_manager: SkillManager 实例
        """
        self.skill_manager = skill_manager

    def set_skill_manager(self, manager: Any) -> None:
        """设置 SkillManager。

        Args:
            manager: SkillManager 实例
        """
        self.skill_manager = manager

    def execute(self, name: str, **kwargs: Any) -> dict[str, Any]:
        """执行技能加载。

        Args:
            name: 技能名称
            **kwargs: 其他参数

        Returns:
            加载结果
        """
        if self.skill_manager is None:
            return {
                "success": False,
                "error": "SkillManager not configured",
            }

        try:
            content = self.skill_manager.load_skill(name)
            return {
                "success": True,
                "name": name,
                "content": content,
            }
        except KeyError:
            return {
                "success": False,
                "error": f"Skill not found: {name}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def get_parameters_schema(self) -> dict:
        """获取参数 schema。"""
        # Get available skills if skill_manager is set
        available_skills = []
        if self.skill_manager and hasattr(self.skill_manager, "loader"):
            available_skills = self.skill_manager.loader.list_skills()

        description = "Name of the skill to load"
        if available_skills:
            description += f". Available: {', '.join(available_skills)}"

        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": description,
                },
            },
            "required": ["name"],
        }

    def list_available_skills(self) -> list[str]:
        """列出可用的技能。

        Returns:
            技能名称列表
        """
        if self.skill_manager and hasattr(self.skill_manager, "loader"):
            return self.skill_manager.loader.list_skills()
        return []