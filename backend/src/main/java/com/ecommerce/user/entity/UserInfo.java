package com.ecommerce.user.entity;

import lombok.AllArgsConstructor;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@AllArgsConstructor
public class UserInfo {
    private Long id;
    private String username;
    private String email;
    private LocalDateTime createdAt;
}
