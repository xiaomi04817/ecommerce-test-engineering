package com.ecommerce.address.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.ecommerce.address.entity.Address;
import com.ecommerce.address.mapper.AddressMapper;
import com.ecommerce.common.BusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class AddressService {
    private final AddressMapper addressMapper;
    private static final int MAX_ADDRESS = 10;

    public List<Address> listAddresses(Long userId) {
        return addressMapper.selectList(new LambdaQueryWrapper<Address>().eq(Address::getUserId, userId));
    }

    public Address createAddress(Long userId, Address address) {
        long count = addressMapper.selectCount(new LambdaQueryWrapper<Address>().eq(Address::getUserId, userId));
        if (count >= MAX_ADDRESS) throw new BusinessException("收货地址最多10个");
        address.setUserId(userId);
        addressMapper.insert(address);
        return address;
    }

    public void updateAddress(Long userId, Long addressId, Address address) {
        getAndCheck(userId, addressId);
        address.setId(addressId);
        address.setUserId(userId);
        addressMapper.updateById(address);
    }

    public void deleteAddress(Long userId, Long addressId) {
        getAndCheck(userId, addressId);
        addressMapper.deleteById(addressId);  // @TableLogic handles soft delete
    }

    private Address getAndCheck(Long userId, Long addressId) {
        Address address = addressMapper.selectById(addressId);
        if (address == null || !address.getUserId().equals(userId)) {
            throw new BusinessException(404, "地址不存在");
        }
        return address;
    }
}
