package com.ecommerce.cart.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.ecommerce.cart.entity.CartInfo;
import com.ecommerce.cart.entity.CartItem;
import com.ecommerce.cart.entity.CartItemInfo;
import com.ecommerce.cart.mapper.CartItemMapper;
import com.ecommerce.common.BusinessException;
import com.ecommerce.product.entity.Product;
import com.ecommerce.product.mapper.ProductMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

@Service
@RequiredArgsConstructor
public class CartItemService {
    private final CartItemMapper cartItemMapper;
    private final ProductMapper productMapper;

    public CartInfo getCart(Long userId) {
        List<CartItem> items = cartItemMapper.selectList(
            new LambdaQueryWrapper<CartItem>().eq(CartItem::getUserId, userId));
        List<CartItemInfo> infoList = new ArrayList<>();
        BigDecimal total = BigDecimal.ZERO;
        for (CartItem item : items) {
            Product product = productMapper.selectById(item.getProductId());
            if (product == null) continue;
            CartItemInfo info = new CartItemInfo();
            info.setId(item.getId());
            info.setProductId(product.getId());
            info.setProductName(product.getName());
            info.setPrice(product.getPrice());
            info.setQuantity(item.getQuantity());
            info.setSubtotal(product.getPrice().multiply(BigDecimal.valueOf(item.getQuantity())));
            infoList.add(info);
            total = total.add(info.getSubtotal());
        }
        CartInfo cart = new CartInfo();
        cart.setItems(infoList);
        cart.setTotalAmount(total);
        return cart;
    }

    public void addItem(Long userId, Long productId, int quantity) {
        Product product = productMapper.selectById(productId);
        if (product == null) throw new BusinessException("商品不存在");
        if (product.getStock() < quantity) throw new BusinessException("库存不足");

        CartItem exist = cartItemMapper.selectOne(new LambdaQueryWrapper<CartItem>()
            .eq(CartItem::getUserId, userId).eq(CartItem::getProductId, productId));
        if (exist != null) {
            exist.setQuantity(exist.getQuantity() + quantity);
            cartItemMapper.updateById(exist);
        } else {
            CartItem item = new CartItem();
            item.setUserId(userId);
            item.setProductId(productId);
            item.setQuantity(quantity);
            cartItemMapper.insert(item);
        }
    }

    public void updateQuantity(Long userId, Long cartItemId, int quantity) {
        CartItem item = cartItemMapper.selectById(cartItemId);
        if (item == null || !item.getUserId().equals(userId)) throw new BusinessException("购物车项不存在");
        Product product = productMapper.selectById(item.getProductId());
        if (product != null && product.getStock() < quantity) throw new BusinessException("库存不足");
        item.setQuantity(quantity);
        cartItemMapper.updateById(item);
    }

    public void deleteItem(Long userId, Long cartItemId) {
        CartItem item = cartItemMapper.selectById(cartItemId);
        if (item == null || !item.getUserId().equals(userId)) throw new BusinessException("购物车项不存在");
        cartItemMapper.deleteById(cartItemId);
    }

    public void clearCartItems(Long userId, List<Long> productIds) {
        for (Long productId : productIds) {
            cartItemMapper.delete(new LambdaQueryWrapper<CartItem>()
                .eq(CartItem::getUserId, userId).eq(CartItem::getProductId, productId));
        }
    }
}
