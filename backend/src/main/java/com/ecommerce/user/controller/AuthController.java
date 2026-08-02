package com.ecommerce.user.controller;

import com.ecommerce.common.Result;
import com.ecommerce.user.entity.RegisterRequest;
import com.ecommerce.user.entity.UserInfo;
import com.ecommerce.user.service.UserService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {
    private final UserService userService;

    @PostMapping("/register")
    public Result<UserInfo> register(@Valid @RequestBody RegisterRequest req) {
        UserInfo user = userService.register(
            req.getUsername(), req.getPassword(), req.getEmail());
        return Result.ok(user);
    }

    @PostMapping("/login")
    public Result<Map<String, Object>> login(@RequestBody Map<String, String> body) {
        return Result.ok(userService.login(body.get("username"), body.get("password")));
    }
}
