"""
Test script for markdown_to_html function with LaTeX formula protection.

This tests the Zotero-optimized Markdown to HTML conversion, specifically
verifying that LaTeX formulas are correctly converted to Zotero's native
MathML format without being mangled by the markdown parser.

Usage:
    conda activate jarvis
    python tests/test_markdown_to_html.py
"""

from stable_jarvis import markdown_to_html


def run_test(name: str, func) -> bool:
    """Run a single test and print result."""
    try:
        func()
        print(f"  ✓ {name}")
        return True
    except AssertionError as e:
        print(f"  ✗ {name}")
        print(f"    AssertionError: {e}")
        return False
    except Exception as e:
        print(f"  ✗ {name}")
        print(f"    {type(e).__name__}: {e}")
        return False


class TestInlineMath:
    """Tests for inline math ($...$) processing."""
    
    def test_simple_inline_math(self) -> None:
        """Test basic inline math is converted to MathML."""
        md = "The equation $x^2$ is simple."
        html = markdown_to_html(md)
        
        assert '<math display="inline">' in html
        assert '<annotation encoding="application/x-tex">x^2</annotation>' in html
        assert '</semantics></math>' in html
    
    def test_underscore_preserved_in_inline_math(self) -> None:
        """Test that underscores in math are NOT converted to italic."""
        md = "The state is $v_w(t), \\omega_b(t), \\Theta(t)$."
        html = markdown_to_html(md)
        
        # Underscores should be preserved, not converted to <em>
        assert '<em>' not in html
        assert 'v_w(t)' in html
        assert '\\omega_b(t)' in html
    
    def test_multiple_inline_math(self) -> None:
        """Test multiple inline math expressions in same text."""
        md = "We have $a$ and $b$ and $c$."
        html = markdown_to_html(md)
        
        # Should have 3 math blocks
        assert html.count('<math display="inline">') == 3
        assert '>a</annotation>' in html
        assert '>b</annotation>' in html
        assert '>c</annotation>' in html
    
    def test_dollar_sign_not_math(self) -> None:
        """Test that isolated dollar amounts are not treated as math."""
        md = "The price is $100 for the item."
        html = markdown_to_html(md)
        
        # Should NOT have math tags (no closing $)
        assert '<math' not in html
        assert '$100' in html


class TestDisplayMath:
    """Tests for display math ($$...$$) processing."""
    
    def test_simple_display_math(self) -> None:
        """Test basic display math is converted to MathML block."""
        md = "The equation is:\n$$\nx^2 + y^2 = z^2\n$$"
        html = markdown_to_html(md)
        
        assert '<math display="block">' in html
        assert 'x^2 + y^2 = z^2' in html
    
    def test_complex_display_math(self) -> None:
        """Test complex LaTeX with subscripts, superscripts, and commands."""
        md = """The reward function:
$$
r(t) = k_p r_p + r_c + k_d r_d + k_v r_v + k_s \\|\\omega_b\\| + r_f
$$
"""
        html = markdown_to_html(md)
        
        assert '<math display="block">' in html
        # Underscores preserved
        assert 'k_p' in html
        assert 'r_p' in html
        # Backslashes preserved
        assert '\\omega_b' in html
    
    def test_multiline_display_math(self) -> None:
        """Test display math spanning multiple lines."""
        md = """$$
\\begin{aligned}
a &= b + c \\\\
d &= e + f
\\end{aligned}
$$"""
        html = markdown_to_html(md)
        
        assert '<math display="block">' in html
        assert '\\begin{aligned}' in html
        assert '\\end{aligned}' in html


class TestHtmlEscaping:
    """Tests for HTML entity escaping in math."""
    
    def test_less_than_escaped(self) -> None:
        """Test that < in math is escaped to &lt;"""
        md = "When $a < b$, then..."
        html = markdown_to_html(md)
        
        assert '&lt;' in html
        assert 'a < b' not in html  # Raw < should be escaped
    
    def test_greater_than_escaped(self) -> None:
        """Test that > in math is escaped to &gt;"""
        md = "When $x > 0$, then..."
        html = markdown_to_html(md)
        
        assert '&gt;' in html
    
    def test_ampersand_escaped(self) -> None:
        """Test that & in math is escaped to &amp;"""
        md = "The alignment $a & b$ uses ampersand."
        html = markdown_to_html(md)
        
        assert '&amp;' in html


