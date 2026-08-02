package com.ecommerce.product.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.ecommerce.common.BusinessException;
import com.ecommerce.common.Result;
import com.ecommerce.product.entity.Product;
import com.ecommerce.product.service.ProductService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/products")
@RequiredArgsConstructor
public class ProductController {
    private final ProductService productService;

    @GetMapping
    public Result<Page<Product>> list(
        @RequestParam(defaultValue = "1") int page,
        @RequestParam(defaultValue = "20") int size) {
        if (page < 1) throw new BusinessException(400, "页码必须 >= 1");
        if (size < 1 || size > 100) throw new BusinessException(400, "每页条数需在 1-100 之间");
        return Result.ok(productService.listProducts(page, size));
    }

    @GetMapping("/search")
    public Result<Page<Product>> search(
        @RequestParam String keyword,
        @RequestParam(defaultValue = "1") int page,
        @RequestParam(defaultValue = "20") int size) {
        if (keyword == null || keyword.trim().length() < 1)
            throw new BusinessException(400, "搜索关键词不能为空");
        if (keyword.trim().length() < 2)
            throw new BusinessException(400, "搜索关键词至少2个字符");
        if (page < 1) throw new BusinessException(400, "页码必须 >= 1");
        if (size < 1 || size > 100) throw new BusinessException(400, "每页条数需在 1-100 之间");
        return Result.ok(productService.searchProducts(keyword, page, size));
    }

    @GetMapping("/{id}")
    public Result<Product> get(@PathVariable Long id) {
        return Result.ok(productService.getProduct(id));
    }
}
