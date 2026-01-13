CHAT_MODES = { 0: '日常', 1: '专注', 2: '精深', 3: '沉思', 4: '拓展' }
CHAT_MODE_RAG_MODES = {
    0: None,
    1: 'naive',
    2: 'mix',
    3: 'community',
    4: 'global',
}
CHAT_MODE_DESCRIPTIONS = {
    0: '专属模型的工作日常',
    1: '垂直领域的专业问答',
    2: '领域专家的精研深究',
    3: '基于联想的深入思考',
    4: '发散思维的广泛探索',
}

MAIN_PAGE_STYLES = '''
/* For Webkit-based browsers (Chrome, Edge, Safari) */
::-webkit-scrollbar {
    width: 8px;  /* Width of the vertical scrollbar */
    height: 8px; /* Height of the horizontal scrollbar */
}

::-webkit-scrollbar-track {
    background: transparent; /* Make the track invisible */
}

::-webkit-scrollbar-thumb {
    background-color: #d1d5db; /* Light gray like gray-300 */
    border-radius: 10px;      /* Rounded corners for the thumb */
    border: 2px solid transparent; /* Padding around the thumb */
    background-clip: content-box;
}

::-webkit-scrollbar-thumb:hover {
    background-color: #9ca3af; /* Darker gray , like gray-400 */
}

/* For Firefox */
* {
    scrollbar-width: thin;
    scrollbar-color: #d1d5db transparent; /* thumb and track color */
}

/* Markdown width/overflow constraints */
.chat-md {
    width: 100%;
    max-width: 100%;
    overflow-x: hidden;
    overflow-wrap: anywhere;
}
.chat-md :where(img, svg, video, iframe, canvas) {
    max-width: 100%;
    height: auto;
}
.chat-md :where(pre) { max-width: 100%; overflow-x: auto; white-space: pre; }
.chat-md :where(code) { white-space: pre; }
.chat-md :where(table) {
    display: block;
    width: 100%;
    max-width: 100%;
    table-layout: fixed;
    overflow-x: auto;       /* table scrolls inside markdown, not container */
}
.chat-md :where(th, td) { word-break: break-word; }

/* Ensure the chat column never gets a horizontal scrollbar */
.chat-scroll { overflow-x: hidden; overflow-y: scroll; }

.nicegui-markdown h1 { font-size: 28px; font-weight: 600; }
.nicegui-markdown h2 { font-size: 26px; font-weight: 600; }
.nicegui-markdown h3 { font-size: 24px; font-weight: 600; }
.nicegui-markdown h4 { font-size: 22px; font-weight: 600; }
.nicegui-markdown h5 { font-size: 20px; font-weight: 600; }
.nicegui-markdown h6 { font-size: 18px; font-weight: 600; }
'''

SCROLL_TO_BOTTOM_JS = """
(() => {
    const el = document.getElementById('scrollable-card');
    if (!el) return false;
    return el.scrollTop + el.clientHeight >= el.scrollHeight - 20;
})()
"""

RAG_PROMPT_TEMPLATE = """你是一名知识库问答助手，能够根据提供的相关知识段，准确且简洁地回答用户的问题。

## 任务

现已提供一组与用户问题相关的知识片段，每个片段包含知识内容、文档元数据和相关性分数，相关性分数越高表示与问题越相关。

文档元数据包含文档标题、发布日期、生效/废止时间、文号、发布机构路径、上一版本、上位版本等信息。

请基于这些知识段，结合你的语言理解能力，生成对用户问题的回答。

## 回答要求

请遵循以下要求进行回答：
1. **内容依据**：必须基于上述知识段内容和文档元数据作答，不得编造或引入外部知识。
2. **元数据考量**：回答时务必考虑文档的时效性（生效/废止日期）、版本关系（上位版本、替代版本）和权威性（法令号、发布路径）。
3. **不确定性处理**：若知识不足以回答问题，明确说明"根据提供的资料无法确定"。
4. **版本意识**：若存在多个版本，以最新有效版本为准；若提及被废止文件，需明确标注其已废止。
5. **简洁专业**：回答应准确、简洁、友好，必要时可给出简要背景解释，但不得虚构。

## 知识段

以下是为你检索到的知识段：

{knowledge_segments}

请基于上述知识回答用户的问题。

## 用户问题

以下是用户提出的问题：

{query}

## 请回答：
"""

def create_rag_prompt(
    query: str,
    knowledge_list: list[dict],
    kn_limit: int|None = None,
) -> str:
    """
    Create a prompt for RAG based on the user query and knowledge segments.

    Arguments:
        query: The user query.
        knowledge_list: The list of knowledge segments.
        kn_limit: The maximum number of knowledge segments to include.
    Returns:
        The constructed prompt string.
    """
    knowledge_segments = []
    for idx, item in enumerate(
        knowledge_list[:kn_limit] if kn_limit else knowledge_list
    ):
        content = item["content"].strip()
        score = item["score"]
        metadata = item["metadata"]
        doc_title = metadata["title"]
        doc_sn = metadata["sn"]
        doc_date = metadata["date"]
        doc_valid_from = metadata["valid_from"]
        doc_valid_to = metadata["valid_to"]
        doc_replaces = metadata["replaces"]
        doc_localizes = metadata["localizes"]
        doc_pub_path = metadata["pub_path"]

        knowledge_segments.append(
            f"### 知识段 {idx + 1}\n"
            f"- **内容**: {content}\n"
            f"- **相关性分数**: {score:.4f}\n"
            f"- **文档元数据**\n"
            f"  - **文档标题**: {doc_title}\n"
            f"  - **法令号/文号**: { doc_sn if doc_sn else '无' }\n"
            f"  - **发布日期**: {doc_date.split('T')[0]}\n"
            f"  - **生效日期**: {doc_valid_from.split('T')[0]}\n"
            f"  - **废止日期**: {doc_valid_to.split('T')[0] if doc_valid_to else '未废止'}\n"
            f"  - **上一版本**: {doc_replaces if doc_replaces else '无'}\n"
            f"  - **上位版本**: {doc_localizes if doc_localizes else '无'}\n"
            f"  - **发布机构路径**: {doc_pub_path}"
        )

    prompt = RAG_PROMPT_TEMPLATE.format(
        knowledge_segments="\n\n".join(knowledge_segments),
        query=query,
    )
    return prompt

