package com.ecommerce.cart.entity;

import lombok.Data;

import java.math.BigDecimal;
import java.util.List;

@Data
public class CartInfo {
    private List<CartItemInfo> items;
    private BigDecimal totalAmount;
}
