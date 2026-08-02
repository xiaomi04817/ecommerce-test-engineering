package com.ecommerce.cart.controller;

import com.ecommerce.cart.entity.CartInfo;
import com.ecommerce.cart.service.CartItemService;
import com.ecommerce.common.BusinessException;
import com.ecommerce.common.Result;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/cart")
@RequiredArgsConstructor
public class CartController {
    private final CartItemService cartItemService;

    @GetMapping
    public Result<CartInfo> getCart(HttpServletRequest request) {
        Long userId = (Long) request.getAttribute("userId");
        return Result.ok(cartItemService.getCart(userId));
    }

    @PostMapping("/items")
    public Result<?> addItem(HttpServletRequest request, @RequestBody Map<String, Object> body) {
        Long userId = (Long) request.getAttribute("userId");
        Long productId = Long.valueOf(body.get("productId").toString());
        int quantity = Integer.parseInt(body.get("quantity").toString());
        if (quantity < 1) throw new BusinessException(400, "商品数量必须 >= 1");
        cartItemService.addItem(userId, productId, quantity);
        return Result.ok();
    }

    @PutMapping("/items/{id}")
    public Result<?> updateItem(HttpServletRequest request, @PathVariable Long id,
                                 @RequestBody Map<String, Object> body) {
        Long userId = (Long) request.getAttribute("userId");
        int quantity = Integer.parseInt(body.get("quantity").toString());
        if (quantity < 1) throw new BusinessException(400, "商品数量必须 >= 1");
        cartItemService.updateQuantity(userId, id, quantity);
        return Result.ok();
    }

    @DeleteMapping("/items/{id}")
    public Result<?> deleteItem(HttpServletRequest request, @PathVariable Long id) {
        Long userId = (Long) request.getAttribute("userId");
        cartItemService.deleteItem(userId, id);
        return Result.ok();
    }
}
