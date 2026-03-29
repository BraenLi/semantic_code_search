"""技能加载器 - 两层加载模式。

设计原则:
1. Layer 1: 元数据在 system prompt (短描述)
2. Layer 2: 完整内容按需加载 (通过 tool_result)
"""

import re
from pathlib import Path
from typing import Any


class SkillLoader:
    """技能加载器 - 从 markdown 文件加载技能。

    技能文件格式:
    ---
    name: skill-name
    description: 简短描述，用于 system prompt
    tags: category,optional
    ---

    # Skill Body

    完整的技能说明...
    """

    def __init__(self, skills_dir: str | Path | None = None):
        """初始化技能加载器。

        Args:
            skills_dir: 技能目录，默认为 ./skills
        """
        if skills_dir is None:
            skills_dir = Path(__file__).parent.parent.parent.parent / "skills"
        else:
            skills_dir = Path(skills_dir)

        self.skills_dir = skills_dir
        self.skills: dict[str, dict[str, Any]] = {}
        self._load_all()

    def _load_all(self) -> None:
        """加载所有技能。"""
        if not self.skills_dir.exists():
            self.skills_dir.mkdir(parents=True, exist_ok=True)
            return

        for file_path in self.skills_dir.glob("*.md"):
            try:
                skill_data = self._parse_skill(file_path)
                self.skills[skill_data["name"]] = skill_data
            except Exception as e:
                print(f"Failed to load skill from {file_path}: {e}")

    def _parse_skill(self, file_path: Path) -> dict[str, Any]:
        """解析技能文件。

        Args:
            file_path: 技能文件路径

        Returns:
            技能数据字典

        Raises:
            ValueError: 文件格式错误
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 解析 frontmatter
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
        if not match:
            raise ValueError(f"Invalid skill format: {file_path}")

        frontmatter = match.group(1)
        body = match.group(2).strip()

        # 解析元数据
        meta = {}
        for line in frontmatter.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                meta[key.strip()] = value.strip()

        if "name" not in meta:
            raise ValueError(f"Missing 'name' in skill frontmatter: {file_path}")

        return {
            "name": meta.get("name"),
            "description": meta.get("description", ""),
            "tags": meta.get("tags", "").split(","),
            "path": str(file_path),
            "body": body,
            "full_content": f"---\n{frontmatter}\n---\n\n{body}",
        }

    def get_descriptions(self) -> str:
        """Layer 1: 获取所有技能的短描述，用于 system prompt。

        Returns:
            技能描述字符串
        """
        if not self.skills:
            return "No skills available."

        lines = ["Available skills:"]
        for name, skill in self.skills.items():
            desc = skill.get("description", "No description")
            tags = ", ".join(skill.get("tags", []))
            lines.append(f"- {name}: {desc} (tags: {tags})")

        return "\n".join(lines)

    def get_content(self, name: str) -> str:
        """Layer 2: 获取技能的完整内容。

        Args:
            name: 技能名称

        Returns:
            技能完整内容

        Raises:
            KeyError: 技能不存在
        """
        if name not in self.skills:
            raise KeyError(f"Skill not found: {name}")

        return self.skills[name]["full_content"]

    def get_skill(self, name: str) -> dict[str, Any]:
        """获取技能数据。

        Args:
            name: 技能名称

        Returns:
            技能数据字典

        Raises:
            KeyError: 技能不存在
        """
        if name not in self.skills:
            raise KeyError(f"Skill not found: {name}")

        return self.skills[name]

    def list_skills(self) -> list[str]:
        """获取所有技能名称。

        Returns:
            技能名称列表
        """
        return list(self.skills.keys())

    def search_skills(self, keyword: str) -> list[str]:
        """搜索技能。

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的技能名称列表
        """
        matched = []
        for name, skill in self.skills.items():
            if (
                keyword.lower() in name.lower()
                or keyword.lower() in skill.get("description", "").lower()
                or any(keyword.lower() in tag.lower() for tag in skill.get("tags", []))
            ):
                matched.append(name)
        return matched

    def reload(self) -> None:
        """重新加载所有技能。"""
        self.skills.clear()
        self._load_all()
