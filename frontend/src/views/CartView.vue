<template>
  <div class="cart-container">
    <el-container>
      <el-header class="page-header">
        <div class="header-left">
          <el-button text @click="$router.push('/products')">
            <el-icon><ArrowLeft /></el-icon>
            继续购物
          </el-button>
          <h2>购物车</h2>
        </div>
      </el-header>

      <el-main>
        <!-- Loading -->
        <div v-if="loading" class="loading-area">
          <el-skeleton :rows="4" animated />
        </div>

        <!-- Empty -->
        <el-empty v-else-if="!cart || cart.items.length === 0" description="购物车是空的">
          <el-button type="primary" @click="$router.push('/products')">
            去逛逛
          </el-button>
        </el-empty>

        <!-- Cart Table -->
        <template v-else>
          <el-table :data="cart.items" border stripe style="width: 100%">
            <el-table-column label="商品名称" min-width="200">
              <template #default="{ row }">
                <span class="product-name-link" @click="$router.push(`/products/${row.productId}`)">
                  {{ row.productName }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="单价" width="120" align="right">
              <template #default="{ row }">
                &yen;{{ row.price.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column label="数量" width="160" align="center">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.quantity"
                  :min="1"
                  :max="99"
                  size="small"
                  @change="(val: number) => handleQuantityChange(row, val)"
                />
              </template>
            </el-table-column>
            <el-table-column label="小计" width="120" align="right">
              <template #default="{ row }">
                <span class="subtotal">&yen;{{ row.subtotal.toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" align="center">
              <template #default="{ row }">
                <el-button
                  type="danger"
                  size="small"
                  text
                  @click="handleDeleteItem(row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- Cart Footer -->
          <div class="cart-footer">
            <div class="total-amount">
              合计：<span class="amount-value">&yen;{{ cart.totalAmount.toFixed(2) }}</span>
            </div>
            <el-button type="primary" size="large" @click="handleCheckout">
              去结算
            </el-button>
          </div>
        </template>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../utils/api'

const router = useRouter()
const cart = ref<any>(null)
const loading = ref(false)

async function fetchCart() {
  loading.value = true
  try {
    const res = await api.get('/cart')
    cart.value = res.data.data
  } catch {
    cart.value = null
  } finally {
    loading.value = false
  }
}

async function handleQuantityChange(row: any, val: number) {
  if (!val || val < 1) {
    row.quantity = 1
    return
  }
  try {
    await api.put(`/cart/items/${row.id}`, { quantity: val })
    // Recalculate subtotal
    row.subtotal = row.price * val
    // Recalculate total
    if (cart.value) {
      cart.value.totalAmount = cart.value.items.reduce(
        (sum: number, item: any) => sum + item.subtotal,
        0
      )
    }
    ElMessage.success('数量已更新')
  } catch {
    // Restore on failure by refetching
    fetchCart()
  }
}

async function handleDeleteItem(row: any) {
  try {
    await ElMessageBox.confirm(
      `确定要从购物车中删除 "${row.productName}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
  } catch {
    return
  }
  try {
    await api.delete(`/cart/items/${row.id}`)
    ElMessage.success('已从购物车中移除')
    fetchCart()
  } catch {
    // Error handled by interceptor
  }
}

function handleCheckout() {
  if (!cart.value || cart.value.items.length === 0) {
    ElMessage.warning('购物车是空的')
    return
  }
  router.push('/orders/confirm')
}

onMounted(() => {
  fetchCart()
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

.product-name-link {
  color: #409eff;
  cursor: pointer;
}

.product-name-link:hover {
  text-decoration: underline;
}

.subtotal {
  font-weight: 600;
  color: #f56c6c;
}

.cart-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 24px;
  margin-top: 20px;
  padding: 16px 0;
  border-top: 1px solid #ebeef5;
}

.total-amount {
  font-size: 16px;
  color: #303133;
}

.amount-value {
  font-size: 24px;
  font-weight: 700;
  color: #f56c6c;
}
</style>
