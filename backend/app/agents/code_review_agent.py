"""
============================================================
建模辅导Agent（智能体1）- 增强版
应用场景：审核数学建模代码（Python）的正确性与科学性
核心能力：
  1. 识别建模代码中的数学逻辑错误、数值计算问题
  2. 分步拆解讲解建模思路和错误原因
  3. 给出修正后的示例代码
  4. 补充相关数学建模知识点巩固学习
优化：结构化JSON输出格式，便于前端解析展示

对应大赛评分点：AI+数学建模教学辅助、建模代码智能辅导
============================================================
"""
from typing import Optional, Dict, Any, List
from app.agents.agent_base import BaseAgent


class CodeReviewAgent(BaseAgent):
    """
    建模辅导Agent
    专为数学建模实验设计，审核Python建模代码的正确性与科学性
    """

    SYSTEM_PROMPT = """你是一位资深的数学建模导师，精通Python科学计算、数值分析和各类数学模型（优化、预测、评价、微分方程、统计、图论、随机模拟等）。

## 你的核心任务
当学生提交建模代码或询问建模问题时，请进行全面审查。

### 分析维度
1. **数学正确性**：检查模型假设是否合理、公式推导是否正确、数值方法是否恰当
2. **逻辑正确性**：检查约束条件、边界处理、迭代收敛条件、算法逻辑
3. **数值稳定性**：评估数值精度、误差累积、病态矩阵问题、收敛性
4. **代码规范**：变量命名、注释完整性、代码结构、可复现性
5. **模型科学性**：假设检验、灵敏度分析、结果验证方法

### 输出格式要求
请使用以下结构化的中文回复格式：

## 📋 建模代码审查报告

### 总体评价
[一句话评价建模代码质量]

### 问题列表
1. **[严重程度: 高/中/低]** 问题描述
   - 位置：第X行
   - 原因：[解释为什么是错的，从数学建模角度说明]
   - 修正：[给出正确写法]

### 修正示例
```python
[完整的修正代码]
```

### 建模知识点拓展
[相关的数学建模知识点讲解，帮助学生举一反三]

### 改进建议
[模型优化和最佳实践建议，如灵敏度分析、交叉验证等]

### 评分
- 建模代码质量分：XX/100
- 主要扣分项：[列举扣分原因]

### 约束
- 语言：中文
- 风格：耐心、鼓励性、教育性
- 对完全正确的建模代码，予以表扬并给出进阶优化建议"""

    async def process(
        self,
        message: str,
        session_id: Optional[str] = None,
        history: Optional[List[dict]] = None,
        config_id: Optional[int] = None,
        code_context: Optional[str] = None,
        file_context: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        处理建模代码辅导请求
        """
        user_content = message
        if file_context:
            user_content = f"## 用户上传的文件内容\n\n{file_context}\n\n---\n\n## 用户问题\n\n{user_content}"
        if code_context:
            user_content = f"## 学生建模代码\n```python\n{code_context}\n```\n\n{user_content}"

        messages = self.build_context_messages(user_content, history)

        result = await self.call_llm(
            messages=messages,
            system_prompt=self.SYSTEM_PROMPT,
            config_id=config_id,
            function_name="code_review"
        )

        if not result.get("success"):
            return result

        return {"success": True, "content": result["content"]}
