<template>
  <div class="order-detail-container">
    <el-container>
      <el-header class="page-header">
        <div class="header-left">
          <el-button text @click="$router.push('/orders')">
            <el-icon><ArrowLeft /></el-icon>
            返回订单列表
          </el-button>
          <h2>订单详情</h2>
        </div>
      </el-header>

      <el-main>
        <!-- Loading -->
        <div v-if="loading" class="loading-area">
          <el-skeleton :rows="6" animated />
        </div>

        <!-- Not Found -->
        <el-empty v-else-if="!order" description="订单不存在" />

        <!-- Order Detail -->
        <template v-else>
          <!-- Order Status Header -->
          <el-card class="section-card">
            <div class="status-header">
              <div>
                <span class="label">订单号：</span>
                <span class="value">{{ order.orderNo }}</span>
              </div>
              <el-tag :type="statusTagType(order.status)" size="large">
                {{ statusLabel(order.status) }}
              </el-tag>
            </div>
            <div class="status-meta">
              <span>创建时间：{{ formatDate(order.createdAt) }}</span>
              <span v-if="order.updatedAt !== order.createdAt">
                更新时间：{{ formatDate(order.updatedAt) }}
              </span>
            </div>
          </el-card>

          <!-- Status Timeline -->
          <el-card class="section-card">
            <template #header>
              <h3>订单状态</h3>
            </template>
            <el-steps
              :active="currentStep"
              finish-status="success"
              align-center
            >
              <el-step title="待支付" description="等待付款" />
              <el-step title="已支付" description="付款完成" />
              <el-step title="已发货" description="商品已发出" />
              <el-step title="已收货" description="确认收货" />
            </el-steps>
            <div
              v-if="['CANCELLED', 'REFUNDED'].includes(order.status)"
              class="terminal-tag"
            >
              <el-tag type="danger" size="large">
                {{ order.status === 'CANCELLED' ? '订单已取消' : '订单已退款' }}
              </el-tag>
            </div>
          </el-card>

          <!-- Order Items -->
          <el-card class="section-card">
            <template #header>
              <h3>商品信息</h3>
            </template>
            <el-table :data="order.orderItems" border stripe>
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
              订单总额：
              <span class="total-amount">&yen;{{ order.totalAmount.toFixed(2) }}</span>
            </div>
          </el-card>

          <!-- Address Info -->
          <el-card v-if="addressInfo" class="section-card">
            <template #header>
              <h3>收货信息</h3>
            </template>
            <div class="address-info">
              <p>
                <span class="label">收件人：</span>
                {{ addressInfo.receiverName }}
                <span class="phone">{{ addressInfo.phone }}</span>
              </p>
              <p>
                <span class="label">地址：</span>
                {{ addressInfo.province }}{{ addressInfo.city
                }}{{ addressInfo.district }} {{ addressInfo.detail }}
              </p>
            </div>
          </el-card>

          <!-- Remark -->
          <el-card v-if="order.remark" class="section-card">
            <template #header>
              <h3>订单备注</h3>
            </template>
            <p class="remark-text">{{ order.remark }}</p>
          </el-card>

          <!-- Action Buttons -->
          <div v-if="actionButtons.length > 0" class="action-bar">
            <el-button
              v-for="btn in actionButtons"
              :key="btn.action"
              :type="btn.type"
              :loading="actionLoading === btn.action"
              :disabled="actionLoading !== null && actionLoading !== btn.action"
              @click="handleAction(btn.action)"
            >
              {{ btn.label }}
            </el-button>
          </div>
        </template>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../utils/api'

const route = useRoute()
const router = useRouter()
const order = ref<any>(null)
const loading = ref(false)
const actionLoading = ref<string | null>(null)

const statusStepMap: Record<string, number> = {
  PENDING: 0,
  PAID: 1,
  SHIPPED: 2,
  RECEIVED: 3,
  CANCELLED: -1,
  REFUNDED: -1
}