class TestMixedContent:
    """Tests for mixed markdown and math content."""
    
    def test_headers_with_math(self) -> None:
        """Test headers containing math expressions."""
        md = "# Title with $x^2$\n\nSome content."
        html = markdown_to_html(md)
        
        # toc extension adds id attribute, so check for <h1 not <h1>
        assert '<h1' in html
        assert '<math display="inline">' in html
    
    def test_lists_with_math(self) -> None:
        """Test bullet lists containing math."""
        md = """- First item with $a$
- Second item with $b$
- Third item"""
        html = markdown_to_html(md)
        
        assert '<li>' in html
        assert html.count('<math display="inline">') == 2
    
    def test_bold_and_math(self) -> None:
        """Test that bold text works alongside math."""
        md = "This is **bold** and this is $math$."
        html = markdown_to_html(md)
        
        assert '<strong>bold</strong>' in html
        assert '<math display="inline">' in html
    
    def test_code_blocks_preserved(self) -> None:
        """Test that code blocks are not affected by math processing."""
        md = """```python
price = "$100"
```

And math $x^2$."""
        html = markdown_to_html(md)
        
        # Code block should be preserved
        assert '<code' in html
        # Math should still work
        assert '<math display="inline">' in html


class TestImageStripping:
    """Tests for image stripping functionality."""
    
    def test_images_stripped_by_default(self) -> None:
        """Test that images are removed by default."""
        md = "![Alt text](image.png)\n\nSome text."
        html = markdown_to_html(md)
        
        assert 'image.png' not in html
        assert '![' not in html
    
    def test_images_with_math(self) -> None:
        """Test that images are stripped but math is preserved."""
        md = """# Title

![Figure 1](fig1.png)

The equation $x^2 + y^2$ is shown above.

$$
E = mc^2
$$

![Figure 2](fig2.png)
"""
        html = markdown_to_html(md)
        
        # Images should be gone
        assert 'fig1.png' not in html
        assert 'fig2.png' not in html
        
        # Math should be preserved
        assert html.count('<math') == 2
        assert 'x^2 + y^2' in html
        assert 'E = mc^2' in html
    
    def test_images_preserved_when_disabled(self) -> None:
        """Test that images are kept when strip_images=False."""
        md = "![Alt text](image.png)"
        html = markdown_to_html(md, strip_images=False)
        
        # Image should become an img tag
        assert '<img' in html or 'image.png' in html


class TestZoteroMathMLFormat:
    """Tests verifying exact Zotero MathML structure."""
    
    def test_inline_math_structure(self) -> None:
        """Verify exact MathML structure for inline math."""
        md = "$x$"
        html = markdown_to_html(md)
        
        expected = (
            '<math display="inline">'
            '<semantics>'
            '<annotation encoding="application/x-tex">x</annotation>'
            '</semantics>'
            '</math>'
        )
        assert expected in html
    
    def test_block_math_structure(self) -> None:
        """Verify exact MathML structure for display math."""
        md = "$$y$$"
        html = markdown_to_html(md)
        
        expected = (
            '<math display="block">'
            '<semantics>'
            '<annotation encoding="application/x-tex">y</annotation>'
            '</semantics>'
            '</math>'
        )
        assert expected in html


class TestEdgeCases:
    """Tests for edge cases and potential issues."""
    
    def test_empty_math(self) -> None:
        """Test handling of empty math delimiters."""
        md = "Empty $$ and empty $$."
        html = markdown_to_html(md)
        # Should handle gracefully (empty annotation)
        assert '<math display="block">' in html
    
    def test_nested_dollar_signs(self) -> None:
        """Test that $$ is not broken by inline $ regex."""
        md = "Display: $$a_b$$ and inline: $c_d$."
        html = markdown_to_html(md)
        
        # Should have one block and one inline
        assert html.count('<math display="block">') == 1
        assert html.count('<math display="inline">') == 1
    
    def test_no_math_content(self) -> None:
        """Test content with no math expressions."""
        md = "Just regular **markdown** content."
        html = markdown_to_html(md)
        
        assert '<math' not in html
        assert '<strong>markdown</strong>' in html
    
    def test_preserve_tables(self) -> None:
        """Test that markdown tables work with math."""
        md = """| Variable | Value |
|----------|-------|
| $x$ | 1 |
| $y$ | 2 |"""
        html = markdown_to_html(md)
        
        assert '<table>' in html
        assert html.count('<math display="inline">') == 2


if __name__ == "__main__":
    test_classes = [
        TestInlineMath,
        TestDisplayMath,
        TestHtmlEscaping,
        TestMixedContent,
        TestImageStripping,
        TestZoteroMathMLFormat,
        TestEdgeCases,
    ]
    
    passed = 0
    failed = 0
    
    for cls in test_classes:
        print(f"\n{cls.__name__}:")
        instance = cls()
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                if run_test(method_name, getattr(instance, method_name)):
                    passed += 1
                else:
                    failed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("All tests passed!")
    else:
        exit(1)
