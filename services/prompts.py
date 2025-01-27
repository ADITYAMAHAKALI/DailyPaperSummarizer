# services/prompts.py

SUMMARIZER_PROMPT = """
Summarize the following paper:
Title: {title}
Content: {content}
"""

LINKEDIN_POST_CREATOR = """
I want to create a LinkedIn post about the following AI research papers. 
For each paper, write a concise, human-friendly paragraph highlighting the key idea, 
why it's important, and any interesting insights or applications. 
End each paragraph with the paper's link, preceded by "Link: ".

Use Markdown formatting, add headings and highlight important parts and Feel free to include emojis with spacing for emphasis. 
Leave a blank line between each paper's paragraph.
At the end Summarise where AI research is moving as a whole if you observe any patterns 
{papers}
"""
