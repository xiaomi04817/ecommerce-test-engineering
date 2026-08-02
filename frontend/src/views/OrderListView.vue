<template>
  <div class="order-list-container">
    <el-container>
      <el-header class="page-header">
        <div class="header-left">
          <el-button text @click="$router.push('/products')">
            <el-icon><ArrowLeft /></el-icon>
            返回商品列表
          </el-button>
          <h2>我的订单</h2>
        </div>
      </el-header>

      <el-main>
        <!-- Status Filter Tabs -->
        <div class="filter-tabs">
          <el-radio-group
            v-model="statusFilter"
            @change="handleFilterChange"
          >
            <el-radio-button value="">全部</el-radio-button>
            <el-radio-button value="PENDING">待支付</el-radio-button>
            <el-radio-button value="PAID">已支付</el-radio-button>
            <el-radio-button value="SHIPPED">已发货</el-radio-button>
            <el-radio-button value="RECEIVED">已收货</el-radio-button>
            <el-radio-button value="CANCELLED">已取消</el-radio-button>
            <el-radio-button value="REFUNDED">已退款</el-radio-button>
          </el-radio-group>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="loading-area">
          <el-skeleton :rows="4" animated />
        </div>

        <!-- Empty -->
        <el-empty v-else-if="orders.length === 0" description="暂无订单" />

        <!-- Order List -->
        <div v-else class="order-list">
          <el-card
            v-for="order in orders"
            :key="order.id"
            class="order-card"
            shadow="hover"
            @click="goToDetail(order.id)"
          >
            <div class="order-header">
              <span class="order-no">订单号：{{ order.orderNo }}</span>
              <el-tag :type="statusTagType(order.status)" size="small">
                {{ statusLabel(order.status) }}
              </el-tag>
            </div>
            <div class="order-body">
              <div class="order-items">
                <span
                  v-for="item in order.orderItems"
                  :key="item.id"
                  class="order-item-name"
                >
                  {{ item.productName }} x{{ item.quantity }}
                </span>
              </div>
              <div class="order-info">
                <div class="order-total">
                  &yen;{{ order.totalAmount.toFixed(2) }}
                </div>
                <div class="order-date">
                  {{ formatDate(order.createdAt) }}
                </div>
              </div>
            </div>
          </el-card>
        </div>

        <!-- Pagination -->
        <div v-if="total > 0" class="pagination-area">
          <el-pagination
            v-model:current-page="page"
            v-model:page-size="size"
            :page-sizes="[10, 20, 50]"
            :total="total"
            layout="total, prev, pager, next"
            @current-change="handlePageChange"
          />
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../utils/api'

const router = useRouter()
const orders = ref<any[]>([])
const loading = ref(false)
const page = ref(1)
const size = ref(20)
const total = ref(0)
const statusFilter = ref('')

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
  return `${y}-${m}-${day} ${h}:${min}`
}

async function fetchOrders() {
  loading.value = true
  try {
    const params: any = {
      page: page.value,
      size: size.value
    }
    if (statusFilter.value) {
      params.status = statusFilter.value
    }
    const res = await api.get('/orders', { params })
    const data = res.data.data
    orders.value = data.records || []
    total.value = data.total || 0
  } catch {
    orders.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function handleFilterChange() {
  page.value = 1
  fetchOrders()
}

function handlePageChange(val: number) {
  page.value = val
  fetchOrders()
}

function goToDetail(id: number) {
  router.push(`/orders/${id}`)
}

onMounted(() => {
  fetchOrders()
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

.filter-tabs {
  margin-bottom: 20px;
}

.loading-area {
  padding: 40px 0;
}

.order-card {
  margin-bottom: 12px;
  cursor: pointer;
  transition: transform 0.2s;
}

.order-card:hover {
  transform: translateY(-1px);
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 10px;
}

.order-no {
  font-size: 14px;
  color: #606266;
}

.order-body {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.order-items {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  flex: 1;
}

.order-item-name {
  color: #303133;
  font-size: 14px;
  background: #f5f7fa;
  padding: 2px 8px;
  border-radius: 4px;
}

.order-info {
  text-align: right;
  flex-shrink: 0;
  margin-left: 16px;
}

.order-total {
  font-size: 18px;
  font-weight: 700;
  color: #f56c6c;
}

.order-date {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.pagination-area {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style>
