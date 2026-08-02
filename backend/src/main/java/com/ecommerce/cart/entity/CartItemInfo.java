package com.ecommerce.cart.entity;

import lombok.Data;

import java.math.BigDecimal;

@Data
public class CartItemInfo {
    private Long id;
    private Long productId;
    private String productName;
    private BigDecimal price;
    private Integer quantity;
    private BigDecimal subtotal;
}
