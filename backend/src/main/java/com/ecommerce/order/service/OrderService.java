package com.ecommerce.order.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.ecommerce.address.entity.Address;
import com.ecommerce.address.mapper.AddressMapper;
import com.ecommerce.cart.service.CartItemService;
import com.ecommerce.common.BusinessException;
import com.ecommerce.order.entity.Order;
import com.ecommerce.order.entity.OrderItem;
import com.ecommerce.order.entity.OrderItemRequest;
import com.ecommerce.order.mapper.OrderItemMapper;
import com.ecommerce.order.mapper.OrderMapper;
import com.ecommerce.product.entity.Product;
import com.ecommerce.product.mapper.ProductMapper;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import lombok.RequiredArgsConstructor;
import lombok.SneakyThrows;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.*;

@Service
@RequiredArgsConstructor
public class OrderService {
    private final OrderMapper orderMapper;
    private final OrderItemMapper orderItemMapper;
    private final AddressMapper addressMapper;
    private final ProductMapper productMapper;
    private final CartItemService cartItemService;
    private final ObjectMapper objectMapper = new ObjectMapper().registerModule(new JavaTimeModule());

    private static final Set<String> TERMINAL_STATUSES = Set.of("RECEIVED", "CANCELLED", "REFUNDED");
    private static final Map<String, Set<String>> ALLOWED_TRANSITIONS = Map.of(
        "PENDING", Set.of("PAID", "CANCELLED"),
        "PAID", Set.of("SHIPPED", "REFUNDED"),
        "SHIPPED", Set.of("RECEIVED", "REFUNDED")
    );

    @Transactional
    public Order createOrder(Long userId, Long addressId, List<OrderItemRequest> items, String remark) {
        Address address = addressMapper.selectById(addressId);
        if (address == null || !address.getUserId().equals(userId)) {
            throw new BusinessException("收货地址不存在");
        }
        if (items == null || items.isEmpty()) throw new BusinessException("订单商品不能为空");

        // Build order
        Order order = new Order();
        order.setUserId(userId);
        order.setOrderNo(generateOrderNo());
        order.setStatus("PENDING");
        order.setRemark(remark);
        order.setAddressSnapshot(toJson(address));

        List<OrderItem> orderItems = new ArrayList<>();
        BigDecimal total = BigDecimal.ZERO;
        List<Long> cartProductIds = new ArrayList<>();

        for (OrderItemRequest req : items) {
            if (req.getQuantity() == null || req.getQuantity() <= 0)
                throw new BusinessException("商品数量必须大于0");
            Product product = productMapper.selectById(req.getProductId());
            if (product == null) throw new BusinessException("商品不存在: " + req.getProductId());
            if (product.getStock() < req.getQuantity()) throw new BusinessException("商品库存不足: " + product.getName());

            // Deduct stock
            boolean deducted = deductStock(product.getId(), req.getQuantity());
            if (!deducted) throw new BusinessException("商品库存不足: " + product.getName());

            OrderItem oi = new OrderItem();
            oi.setProductId(product.getId());
            oi.setProductName(product.getName());
            oi.setPrice(product.getPrice());
            oi.setQuantity(req.getQuantity());
            oi.setSubtotal(product.getPrice().multiply(BigDecimal.valueOf(req.getQuantity())));
            orderItems.add(oi);
            total = total.add(oi.getSubtotal());
            cartProductIds.add(req.getProductId());
        }

        order.setTotalAmount(total);
        orderMapper.insert(order);

        for (OrderItem oi : orderItems) {
            oi.setOrderId(order.getId());
            orderItemMapper.insert(oi);
        }

        order.setOrderItems(orderItems);

        // Clear purchased items from cart
        cartItemService.clearCartItems(userId, cartProductIds);

        return order;
    }

    public Page<Order> listOrders(Long userId, int page, int size, String status) {
        LambdaQueryWrapper<Order> wrapper = new LambdaQueryWrapper<Order>()
            .eq(Order::getUserId, userId)
            .eq(status != null && !status.isEmpty(), Order::getStatus, status)
            .orderByDesc(Order::getCreatedAt);
        Page<Order> result = orderMapper.selectPage(new Page<>(page, size), wrapper);
        // Load order items for each order
        for (Order order : result.getRecords()) {
            loadOrderItems(order);
        }
        return result;
    }

    public Order getOrder(Long orderId, Long userId) {
        Order order = orderMapper.selectById(orderId);
        if (order == null) throw new BusinessException(404, "订单不存在");
        if (!order.getUserId().equals(userId)) throw new BusinessException(403, "无权查看该订单");
        loadOrderItems(order);
        return order;
    }

    @Transactional
    public Order updateStatus(Long orderId, String action, Long userId) {
        Order order = orderMapper.selectById(orderId);
        if (order == null) throw new BusinessException(404, "订单不存在");

        // Determine target status
        String targetStatus = switch (action) {
            case "pay" -> "PAID";
            case "ship" -> "SHIPPED";
            case "receive" -> "RECEIVED";
            case "cancel" -> "CANCELLED";
            case "refund" -> "REFUNDED";
            default -> throw new BusinessException("非法操作: " + action);
        };

        // Permission check
        if ("ship".equals(action)) {
            if (userId != 1) throw new BusinessException(403, "仅管理员可执行发货操作");
        } else {
            if (!order.getUserId().equals(userId)) throw new BusinessException(403, "无权操作该订单");
        }

        // State machine validation
        if (TERMINAL_STATUSES.contains(order.getStatus())) {
            throw new BusinessException("订单已结束，无法操作");
        }
        Set<String> allowed = ALLOWED_TRANSITIONS.getOrDefault(order.getStatus(), Set.of());
        if (!allowed.contains(targetStatus)) {
            throw new BusinessException("不允许从 " + order.getStatus() + " 变更为 " + targetStatus);
        }

        // Restore stock on cancel/refund
        if ("CANCELLED".equals(targetStatus) || "REFUNDED".equals(targetStatus)) {
            List<OrderItem> items = orderItemMapper.selectList(
                new LambdaQueryWrapper<OrderItem>().eq(OrderItem::getOrderId, orderId));
            for (OrderItem item : items) {
                LambdaUpdateWrapper<Product> wrapper = new LambdaUpdateWrapper<>();
                wrapper.setSql("stock = stock + " + item.getQuantity())
                       .eq(Product::getId, item.getProductId());
                productMapper.update(null, wrapper);
            }
        }

        order.setStatus(targetStatus);
        orderMapper.updateById(order);
        loadOrderItems(order);
        return order;
    }

    private boolean deductStock(Long productId, int quantity) {
        // Read entity first to get current version for optimistic locking
        Product product = productMapper.selectById(productId);
        if (product == null || product.getStock() < quantity) {
            return false;
        }
        product.setStock(product.getStock() - quantity);
        // updateById works correctly with @Version: adds AND version = ? to WHERE
        return productMapper.updateById(product) > 0;
    }

    private void loadOrderItems(Order order) {
        List<OrderItem> items = orderItemMapper.selectList(
            new LambdaQueryWrapper<OrderItem>().eq(OrderItem::getOrderId, order.getId()));
        order.setOrderItems(items);
    }

    @SneakyThrows
    private String toJson(Object obj) {
        return objectMapper.writeValueAsString(obj);
    }

    private String generateOrderNo() {
        String date = LocalDate.now().format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        String chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
        StringBuilder sb = new StringBuilder();
        Random random = new Random();
        for (int i = 0; i < 6; i++) sb.append(chars.charAt(random.nextInt(chars.length())));
        return date + "-" + sb.toString();
    }
}