const currentStep = computed(() => {
  if (!order.value) return 0
  return statusStepMap[order.value.status] ?? 0
})

interface ActionButton {
  action: string
  label: string
  type: string
}

const actionButtons = computed<ActionButton[]>(() => {
  if (!order.value) return []
  const status = order.value.status
  switch (status) {
    case 'PENDING':
      return [
        { action: 'pay', label: '去支付', type: 'primary' },
        { action: 'cancel', label: '取消订单', type: 'default' }
      ]
    case 'PAID':
      return [
        { action: 'refund', label: '申请退款', type: 'warning' }
      ]
    case 'SHIPPED':
      return [
        { action: 'receive', label: '确认收货', type: 'success' },
        { action: 'refund', label: '申请退款', type: 'warning' }
      ]
    default:
      return []
  }
})

const addressInfo = computed(() => {
    if (!order.value) return null
    if (order.value.address) return order.value.address
    if (order.value.addressSnapshot) {
      try {
        return typeof order.value.addressSnapshot === 'string'
          ? JSON.parse(order.value.addressSnapshot)
          : order.value.addressSnapshot
      } catch { return null }
    }
    return null
  })

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    PENDING: '待支付',
    PAID: '已支付',
    SHIPPED: '已发货',
    RECEIVED: '已收货',
    CANCELLED: '已取消',
    REFUNDED: '已退款'
  }
  return map[status] || status
}

function statusTagType(status: string): string {
  const map: Record<string, string> = {
    PENDING: 'warning',
    PAID: 'success',
    SHIPPED: '',
    RECEIVED: 'info',
    CANCELLED: 'info',
    REFUNDED: 'danger'
  }
  return map[status] || ''
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  const sec = String(d.getSeconds()).padStart(2, '0')
  return `${y}-${m}-${day} ${h}:${min}:${sec}`
}

async function fetchOrder() {
  const id = route.params.id
  loading.value = true
  try {
    const res = await api.get(`/orders/${id}`)
    order.value = res.data.data
  } catch {
    order.value = null
  } finally {
    loading.value = false
  }
}

async function handleAction(action: string) {
  const confirmMessages: Record<string, { title: string; message: string }> = {
    pay: { title: '确认支付', message: '确认要支付此订单吗？' },
    cancel: { title: '取消订单', message: '确定要取消此订单吗？' },
    receive: { title: '确认收货', message: '确认已收到商品吗？' },
    refund: { title: '申请退款', message: '确定要申请退款吗？' }
  }

  const confirmMsg = confirmMessages[action]
  if (confirmMsg) {
    try {
      await ElMessageBox.confirm(confirmMsg.message, confirmMsg.title, {
        type: 'warning'
      })
    } catch {
      return
    }
  }

  actionLoading.value = action
  try {
    const res = await api.put(`/orders/${order.value.id}/status`, {
      action
    })
    order.value = res.data.data
    ElMessage.success('操作成功')
  } catch {
    // Error handled by interceptor
  } finally {
    actionLoading.value = null
  }
}

onMounted(() => {
  fetchOrder()
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

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.label {
  color: #909399;
}

.value {
  color: #303133;
  font-weight: 600;
}

.status-meta {
  display: flex;
  gap: 24px;
  margin-top: 8px;
  font-size: 13px;
  color: #909399;
}

.terminal-tag {
  text-align: center;
  margin-top: 16px;
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
}

.total-amount {
  font-size: 24px;
  font-weight: 700;
  color: #f56c6c;
}

.address-info p {
  margin: 0 0 8px;
  color: #303133;
}

.address-info .phone {
  color: #909399;
  font-size: 13px;
  margin-left: 12px;
}

.remark-text {
  margin: 0;
  color: #606266;
}

.action-bar {
  text-align: center;
  padding: 16px 0;
  display: flex;
  justify-content: center;
  gap: 16px;
}
</style>
