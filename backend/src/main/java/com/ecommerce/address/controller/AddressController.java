package com.ecommerce.address.controller;

import com.ecommerce.address.entity.Address;
import com.ecommerce.address.entity.AddressRequest;
import com.ecommerce.address.service.AddressService;
import com.ecommerce.common.Result;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/addresses")
@RequiredArgsConstructor
public class AddressController {
    private final AddressService addressService;

    @GetMapping
    public Result<List<Address>> list(HttpServletRequest request) {
        Long userId = (Long) request.getAttribute("userId");
        return Result.ok(addressService.listAddresses(userId));
    }

    @PostMapping
    public Result<Address> create(HttpServletRequest request, @Valid @RequestBody AddressRequest req) {
        Long userId = (Long) request.getAttribute("userId");
        Address address = toAddress(req);
        return Result.ok(addressService.createAddress(userId, address));
    }

    @PutMapping("/{id}")
    public Result<?> update(HttpServletRequest request, @PathVariable Long id, @Valid @RequestBody AddressRequest req) {
        Long userId = (Long) request.getAttribute("userId");
        addressService.updateAddress(userId, id, toAddress(req));
        return Result.ok();
    }

    @DeleteMapping("/{id}")
    public Result<?> delete(HttpServletRequest request, @PathVariable Long id) {
        Long userId = (Long) request.getAttribute("userId");
        addressService.deleteAddress(userId, id);
        return Result.ok();
    }

    private Address toAddress(AddressRequest req) {
        Address addr = new Address();
        addr.setReceiverName(req.getReceiverName());
        addr.setPhone(req.getPhone());
        addr.setProvince(req.getProvince());
        addr.setCity(req.getCity());
        addr.setDistrict(req.getDistrict());
        addr.setDetail(req.getDetail());
        addr.setIsDefault(req.getIsDefault());
        return addr;
    }
}
