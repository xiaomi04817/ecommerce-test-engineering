package com.ecommerce.product.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.ecommerce.common.BusinessException;
import com.ecommerce.product.entity.Product;
import com.ecommerce.product.mapper.ProductMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class ProductService {
    private final ProductMapper productMapper;

    public Page<Product> listProducts(int page, int size) {
        return productMapper.selectPage(new Page<>(page, size), null);
    }

    public Product getProduct(Long id) {
        Product product = productMapper.selectById(id);
        if (product == null) throw new BusinessException(404, "商品不存在");
        return product;
    }

    public Page<Product> searchProducts(String keyword, int page, int size) {
        LambdaQueryWrapper<Product> wrapper = new LambdaQueryWrapper<>();
        wrapper.like(Product::getName, keyword);
        return productMapper.selectPage(new Page<>(page, size), wrapper);
    }

    public boolean deductStock(Long productId, int quantity) {
        LambdaUpdateWrapper<Product> wrapper = new LambdaUpdateWrapper<>();
        wrapper.setSql("stock = stock - " + quantity)
               .eq(Product::getId, productId)
               .ge(Product::getStock, quantity);
        return productMapper.update(null, wrapper) > 0;
    }

    public void restoreStock(Long productId, int quantity) {
        LambdaUpdateWrapper<Product> wrapper = new LambdaUpdateWrapper<>();
        wrapper.setSql("stock = stock + " + quantity).eq(Product::getId, productId);
        productMapper.update(null, wrapper);
    }
}
