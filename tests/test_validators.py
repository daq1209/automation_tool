"""
Unit tests for input validators.
"""

import pytest
from src.utils.validators import validate_product_data, validate_sheet_structure, ProductImport
from pydantic import ValidationError


class TestProductValidation:
    """Test product data validation."""
    
    def test_valid_product(self):
        """Test validation with valid product data."""
        product = {
            'sku': 'TEST123',
            'title': 'Test Product',
            'price': 19.99,
            'description': 'A test product',
            'images': ['https://example.com/image.jpg']
        }
        
        is_valid, error, validated = validate_product_data(product)
        
        assert is_valid is True
        assert error is None
        assert validated.sku == 'TEST123'
        assert validated.title == 'Test Product'
    
    def test_invalid_sku(self):
        """Test validation with invalid SKU."""
        product = {
            'sku': '',  # Empty SKU
            'title': 'Test Product'
        }
        
        is_valid, error, validated = validate_product_data(product)
        
        assert is_valid is False
        assert 'sku' in error.lower()
    
    def test_invalid_price(self):
        """Test validation with invalid price."""
        product = {
            'sku': 'TEST123',
            'title': 'Test Product',
            'price': -10  # Negative price
        }
        
        is_valid, error, validated = validate_product_data(product)
        
        assert is_valid is False
        assert 'price' in error.lower()
    
    def test_sku_with_dangerous_chars(self):
        """Test validation rejects SKU with dangerous characters."""
        product = {
            'sku': 'TEST<script>',
            'title': 'Test Product'
        }
        
        is_valid, error, validated = validate_product_data(product)
        
        assert is_valid is False
        assert 'invalid characters' in error.lower()
    
    def test_image_url_filtering(self):
        """Test that only valid HTTP(S) URLs are kept."""
        product = {
            'sku': 'TEST123',
            'title': 'Test Product',
            'images': [
                'https://example.com/valid.jpg',
                'invalid-url',
                'http://example.com/also-valid.jpg',
                'ftp://not-http.com/image.jpg'
            ]
        }
        
        is_valid, error, validated = validate_product_data(product)
        
        assert is_valid is True
        assert len(validated.images) == 2
        assert 'https://example.com/valid.jpg' in validated.images


class TestSheetStructureValidation:
    """Test sheet structure validation."""
    
    def test_valid_sheet_structure(self):
        """Test validation with all required columns."""
        headers = [
            'Check_update', 'ID', 'Type', 'Name', 
            'Published', 'Regular price', 'Images'
        ]
        
        is_valid, error = validate_sheet_structure(headers)
        
        assert is_valid is True
        assert error is None
    
    def test_missing_columns(self):
        """Test validation with missing required columns."""
        headers = ['ID', 'Name']  # Missing other required columns
        
        is_valid, error = validate_sheet_structure(headers)
        
        assert is_valid is False
        assert 'Missing required columns' in error
        assert 'Check_update' in error
    
    def test_extra_columns_ok(self):
        """Test that extra columns don't cause validation to fail."""
        headers = [
            'Check_update', 'ID', 'Type', 'Name', 
            'Published', 'Regular price', 'Images',
            'Extra_Column_1', 'Extra_Column_2'
        ]
        
        is_valid, error = validate_sheet_structure(headers)
        
        assert is_valid is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
