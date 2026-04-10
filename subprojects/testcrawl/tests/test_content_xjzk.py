from app.services.content_extractor import extract_xjzk_detail_text


def test_extract_xjzk_pdf_only_article():
    html = """
    <html><body>
      <div id="detail_conts">
        <div class="tabPanel"><p class="ttl">当前位置：首页</p></div>
        <h1>国家教育考试违规处理办法（摘录）</h1>
        <div class="date">发布时间：2023-02-07</div>
        <div class="txt"><p><a href="/upload/x.pdf">办法摘录.pdf</a></p></div>
      </div>
      <footer>页脚导航很多字</footer>
    </body></html>
    """
    text = extract_xjzk_detail_text(html, "https://www.xjzk.gov.cn/c/2023-02-07/488866.shtml")
    assert text
    assert "国家教育考试违规处理办法" in text
    assert "页脚导航" not in text
    assert "www.xjzk.gov.cn/upload/x.pdf" in text


def test_extract_xjzk_with_body_text():
    html = """
    <div id="detail_conts">
      <h1>标题</h1>
      <div class="date">2024-01-01</div>
      <div class="txt"><p>正文段落一。</p><p>正文二。</p></div>
    </div>
    """
    text = extract_xjzk_detail_text(html, "https://www.xjzk.gov.cn/c/1.shtml")
    assert "正文段落一" in text
    assert "标题" in text
