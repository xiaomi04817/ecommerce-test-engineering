<template>
  <div class="order-confirm-container">
    <el-container>
      <el-header class="page-header">
        <div class="header-left">
          <el-button text @click="$router.push('/cart')">
            <el-icon><ArrowLeft /></el-icon>
            返回购物车
          </el-button>
          <h2>确认订单</h2>
        </div>
      </el-header>

      <el-main>
        <!-- Loading -->
        <div v-if="loading" class="loading-area">
          <el-skeleton :rows="6" animated />
        </div>

        <template v-else>
          <!-- Order Items -->
          <el-card class="section-card">
            <template #header>
              <h3>订单商品</h3>
            </template>
            <el-table :data="cartItems" border stripe>
              <el-table-column label="商品名称" min-width="180">
                <template #default="{ row }">
                  {{ row.productName }}
                </template>
              </el-table-column>
              <el-table-column label="单价" width="120" align="right">
                <template #default="{ row }">
                  &yen;{{ row.price.toFixed(2) }}
                </template>
              </el-table-column>
              <el-table-column label="数量" width="100" align="center">
                <template #default="{ row }">
                  {{ row.quantity }}
                </template>
              </el-table-column>
              <el-table-column label="小计" width="120" align="right">
                <template #default="{ row }">
                  <span class="subtotal">&yen;{{ row.subtotal.toFixed(2) }}</span>
                </template>
              </el-table-column>
            </el-table>
            <div class="total-row">
              合计：
              <span class="total-amount">&yen;{{ totalAmount.toFixed(2) }}</span>
            </div>
          </el-card>

          <!-- Address Selection -->
          <el-card class="section-card">
            <template #header>
              <div class="section-header">
                <h3>收货地址</h3>
                <el-button size="small" @click="$router.push('/addresses')">
                  管理地址
                </el-button>
              </div>
            </template>
            <div v-if="addresses.length === 0" class="no-address">
              <p>暂无收货地址，请先添加地址</p>
              <el-button type="primary" @click="$router.push('/addresses')">
                添加地址
              </el-button>
            </div>
            <el-radio-group v-else v-model="selectedAddressId" class="address-radio-group">
              <div
                v-for="addr in addresses"
                :key="addr.id"
                class="address-option"
                :class="{ 'is-selected': selectedAddressId === addr.id }"
              >
                <el-radio :value="addr.id">
                  <span class="receiver">{{ addr.receiverName }}</span>
                  <span class="phone">{{ addr.phone }}</span>
                  <el-tag v-if="addr.isDefault" type="success" size="small">默认</el-tag>
                </el-radio>
                <div class="address-text">
                  {{ addr.province }}{{ addr.city }}{{ addr.district }} {{ addr.detail }}
                </div>
              </div>
            </el-radio-group>
          </el-card>

          <!-- Remark -->
          <el-card class="section-card">
            <template #header>
              <h3>订单备注</h3>
            </template>
            <el-input
              v-model="remark"
              type="textarea"
              :rows="3"
              maxlength="200"
              show-word-limit
              placeholder="选填：请输入订单备注（最多200字）"
            />
          </el-card>

          <!-- Place Order -->
          <div class="order-actions">
            <el-button
              type="primary"
              size="large"
              :loading="submitting"
              :disabled="!selectedAddressId"
              @click="handlePlaceOrder"
            >
              提交订单
            </el-button>
            <span v-if="!selectedAddressId && addresses.length > 0" class="tip">
              请选择收货地址
            </span>
          </div>
        </template>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../utils/api'

const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const cartItems = ref<any[]>([])
const totalAmount = ref(0)
const addresses = ref<any[]>([])
const selectedAddressId = ref<number | null>(null)
const remark = ref('')

async function fetchData() {
  loading.value = true
  try {
    const [cartRes, addrRes] = await Promise.all([
      api.get('/cart'),
      api.get('/addresses')
    ])
    const cartData = cartRes.data.data
    cartItems.value = cartData.items || []
    totalAmount.value = cartData.totalAmount || 0
    addresses.value = addrRes.data.data || []

    // Auto-select default address
    if (addresses.value.length > 0) {
      const defaultAddr = addresses.value.find((a: any) => a.isDefault)
      selectedAddressId.value = defaultAddr ? defaultAddr.id : addresses.value[0].id
    }
  } catch {
    cartItems.value = []
    addresses.value = []
  } finally {
    loading.value = false
  }
}

async function handlePlaceOrder() {
  if (!selectedAddressId.value) {
    ElMessage.warning('请选择收货地址')
    return
  }
  if (cartItems.value.length === 0) {
    ElMessage.warning('购物车是空的')
    return
  }

  submitting.value = true
  try {
    const res = await api.post('/orders', {
      addressId: selectedAddressId.value,
      items: cartItems.value.map((item: any) => ({
        productId: item.productId,
        quantity: item.quantity
      })),
      remark: remark.value || undefined
    })
    const order = res.data.data
    ElMessage.success('订单已创建')
    router.push(`/orders/${order.id}`)
  } catch {
    // Error handled by interceptor
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  padding: 0 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  height: 60px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h2 {
  margin: 0;
  font-size: 18px;
}

.loading-area {
  padding: 40px 0;
}

.section-card {
  margin-bottom: 16px;
}

.section-card h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.subtotal {
  font-weight: 600;
  color: #f56c6c;
}

.total-row {
  text-align: right;
  padding: 16px 0 0;
  font-size: 16px;
  color: #303133;
  border-top: 1px solid #ebeef5;
  margin-top: 12px;
}

.total-amount {
  font-size: 24px;
  font-weight: 700;
  color: #f56c6c;
}

.no-address {
  text-align: center;
  padding: 20px 0;
  color: #909399;
}

.address-radio-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.address-option {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 10px 14px;
  transition: border-color 0.2s;
}

.address-option.is-selected {
  border-color: #409eff;
}

.address-text {
  margin-top: 4px;
  margin-left: 24px;
  color: #606266;
  font-size: 14px;
}

.receiver {
  font-weight: 600;
  margin-right: 8px;
}

.phone {
  color: #909399;
  font-size: 13px;
  margin-right: 8px;
}

.order-actions {
  text-align: center;
  padding: 24px 0;
}

.tip {
  color: #f56c6c;
  font-size: 13px;
  margin-left: 12px;
}
</style>
