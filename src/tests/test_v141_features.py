"""Test v1.4.1 features: extract_alpha_only and search_text_in_pdf"""

from stable_jarvis.annotation.coordinates import (
    CoordinateExtractor,
    get_pdf_info,
    search_text_in_pdf,
)


def test_extract_alpha_only():
    """Test extract_alpha_only removes non-letter characters."""
    # Test basic case
    result = CoordinateExtractor.extract_alpha_only("gradient ∇f(x) descent")
    assert result == "gradient descent", f"Expected 'gradient descent', got {result!r}"
    
    # Single letters should be filtered out
    result = CoordinateExtractor.extract_alpha_only("where d∂ is the gradient")
    assert "is" in result and "the" in result and "gradient" in result
    assert "d" not in result.split()  # 'd' alone should be filtered
    
    # Math-heavy text
    result = CoordinateExtractor.extract_alpha_only("θ = α + β * γ")
    assert result == "", f"Expected empty string, got {result!r}"
    
    # Mixed text
    result = CoordinateExtractor.extract_alpha_only("The loss L = Σ(yi - ŷi)²")
    assert "The" in result and "loss" in result
    
    print("✓ extract_alpha_only tests passed")


def test_pdf_info_find_text():
    """Test PDFInfo.find_text method."""
    from stable_jarvis.annotation.coordinates import PDFInfo
    
    # Create a mock PDFInfo
    info = PDFInfo(
        total_pages=3,
        page_dimensions=[(612, 792), (612, 792), (612, 792)],
        has_cover=False,
        page_labels=["1", "2", "3"],
        page_previews=[
            "Introduction to machine learning and neural networks",
            "We propose a novel gradient descent optimization method",
            "Experimental results show significant improvement",
        ],
    )
    
    # Test direct match
    results = info.find_text("gradient descent")
    assert len(results) > 0
    assert results[0]["page"] == 1
    assert results[0]["confidence"] == 1.0
    
    # Test no match
    results = info.find_text("quantum physics")
    assert len(results) == 0
    
    print("✓ PDFInfo.find_text tests passed")


def test_imports():
    """Test all new exports are importable."""
    # These should not raise ImportError
    from stable_jarvis.annotation.coordinates import (
        CoordinateExtractor,
        PDFInfo,
        TextMatch,
        get_pdf_info,
        search_text_in_pdf,
    )
    
    # Verify extract_alpha_only is a method
    assert hasattr(CoordinateExtractor, "extract_alpha_only")
    assert callable(CoordinateExtractor.extract_alpha_only)
    
    # Verify PDFInfo has page_previews field
    assert hasattr(PDFInfo, "__dataclass_fields__")
    assert "page_previews" in PDFInfo.__dataclass_fields__
    
    # Verify search_text_in_pdf is callable
    assert callable(search_text_in_pdf)
    
    print("✓ Import tests passed")


if __name__ == "__main__":
    test_imports()
    test_extract_alpha_only()
    test_pdf_info_find_text()
    print("\n✅ All v1.4.1 tests passed!")
