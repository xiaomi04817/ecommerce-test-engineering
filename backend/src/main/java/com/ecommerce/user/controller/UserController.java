package com.ecommerce.user.controller;

import com.ecommerce.common.Result;
import com.ecommerce.user.entity.UserInfo;
import com.ecommerce.user.service.UserService;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
public class UserController {
    private final UserService userService;

    @GetMapping("/me")
    public Result<UserInfo> me(HttpServletRequest request) {
        Long userId = (Long) request.getAttribute("userId");
        return Result.ok(userService.getUserInfo(userId));
    }
}
