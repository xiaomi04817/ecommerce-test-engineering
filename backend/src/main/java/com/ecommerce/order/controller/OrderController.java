package com.ecommerce.order.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.ecommerce.common.Result;
import com.ecommerce.order.entity.Order;
import com.ecommerce.order.entity.OrderItemRequest;
import com.ecommerce.order.service.OrderService;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/orders")
@RequiredArgsConstructor
public class OrderController {
    private final OrderService orderService;

    @PostMapping
    public Result<Order> create(HttpServletRequest request,
                                 @RequestBody Map<String, Object> body) {
        Long userId = (Long) request.getAttribute("userId");
        Long addressId = Long.valueOf(body.get("addressId").toString());
        String remark = (String) body.getOrDefault("remark", null);

        @SuppressWarnings("unchecked")
        List<Map<String, Object>> itemsRaw = (List<Map<String, Object>>) body.get("items");
        List<OrderItemRequest> items = itemsRaw.stream().map(m -> {
            OrderItemRequest req = new OrderItemRequest();
            req.setProductId(Long.valueOf(m.get("productId").toString()));
            req.setQuantity(Integer.parseInt(m.get("quantity").toString()));
            return req;
        }).toList();

        return Result.ok(orderService.createOrder(userId, addressId, items, remark));
    }

    @GetMapping
    public Result<Page<Order>> list(HttpServletRequest request,
                                     @RequestParam(defaultValue = "1") int page,
                                     @RequestParam(defaultValue = "20") int size,
                                     @RequestParam(required = false) String status) {
        Long userId = (Long) request.getAttribute("userId");
        return Result.ok(orderService.listOrders(userId, page, size, status));
    }

    @GetMapping("/{id}")
    public Result<Order> get(HttpServletRequest request, @PathVariable Long id) {
        Long userId = (Long) request.getAttribute("userId");
        return Result.ok(orderService.getOrder(id, userId));
    }

    @PutMapping("/{id}/status")
    public Result<Order> updateStatus(HttpServletRequest request, @PathVariable Long id,
                                       @RequestBody Map<String, String> body) {
        Long userId = (Long) request.getAttribute("userId");
        String action = body.get("action");
        return Result.ok(orderService.updateStatus(id, action, userId));
    }
}
