# conductor Skill

## 触发条件
当用户提供材料或网站时触发。

## 输入
- 参考材料（文档/示例/论文）
- 或网站 URL

## 处理流程
1. 解析材料/网站提取函数体信息
2. 根据函数体识别参数规范（DataMapper）
3. 提取美学映射规则（存入独立文件）
4. 创建并存储 handler

## 输出
- FunctionBody 定义
- 参数规范（DataMapper）
- AestheticMapping 配置（独立文件）
