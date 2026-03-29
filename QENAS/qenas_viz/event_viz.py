"""事件时间线可视化.

提供事件时间线、事件影响分布、事件类型统计等可视化功能.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from collections import defaultdict

from qenas_data.feeders.base import EventData, EventType, EventImpact


# 尝试导入 matplotlib
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


# 事件类型颜色映射
EVENT_TYPE_COLORS = {
    EventType.MACRO_ECONOMIC: '#1f77b4',    # 蓝色
    EventType.CENTRAL_BANK: '#1f77b4',
    EventType.ECONOMIC_DATA: '#1f77b4',
    EventType.EARNINGS: '#2ca02c',          # 绿色
    EventType.DIVIDEND: '#2ca02c',
    EventType.MERGER: '#2ca02c',
    EventType.EXECUTIVE_CHANGE: '#2ca02c',
    EventType.GEOPOLITICAL: '#d62728',      # 红色
    EventType.ELECTION: '#d62728',
    EventType.TRADE_POLICY: '#d62728',
    EventType.NATURAL_DISASTER: '#9467bd',  # 紫色
    EventType.REGULATORY: '#ff7f0e',        # 橙色
    EventType.INDUSTRY_NEWS: '#8c564b',     # 棕色
    EventType.MARKET_SENTIMENT: '#e377c2',  # 粉色
}

# 影响级别标记映射
IMPACT_MARKER_MAP = {
    EventImpact.LOW: 'o',
    EventImpact.MEDIUM: 's',
    EventImpact.HIGH: '^',
    EventImpact.CRITICAL: 'D',
}


class EventTimelineVisualizer:
    """
    事件时间线可视化器.

    功能:
    - 绘制事件时间线
    - 事件类型统计
    - 事件影响分布
    - 事件密度热力图
    """

    def __init__(self):
        """初始化可视化器."""
        self.events: List[EventData] = []

    def add_events(self, events: List[EventData]) -> None:
        """
        添加事件.

        Args:
            events: 事件数据列表
        """
        self.events.extend(events)

    def clear_events(self) -> None:
        """清空事件列表."""
        self.events.clear()

    def plot_timeline(
        self,
        events: Optional[List[EventData]] = None,
        title: str = "事件时间线",
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> Optional[Any]:
        """
        绘制事件时间线.

        Args:
            events: 事件列表（不提供则使用内部列表）
            title: 图表标题
            save_path: 保存路径
            show: 是否显示

        Returns:
            figure 对象
        """
        event_list = events or self.events

        if not event_list:
            print("没有事件数据可绘制")
            return None

        if not HAS_MATPLOTLIB:
            return self._text_timeline(event_list, title)

        fig, ax = plt.subplots(figsize=(14, 8))

        # 按时间排序
        sorted_events = sorted(event_list, key=lambda e: e.timestamp)

        # 分组数据
        y_positions: Dict[EventType, float] = {}
        current_y = 0
        type_spacing = 1.5

        # 收集散点数据
        scatter_data: Dict[EventType, Dict] = defaultdict(lambda: {'x': [], 'y': [], 's': [], 'c': []})

        for event in sorted_events:
            event_type = event.event_type

            # 为每种事件类型分配 y 位置
            if event_type not in y_positions:
                y_positions[event_type] = current_y
                current_y += type_spacing

            y = y_positions[event_type]

            # 影响级别决定点的大小
            size_map = {
                EventImpact.LOW: 50,
                EventImpact.MEDIUM: 100,
                EventImpact.HIGH: 200,
                EventImpact.CRITICAL: 400,
            }
            size = size_map.get(event.impact_level, 100)

            # 情感决定颜色深浅
            color = EVENT_TYPE_COLORS.get(event_type, '#666666')

            scatter_data[event_type]['x'].append(event.timestamp)
            scatter_data[event_type]['y'].append(y)
            scatter_data[event_type]['s'].append(size)
            scatter_data[event_type]['c'].append(color)

        # 绘制每种事件类型
        for event_type, data in scatter_data.items():
            ax.scatter(data['x'], data['y'], s=data['s'],
                      c=data['c'], label=event_type.value, alpha=0.7,
                      edgecolors='black', linewidth=0.5)

        # 设置 y 轴标签
        ax.set_yticks(list(y_positions.values()))
        ax.set_yticklabels([et.value.replace('_', ' ').title() for et in y_positions.keys()])

        # 设置 x 轴日期格式
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45, ha='right')

        # 添加图例
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(handles, labels, loc='upper left', bbox_to_anchor=(1, 1))

        ax.set_xlabel('时间')
        ax.set_ylabel('事件类型')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)

        fig.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            return None

        if show:
            plt.show()
            return None

        return fig

    def plot_type_distribution(
        self,
        events: Optional[List[EventData]] = None,
        title: str = "事件类型分布",
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> Optional[Any]:
        """
        绘制事件类型分布饼图.

        Args:
            events: 事件列表
            title: 图表标题
            save_path: 保存路径
            show: 是否显示

        Returns:
            figure 对象
        """
        event_list = events or self.events

        if not event_list:
            print("没有事件数据可绘制")
            return None

        if not HAS_MATPLOTLIB:
            return self._text_type_distribution(event_list, title)

        # 统计每种类型的数量
        type_counts = defaultdict(int)
        for event in event_list:
            type_counts[event.event_type] += 1

        fig, ax = plt.subplots(figsize=(10, 8))

        labels = [t.value.replace('_', ' ').title() for t in type_counts.keys()]
        sizes = list(type_counts.values())
        colors = [EVENT_TYPE_COLORS.get(t, '#666666') for t in type_counts.keys()]

        wedges, texts, autotexts = ax.pie(sizes, colors=colors, autopct='%1.1f%%',
                                          startangle=90, pctdistance=0.85)

        # 添加中心圆，形成甜甜圈图
        centre_circle = plt.Circle((0, 0), 0.70, fc='white')
        ax.add_artist(centre_circle)

        # 设置字体
        for text in texts:
            text.set_fontsize(9)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(8)

        # 添加图例
        ax.legend(wedges, labels, title="事件类型", loc="center left",
                 bbox_to_anchor=(1, 0, 0.5, 1))

        ax.set_title(title)
        fig.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            return None

        if show:
            plt.show()
            return None

        return fig

    def plot_impact_distribution(
        self,
        events: Optional[List[EventData]] = None,
        title: str = "事件影响级别分布",
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> Optional[Any]:
        """
        绘制事件影响级别分布柱状图.

        Args:
            events: 事件列表
            title: 图表标题
            save_path: 保存路径
            show: 是否显示

        Returns:
            figure 对象
        """
        event_list = events or self.events

        if not event_list:
            print("没有事件数据可绘制")
            return None

        if not HAS_MATPLOTLIB:
            return self._text_impact_distribution(event_list, title)

        # 统计每种影响级别数量
        impact_counts = defaultdict(int)
        for event in event_list:
            impact_counts[event.impact_level] += 1

        fig, ax = plt.subplots(figsize=(10, 6))

        impacts = sorted(impact_counts.keys(), key=lambda x: x.value)
        labels = [i.name for i in impacts]
        counts = [impact_counts[i] for i in impacts]
        colors = ['#90EE90', '#FFD700', '#FF6347', '#DC143C']  # 绿->金->红->深红

        bars = ax.bar(labels, counts, color=colors[:len(labels)])

        # 添加数值标签
        for bar, count in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                   str(count), ha='center', va='bottom', fontsize=12)

        ax.set_xlabel('影响级别')
        ax.set_ylabel('事件数量')
        ax.set_title(title)
        ax.grid(True, alpha=0.3, axis='y')

        fig.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            return None

        if show:
            plt.show()
            return None

        return fig

    def plot_sentiment_timeline(
        self,
        events: Optional[List[EventData]] = None,
        title: str = "事件情感变化",
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> Optional[Any]:
        """
        绘制事件情感时间线.

        Args:
            events: 事件列表
            title: 图表标题
            save_path: 保存路径
            show: 是否显示

        Returns:
            figure 对象
        """
        event_list = events or self.events

        if not event_list:
            print("没有事件数据可绘制")
            return None

        if not HAS_MATPLOTLIB:
            return self._text_sentiment_timeline(event_list, title)

        sorted_events = sorted(event_list, key=lambda e: e.timestamp)

        fig, ax = plt.subplots(figsize=(14, 6))

        timestamps = [e.timestamp for e in sorted_events]
        sentiments = [e.sentiment_score for e in sorted_events]
        sizes = [e.impact_level.value * 50 for e in sorted_events]

        # 颜色根据正负情感
        colors = ['#2ca02c' if s > 0 else '#d62728' if s < 0 else '#666666' for s in sentiments]

        ax.scatter(timestamps, sentiments, s=sizes, c=colors, alpha=0.7,
                  edgecolors='black', linewidth=0.5)

        # 添加零线
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45, ha='right')

        ax.set_xlabel('时间')
        ax.set_ylabel('情感分数 (-1 到 +1)')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(-1.1, 1.1)

        fig.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            return None

        if show:
            plt.show()
            return None

        return fig

    def get_event_summary(self, events: Optional[List[EventData]] = None) -> Dict[str, Any]:
        """
        获取事件摘要统计.

        Args:
            events: 事件列表

        Returns:
            摘要统计字典
        """
        event_list = events or self.events

        if not event_list:
            return {}

        type_counts = defaultdict(int)
        impact_counts = defaultdict(int)
        sentiment_sum = 0

        for event in event_list:
            type_counts[event.event_type.value] += 1
            impact_counts[event.impact_level.name] += 1
            sentiment_sum += event.sentiment_score

        return {
            "total_events": len(event_list),
            "type_distribution": dict(type_counts),
            "impact_distribution": dict(impact_counts),
            "avg_sentiment": sentiment_sum / len(event_list) if event_list else 0,
            "date_range": {
                "start": min(e.timestamp for e in event_list),
                "end": max(e.timestamp for e in event_list),
            } if event_list else None,
        }

    def _text_timeline(self, events: List[EventData], title: str) -> str:
        """文本模式时间线."""
        lines = [f"\n{title}", "=" * 60]

        sorted_events = sorted(events, key=lambda e: e.timestamp)

        for event in sorted_events[:20]:  # 限制显示 20 条
            impact_marker = IMPACT_MARKER_MAP.get(event.impact_level, 'o')
            sentiment_icon = '+' if event.sentiment_score > 0 else '-' if event.sentiment_score < 0 else '0'
            lines.append(
                f"  {impact_marker} [{event.timestamp.strftime('%Y-%m-%d %H:%M')}] "
                f"{event.event_type.value}: {event.title[:40]} "
                f"[{sentiment_icon}{abs(event.sentiment_score):.1f}]"
            )

        if len(sorted_events) > 20:
            lines.append(f"  ... 还有 {len(sorted_events) - 20} 条事件")

        return "\n".join(lines)

    def _text_type_distribution(self, events: List[EventData], title: str) -> str:
        """文本模式类型分布."""
        type_counts = defaultdict(int)
        for event in events:
            type_counts[event.event_type.value] += 1

        lines = [f"\n{title}", "=" * 40]
        for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            pct = count / len(events) * 100
            lines.append(f"  {t}: {count} ({pct:.1f}%)")

        return "\n".join(lines)

    def _text_impact_distribution(self, events: List[EventData], title: str) -> str:
        """文本模式影响分布."""
        impact_counts = defaultdict(int)
        for event in events:
            impact_counts[event.impact_level.name] += 1

        lines = [f"\n{title}", "=" * 40]
        for impact, count in sorted(impact_counts.items(), key=lambda x: {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2, 'CRITICAL': 3}.get(x[0], 0)):
            lines.append(f"  {impact}: {count}")

        return "\n".join(lines)

    def _text_sentiment_timeline(self, events: List[EventData], title: str) -> str:
        """文本模式情感时间线."""
        sorted_events = sorted(events, key=lambda e: e.timestamp)

        lines = [f"\n{title}", "=" * 60]
        for event in sorted_events[:20]:
            icon = '🟢' if event.sentiment_score > 0 else '🔴' if event.sentiment_score < 0 else '⚪'
            lines.append(
                f"  {icon} [{event.timestamp.strftime('%m-%d %H:%M')}] "
                f"{event.title[:40]} ({event.sentiment_score:+.2f})"
            )

        return "\n".join(lines)
