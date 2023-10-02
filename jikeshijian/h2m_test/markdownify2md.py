html_text = """
<pre><code class=\"language-python\">#!/usr/bin/Python3\nprint (\"Hello, Python!\")\n</code></pre><!-- [[[read_end]]] -->
<pre><code>#!/usr/bin/java\nprint (\"Hello, Python!\")\n</code></pre><!-- [[[read_end]]] -->
"""

def code_language_callback(el):
    code_tag = el.find('code')
    print(type(code_tag))
    if code_tag.has_attr('class'):
        class_value = code_tag['class'][0].split('-')[-1]
    else:
        class_value=''
    return class_value
    

from markdownify import markdownify as md
text=md(html_text,code_language_callback=code_language_callback)
print(text)  
print('*'*50)



