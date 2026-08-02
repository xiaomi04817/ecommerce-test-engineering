package com.ecommerce.order.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

@Data
@TableName("orders")
public class Order {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String orderNo;
    private Long userId;
    private String status;  // PENDING, PAID, SHIPPED, RECEIVED, CANCELLED, REFUNDED
    private BigDecimal totalAmount;
    private String addressSnapshot;
    private String remark;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    @TableField(exist = false)
    private List<OrderItem> orderItems;
}
